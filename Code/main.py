"""
================================================================================
写在前面
================================================================================
CAPQuake 是一个基于 Python + Pygame 构建的桌面端地震资讯整合应用程序。
此项目的代码将取决于编写进度逐步开源。
此项目数据源来自于多个不同的API。
立刻观看目前项目编写进度/运行效果：https://space.bilibili.com/1680353559



================================================================================
CAPQuake 主程序入口模块
================================================================================

模块名称: main
版本: v0.2.0
最后更新: 2026-04-02
维护者: CelestialAsPeak

概述
----
本模块是 CAPQuake 地震预警应用程序的启动入口和核心控制器。
它负责整个应用程序的生命周期管理，包括初始化、事件循环、数据流协调和资源清理。

================================================================================
编程规范 (Coding Standards)
================================================================================

1. 代码风格
   - 遵循 PEP 8 规范，使用 4 空格缩进，行长度不超过 120 字符。
   - 类名使用 PascalCase，方法名和变量名使用 snake_case。
   - 常量定义在 config.py 中，使用 UPPER_SNAKE_CASE。

2. 文档字符串 (Docstring)
   - 所有公共模块、类、函数必须包含 docstring。
   - 使用三重双引号，遵循 Google 风格（参见下方示例）。
   - 内容应包含：功能描述、参数说明（类型+含义）、返回值、可能引发的异常、
     依赖的模块/全局变量、工作流程简述。

3. 类型注解
   - 所有函数参数和返回值必须添加类型注解。
   - 使用 typing 模块中的 Optional, List, Tuple, Dict, Any 等。

4. 错误处理
   - 捕获异常时，应明确异常类型，避免裸露的 except:。
   - 关键操作（如数据获取、文件读写）必须有异常处理并记录日志。

5. 线程安全
   - 共享数据（如 state 中的队列、事件列表）必须使用线程安全机制（queue.Queue、threading.Lock）。
   - 数据源线程应设置为 daemon=True，但主程序退出前应显式停止。

6. 日志与调试
   - 使用 print() 输出关键状态信息，格式为 "[模块名] 信息内容"。
   - 调试信息使用 "[DEBUG]" 前缀，正式发布时可屏蔽。

7. 性能考虑
   - 渲染循环中避免频繁创建对象，尽量复用 Surface 和缓存。
   - 瓦片加载使用异步线程池，避免阻塞主线程。

8. 国际化
   - 用户可见字符串建议使用英文或中文，本项目以中文为主。

================================================================================
工作流 (Workflow)
================================================================================

程序启动后的完整执行流程如下（按时间顺序）：

1. 实例化 CAPQuakeApp
   ├─ _init_pygame()        : 初始化 Pygame 环境、创建窗口、设置地图投影和瓦片管理器
   ├─ _init_components()    : 加载字体，构建 UI 组件树，启动数据监控器和数据源线程
   ├─ _preload_tiles()      : 预加载低级别瓦片和当前视口瓦片，提升地图滚动体验
   └─ _log_initialization() : 输出初始化完成日志，便于调试

2. 进入主循环 run()
   ┌─────────────────────────────────────────────────────────────────────┐
   │ 每帧 (目标 60 FPS) 重复执行以下步骤：                                 │
   │ ├─ _handle_events()      : 轮询 Pygame 事件队列，处理鼠标、键盘、窗口 │
   │ ├─ _process_queues()     : 从线程安全队列中取出地震/预警数据并合并    │
   │ ├─ _auto_jump_to_earthquake() : 新地震首次出现时自动跳转视野        │
   │ ├─ _update_components()  : 更新 EEW 管理器（过期清理）、烈度图层、视野跟随│
   │ ├─ _update_tile_level()  : 当目标瓦片级别全部缓存后，切换当前级别    │
   │ └─ _render()             : 绘制地图底图 + UI 叠加层并刷新屏幕        │
   └─────────────────────────────────────────────────────────────────────┘

3. 退出程序时调用 shutdown()
   ├─ 停止所有数据源线程 (FAN, P2P, USGS, CENC, JMA)
   ├─ 停止所有监控器 (PGA, S-net, 测站, Yahoo, KMA)
   ├─ 停止波形显示后台线程
   └─ 调用 pygame.quit() 和 sys.exit() 释放资源

================================================================================
模块说明 (Module Description)
================================================================================

本模块依赖以下核心子模块（按功能分组）：

【配置与状态】
- config          : 全局配置参数（窗口尺寸、颜色、数据源开关、阈值等）
- state           : 运行时共享状态（地图参数、事件列表、队列、视角等）

【地图核心】
- map_utils       : 地图投影、经纬度/屏幕坐标转换、视口计算、瓦片索引
- tile_manager    : 异步瓦片加载、LRU 缓存、备用机制（低级别裁剪）

【数据流】
- data_fetchers   : 多源数据获取器（FAN WebSocket, P2P, USGS, CENC, JMA, ICL, Wolfx）
- data_merger     : 地震事件合并（精确匹配、相似匹配、优先级、数据源记录）

【绘制】
- draw            : 地图和 UI 的绘制逻辑（分离为 map_surface 和 UI overlay）
- eew_wave_enhanced : 增强版预警波绘制（P波/S波、震中叉号）

【预警系统】
- eew_manager     : 预警生命周期管理（过期清理、动态存活时间）、自动视野跟随算法
- eew_popup       : 预警弹窗组件（多弹窗、烈度矩形、文字裁剪）

【UI 组件】
- time_display    : 右下角时间与 API 状态显示组件
- function_buttons: 右上角功能按钮区（模式切换、视角保存/恢复、缩放等）
- jma_intensity_display : JMA 震度观测点列表面板（分组、换行、高度自适应）
- excel_intensity_reader/display : Excel 烈度数据读取与展示（区域填充、速报列表）
- waveform_display: 实时波形图组件（基于 ObsPy，多台站）
- max_intensity_display : S-net 和 KMA 最大烈度面板（双列卡片）

【监控器】
- station.station_monitor   : 静态台站监控器（从 JSON 加载）
- station.yahoo_kyoshin_monitor : Yahoo 强震监控（实时震度 0-20）
- station.kma_monitor       : KMA PEWS 测站监控（WebSocket, MMI 值）
- station.snet_monitor      : S-net 海底测站监控（瓦片图像解析）
- station.global_pga_monitor: 全球 PGA 监控（基于 ObsPy 波形）

【辅助】
- intensity_layer : 烈度速报图层（日本/中国行政区填色，支持 TopoJSON 动态校准）
- test_eew_generator : 测试预警生成器（用于 F1/F2/F3 调试）

================================================================================
变量说明 (Variable Descriptions)
================================================================================

CAPQuakeApp 类的主要实例变量：

- screen (pygame.Surface)            : 主显示表面，由 pygame.display.set_mode() 创建
- clock (pygame.time.Clock)          : 帧率控制器，用于限制循环速度 (目标 60 FPS)
- app_state (AppState)               : 应用程序状态 (RUNNING / EXIT)
- show_list (bool)                   : 是否显示右侧地震列表（空格键切换）
- ui (UIContext)                     : 聚合所有 UI 组件（字体、时间显示、按钮、波形等）
- monitors (MonitorContext)          : 聚合所有数据监控器（测站、Yahoo、KMA、PGA 等）
- eew_manager (EEWManager)           : 预警管理器，负责预警的生命周期、视野跟随
- intensity_layer (IntensityLayer)   : 烈度速报图层（可选，由 config.INTENSITY_LAYER_ENABLED 控制）
- map_surface (pygame.Surface)       : 地图绘制表面（与 UI 分离，用于过渡效果和性能优化）

================================================================================
接口说明 (Interface Description)
================================================================================

1. 模块级公共函数（供其他模块或测试调用）：

   prefetch_viewport_tiles(tile_manager, screen_width, screen_height, level)
       预加载当前视口及周围一圈的瓦片，提升滚动体验。
       依赖: map_utils.tiles_in_viewport, map_utils.tile_to_bbox, map_utils.lonlat_to_screen

   restore_custom_view() -> bool
       恢复到用户保存的视角，成功返回 True，否则 False。
       依赖: state.SAVED_CUSTOM_VIEW, map_utils.update_map_range_by_zoom, map_utils.calc_tile_level

   load_fonts() -> FontContext
       加载所有字体，若自定义字体不可用则回退到系统字体。
       依赖: config.FONT_PATH, pygame.font.Font

   create_waveform_displays(font_small) -> List[波形对象]
       创建所有波形显示对象（按优先级排序）。
       依赖: waveform_display 中各台站类

   start_data_fetchers(time_display, eew_manager) -> List[Thread]
       启动所有数据源线程，返回线程列表。
       依赖: data_fetchers 中的各个获取器类, config.P2P_HISTORY_ENABLED

   stop_data_fetchers(fetchers)
       停止所有数据源线程，捕获异常避免崩溃。

2. CAPQuakeApp 类公共方法：

   run()
       启动主循环，程序开始运行。内部调用 _handle_events, _process_queues, _update_components, _render 等。

   shutdown()
       清理资源，停止所有线程，退出程序。应在 try-finally 块中调用。

3. 与外部模块的交互接口（通过 state 模块和队列）：

   state.earthquake_queue (queue.Queue)
       接收来自 data_fetchers 的地震事件原始数据（生产-消费者模式）。
       消费者: data_merger.merge_earthquake

   state.eew_queue (queue.Queue)
       接收预警原始数据。
       消费者: eew_manager.update

   state.earthquake_events (list)
       合并后的地震事件列表，由 data_merger 维护。
       供 draw.py 和 jma_intensity_display.py 读取。

   state.tile_manager (TileManager)
       瓦片管理器实例，供 draw.draw_map_to_surface 和 _update_tile_level 使用。

   state.MAP_CENTER_LON, MAP_CENTER_LAT, MAP_ZOOM_FACTOR
       地图状态变量，供 map_utils 读写，实现地图平移和缩放。

   state.EPICENTER_MODE (int)
       震中绘制模式（0=所有事件，1=各源最新震中），由功能按钮切换。

   state.SAVED_CUSTOM_VIEW (tuple)
       保存的用户视角 (lon, lat, zoom)，用于恢复。

   state.LAST_USER_INTERACTION_TIME (float)
       最后一次用户交互的时间戳，用于 EEW 跟随模式的冷却判断。

================================================================================
注意事项 (Notes)
================================================================================

- 所有数据源线程均设置为 daemon=True，但 shutdown() 中仍显式调用 stop() 确保优雅退出。
- 事件处理中会更新 state.LAST_USER_INTERACTION_TIME，用于 EEW 跟随模式的冷却判断。
- 瓦片级别切换采用“目标级别全部缓存后再切换”的策略，避免画面闪烁。
- 程序崩溃时 faulthandler 会输出详细堆栈，便于调试。
- 配置文件 config.py 中的路径（如 FONT_PATH, TILE_DIR）需根据实际环境修改。

================================================================================
"""

