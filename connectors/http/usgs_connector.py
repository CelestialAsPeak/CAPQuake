"""
data/connectors/http/usgs_connector.py
USGS HTTP 轮询连接器。
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject

from .base import HttpPoller


class UsgsConnector(HttpPoller):
    """USGS 全球地震数据连接器。"""

    USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(
            source_id="usgs",
            url=self.USGS_URL,
            interval_sec=30,
            retry_on_failure=True,
            parent=parent,
        )
