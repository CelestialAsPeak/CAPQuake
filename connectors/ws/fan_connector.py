"""
data/connectors/ws/fan_connector.py
FAN Studio WebSocket 连接器。
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject

from .base import WebSocketConnector


class FanConnector(WebSocketConnector):
    """FAN Studio WebSocket 连接器。"""

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(
            source_id="fan",
            urls=[
                "wss://ws.fanstudio.tech/all",
                "wss://ws.fanstudio.hk/all",
            ],
            init_messages=['{"type":"query"}'],
            ping_interval=30,
            parent=parent,
        )