import pygame
import sys
import queue
import time
import math
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum, auto
from threading import Thread
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

# 导入项目内部模块
import config
import state
import map_utils
import draw
import data_fetchers
import data_merger
from time_display import TimeDisplay
from function_buttons import FunctionButtonArea
from jma_intensity_display import JMAIntensityDisplay
from eew_manager import EEWManager
from eew_popup import EEWPopup
from waveform_display import (
    KamchatkaWaveformDisplay, TaiwanWaveformDisplay,
    TongaWaveformDisplay, TokyoWaveformDisplay, AomoriWaveformDisplay,
    AlbuquerqueWaveformDisplay, CollegeWaveformDisplay, KongsbergWaveformDisplay,
    PohakuloaWaveformDisplay, TucsonWaveformDisplay, YuzhnoSakhalinskWaveformDisplay,
    NewZealandWaveformDisplay, FijiWaveformDisplay, PapuaNewGuineaWaveformDisplay,
    AleutianWaveformDisplay
)
from station.station_monitor import StationMonitor
from tile_manager import TileManager
from intensity_layer import IntensityLayer
from station.yahoo_kyoshin_monitor import YahooKyoshinMonitor
from excel_intensity_reader import ExcelIntensityReader
from excel_intensity_display import ExcelIntensityDisplay
from station.kma_monitor import KMAMonitor
from station.global_pga_monitor import GlobalPgaMonitor
from station.snet_monitor import SnetMonitor
from max_intensity_display import MaxIntensityDisplay
from test_eew_generator import generate_cenc_test, generate_jma_test, generate_cwa_test
import faulthandler


# 启用故障处理器，便于调试崩溃
faulthandler.enable()

# ============================================================================
# 枚举定义
# ============================================================================

class AppState(Enum):
    """应用程序运行状态枚举"""
    RUNNING = auto()   # 正常运行
    EXIT = auto()      # 退出


class ButtonAction(Enum):
    """功能按钮动作枚举，便于事件处理"""
    MODE_SWITCH = "模式切换"
    SAVE_VIEW = "保存视角"
    RESTORE_VIEW = "跳转视角"
    # 如需扩展其他按钮，在此添加


# ============================================================================
# 数据类（用于组织组件）
# ============================================================================

@dataclass
class FontContext:
    """
    字体上下文，将所有字体对象集中存放，便于传递。

    属性:
        font_small: 小号字体（用于辅助文字）
        font_button_line1: 按钮第一行字体（软件名）
        font_button_line2: 按钮第二行字体（时间）
        font_line1: 地震列表第一行字体（震源地区）
        font_line2: 地震列表第二行字体（发震时间）
        font_line3: 地震列表第三行字体（震级+深度）
        font_source: 数据源字体
        font_intensity: 烈度数字字体
    """
    font_small: pygame.font.Font
    font_button_line1: pygame.font.Font
    font_button_line2: pygame.font.Font
    font_line1: pygame.font.Font
    font_line2: pygame.font.Font
    font_line3: pygame.font.Font
    font_source: pygame.font.Font
    font_intensity: pygame.font.Font


