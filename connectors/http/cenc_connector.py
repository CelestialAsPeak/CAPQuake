"""
data/connectors/http/cenc_connector.py
CENC 中国地震台网 HTTP 轮询连接器。
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject

from .base import HttpPoller


class CencConnector(HttpPoller):
    """CENC 中国地震台网数据连接器。

    注：数据由 Wolfx 代转发，CENC 官方暂未提供稳定的公开 JSON API。
    """

    CENC_URL = "https://api.wolfx.jp/cenc_eqlist.json"

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(
            source_id="cenc",
            url=self.CENC_URL,
            interval_sec=30,
            retry_on_failure=True,
            parent=parent,
        )
