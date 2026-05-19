"""
data/connectors/station/kma_connector.py
KMA PEWS 韩国气象厅测站 WebSocket 连接器。

数据源：FAN Studio 的 /kma-station 端点，接收韩国气象厅实时测站 mmi 数据。
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject

from ..ws.base import WebSocketConnector


class KmaConnector(WebSocketConnector):
    """KMA PEWS 韩国气象厅测站数据连接器。"""

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(
            source_id="kma-station",
            urls=[
                "wss://ws.fanstudio.tech/kma-station",
                "wss://ws.fanstudio.hk/kma-station",
            ],
            ping_interval=30,
            parent=parent,
        )