@dataclass
class UIContext:
    """
    UI 组件上下文，聚合所有可视组件，减少 __init__ 参数数量。

    属性:
        fonts: 字体上下文
        time_display: 时间显示组件
        function_buttons: 功能按钮区
        jma_intensity_display: JMA 震度情报组件
        excel_intensity_display: Excel 烈度显示组件
        eew_popup: 预警弹窗组件
        waveforms: 波形显示对象列表
        max_intensity_display: 最大烈度显示面板
    """
    fonts: FontContext
    time_display: TimeDisplay
    function_buttons: FunctionButtonArea
    jma_intensity_display: JMAIntensityDisplay
    excel_intensity_display: ExcelIntensityDisplay
    eew_popup: EEWPopup
    waveforms: List[Any]   # 波形显示对象列表
    max_intensity_display: MaxIntensityDisplay


@dataclass
class MonitorContext:
    """
    监控器上下文，包含所有数据监控器和数据源线程。

    属性:
        station_monitor: 静态测站监控器
        yahoo_monitor: Yahoo 强震监控器
        kma_monitor: KMA 测站监控器
        snet_monitor: S-net 海底测站监控器（可选）
        pga_monitor: 全球 PGA 监控器（可选）
        fetchers: 数据源线程列表
    """
    station_monitor: StationMonitor
    yahoo_monitor: YahooKyoshinMonitor
    kma_monitor: KMAMonitor
    snet_monitor: Optional[SnetMonitor]
    pga_monitor: Optional[GlobalPgaMonitor]
    fetchers: List[Thread]   # 所有数据源线程


# ============================================================================
# 辅助函数（独立工具）
# ============================================================================

def prefetch_viewport_tiles(
    tile_manager: TileManager,
    screen_width: int,
    screen_height: int,
    level: int
) -> None:
    """
    预加载当前视口及周围一圈的瓦片，提升滚动体验。

    工作原理:
        1. 根据当前屏幕尺寸和地图投影，计算视口覆盖的瓦片范围（使用标准级别 level+2）。
        2. 向外扩展一圈，避免滚动时出现空白瓦片。
        3. 为每个瓦片计算其在屏幕上渲染时的目标尺寸（通过四个角点投影得到）。
        4. 将 (level, x, y, target_w, target_h) 提交给瓦片管理器的预取队列。

    工作流:
        调用 → tiles_in_viewport → 扩展范围 → 遍历瓦片 → 计算地理边界 → 投影到屏幕 → 获取尺寸 → tile_manager.prefetch

    依赖:
        map_utils.tiles_in_viewport, map_utils.tile_to_bbox, map_utils.lonlat_to_screen
        tile_manager.prefetch

    参数:
        tile_manager: 瓦片管理器实例
        screen_width: 屏幕宽度（像素）
        screen_height: 屏幕高度（像素）
        level: 目标瓦片级别（新级别，0~MAX_ZOOM_LEVEL）
    """
    if not tile_manager:
        return

    # 计算在标准级别 (level+2) 下视口覆盖的瓦片范围
    z_std = level + 2
    x_min, x_max, y_min, y_max = map_utils.tiles_in_viewport(screen_width, screen_height, z_std)

    # 向外扩展一圈，避免滚动时出现空白
    x_min = max(0, x_min - 1)
    x_max = min(2**z_std - 1, x_max + 1)
    y_min = max(0, y_min - 1)
    y_max = min(2**z_std - 1, y_max + 1)

    prefetch_list = []
    for xt in range(x_min, x_max + 1):
        for yt in range(y_min, y_max + 1):
            # 获取该瓦片的地理边界
            lon_min_t, lat_min_t, lon_max_t, lat_max_t = map_utils.tile_to_bbox(z_std, xt, yt)
            # 计算四个角点的屏幕坐标
            corners_t = [
                map_utils.lonlat_to_screen(lon_min_t, lat_max_t, screen_width, screen_height),
                map_utils.lonlat_to_screen(lon_max_t, lat_max_t, screen_width, screen_height),
                map_utils.lonlat_to_screen(lon_max_t, lat_min_t, screen_width, screen_height),
                map_utils.lonlat_to_screen(lon_min_t, lat_min_t, screen_width, screen_height)
            ]
            xs = [p[0] for p in corners_t]
            ys = [p[1] for p in corners_t]
            rect_t = pygame.Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
            # 只有面积大于0的瓦片才需要预加载
            if rect_t.width > 0 and rect_t.height > 0:
                prefetch_list.append((level, xt, yt, rect_t.width, rect_t.height))

    # 提交预加载请求（每帧最多处理30个，避免卡顿）
    tile_manager.prefetch(prefetch_list, max_per_frame=30)


def restore_custom_view() -> bool:
    """
    恢复到用户保存的自定义视角。

    工作原理:
        从 state.SAVED_CUSTOM_VIEW 读取三元组 (经度, 纬度, 缩放因子)，
        分别更新 state.MAP_CENTER_LON, MAP_CENTER_LAT, MAP_ZOOM_FACTOR，
        然后调用 map_utils.update_map_range_by_zoom() 重新计算地图边界，
        并重新计算目标瓦片级别。

    工作流:
        检查 SAVED_CUSTOM_VIEW → 读取坐标和缩放 → 更新 state → 更新地图范围 → 计算瓦片级别

    依赖:
        state.SAVED_CUSTOM_VIEW, map_utils.update_map_range_by_zoom, map_utils.calc_tile_level

    返回:
        bool: 成功恢复返回 True，否则返回 False（未保存任何视角）
    """
    if state.SAVED_CUSTOM_VIEW is None:
        print("[自动恢复] 未保存任何视角，无法恢复")
        return False

    lon, lat, zoom = state.SAVED_CUSTOM_VIEW
    state.MAP_CENTER_LON = lon
    state.MAP_CENTER_LAT = lat
    state.MAP_ZOOM_FACTOR = zoom
    map_utils.update_map_range_by_zoom()
    state.target_tile_level = map_utils.calc_tile_level(zoom)
    print(f"[自动恢复] 已恢复保存的视角: 中心({lon:.2f}, {lat:.2f}) 缩放{zoom:.2f}")
    return True


