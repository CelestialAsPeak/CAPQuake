"""
data/connectors/ws/wolfx_connector.py
Wolfx WebSocket 连接器。

订阅所有 EEW 子源（jma/sc/cenc/fj/cwa），
收到 type=heartbeat 时自动回复 pong。
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from PySide6.QtCore import QObject

from .base import WebSocketConnector

logger = logging.getLogger(__name__)


class WolfxConnector(WebSocketConnector):
    """Wolfx WebSocket 连接器。"""

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(
            source_id="wolfx",
            urls=["wss://ws-api.wolfx.jp/all_eew"],
            init_messages=[
                "query_jmaeew",
                "query_sceew",
                "query_cenceew",
                "query_fjeew",
                "query_cwaeew",
            ],
            ping_interval=30,
            parent=parent,
        )

    # ── 覆写：处理 Wolfx 心跳协议 ──

    def _on_message(self, ws, message: str) -> None:
        """收到消息。拦截 heartbeat 并回复 pong，其余直接 emit 避免父类重复 json.loads。"""
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return

        # Wolfx 心跳：回复 pong，不 emit
        if data.get("type") == "heartbeat":
            timestamp = data.get("timestamp", "")
            try:
                ws.send(json.dumps({"type": "pong", "timestamp": timestamp}))
            except Exception:
                pass
            return

        # 直接 emit 已解析数据，不走父类 _on_message 的二次 json.loads
        self._emit_raw(data)
