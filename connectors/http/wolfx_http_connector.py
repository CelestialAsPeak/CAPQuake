"""
data/connectors/http/wolfx_http_connector.py
Wolfx EEW HTTP 备用轮询连接器。

数据源：Wolfx 各子源独立 JSON 端点
当 WebSocket 断连时作为备用，轮询 5 个 EEW 子源。
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Optional

import requests

from PySide6.QtCore import QObject, QTimer

from ..base import DataSourceConnector

logger = logging.getLogger(__name__)

# Wolfx 5 个子源的 HTTP 备用 URL
WOLFX_HTTP_SUB_SOURCES: dict[str, str] = {
    "jma": "https://api.wolfx.jp/jma_eew.json",
    "sc": "https://api.wolfx.jp/sc_eew.json",
    "cenc": "https://api.wolfx.jp/cenc_eew.json",
    "fj": "https://api.wolfx.jp/fj_eew.json",
    "cwa": "https://api.wolfx.jp/cwa_eew.json",
}


class WolfxHttpConnector(DataSourceConnector):
    """Wolfx EEW HTTP 备用连接器。

    轮询 5 个子源的 JSON 端点，每个子源独立 emit 原始数据。
    """

    REQUEST_TIMEOUT: float = 15.0

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__("wolfx-http", parent)
        self._timer: Optional[QTimer] = None
        self._poll_lock = threading.Lock()

    def start(self) -> None:
        super().start()
        self._set_status("connecting", "等待首次轮询 Wolfx HTTP")

        self._timer = QTimer(self)
        self._timer.setInterval(30000)  # 30 秒轮询一次
        self._timer.timeout.connect(self._poll_all)
        self._timer.start()

        self._poll_all()

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        self._set_status("disconnected", "手动停止")
        super().stop()

    def _poll_all(self) -> None:
        """在后台线程轮询所有子源，不阻塞主线程。"""
        if not self._running:
            return
        if not self._poll_lock.acquire(blocking=False):
            return

        self._set_status("connecting", "轮询 Wolfx HTTP 子源")
        thread = threading.Thread(
            target=self._do_poll_all,
            daemon=True,
            name="wolfx-http-poll",
        )
        thread.start()

    def _do_poll_all(self) -> None:
        """后台线程：轮询所有子源并 emit 数据。"""
        if not self._running:
            self._poll_lock.release()
            return

        any_ok = False
        for sub_source, url in WOLFX_HTTP_SUB_SOURCES.items():
            if not self._running:
                break
            if self._poll_one(sub_source, url):
                any_ok = True

        if any_ok:
            self._set_status("connected", "正常")
        self._poll_lock.release()

    def _poll_one(self, sub_source: str, url: str) -> bool:
        """请求单个子源并 emit 原始数据。返回是否成功。"""
        try:
            resp = requests.get(url, timeout=self.REQUEST_TIMEOUT)
        except requests.RequestException as e:
            logger.debug("[wolfx-http] %s 请求失败: %s", sub_source, e)
            return False

        if resp.status_code != 200:
            logger.debug("[wolfx-http] %s HTTP %s", sub_source, resp.status_code)
            return False

        try:
            data = resp.json()
        except Exception as e:
            logger.debug("[wolfx-http] %s JSON 解析失败: %s", sub_source, e)
            return False

        self._emit_raw({
            "sub_source": sub_source,
            "data": data,
        })
        return True
