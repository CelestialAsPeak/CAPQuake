"""
data/connectors/http/usgs_weekly_connector.py
USGS 全球地震周报连接器。

数据源：https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson
返回过去一周 M≥2.5 的全球地震列表（与 all_hour 互补）。
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject

from .base import HttpPoller


class UsgsWeeklyConnector(HttpPoller):
    """USGS 全球地震周报数据连接器。"""

    USGS_WEEKLY_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson"

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(
            source_id="usgs-weekly",
            url=self.USGS_WEEKLY_URL,
            interval_sec=300,
            retry_on_failure=True,
            parent=parent,
        )
