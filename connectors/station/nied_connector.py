"""
data/connectors/station/nied_connector.py
NIED Yahoo Japan 强震监控连接器（旧 Pygame 版 Yahoo 方案）。

数据源：
  - 站点列表: https://weather-kyoshin.east.edge.storage-yahoo.jp/SiteList/sitelist.json
    → {"items": [[lat, lon], [lat, lon], ...]}
  - 实时数据: https://weather-kyoshin.west.edge.storage-yahoo.jp/RealTimeData/{YYYYMMDD}/{YYYYMMDDHHMMSS}.json
    → {"realTimeData": {"intensity": "...", "dataTime": ...}}
    → intensity 是字符串，每个字符通过 ord(ch)-100 解码为 Yahoo 独自震度 0-20

与普通 HttpPoller 不同：
  1. 启动时先获取一次测站列表
  2. 每秒轮询实时数据，URL 随时间变化（含日期路径）
  3. 每次尝试多个时间点（当前秒往前推 5 秒），因为文件生成有延迟
"""

from __future__ import annotations

import logging
import random
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests

from PySide6.QtCore import QObject, QTimer

from ..base import DataSourceConnector

logger = logging.getLogger(__name__)

YAHOO_SITE_LIST_URL = "https://weather-kyoshin.east.edge.storage-yahoo.jp/SiteList/sitelist.json"
YAHOO_REALTIME_BASE_URL = "https://weather-kyoshin.west.edge.storage-yahoo.jp/RealTimeData"

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
]


def _make_headers() -> dict:
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,zh;q=0.6',
        'Referer': 'https://typhoon.yahoo.co.jp/weather/jp/earthquake/kyoshin/',
        'Origin': 'https://typhoon.yahoo.co.jp',
    }


class NiedConnector(DataSourceConnector):
    """NIED Yahoo Japan 强震监控连接器。"""

    REQUEST_TIMEOUT: float = 10.0
    POLL_INTERVAL: float = 1.0
    RETRY_SECONDS: int = 5  # 每次轮询尝试几个时间点（当前秒往前推）

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__("nied", parent)
        self._timer: Optional[QTimer] = None
        self._poll_lock = threading.Lock()
        self._session: Optional[requests.Session] = None

    # ── 生命周期 ──

    def start(self) -> None:
        super().start()
        self._set_status("connecting", "获取测站列表")

        thread = threading.Thread(
            target=self._fetch_site_list,
            daemon=True,
            name="nied-site-list",
        )
        thread.start()

        self._timer = QTimer(self)
        self._timer.setInterval(int(self.POLL_INTERVAL * 1000))
        self._timer.timeout.connect(self._poll)
        self._timer.start()

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        self._set_status("disconnected", "手动停止")
        super().stop()

    # ── Session ──

    def _get_session(self) -> requests.Session:
        """获取或创建 Session（每次换 User-Agent）。"""
        if self._session is not None:
            try:
                self._session.close()
            except Exception:
                pass
        self._session = requests.Session()
        self._session.headers.update(_make_headers())
        return self._session

    # ── 测站列表 ──

    def _fetch_site_list(self) -> None:
        try:
            session = self._get_session()
            resp = session.get(YAHOO_SITE_LIST_URL, timeout=self.REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            self._emit_raw({
                "type": "site_list",
                "data": data,
            })
            logger.info("[nied] 测站列表已获取 (%d 站点)", len(data.get("items", [])))
        except Exception as e:
            logger.warning("[nied] 测站列表获取失败: %s", e)

    # ── 实时数据轮询 ──

    def _poll(self) -> None:
        if not self._running:
            return
        if not self._poll_lock.acquire(blocking=False):
            return

        thread = threading.Thread(
            target=self._do_poll,
            daemon=True,
            name="nied-poll",
        )
        thread.start()

    def _do_poll(self) -> None:
        """后台线程：尝试多个时间点获取实时数据。"""
        if not self._running:
            self._poll_lock.release()
            return

        jst = timezone(timedelta(hours=9))
        now = datetime.now(jst)

        for offset in range(self.RETRY_SECONDS):
            if not self._running:
                self._poll_lock.release()
                return

            target = now - timedelta(seconds=offset)
            date_str = target.strftime("%Y%m%d")
            time_str = target.strftime("%Y%m%d%H%M%S")
            url = f"{YAHOO_REALTIME_BASE_URL}/{date_str}/{time_str}.json"

            try:
                if offset > 0 and offset % 3 == 0:
                    self._get_session()

                resp = self._get_session().get(url, timeout=self.REQUEST_TIMEOUT)

                if resp.status_code == 404:
                    continue
                resp.raise_for_status()

                data = resp.json()
                real_time_data = data.get("realTimeData", {})
                if not real_time_data.get("intensity"):
                    continue

                self._set_status("connected", "正常")
                self._emit_raw({
                    "type": "realtime",
                    "data": data,
                })
                self._poll_lock.release()
                return

            except requests.HTTPError as e:
                if e.response.status_code == 404:
                    continue
                logger.debug("[nied] HTTP 错误: %s", e)
            except Exception as e:
                logger.debug("[nied] 请求异常: %s", e)

        self._poll_lock.release()