def load_fonts() -> FontContext:
    """
    加载所有字体，如果自定义字体不可用则回退到系统字体。

    工作原理:
        尝试使用 pygame.font.Font 从 config.FONT_PATH 加载自定义字体（通常是微软雅黑）。
        若加载失败（文件不存在或格式错误），捕获异常并使用 pygame.font.SysFont 加载系统字体 'simhei'（黑体）。
        最终将所有字体对象封装到 FontContext 数据类中返回。

    工作流:
        尝试加载自定义字体 → 若失败则加载系统字体 → 构建 FontContext

    依赖:
        config.FONT_PATH, config.*_FONT_SIZE 常量

    返回:
        FontContext: 包含所有字体的数据类对象
    """
    try:
        font_small = pygame.font.Font(config.FONT_PATH, 20)
        font_button_line1 = pygame.font.Font(config.FONT_PATH, config.LINE1_BUTTON_FONT_SIZE)
        font_button_line2 = pygame.font.Font(config.FONT_PATH, config.LINE2_BUTTON_FONT_SIZE)
        font_line1 = pygame.font.Font(config.FONT_PATH, config.LINE1_FONT_SIZE)
        font_line2 = pygame.font.Font(config.FONT_PATH, config.LINE2_FONT_SIZE)
        font_line3 = pygame.font.Font(config.FONT_PATH, config.LINE3_FONT_SIZE)
        font_source = pygame.font.Font(config.FONT_PATH, config.SOURCE_FONT_SIZE)
        font_intensity = pygame.font.Font(config.FONT_PATH, config.INTENSITY_FONT_SIZE)
    except Exception as e:
        print(f"[系统警告] 字体加载失败: {e}，使用系统默认字体")
        font_small = pygame.font.SysFont('simhei', 20)
        font_button_line1 = pygame.font.SysFont('simhei', config.LINE1_BUTTON_FONT_SIZE)
        font_button_line2 = pygame.font.SysFont('simhei', config.LINE2_BUTTON_FONT_SIZE)
        font_line1 = pygame.font.SysFont('simhei', config.LINE1_FONT_SIZE)
        font_line2 = pygame.font.SysFont('simhei', config.LINE2_FONT_SIZE)
        font_line3 = pygame.font.SysFont('simhei', config.LINE3_FONT_SIZE)
        font_source = pygame.font.SysFont('simhei', config.SOURCE_FONT_SIZE)
        font_intensity = pygame.font.SysFont('simhei', config.INTENSITY_FONT_SIZE)

    return FontContext(
        font_small=font_small,
        font_button_line1=font_button_line1,
        font_button_line2=font_button_line2,
        font_line1=font_line1,
        font_line2=font_line2,
        font_line3=font_line3,
        font_source=font_source,
        font_intensity=font_intensity
    )


def create_waveform_displays(font_small: pygame.font.Font) -> List[Any]:
    """
    创建所有波形显示对象，并按优先级排序。

    工作原理:
        实例化预定义的波形显示类列表（每个类继承自 BaseWaveformDisplay）。
        按优先级排列（越靠前的波形显示在屏幕越上方）。
        为每个波形对象设置字体。

    工作流:
        创建对象列表 → 遍历设置字体 → 返回列表

    依赖:
        waveform_display 模块中的各台站类

    参数:
        font_small: 用于标签的小字体

    返回:
        List[波形对象]: 按优先级排序的波形显示实例列表
    """
    waveforms = [
        TaiwanWaveformDisplay(),        # 1. 台湾台北
        KamchatkaWaveformDisplay(),     # 2. 俄罗斯勘察加
        TokyoWaveformDisplay(),         # 3. 日本东京
        TongaWaveformDisplay(),         # 4. 汤加努库阿洛法
        CollegeWaveformDisplay(),       # 5. 美国阿拉斯加科利奇
        AleutianWaveformDisplay(),      # 6. 阿留申群岛阿图岛
        NewZealandWaveformDisplay(),    # 7. 新西兰
        FijiWaveformDisplay(),          # 8. 斐济
        PapuaNewGuineaWaveformDisplay(),# 9. 巴布亚新几内亚
        AomoriWaveformDisplay(),        # 10. 日本青森
        AlbuquerqueWaveformDisplay(),   # 11. 美国阿尔伯克基
        KongsbergWaveformDisplay(),     # 12. 挪威孔斯贝格
        PohakuloaWaveformDisplay(),     # 13. 夏威夷波哈库洛阿
        TucsonWaveformDisplay(),        # 14. 美国图森
        YuzhnoSakhalinskWaveformDisplay() # 15. 俄罗斯南萨哈林斯克
    ]
    for w in waveforms:
        w.set_font(font_small)
    return waveforms


def start_data_fetchers(
    time_display: TimeDisplay,
    eew_manager: EEWManager
) -> List[Thread]:
    """
    启动所有数据源线程。

    工作原理:
        创建多个数据获取器实例，每个获取器在独立线程中运行。
        获取器通过 WebSocket 或 HTTP 轮询接收数据，解析后放入 state.earthquake_queue 和 state.eew_queue。
        主线程通过队列消费者获取数据并合并。

    工作流:
        创建 FanDataFetcher → start() → 添加到列表
        若 P2P_HISTORY_ENABLED 则创建 P2PHistoryFetcher → start()
        创建 USGSFetcher → start()
        创建 CENCListFetcher → start()
        创建 JMAFetcher → start()
        （ICL 和 Wolfx 目前被注释）
        返回获取器列表

    依赖:
        data_fetchers 模块中的各个获取器类, config.P2P_HISTORY_ENABLED

    参数:
        time_display: 时间显示组件，用于更新 API 连接状态
        eew_manager: 预警管理器，用于将预警数据传递给 Wolfx 获取器（可选）

    返回:
        List[Thread]: 已启动的数据获取器列表（每个获取器都有 stop() 方法）
    """
    fetchers = []

    # FAN WebSocket（主数据源，包含地震和预警）
    fetcher = data_fetchers.FanDataFetcher(url="wss://ws.fanstudio.tech/all", time_display=time_display)
    fetcher.start()
    fetchers.append(fetcher)

    # P2P 历史数据（通过 HTTP 轮询）
    if config.P2P_HISTORY_ENABLED:
        p2p_fetcher = data_fetchers.P2PHistoryFetcher(time_display=time_display)
        p2p_fetcher.start()
        fetchers.append(p2p_fetcher)

    # USGS 实时地震 Feed
    usgs_fetcher = data_fetchers.USGSFetcher()
    usgs_fetcher.start()
    fetchers.append(usgs_fetcher)

    # CENC 地震列表（中国台网）
    cenc_list_fetcher = data_fetchers.CENCListFetcher()
    cenc_list_fetcher.start()
    fetchers.append(cenc_list_fetcher)

    # JMA 地震列表（日本气象厅）
    jma_fetcher = data_fetchers.JMAFetcher()
    jma_fetcher.start()
    fetchers.append(jma_fetcher)

    # ICL 预警（成都高新减灾研究所）—— 暂时禁用
    #icl_fetcher = data_fetchers.ICLFetcher(interval=3)
    #icl_fetcher.start()
    #fetchers.append(icl_fetcher)

    # Wolfx EEW（被注释，可根据需要启用）
    # wolfx_eew_fetcher = data_fetchers.WolfxEEWFetcher(eew_manager)
    # wolfx_eew_fetcher.start()
    # fetchers.append(wolfx_eew_fetcher)

    print("[系统信息] 所有数据源线程已启动")
    return fetchers


