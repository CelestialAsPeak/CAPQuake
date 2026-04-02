# CAPQuake — 全球地震震讯，地震预警与实时可视化以及气象整合系统

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Pygame](https://img.shields.io/badge/Pygame-2.5.0-green)](https://pygame.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

***此项目在快速迭代 功能在不断增加 预计后续内测后会完整公开***

***当前项目版本:0.2.0(Beta)***

***当前README.MD版本:0.2***

**CAPQuake** 是一个基于Python+Pygame+Obspy的地震预警桌面应用程序，依靠Obspy库的支持以及多个公开API接口，紧急地震速报（EEW）跟随、实时波形显示，全球地震震讯与专业参数计算等功能。
此外，该项目在未来计划接入气象相关模块。

**可以前往我的bilibili主页，立刻观看项目最新运行效果:https://space.bilibili.com/1680353559**

- 此项目会**全部开源**，并提供**国标标准版**和**完整版**。推荐使用国标标准版，遵守中国大陆的法律法规。

- 此项目会预留修改接口，但如果你改编了这个项目，你也需要把你的改编项目**全部开源**。



---
##  ✨ 项目特性
- 后续再写(咕咕咕)
---
## 🌐 目前接入的数据源(会不断增加)
- 特别鸣谢 @LMG-LIVE 提供的大量新接口
- **常规数据源**:

| 数据源 | 提供的数据 |
|--------|------------|
| FAN Studio | 多源地震情报及紧急地震速报（EEW），国气象厅实时测站 MMI 数据 |
| Wolfx | 多源地震情报及紧急地震速报（EEW） |
| P2P | 日本地震情报及紧急地震速报（EEW）、震度速报 |
| USGS | 全球实时地震情报 |
| NIED 测站 | 日本实时震度观测点数据 |
| S-net 测站| 日本海底震度数据 |
| EarthScope  | 全球台站实时波形数据 |


- **特别数据源**:

| 数据源 | 提供的数据 |
|--------|------------|
| 香港天文台 | 海啸信息 |
| 自然资源部南海预报减灾中心 |  海啸警报 |
| 广西地震局 | 地震速报 |
|福建省海洋预报台|海啸警报|
|北京市地震局|地震速报|
|广东省海洋预报台|海啸警报|
| 俄罗斯科学院统一地球物理局 勘察加分部 | 地震目录，震源机制解|
| 古巴国家地震局 | 地震情报 | 
|泰国气象厅|地震信息|
|委内瑞拉地震研究基金会|地震情报|
印度国家海洋信息服务中心|海啸警报|
印度尼西亚海啸预警系统|海啸警报|
澳大利亚联合海啸预警中心|海啸警报|
## 🖥️ 系统要求

- **操作系统**：Windows 10/11（推荐）
- **Python**：3.8 或更高版本（建议 3.10+）
- **网络**：可能需要VPN以获取实时地震数据和波形（作者不用VPN一切正常 但开了体验会更好）

---

## 📦 针对开发者的安装步骤
 - 如果你想改编 下载好源代码后 请安装以下环境:
### 1. 下载Pygame

```bash
pip install pygame
```
### 2. 下载Obspy
- 建议用Conda环境下载Obspy

```bash
conda config --add channels conda-forge
conda config --set channel_priority strict
conda create -n obspy_env python=3.9 obspy
# Windows / macOS / Linux
conda activate obspy_env
conda install -c conda-forge obspy cartopy
```

### 3. 解决其他库依赖

**库版本建议：**
- pygame>=2.5.0
- obspy>=1.4.0
- requests>=2.28.0
- websocket-client>=1.5.0
- pandas>=2.0.0
- openpyxl>=3.1.0
- shapely>=2.0.0
- numpy>=1.24.0
- Pillow>=10.0.0
- pytz>=2023.3

```bash
pip install requests ....#自己按需添加
```
