"""
data/connectors/station/palert_connector.py
P-Alert 台湾测站连接器。

数据源：https://palert.earth.sinica.edu.tw/graphql/
使用 realtimePGA 查询获取各测站实时 PGA 值（gal），
原始响应为 {station_id: pga_gal} 格式字典。

注意：该服务器 SSL 证书不完整，需 verify=False。
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

import requests
import urllib3

from PySide6.QtCore import QObject, QTimer

from ..base import DataSourceConnector

# 禁用 SSL 警告（该服务器证书不完整）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

PALERT_GRAPHQL_URL = "https://palert.earth.sinica.edu.tw/graphql/"

PALERT_QUERY = """\
query ($recordTime: Float, $type: Int, $token: String) {
  realtimePGA(recordTime: $recordTime, type: $type, token: $token) {
    dataVals
    timestamp
  }
}
"""

PALERT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Content-Type": "application/json",
    "Origin": "https://palert.earth.sinica.edu.tw",
    "Referer": "https://palert.earth.sinica.edu.tw/realtime",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36"
    ),
}


class PalertConnector(DataSourceConnector):
    """P-Alert 台湾地震预警测站数据连接器。"""

    REQUEST_TIMEOUT: float = 10.0

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__("palert", parent)
        self._timer: Optional[QTimer] = None
        self._poll_lock = threading.Lock()

    # ── 生命周期 ──

    def start(self) -> None:
        super().start()
        self._set_status("connecting", "等待首次轮询 P-Alert")

        self._timer = QTimer(self)
        self._timer.setInterval(1000)  # 原项目 1s 轮询
        self._timer.timeout.connect(self._poll)
        self._timer.start()

        self._poll()

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        self._set_status("disconnected", "手动停止")
        super().stop()

    # ── 轮询 ──

    def _poll(self) -> None:
        """触发一次异步 GraphQL 查询（非阻塞）。"""
        if not self._running:
            return
        if not self._poll_lock.acquire(blocking=False):
            return

        thread = threading.Thread(
            target=self._do_poll,
            daemon=True,
            name="palert-poll",
        )
        thread.start()

    def _do_poll(self) -> None:
        """后台线程：执行 GraphQL 查询并 emit 数据。"""
        if not self._running:
            self._poll_lock.release()
            return

        payload = {
            "query": PALERT_QUERY,
            "variables": {
                "recordTime": 0,
                "token": "",
                "type": 0,
            },
        }

        try:
            resp = requests.post(
                PALERT_GRAPHQL_URL,
                json=payload,
                headers=PALERT_HEADERS,
                timeout=self.REQUEST_TIMEOUT,
                verify=False,
            )
        except requests.RequestException as e:
            logger.debug("[palert] 请求失败: %s", e)
            self._poll_lock.release()
            return

        if resp.status_code != 200:
            logger.debug("[palert] HTTP %s", resp.status_code)
            self._poll_lock.release()
            return

        try:
            data = resp.json()
        except Exception as e:
            logger.debug("[palert] JSON 解析失败: %s", e)
            self._poll_lock.release()
            return

        self._set_status("connected", "正常")
        self._emit_raw(data.get("data", {}))
        self._poll_lock.release()