def stop_data_fetchers(fetchers: List[Thread]) -> None:
    """
    停止所有数据源线程，并捕获异常避免程序崩溃。

    工作原理:
        遍历 fetchers 列表，调用每个获取器的 stop() 方法。
        若某个获取器停止时抛出异常，捕获并打印警告，不影响其他获取器。

    依赖:
        每个获取器必须实现 stop() 方法。

    参数:
        fetchers: 数据获取器列表（由 start_data_fetchers 返回）
    """
    for f in fetchers:
        try:
            f.stop()
        except Exception as e:
            print(f"[系统警告] 停止 {f.__class__.__name__} 时出错: {e}")


# ============================================================================
# 主应用程序类
# ============================================================================

class CAPQuakeApp:
    """
    地震预警应用程序的主类。

    职责:
        - 初始化 Pygame 环境、窗口、地图投影、瓦片管理器
        - 构建并管理所有 UI 组件和数据监控器
        - 启动数据源线程
        - 运行主循环：事件处理 → 数据消费 → 组件更新 → 渲染
        - 程序退出时清理资源

    属性:
        screen: 主显示表面
        clock: 帧率控制器
        app_state: 应用程序状态
        show_list: 是否显示地震列表
        ui: UI 组件上下文
        monitors: 监控器上下文
        eew_manager: 预警管理器
        intensity_layer: 烈度图层（可选）
        map_surface: 地图绘制表面
    """

    def __init__(self) -> None:
        """初始化应用程序，创建所有组件并启动数据源。"""
        self.screen: Optional[pygame.Surface] = None
        self.clock = pygame.time.Clock()
        self.app_state = AppState.RUNNING
        self.show_list = True           # 是否显示地震列表
        self.ui: Optional[UIContext] = None
        self.monitors: Optional[MonitorContext] = None
        self.eew_manager = EEWManager()
        self.intensity_layer: Optional[IntensityLayer] = None
        self.map_surface: Optional[pygame.Surface] = None

        # 启动初始化流程
        self._init_pygame()
        self._init_components()
        self._preload_tiles()
        self._log_initialization()

    # ==================== 初始化步骤 ====================

    def _init_pygame(self) -> None:
        """初始化 Pygame 和显示窗口。"""
        pygame.init()
        self.screen = pygame.display.set_mode(
            (config.GlobalInit_WIDTH, config.GlobalInit_HEIGHT),
            pygame.RESIZABLE
        )
        pygame.display.set_caption(config.Name_Windows)

        # 设置初始地图状态（经纬度范围、缩放因子等）
        state.INITIAL_VIEW = (state.MAP_LON_MIN, state.MAP_LON_MAX,
                              state.MAP_LAT_MIN, state.MAP_LAT_MAX)
        state.MAP_ZOOM_FACTOR = max(config.MIN_ZOOM_FACTOR,
                                    min(config.MAX_ZOOM_FACTOR, state.MAP_ZOOM_FACTOR))
        map_utils.adjust_map_range_to_aspect(config.GlobalInit_WIDTH, config.GlobalInit_HEIGHT)
        map_utils.update_map_range_by_zoom()

        # 初始化瓦片级别
        if 'target_tile_level' not in dir(state) or state.target_tile_level is None:
            state.target_tile_level = map_utils.calc_tile_level(state.MAP_ZOOM_FACTOR)
        state.current_tile_level = state.target_tile_level

        # 创建瓦片管理器
        state.tile_manager = TileManager(tile_root="tiles", cache_size=5000, max_workers=8)

        # 创建地图绘制用的 Surface
        self.map_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

    def _init_components(self) -> None:
        """初始化所有组件：字体、UI、监控器、数据源。"""
        fonts = load_fonts()
        self.ui = self._build_ui(fonts)
        self.monitors = self._build_monitors()
        self.intensity_layer = self._build_intensity_layer()
        self._start_data_fetchers()

    def _build_ui(self, fonts: FontContext) -> UIContext:
        """组装所有 UI 组件。"""
        # 时间显示组件
        time_display = TimeDisplay(
            fonts.font_button_line1,
            fonts.font_button_line2,
            fonts.font_small
        )

        # JMA 震度情报组件
        jma_intensity_display = JMAIntensityDisplay()
        jma_intensity_display.set_fonts(
            info_font1=pygame.font.Font(config.FONT_PATH, config.JMA_INFO_FONT1_SIZE),
            info_font2=pygame.font.Font(config.FONT_PATH, config.JMA_INFO_FONT2_SIZE),
            info_font3=pygame.font.Font(config.FONT_PATH, config.JMA_INFO_FONT3_SIZE),
            scale_title_font=pygame.font.Font(config.FONT_PATH, config.JMA_SCALE_TITLE_FONT_SIZE),
            pref_font=pygame.font.Font(config.FONT_PATH, config.JMA_PREF_FONT_SIZE),
            source_font=pygame.font.Font(config.FONT_PATH, config.JMA_SOURCE_FONT_SIZE),
            default_font=fonts.font_small
        )

        # 波形显示对象
        waveforms = create_waveform_displays(fonts.font_small)

        # 功能按钮区
        function_buttons = FunctionButtonArea()
        function_buttons.set_font(fonts.font_small)

        # Excel 烈度显示组件
        excel_intensity_display = ExcelIntensityDisplay()
        excel_intensity_display.set_fonts(
            fonts.font_small,
            title_font=fonts.font_line1,
            pref_font=fonts.font_line2
        )
        # 从读取器获取初始数据
        state.excel_intensity_reader = ExcelIntensityReader()
        excel_intensity_display.update_data(state.excel_intensity_reader)

        # 预警弹窗组件
        eew_popup = EEWPopup()

        # 最大烈度显示面板（依赖于 KMA 和 S-net 监控器，将在之后填充）
        # 这里暂时创建空对象，等监控器就绪后更新
        max_intensity_display = MaxIntensityDisplay(None, None)  # 稍后更新

        return UIContext(
            fonts=fonts,
            time_display=time_display,
            function_buttons=function_buttons,
            jma_intensity_display=jma_intensity_display,
            excel_intensity_display=excel_intensity_display,
            eew_popup=eew_popup,
            waveforms=waveforms,
            max_intensity_display=max_intensity_display
        )

    def _build_monitors(self) -> MonitorContext:
        """构建所有监控器实例。"""
        # 静态测站监控器（从 JSON 加载全球台站）
        station_monitor = StationMonitor(config.GLOBAL_STATIONS_JSON)
        station_monitor.start()

        # Yahoo Japan 强震监控
        yahoo_monitor = YahooKyoshinMonitor()
        yahoo_monitor.start()

        # KMA 测站监控
        kma_monitor = KMAMonitor()
        kma_monitor.start()

        # S-net 海底测站监控（可选）
        snet_monitor = None
        if config.SNET_MONITOR_ENABLED:
            snet_monitor = SnetMonitor()
            snet_monitor.start()
            state.snet_monitor = snet_monitor

        # 全球 PGA 监控（可选，需要台站信息）
        pga_monitor = None
        if config.PGA_MONITOR_ENABLED:
            station_info = station_monitor.get_station_info_dict()
            if station_info:
                pga_monitor = GlobalPgaMonitor(station_info)
                state.global_pga_monitor = pga_monitor
                print("[系统信息] 全球 PGA 监控已启动")
            else:
                print("[系统警告] 无台站信息，无法启动 PGA 监控")

        # 数据源线程列表（稍后启动）
        fetchers = []

        return MonitorContext(
            station_monitor=station_monitor,
            yahoo_monitor=yahoo_monitor,
            kma_monitor=kma_monitor,
            snet_monitor=snet_monitor,
            pga_monitor=pga_monitor,
            fetchers=fetchers
        )

    def _build_intensity_layer(self) -> Optional[IntensityLayer]:
        """构建烈度图层（如果配置启用）。"""
        if not config.INTENSITY_LAYER_ENABLED:
            return None
        provinces_path = r"C:\Users\ZhuanZ.DESKTOP-PH97BKO\Desktop\CAPQuake\provinces"
        japan_cities_path = r"C:\Users\ZhuanZ.DESKTOP-PH97BKO\Desktop\CAPQuake\map\JapenCity.json"
        return IntensityLayer(provinces_path, japan_cities_path)

    def _start_data_fetchers(self) -> None:
        """启动数据源线程，并将它们存入监控上下文中。"""
        fetchers = start_data_fetchers(self.ui.time_display, self.eew_manager)
        self.monitors.fetchers = fetchers

    def _preload_tiles(self) -> None:
        """预加载低级别瓦片和当前视口的瓦片。"""
        tile_mgr = state.tile_manager
        if not tile_mgr:
            return

        # 预加载级别 0 和 1 的瓦片（作为备用）
        print("[系统信息] 预加载级别0和1瓦片...")
        for z in [0, 1]:
            max_coord = 2 ** (z + 2)
            for x in range(max_coord):
                for y in range(max_coord):
                    tile_mgr.get_tile(z, x, y, 512, 512)

        # 预加载当前视野所需的高级别瓦片
        if self.screen:
            width, height = self.screen.get_size()
            current_level = state.target_tile_level
            if current_level > 0:
                prefetch_viewport_tiles(tile_mgr, width, height, current_level)
                if current_level > 1:
                    prefetch_viewport_tiles(tile_mgr, width, height, current_level - 1)

    def _log_initialization(self) -> None:
        """输出初始化完成信息。"""
        print(f"[系统] 初始化完成，地图中心: ({state.MAP_CENTER_LON}, {state.MAP_CENTER_LAT}), "
              f"等级: {state.target_tile_level}")

    # ==================== 事件处理 ====================

    def _handle_events(self) -> None:
        """
        处理所有输入事件，并更新应用程序状态。

        工作原理:
            遍历 Pygame 事件队列，根据事件类型分发到对应的处理方法。
            支持的事件类型: QUIT, VIDEORESIZE, KEYDOWN, MOUSEWHEEL, MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEBUTTONUP。

        依赖:
            pygame.event.get(), map_utils.get_map_viewport
        """
        if not self.screen:
            return

        width, height = self.screen.get_size()
        view = map_utils.get_map_viewport(width, height)

        for event in pygame.event.get():
            # 退出事件
            if event.type == pygame.QUIT:
                self.app_state = AppState.EXIT
                return

            # 窗口大小改变事件
            elif event.type == pygame.VIDEORESIZE:
                self._handle_resize(event.w, event.h)
                width, height = event.w, event.h
                view = map_utils.get_map_viewport(width, height)

            # 键盘事件
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            # 鼠标滚轮事件（缩放地图）
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_mousewheel(event, view, width, height)

            # 鼠标左键事件（拖动地图或点击按钮）
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse_click(event, view)

            # 鼠标移动事件（拖动时更新地图中心）
            elif event.type == pygame.MOUSEMOTION and state.MOUSE_DRAGGING:
                self._handle_mouse_drag(event, view, width, height)

            # 鼠标释放事件
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                state.MOUSE_DRAGGING = False

    def _handle_resize(self, new_width: int, new_height: int) -> None:
        """
        处理窗口大小改变。

        工作流:
            重新创建主表面 → 更新窗口标题 → 重新创建地图表面 → 调整地图投影以适应新宽高比

        参数:
            new_width: 新窗口宽度
            new_height: 新窗口高度
        """
        self.screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
        pygame.display.set_caption(f"{config.Name_Windows} - {new_width}x{new_height}")
        self.map_surface = pygame.Surface((new_width, new_height), pygame.SRCALPHA)
        # 调整地图范围以保持投影
        map_utils.adjust_map_range_to_aspect(new_width, new_height)

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """
        处理键盘按键事件。

        支持的按键:
            SPACE : 切换地震列表显示/隐藏
            F1    : 生成 CENC 测试预警
            F2    : 生成 JMA 测试预警
            F3    : 生成 CWA 测试预警

        参数:
            event: Pygame 键盘事件对象
        """
        if event.key == pygame.K_SPACE:
            self.show_list = not self.show_list
        elif event.key == pygame.K_F1:
            state.eew_queue.put(generate_cenc_test())
        elif event.key == pygame.K_F2:
            state.eew_queue.put(generate_jma_test())
        elif event.key == pygame.K_F3:
            state.eew_queue.put(generate_cwa_test())

    def _handle_mousewheel(
        self,
        event: pygame.event.Event,
        view: pygame.Rect,
        width: int,
        height: int
    ) -> None:
        """
        处理鼠标滚轮缩放地图。

        工作原理:
            1. 记录用户交互时间（用于 EEW 跟随冷却）。
            2. 获取鼠标位置对应的经纬度（作为缩放中心点）。
            3. 根据滚轮方向计算新的缩放因子。
            4. 调整地图中心点，使鼠标位置对应的经纬度在缩放后保持不变。
            5. 更新地图范围，并预加载新级别的瓦片。

        参数:
            event: Pygame 滚轮事件对象（event.y > 0 表示向上滚动放大）
            view: 当前地图视口矩形
            width: 屏幕宽度
            height: 屏幕高度
        """
        state.LAST_USER_INTERACTION_TIME = time.time()

        # 获取鼠标位置对应的经纬度
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if view.width > 0 and view.height > 0:
            try:
                mouse_lon, mouse_lat = map_utils.screen_to_lonlat(mouse_x, mouse_y, width, height)
            except:
                mouse_lon, mouse_lat = state.MAP_CENTER_LON, state.MAP_CENTER_LAT
        else:
            mouse_lon, mouse_lat = state.MAP_CENTER_LON, state.MAP_CENTER_LAT

        # 计算新的缩放因子
        current_zoom = state.MAP_ZOOM_FACTOR
        zoom_step = config.MOUSE_ZOOM_STEP
        if event.y > 0:
            new_target = current_zoom * zoom_step
        else:
            new_target = current_zoom / zoom_step
        new_target = max(config.MIN_ZOOM_FACTOR, min(config.MAX_ZOOM_FACTOR, new_target))
        if abs(new_target - current_zoom) < 1e-6:
            return

        # 应用缩放，并调整中心点使鼠标位置保持不动
        state.MAP_ZOOM_FACTOR = new_target
        ratio = current_zoom / new_target
        new_center_lon = mouse_lon - (mouse_lon - state.MAP_CENTER_LON) * ratio
        new_center_lat = mouse_lat - (mouse_lat - state.MAP_CENTER_LAT) * ratio
        state.MAP_CENTER_LON = new_center_lon
        state.MAP_CENTER_LAT = new_center_lat
        map_utils.update_map_range_by_zoom()

        # 预加载新级别的瓦片
        new_level = map_utils.calc_tile_level(state.MAP_ZOOM_FACTOR)
        if new_level != state.target_tile_level:
            state.target_tile_level = new_level
            if state.tile_manager:
                prefetch_viewport_tiles(state.tile_manager, width, height, new_level)

    def _handle_mouse_click(self, event: pygame.event.Event, view: pygame.Rect) -> None:
        """
        处理鼠标左键点击。

        工作流:
            1. 记录用户交互时间。
            2. 先检查是否点击了功能按钮区。
            3. 如果点击了按钮，执行对应动作；否则开始拖动地图。

        参数:
            event: Pygame 鼠标事件对象
            view: 当前地图视口矩形
        """
        state.LAST_USER_INTERACTION_TIME = time.time()
        clicked = self.ui.function_buttons.handle_event(event)
        if clicked:
            self._handle_button_action(clicked)
        else:
            # 没有点击按钮，开始拖动地图
            state.MOUSE_DRAGGING = True
            state.DRAG_START_POS = event.pos
            state.DRAG_START_CENTER = (state.MAP_CENTER_LON, state.MAP_CENTER_LAT)

    def _handle_button_action(self, label: str) -> None:
        """
        处理功能按钮的动作。

        支持的按钮:
            模式切换 : 切换震中绘制模式（全部 / 各源最新）
            保存视角 : 将当前地图状态保存到 state.SAVED_CUSTOM_VIEW
            跳转视角 : 恢复到之前保存的视角

        参数:
            label: 按钮标签文本
        """
        if label == ButtonAction.MODE_SWITCH.value:
            state.EPICENTER_MODE = 1 - state.EPICENTER_MODE
            mode_str = "全部震中" if state.EPICENTER_MODE == 0 else "各源最新震中"
            print(f"[系统] 震中模式切换为: {mode_str}")
        elif label == ButtonAction.SAVE_VIEW.value:
            state.SAVED_CUSTOM_VIEW = (
                state.MAP_CENTER_LON,
                state.MAP_CENTER_LAT,
                state.MAP_ZOOM_FACTOR
            )
            print(f"[视角] 已保存当前视角: 中心({state.MAP_CENTER_LON:.2f}, {state.MAP_CENTER_LAT:.2f}) "
                  f"缩放{state.MAP_ZOOM_FACTOR:.2f}")
        elif label == ButtonAction.RESTORE_VIEW.value:
            if state.SAVED_CUSTOM_VIEW is None:
                print("[视角] 尚未保存任何视角，请先点击保存视角按钮")
            else:
                lon, lat, zoom = state.SAVED_CUSTOM_VIEW
                state.MAP_CENTER_LON = lon
                state.MAP_CENTER_LAT = lat
                state.MAP_ZOOM_FACTOR = zoom
                map_utils.update_map_range_by_zoom()
                state.target_tile_level = map_utils.calc_tile_level(zoom)
                print(f"[视角] 已恢复保存的视角: 中心({lon:.2f}, {lat:.2f}) 缩放{zoom:.2f}")

    def _handle_mouse_drag(
        self,
        event: pygame.event.Event,
        view: pygame.Rect,
        width: int,
        height: int
    ) -> None:
        """
        处理鼠标拖动地图。

        工作原理:
            根据鼠标移动的像素偏移量，计算经纬度的变化量，更新地图中心点。

        参数:
            event: Pygame 鼠标移动事件对象
            view: 当前地图视口矩形
            width: 屏幕宽度
            height: 屏幕高度
        """
        state.LAST_USER_INTERACTION_TIME = time.time()
        dx = event.pos[0] - state.DRAG_START_POS[0]
        dy = event.pos[1] - state.DRAG_START_POS[1]
        if view.width > 0 and view.height > 0:
            lon_span = state.MAP_LON_MAX - state.MAP_LON_MIN
            lat_span = state.MAP_LAT_MAX - state.MAP_LAT_MIN
            delta_lon = -dx / view.width * lon_span
            delta_lat = dy / view.height * lat_span
            state.MAP_CENTER_LON = state.DRAG_START_CENTER[0] + delta_lon
            state.MAP_CENTER_LAT = state.DRAG_START_CENTER[1] + delta_lat
            map_utils.update_map_range_by_zoom()

    # ==================== 数据更新 ====================

    def _process_queues(self) -> None:
        """
        处理数据队列：地震和预警。

        工作原理:
            从 state.earthquake_queue 中取出所有地震数据，调用 data_merger.merge_earthquake 进行合并。
            从 state.eew_queue 中取出所有预警数据，调用 eew_manager.update 进行处理。
            使用 queue.get_nowait() 非阻塞获取，直到队列为空。

        依赖:
            data_merger.merge_earthquake, eew_manager.update, state.earthquake_queue, state.eew_queue
        """
        # 合并地震数据
        try:
            while True:
                data_merger.merge_earthquake(state.earthquake_queue.get_nowait())
        except queue.Empty:
            pass

        # 处理预警数据
        try:
            while True:
                self.eew_manager.update(state.eew_queue.get_nowait(), api_source='FAN')
        except queue.Empty:
            pass

    def _auto_jump_to_earthquake(self) -> None:
        """
        新地震自动跳转视野（仅第一次）。

        工作原理:
            检查 earthquake_events 中最新的地震事件，如果其 ID 不在 jumped_earthquake_ids 集合中，
            则将地图视野移动到该地震震中（直径 800 公里），并记录已跳转，同时设置 5 分钟后自动恢复视角的计时器。

        依赖:
            map_utils.set_view_center_diameter, state.earthquake_events, state.jumped_earthquake_ids
        """
        if not state.earthquake_events:
            return

        new_event = state.earthquake_events[0]
        event_id = new_event.get('id') or new_event.get('main', {}).get('time', '')
        if event_id and event_id not in state.jumped_earthquake_ids:
            main_data = new_event.get('main', {})
            lat = main_data.get('lat')
            lon = main_data.get('lon')
            if lat is not None and lon is not None and self.screen:
                width, height = self.screen.get_size()
                map_utils.set_view_center_diameter(lon, lat, 800, width, height)
                map_utils.update_map_range_by_zoom()
                state.target_tile_level = map_utils.calc_tile_level(state.MAP_ZOOM_FACTOR)
                state.jumped_earthquake_ids.add(event_id)
                print(f"[视野跳转] 新地震: {main_data.get('place', 'Unknown')} (仅此一次)")
                # 设置5分钟后自动恢复视角的计时器
                state.NEW_EVENT_RESET_TIME = time.time() + 300

    def _update_components(self) -> None:
        """更新各组件状态。"""
        # 清理过期预警
        self.eew_manager.remove_expired(datetime.now())

        # 更新烈度图层（如果启用）
        if self.intensity_layer:
            active_eews = self.eew_manager.get_all_active()
            self.intensity_layer.update(active_eews)

        # 视野跟随（自动调整视野以包含所有预警）
        self.eew_manager.tick_view_follow()

        # 更新 Excel 烈度显示数据
        if state.excel_intensity_reader:
            self.ui.excel_intensity_display.update_data(state.excel_intensity_reader)

        # 更新最大烈度显示面板的监控器引用（因为之前创建时为空）
        if self.monitors.snet_monitor and self.monitors.kma_monitor:
            # 如果面板尚未设置监控器，则更新
            if not self.ui.max_intensity_display.snet_monitor:
                self.ui.max_intensity_display = MaxIntensityDisplay(
                    self.monitors.snet_monitor,
                    self.monitors.kma_monitor
                )

    # ==================== 瓦片级别切换 ====================

    def _update_tile_level(self) -> None:
        """
        检查目标级别瓦片是否已全部缓存，若是则切换当前级别。

        工作原理:
            获取当前视口在目标级别下覆盖的所有瓦片索引，检查每个瓦片是否已在缓存中。
            如果全部缓存，则将 state.current_tile_level 设置为 state.target_tile_level，
            后续渲染将使用新级别的瓦片。

        依赖:
            state.tile_manager, map_utils.tiles_in_viewport, tile_manager.is_tile_cached
        """
        if not state.tile_manager or not self.screen:
            return
        if state.target_tile_level == state.current_tile_level:
            return

        width, height = self.screen.get_size()
        z_std = state.target_tile_level + 2
        x_min, x_max, y_min, y_max = map_utils.tiles_in_viewport(width, height, z_std)
        all_cached = True
        for xt in range(x_min, x_max + 1):
            for yt in range(y_min, y_max + 1):
                if not state.tile_manager.is_tile_cached(state.target_tile_level, xt, yt):
                    all_cached = False
                    break
            if not all_cached:
                break
        if all_cached:
            state.current_tile_level = state.target_tile_level

    # ==================== 渲染 ====================

    def _render(self) -> None:
        """执行所有渲染操作。"""
        if not self.screen or not self.map_surface:
            return

        width, height = self.screen.get_size()
        self.map_surface.fill(config.MAP_COLOR)

        # 绘制地图元素（底图、预警波、测站等）
        draw.draw_map_to_surface(
            self.map_surface,
            (width, height),
            state.tile_manager,
            self.eew_manager,
            self.ui.fonts.font_intensity,
            self.monitors.station_monitor,
            yahoo_monitor=self.monitors.yahoo_monitor,
            intensity_layer=self.intensity_layer,
            kma_monitor=self.monitors.kma_monitor,
            pga_monitor=self.monitors.pga_monitor,
            snet_monitor=self.monitors.snet_monitor
        )
        self.screen.blit(self.map_surface, (0, 0))

        # 绘制 UI 叠加层
        draw.draw_ui_overlay(
            self.screen, self.show_list,
            self.ui.fonts.font_small,
            self.ui.time_display,
            self.ui.fonts.font_line1,
            self.ui.fonts.font_line2,
            self.ui.fonts.font_line3,
            self.ui.fonts.font_source,
            self.ui.fonts.font_intensity,
            self.ui.function_buttons,
            self.ui.jma_intensity_display,
            self.ui.waveforms,
            self.eew_manager,
            self.ui.eew_popup,
            max_intensity_display=self.ui.max_intensity_display,
            skip_backgrounds=False
        )

        # 自动恢复视角计时器
        now = time.time()
        if state.SAVED_CUSTOM_VIEW is not None:
            if state.NEW_EVENT_RESET_TIME is not None and now >= state.NEW_EVENT_RESET_TIME:
                restore_custom_view()
                state.NEW_EVENT_RESET_TIME = None
            if state.EEW_RESET_TIME is not None and now >= state.EEW_RESET_TIME:
                restore_custom_view()
                state.EEW_RESET_TIME = None

        # 绘制 Excel 烈度面板（位于 JMA 组件下方）
        jma_bottom = self.ui.jma_intensity_display.y + self.ui.jma_intensity_display.last_height \
                     if hasattr(self.ui.jma_intensity_display, 'last_height') else None
        self.ui.excel_intensity_display.draw(self.screen, jma_bottom=jma_bottom)

        # 更新显示
        pygame.display.flip()

    # ==================== 主循环 ====================

    def run(self) -> None:
        """
        主循环：事件处理 → 数据更新 → 渲染。

        工作流:
            每帧执行:
                1. 控制帧率 (60 FPS)
                2. 处理输入事件
                3. 处理数据队列
                4. 新地震自动跳转视野
                5. 更新组件状态
                6. 检查瓦片级别切换
                7. 渲染画面
            当 app_state 变为 EXIT 时退出循环。
        """
        while self.app_state == AppState.RUNNING:
            dt = self.clock.tick(60) / 1000.0   # 帧间隔（秒），保留但未使用

            # 处理输入事件
            self._handle_events()
            if self.app_state != AppState.RUNNING:
                break

            # 处理数据队列
            self._process_queues()

            # 新地震自动跳转视野
            self._auto_jump_to_earthquake()

            # 更新组件状态
            self._update_components()

            # 检查瓦片级别切换
            self._update_tile_level()

            # 渲染画面
            self._render()

    # ==================== 清理 ====================

    def shutdown(self) -> None:
        """清理资源，停止所有线程。"""
        print("[系统] 正在关闭程序...")

        # 停止所有数据源线程
        if self.monitors and self.monitors.fetchers:
            stop_data_fetchers(self.monitors.fetchers)

        # 停止其他监控器
        if self.monitors:
            if self.monitors.pga_monitor:
                self.monitors.pga_monitor.stop()
            if self.monitors.snet_monitor:
                self.monitors.snet_monitor.stop()
            self.monitors.station_monitor.stop()
            self.monitors.yahoo_monitor.stop()
            self.monitors.kma_monitor.stop()

        # 停止波形线程
        for w in self.ui.waveforms:
            w.stop()

        # 退出 Pygame
        pygame.quit()
        sys.exit()


# ============================================================================
# 程序入口
# ============================================================================

if __name__ == "__main__":
    app = CAPQuakeApp()
    try:
        app.run()
    finally:
        app.shutdown()
