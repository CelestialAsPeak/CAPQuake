"""
data/connectors/ws/p2p_connector.py
P2PQuake WebSocket 连接器。
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject

from .base import WebSocketConnector


class P2pConnector(WebSocketConnector):
    """P2PQuake WebSocket 连接器。"""

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(
            source_id="p2p",
            urls=["wss://api.p2pquake.net/v2/ws"],
            auto_messages=["ping"],
            ping_interval=30,
            parent=parent,
        )
