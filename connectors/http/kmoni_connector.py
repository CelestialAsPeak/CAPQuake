"""
data/connectors/http/kmoni_connector.py
NIED Kmoni（强震监控）最新震源连接器。

数据源：http://www.kmoni.bosai.go.jp/webservice/server/pros/latest.json
返回 NIED 强震监控系统的最新震源信息。
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject

from .base import HttpPoller


class KmoniConnector(HttpPoller):
    """NIED Kmoni 最新震源数据连接器。"""

    KMONI_URL = "http://www.kmoni.bosai.go.jp/webservice/server/pros/latest.json"

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(
            source_id="kmoni",
            url=self.KMONI_URL,
            interval_sec=30,
            retry_on_failure=True,
            parent=parent,
        )
