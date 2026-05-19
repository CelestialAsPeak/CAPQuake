"""
data/connectors/base.py
连接器抽象基类 + 状态定义。

所有连接器（WebSocket / HTTP / 测站）的公共接口。
连接器只做三件事:
  - 建立/维持连接
  - 收到原始数据 → json.loads → emit
  - 报告连接状态
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QObject, Signal


@dataclass
class ConnectorStatus:
    """连接器当前状态快照。不可变，每次变化发新实例。"""
    source_id: str                          # 数据源标识 "fan" / "wolfx" / ...
    state: str = "disconnected"             # connecting / connected / disconnected / error
    message: str = ""                       # 人类可读的状态描述
    last_active: Optional[datetime] = None  # 最后一次成功收到数据的时间


class DataSourceConnector(QObject):
    """
    连接器抽象基类。

    所有具体连接器继承此类，实现 start/stop 逻辑。
    子类在收到数据后调用 _emit_raw(data) 即可。
    """

    raw_data = Signal(object)               # json.loads 后的原始数据（多为 dict，也可能为 list）
    status_changed = Signal(ConnectorStatus)  # 状态变化通知

    def __init__(self, source_id: str, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._source_id = source_id
        self._status = ConnectorStatus(source_id=source_id)
        self._running = False

    # ── 属性 ──

    @property
    def source_id(self) -> str:
        return self._source_id

    @property
    def status(self) -> ConnectorStatus:
        return self._status

    # ── 子类必须实现 ──

    def start(self) -> None:
        """启动连接。子类在此发起网络连接或定时器。"""
        self._running = True

    def stop(self) -> None:
        """停止连接。子类在此关闭网络连接和定时器。"""
        self._running = False

    # ── 公共方法 ──

    def restart(self) -> None:
        """重启连接。"""
        self.stop()
        self.start()

    # ── 子类工具方法 ──

    def _set_status(self, state: str, message: str = "") -> None:
        """更新状态并发射信号。"""
        self._status = ConnectorStatus(
            source_id=self._source_id,
            state=state,
            message=message,
            last_active=self._status.last_active,
        )
        self.status_changed.emit(self._status)

    def _touch_active(self) -> None:
        """标记当前时间为最近活跃时间。"""
        self._status = ConnectorStatus(
            source_id=self._source_id,
            state=self._status.state,
            message=self._status.message,
            last_active=datetime.now(),
        )

    def _emit_raw(self, data: object) -> None:
        """发射原始数据。子类在收到并 json.loads 后调用此方法。"""
        self._touch_active()
        self.raw_data.emit(data)
