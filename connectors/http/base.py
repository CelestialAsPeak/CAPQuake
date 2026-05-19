"""
data/connectors/http/base.py
HTTP 轮询连接器基类。

封装 HTTP 轮询通用行为：
  - QTimer 定时触发请求（非阻塞，HTTP 在后台线程执行）
  - 请求超时处理（requests 的 timeout）
  - 非 200 状态码记录
  - 失败重试（可选）
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Optional

import requests

from PySide6.QtCore import QTimer, QObject, Signal

from ..base import DataSourceConnector

logger = logging.getLogger(__name__)


class HttpPoller(DataSourceConnector):
    """
    HTTP 轮询连接器基类。

    用法:
        class UsgsConnector(HttpPoller):
            def __init__(self, signal_bus):
                super().__init__(
                    source_id="usgs",
                    url="https://earthquake.usgs.gov/...",
                    interval_sec=30,
                )
                self._signal_bus = signal_bus
                self.raw_data.connect(signal_bus.raw_usgs)

    HTTP 请求在后台线程执行，不阻塞 Qt 事件循环。
    """

    REQUEST_TIMEOUT: float = 15.0       # HTTP 请求超时（秒）

    # 后台线程 → 主线程的结果信号
    _http_result = Signal(object)

    def __init__(
        self,
        source_id: str,
        url: str,
        interval_sec: int,
        headers: dict | None = None,
        retry_on_failure: bool = True,
        parent: Optional[QObject] = None,
    ):
        super().__init__(source_id, parent)
        self._url = url
        self._interval_sec = interval_sec
        self._headers = headers or {}
        self._retry_on_failure = retry_on_failure

        self._timer: Optional[QTimer] = None
        self._retry_timer: Optional[QTimer] = None
        self._poll_lock = threading.Lock()
        self._http_result.connect(self._on_http_result)

    # ── 生命周期 ──

    def start(self) -> None:
        super().start()
        self._set_status("connecting", f"等待首次轮询 {self._url}")

        self._timer = QTimer(self)
        self._timer.setInterval(self._interval_sec * 1000)
        self._timer.timeout.connect(self._poll)
        self._timer.start()

        # 立即执行一次
        self._poll()

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        if self._retry_timer:
            self._retry_timer.stop()
            self._retry_timer.deleteLater()
            self._retry_timer = None
        self._set_status("disconnected", "手动停止")
        super().stop()

    # ── 轮询 ──

    def _schedule_retry(self) -> None:
        """安排 5 秒后重试（可被 stop 取消）。"""
        if self._retry_timer:
            self._retry_timer.stop()
        self._retry_timer = QTimer(self)
        self._retry_timer.setSingleShot(True)
        self._retry_timer.setInterval(5000)
        self._retry_timer.timeout.connect(self._poll)
        self._retry_timer.start()

    def _poll(self) -> None:
        """触发一次异步 HTTP 请求（非阻塞）。"""
        if not self._running:
            return

        if not self._poll_lock.acquire(blocking=False):
            return  # 上次请求尚未完成，跳过本轮

        self._set_status("connecting", f"请求中 {self._url}")
        thread = threading.Thread(
            target=self._do_request,
            daemon=True,
            name=f"http-{self._source_id}",
        )
        thread.start()

    def _do_request(self) -> None:
        """在后台线程执行 HTTP 请求，结果通过信号送回主线程。"""
        try:
            resp = requests.get(
                self._url,
                headers=self._headers,
                timeout=self.REQUEST_TIMEOUT,
            )
            self._http_result.emit(("ok", resp.status_code, resp.text))
        except requests.Timeout:
            self._http_result.emit(("error", "timeout", None))
        except requests.ConnectionError as e:
            self._http_result.emit(("error", "connection_error", str(e)))
        except requests.RequestException as e:
            self._http_result.emit(("error", "request_error", str(e)))

    def _on_http_result(self, result: tuple) -> None:
        """在主线程处理 HTTP 结果。"""
        try:
            status = result[0]

            if status == "ok":
                _, resp_code, text = result

                if resp_code != 200:
                    logger.warning("[%s] HTTP %s", self._source_id, resp_code)
                    self._set_status("error", f"HTTP {resp_code}")
                    if self._retry_on_failure and 500 <= resp_code < 600:
                        self._schedule_retry()
                    return

                try:
                    data = json.loads(text)
                except json.JSONDecodeError as e:
                    logger.warning("[%s] JSON 解析失败: %s", self._source_id, e)
                    self._set_status("error", f"JSON 解析失败: {e}")
                    return

                self._set_status("connected", "正常")
                self._emit_raw(data)

            elif status == "error":
                _, err_type, err_msg = result
                if err_type == "timeout":
                    logger.warning("[%s] 请求超时 (%ss)", self._source_id, self.REQUEST_TIMEOUT)
                    self._set_status("error", f"请求超时 ({self.REQUEST_TIMEOUT}s)")
                    if self._retry_on_failure:
                        self._schedule_retry()
                elif err_type == "connection_error":
                    logger.warning("[%s] 连接失败: %s", self._source_id, err_msg)
                    self._set_status("error", f"连接失败: {err_msg}")
                    if self._retry_on_failure:
                        self._schedule_retry()
                elif err_type == "request_error":
                    logger.warning("[%s] 请求异常: %s", self._source_id, err_msg)
                    self._set_status("error", str(err_msg))
        finally:
            self._poll_lock.release()
