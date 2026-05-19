"""
data/connectors/http/p2p_history_connector.py
P2P 地震情報 HTTP 历史数据连接器。

数据源：https://api.p2pquake.net/v2/history
获取 P2P 地震情報（code 551），作为 WebSocket 的备用/补充。
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject

from .base import HttpPoller


class P2pHistoryConnector(HttpPoller):
    """P2P 地震情報 HTTP 历史数据连接器。"""

    P2P_HISTORY_URL = "https://api.p2pquake.net/v2/history?codes=551&limit=50"

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(
            source_id="p2p-history",
            url=self.P2P_HISTORY_URL,
            interval_sec=30,
            retry_on_failure=True,
            parent=parent,
        )
