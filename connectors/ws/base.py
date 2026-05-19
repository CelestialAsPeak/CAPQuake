"""
data/connectors/ws/base.py
WebSocket 连接器基类。

封装 WebSocket 通用行为：
  - 多 URL 故障转移（CAPQuakeProK 模式）
  - 线性退避重连 3s → 4s → ... → 10s → 切 URL
  - 连接超时检测（10s 内无 on_open 判定超时）
  - 自动心跳（定时发送 init/auto messages）
  - 线程安全（websocket 跑在后台 threading.Thread）
"""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Optional

import websocket

from PySide6.QtCore import QObject, Signal

from ..base import DataSourceConnector

logger = logging.getLogger(__name__)


class WebSocketConnector(DataSourceConnector):
    """
    WebSocket 连接器基类。

    用法:
        class FanConnector(WebSocketConnector):
            def __init__(self, signal_bus):
                super().__init__(
                    source_id="fan",
                    urls=["wss://ws.fanstudio.tech/all",
                          "wss://ws.fanstudio.hk/all"],
                    init_messages=['{"type":"query"}'],
                )
                self._signal_bus = signal_bus
                self.raw_data.connect(signal_bus.raw_fan)
    """

    # 子类可重写这些默认值
    MIN_RETRY_INTERVAL: float = 3.0        # 最小重连间隔（秒）
    MAX_RETRY_INTERVAL: float = 10.0       # 最大重连间隔（秒）
    CONNECT_TIMEOUT: float = 10.0          # 连接超时（秒）

    def __init__(
        self,
        source_id: str,
        urls: list[str],
        init_messages: list[str] | None = None,
        auto_messages: list[str] | None = None,
        ping_interval: int = 30,
        parent: Optional[QObject] = None,
    ):
        super().__init__(source_id, parent)
        self._urls = urls
        self._init_messages = init_messages or []
        self._auto_messages = auto_messages or []
        self._ping_interval = ping_interval

        # 运行时状态
        self._url_index = 0
        self._retry_interval = self.MIN_RETRY_INTERVAL
        self._ws: Optional[websocket.WebSocketApp] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._heartbeat_seq = 0  # 递增，旧心跳线程发现不匹配时自动退出

    # ── 生命周期 ──

    def start(self) -> None:
        super().start()
        self._stop_event.clear()
        self._retry_interval = self.MIN_RETRY_INTERVAL
        self._url_index = 0
        self._connect()

    def stop(self) -> None:
        self._stop_event.set()
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None
        self._thread = None
        self._set_status("disconnected", "手动关闭")
        super().stop()

    # ── 内部：连接逻辑 ──

    @property
    def _current_url(self) -> str:
        return self._urls[self._url_index % len(self._urls)]

    def _connect(self) -> None:
        """创建 WebSocketApp 并在后台线程启动。"""
        url = self._current_url
        self._set_status("connecting", f"正在连接 {url}")

        self._ws = websocket.WebSocketApp(
            url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        self._thread = threading.Thread(
            target=self._run_ws,
            name=f"ws-{self._source_id}",
            daemon=True,
        )
        self._thread.start()

        # 另起一个线程检测连接超时
        if self.CONNECT_TIMEOUT > 0:
            timeout_thread = threading.Thread(
                target=self._watch_connect_timeout,
                name=f"ws-timeout-{self._source_id}",
                daemon=True,
            )
            timeout_thread.start()

    def _run_ws(self) -> None:
        """在后台线程中运行 WebSocket 事件循环。"""
        try:
            self._ws.run_forever(ping_interval=self._ping_interval)
        except Exception as e:
            logger.error("[%s] run_forever 异常: %s", self._source_id, e)

    def _watch_connect_timeout(self) -> None:
        """如果 CONNECT_TIMEOUT 秒内未收到 on_open，判定超时并断开。"""
        deadline = time.time() + self.CONNECT_TIMEOUT
        while time.time() < deadline and self._running:
            if self._status.state == "connected":
                return
            time.sleep(0.5)

        if self._status.state != "connected" and self._running:
            # 等待 1s 让 on_open 有机会更新状态，避免刚好在超时判定后触发的竞态
            self._stop_event.wait(1.0)
            if self._status.state == "connected":
                return
            logger.warning("[%s] 连接超时 %ss，主动断开", self._source_id, self.CONNECT_TIMEOUT)
            self._set_status("error", f"连接超时 ({self.CONNECT_TIMEOUT}s)")
            if self._ws:
                try:
                    self._ws.close()
                except Exception:
                    pass

    # ── WebSocket 回调（在后台线程执行）──

    def _on_open(self, ws) -> None:
        """连接建立。发送 init 消息，重置重试间隔。"""
        self._set_status("connected", f"已连接 {self._current_url}")
        self._retry_interval = self.MIN_RETRY_INTERVAL

        # 发送初始化消息
        for msg in self._init_messages:
            self._send(msg)

        # 启动心跳线程。递增序号，旧线程下次循环会因序号不匹配而退出。
        if self._auto_messages:
            self._heartbeat_seq += 1
            seq = self._heartbeat_seq
            t = threading.Thread(
                target=self._heartbeat_loop,
                args=(seq,),
                name=f"ws-heartbeat-{self._source_id}",
                daemon=True,
            )
            t.start()

    def _on_message(self, ws, message: str) -> None:
        """收到消息 → json.loads → emit。"""
        try:
            data = json.loads(message)
        except json.JSONDecodeError as e:
            logger.warning("[%s] JSON 解析失败: %s", self._source_id, e)
            self._set_status("error", f"JSON 解析失败: {e}")
            return

        self._emit_raw(data)

    def _on_error(self, ws, error) -> None:
        """WebSocket 错误。"""
        logger.debug("[%s] WebSocket 错误: %s", self._source_id, error)

    def _on_close(self, ws, close_status_code, close_msg) -> None:
        """连接关闭。如果未手动停止，触发自动重连。"""
        self._set_status("disconnected", f"连接关闭 ({close_msg or 'unknown'})")
        self._ws = None

        if self._running and not self._stop_event.is_set():
            self._schedule_reconnect()

    # ── 重连逻辑 ──

    def _schedule_reconnect(self) -> None:
        """线性退避重连：3s → 4s → 5s → ... → 10s → 切 URL。"""
        delay = self._retry_interval
        logger.info("[%s] %.1fs 后重连...", self._source_id, delay)

        self._retry_interval = min(
            self._retry_interval + 1.0,
            self.MAX_RETRY_INTERVAL,
        )

        # 如果已经达到最大间隔，尝试切换 URL
        if self._retry_interval >= self.MAX_RETRY_INTERVAL:
            self._url_index = (self._url_index + 1) % len(self._urls)
            self._retry_interval = self.MIN_RETRY_INTERVAL

        # 后台线程等待后重连，避免阻塞主线程
        threading.Thread(
            target=self._delayed_reconnect,
            args=(delay,),
            name=f"ws-reconnect-{self._source_id}",
            daemon=True,
        ).start()

    def _delayed_reconnect(self, delay: float) -> None:
        """等待 delay 秒后重连。"""
        if self._stop_event.wait(delay):
            return
        if self._running:
            self._connect()

    # ── 心跳 ──

    def _heartbeat_loop(self, seq: int) -> None:
        """后台心跳循环：每 10 秒发送 auto_messages。"""
        while self._running and not self._stop_event.is_set():
            if seq != self._heartbeat_seq:
                break  # 有新连接，旧线程退出
            if self._ws and self._status.state == "connected":
                for msg in self._auto_messages:
                    self._send(msg)
            self._stop_event.wait(10)

    def _send(self, msg: str) -> None:
        """发送消息（线程安全）。"""
        if self._ws and self._ws.sock and self._ws.sock.connected:
            try:
                self._ws.send(msg)
            except Exception as e:
                logger.debug("[%s] 发送失败: %s", self._source_id, e)
