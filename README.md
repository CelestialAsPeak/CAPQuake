## TODO List

```
//1.[重要]8.10日内测前必须全部搞完
//2.ViewportController优化 性能优化
//3.INTERRUPTED动画流畅度优化
//4.controllers管线性能优化
//5.负一屏完善
//6.地图断层完善
//7.半组件式，左半边式UI风格加入
//8.答题网站防作弊系统完善
//9.wiki完善
```

---

## 10 · 开发规范

### 用户守则（12 条）

1. BUG 修复 commit 格式：`[BUG修复]xxx`
2. 功能新增：`[feat]xxx`
3. 调试日志：`[调试]xxx`
4. 每次修完 BUG 必须更新 `.claude/projects/` 下 memory MD（如有需要）
5. BUG 修复前后必须解释根因
6. 全局改动必须确认，**严禁未经确认改全局常量**
7. 涉及图层渲染的修改，必须在 draw 入口处处理 center_lon 归零
8. 音效、定时器类 BUG 优先用数据本身（时间戳/年龄）判断，不用计时器
9. 地图跳转必须约束经度到当前中心 ±180°
10. 用户说的每一句都是真的，不要怀疑
11. 等用户指令再行动
12. 每一步都要 commit 以防万一

### commit 规范

- 每次改完代码自动 commit + push（不用用户提醒）——**注意**：并行 session 会有未提交改动，commit 前 `git status` 确认工作区只有自己的改动
- 日志目录 `logs/` 已 gitignore

### 添加新数据源流程（7 步）

见 [02-数据源](02-数据源.md) 末尾。

### 配置 Key 命名规范

```
sources/{name}/enabled
filter/{name}/min_magnitude, min_intensity（回退到上级）
filter/{name}/{sub_source}/min_magnitude
display/{category}/{key}
sound/{key}
map/{category}/{key}
```

### 验证链（改完必跑）

```bash
# 1. 编译
python -m py_compile <改动文件>

# 2. undefined name（权威）
python -m pyflakes ui core_service business data | grep "undefined name"

# 3. 冒烟（0 Traceback + 管线活动）
PYTHONIOENCODING=utf-8 timeout 40 python run.py

# 4. 无头验证（交互/数据路径，冒烟测不到）
```

### 每刀拆分标准流程（大文件拆分）

1. grep 定位块边界 + 确认所有调用点/外部引用（**含跨文件**：`grep -rn` 全项目）
2. 读完全部要搬的代码（不许跳读）
3. 写新文件（逐字搬移，函数名保持原名）→ `python -m py_compile` → **commit 新文件**
4. 改旧文件：删段（脚本锚点法，从后往前）+ import 改名 + 调用点委托
5. 清死 import（grep 计数 =1 的是 import 行本身）
6. 编译 + 冒烟 + pyflakes + scan_attr_refs
7. commit 接入

### 页对象模式（overlay 拆分定型）

```python
class XxxPage:  # 普通类，非 QWidget
    def __init__(self, font_getter..., on_redraw, ...): ...
    def paint(self, painter, cp_x, cp_top, cp_w, pad, bg_h, visible_h, sc): ...
    def handle_press(self, pos) -> bool: ...   # True=消费
    def clear_toggles(self) / clear_interactive(self): ...
    def options(self) -> dict: ...
```

### controller 模式（main_window 拆分定型）

- 构造注入（mw 引用 + 具体对象）+ `set_viewport_ctrl` 延迟注入
- 公开属性（mode/view/hold_*）替代私有直读写
- 跨 controller 经 `self._mw.xxx_ctrl` 延迟访问
- **构造前连接的信号用 dispatch 方法**

### 前端铁律（卡片绘制）

1. 字体常量表不乱设（有统一字体常量）
2. 必用 `elidedText` 不硬截断
3. 不偷工：hover + 禁用态做全

### 常用工具函数（core_service/helpers.py）

`to_float, to_int, to_str, parse_ts, parse_cst_time, parse_jst_time, validate_lat/lon, jma_to_mmi, haversine_km, check_display_filter, now_ntp, ntp_synced`

### 数据模型规范

- `@dataclass(frozen=True)` 不可变
- `source_id, event_id` 必填
- 可选字段默认 None；`raw: dict = field(default_factory=dict)`
- EEW `_active` key = `f"{source_id}:{event_id}"`
