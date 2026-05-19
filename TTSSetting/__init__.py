"""
core_service/parsers/__init__.py
解析器子包。

所有解析器注册至 ParserRegistry。
"""

from __future__ import annotations

from .base import BaseParser, ParserRegistry
from .fan_parser import FanParser
from .wolfx_parser import WolfxParser
from .p2p_parser import P2pParser
from .usgs_parser import UsgsParser
from .cenc_parser import CencParser
from .jma_parser import JmaParser
from .kmoni_parser import KmoniParser
from .station_parser import StationParser

__all__ = [
    "BaseParser", "ParserRegistry",
    "FanParser", "WolfxParser", "P2pParser",
    "UsgsParser", "CencParser", "JmaParser",
    "KmoniParser", "StationParser",
]
