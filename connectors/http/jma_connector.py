"""
data/connectors/http/jma_connector.py
JMA 日本气象厅 HTTP 轮询连接器。
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject

from .base import HttpPoller


class JmaConnector(HttpPoller):
    """JMA 日本地震数据连接器。

    注：数据由 Wolfx 代转发，JMA 官方暂未提供稳定的公开 JSON API。
    """

    JMA_URL = "https://api.wolfx.jp/jma_eqlist.json"

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(
            source_id="jma",
            url=self.JMA_URL,
            interval_sec=30,
            retry_on_failure=True,
            parent=parent,
        )
