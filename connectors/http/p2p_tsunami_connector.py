"""
data/connectors/http/p2p_tsunami_connector.py
P2P 海啸预报 HTTP 连接器。

数据源：https://api.p2pquake.net/v2/history
获取 P2P 海啸预报（code 552）。
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject

from .base import HttpPoller


class P2pTsunamiConnector(HttpPoller):
    """P2P 海啸预报数据连接器。"""

    P2P_TSUNAMI_URL = "https://api.p2pquake.net/v2/history?codes=552&limit=1"

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(
            source_id="p2p-tsunami",
            url=self.P2P_TSUNAMI_URL,
            interval_sec=60,
            retry_on_failure=True,
            parent=parent,
        )
