"""
data/connectors/station/snet_connector.py
S-net 日本海底测站连接器。

数据源：MSIL 强震动信息瓦片服务
  - 瓦片 URL: https://www.msil.go.jp/data/tiles/smoni/tileimage/{time}/{time}/5/28/{tile}.png
  - 测站坐标: 内置 REAL_COORDS + 可选本地 ObsPoints.json

data 层只做：
  1. 加载测站坐标列表
  2. 下载 PNG 瓦片（raw bytes）
  3. emit 原始数据（瓦片 bytes + 测站坐标 + 时间戳）

像素解析（RGB → 震度）由 core_service 层处理。
"""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timedelta
from typing import Optional

import requests

from PySide6.QtCore import QObject, QTimer

from ..base import DataSourceConnector

logger = logging.getLogger(__name__)

SNET_TILE_URL = "https://www.msil.go.jp/data/tiles/smoni/tileimage/{time}/{time}/5/28/{tile}.png"
SNET_UPDATE_INTERVAL = 60
SNET_GET_DELAY = 90
# 内部 tile 名称 → URL 中的实际文件名
SNET_TILE_NAMES = {"y11": "11", "y12": "12"}

# 测站真实坐标（从原项目 snet_monitor.py 提取）
SNET_REAL_COORDS = {
    "N.S1N01": (35.8968, 141.0535), "N.S1N02": (35.8424, 141.3772),
    "N.S1N03": (35.7203, 141.6451), "N.S1N04": (35.6036, 141.9041),
    "N.S1N05": (35.4047, 142.0531), "N.S1N06": (35.2277, 141.8692),
    "N.S1N07": (35.2773, 141.5902), "N.S1N08": (35.4536, 141.3898),
    "N.S1N09": (35.2270, 141.3068), "N.S1N10": (35.0925, 141.2021),
    "N.S1N11": (35.1203, 140.9682), "N.S1N12": (35.0228, 140.8091),
    "N.S1N13": (34.8788, 140.9627), "N.S1N14": (34.6407, 141.0907),
    "N.S1N15": (34.5256, 141.3512), "N.S1N16": (34.3686, 141.5402),
    "N.S1N17": (34.1956, 141.3341), "N.S1N18": (34.2620, 141.0316),
    "N.S1N19": (34.2269, 140.7311), "N.S1N20": (34.2592, 140.4159),
    "N.S1N21": (34.4231, 140.2030), "N.S1N22": (34.6443, 140.0906),
    "N.S2N01": (37.8428, 141.3845), "N.S2N02": (37.6922, 141.6387),
    "N.S2N03": (37.7073, 141.9650), "N.S2N04": (37.6739, 142.2975),
    "N.S2N05": (37.6016, 142.6236), "N.S2N06": (37.5259, 142.9350),
    "N.S2N07": (37.4290, 143.2266), "N.S2N08": (37.2220, 143.0700),
    "N.S2N09": (37.0741, 142.8188), "N.S2N10": (37.0948, 142.4979),
    "N.S2N11": (37.1931, 142.1998), "N.S2N12": (37.2772, 141.8790),
    "N.S2N13A": (37.3003, 141.5709), "N.S2N14": (37.0952, 141.3703),
    "N.S2N15": (36.8344, 141.3307), "N.S2N16": (36.6620, 141.5207),
    "N.S2N17": (36.6337, 141.8389), "N.S2N18": (36.6824, 142.1445),
    "N.S2N19": (36.5986, 142.4389), "N.S2N20": (36.3885, 142.6164),
    "N.S2N21": (36.1577, 142.5553), "N.S2N22": (35.9463, 142.4014),
    "N.S2N23": (35.9677, 142.1138), "N.S2N24": (35.9976, 141.7944),
    "N.S2N25": (36.0729, 141.5095), "N.S2N26": (36.1442, 141.2021),
    "N.S3N01": (39.4497, 142.4578), "N.S3N02": (39.3746, 142.7918),
    "N.S3N03": (39.3231, 143.1206), "N.S3N04": (39.2958, 143.4544),
    "N.S3N05": (39.1906, 143.7499), "N.S3N06": (39.0459, 143.9305),
    "N.S3N07": (38.8308, 143.7846), "N.S3N08": (38.7826, 143.4769),
    "N.S3N09": (38.7739, 143.1437), "N.S3N10": (38.8668, 142.8212),
    "N.S3N11": (38.9349, 142.4873), "N.S3N12": (38.8412, 142.1816),
    "N.S3N13": (38.5901, 142.1816), "N.S3N14": (38.4993, 142.5002),
    "N.S3N15": (38.4487, 142.8376), "N.S3N16": (38.4262, 143.1703),
    "N.S3N17": (38.3978, 143.5139), "N.S3N18": (38.3063, 143.7810),
    "N.S3N19": (38.0594, 143.7441), "N.S3N20": (37.9311, 143.5675),
    "N.S3N21": (37.9713, 143.2454), "N.S3N22": (37.9838, 142.9072),
    "N.S3N23": (38.0270, 142.5735), "N.S3N24": (38.0569, 142.2340),
    "N.S3N25": (38.0972, 141.8957), "N.S3N26": (38.1060, 141.5572),
    "N.S4N01": (40.7881, 141.7895), "N.S4N02": (40.9069, 142.1057),
    "N.S4N03": (41.0156, 142.4314), "N.S4N04": (41.0762, 142.7706),
    "N.S4N05": (41.0443, 143.1138), "N.S4N06": (40.9718, 143.4481),
    "N.S4N07": (40.8820, 143.7746), "N.S4N08": (40.7805, 144.0905),
    "N.S4N09": (40.5521, 144.1332), "N.S4N10": (40.4327, 143.8887),
    "N.S4N11": (40.4353, 143.5430), "N.S4N12": (40.4515, 143.2015),
    "N.S4N13": (40.5196, 142.9617), "N.S4N14": (40.5927, 142.6340),
    "N.S4N15": (40.5933, 142.2844), "N.S4N16": (40.3295, 142.2673),
    "N.S4N17": (40.1165, 142.3926), "N.S4N18": (40.1088, 142.6222),
    "N.S4N19": (40.0904, 142.9695), "N.S4N20": (40.0743, 143.3210),
    "N.S4N21": (40.0863, 143.6572), "N.S4N22": (40.0260, 143.9547),
    "N.S4N23": (39.7718, 143.9259), "N.S4N24": (39.6388, 143.7154),
    "N.S4N25": (39.6976, 143.3749), "N.S4N26": (39.7245, 143.0384),
    "N.S4N27": (39.7445, 142.6903), "N.S4N28": (39.7385, 142.3408),
    "N.S5N01": (42.7688, 145.7115), "N.S5N02": (42.6403, 145.4063),
    "N.S5N03": (42.4802, 145.1433), "N.S5N04": (42.2286, 145.2040),
    "N.S5N05": (42.0615, 145.4370), "N.S5N06": (41.8840, 145.6544),
    "N.S5N07": (41.6637, 145.5291), "N.S5N08": (41.5301, 145.2483),
    "N.S5N09": (41.5210, 144.9050), "N.S5N10": (41.6541, 144.6716),
    "N.S5N11": (41.9072, 144.6955), "N.S5N12": (42.0784, 144.6375),
    "N.S5N13": (41.9792, 144.3445), "N.S5N14": (41.7475, 144.1779),
    "N.S5N15": (41.4961, 144.0879), "N.S5N16": (41.3742, 143.8006),
    "N.S5N17": (41.3643, 143.4530), "N.S5N18": (41.4351, 143.1264),
    "N.S5N19": (41.5607, 142.8177), "N.S5N20": (41.6095, 142.4787),
    "N.S5N21": (41.4248, 142.2193), "N.S5N22": (41.1989, 142.0271),
    "N.S5N23": (40.9540, 141.8762),
    "N.S6N01": (42.8064, 146.0211), "N.S6N02": (42.5807, 146.0780),
    "N.S6N03": (42.0943, 146.2316), "N.S6N04": (41.6653, 146.1747),
    "N.S6N05": (41.3717, 145.6053), "N.S6N06": (40.8999, 145.3929),
    "N.S6N07": (40.5360, 144.9381), "N.S6N08": (40.0319, 144.8089),
    "N.S6N09": (39.5172, 144.7191), "N.S6N10": (39.0072, 144.5915),
    "N.S6N11": (38.4990, 144.4536), "N.S6N12": (37.9879, 144.3357),
    "N.S6N13": (37.4862, 144.1757), "N.S6N14": (37.0120, 143.9557),
    "N.S6N15": (36.5748, 143.6059), "N.S6N16": (36.1262, 143.2823),
    "N.S6N17": (35.6745, 142.9688), "N.S6N18": (35.2114, 142.6799),
    "N.S6N19": (34.7118, 142.5208), "N.S6N20": (34.2604, 142.2389),
    "N.S6N21": (33.9619, 141.7291), "N.S6N22": (33.8601, 141.1281),
    "N.S6N23": (33.9448, 140.5189), "N.S6N24": (34.1773, 139.9814),
    "N.S6N25": (34.6696, 139.8167),
    "M.KMA01": (33.8048, 136.5570), "M.KMA02": (33.7524, 136.6488),
    "M.KMA03": (33.6484, 136.6037), "M.KMA04": (33.6781, 136.4674),
    "M.KMB05": (33.4772, 136.9264), "M.KMB06": (33.3584, 136.9216),
    "M.KMB07": (33.3613, 136.8072), "M.KMB08": (33.4664, 136.8039),
    "M.KMC09": (33.0584, 136.8313), "M.KMC10": (33.0533, 136.9335),
    "M.KMC11": (33.0033, 136.7790), "M.KMC12": (33.1279, 136.8188),
    "M.KMC21": (32.9506, 136.7417),
    "M.KMD13": (33.2201, 136.6903), "M.KMD14": (33.1727, 136.5770),
    "M.KMD15": (33.2331, 136.5631), "M.KMD16": (33.3045, 136.5958),
    "M.KME17": (33.4850, 136.4451), "M.KME18": (33.3860, 136.3828),
    "M.KME19": (33.4459, 136.2564), "M.KME20": (33.5444, 136.3325),
    "M.KME22": (33.3303, 136.2702),
    "M.MRA01": (33.4085, 134.7449), "M.MRA02": (33.3393, 134.8641),
    "M.MRA03": (33.2490, 134.7691), "M.MRA04": (33.3205, 134.6724),
    "M.MRB05": (33.3222, 135.0667), "M.MRB06": (33.2252, 135.1698),
    "M.MRB07": (33.1755, 135.0964), "M.MRB08": (33.2750, 134.9869),
    "M.MRC09": (33.2280, 135.4585), "M.MRC10": (33.1251, 135.5249),
    "M.MRC11": (33.0837, 135.4121), "M.MRC12": (33.1752, 135.3414),
    "M.MRD13": (33.1594, 135.7557), "M.MRD14": (33.1359, 135.8584),
    "M.MRD15": (33.1420, 135.9586), "M.MRD16": (33.0299, 135.8401),
    "M.MRD17": (33.0915, 135.7144),
    "M.MRE18": (32.9270, 135.7747), "M.MRE19": (32.8920, 135.8336),
    "M.MRE20": (32.8017, 135.7733), "M.MRE21": (32.8603, 135.6670),
    "M.MRF22": (32.9880, 135.2250), "M.MRF23": (32.8827, 135.3082),
    "M.MRF24": (32.8545, 135.1916), "M.MRF25": (32.8919, 135.1538),
    "M.MRG26": (32.7615, 134.5167), "M.MRG27": (32.7089, 134.5996),
    "M.MRG28": (32.6251, 134.5164), "M.MRG29": (32.6752, 134.4334),
    "N.ST1H": (34.5956, 139.9183), "N.ST2H": (34.7396, 139.8393),
    "N.ST3H": (34.7983, 139.6435), "N.ST4H": (34.8931, 139.5711),
    "N.ST5H": (34.9413, 139.4213), "N.ST6H": (35.0966, 139.3778),
    "N.NAE01": (32.7687, 134.2661), "N.NAE02": (32.4154, 134.3346),
    "N.NAE03": (32.1712, 134.2740), "N.NAE04": (32.0348, 133.9599),
    "N.NAE05": (31.7849, 133.6553), "N.NAE06": (31.5924, 133.3376),
    "N.NAE07": (31.5061, 133.1083), "N.NAE08": (31.2880, 132.7613),
    "N.NAE09": (31.1387, 132.3240), "N.NAE10": (31.1019, 131.9130),
    "N.NAE11": (31.3942, 132.0465), "N.NAE12": (31.5881, 132.4506),
    "N.NAE13": (31.7433, 132.8114), "N.NAE14": (31.9701, 133.0367),
    "N.NAE15": (32.1818, 132.7916), "N.NAE16": (31.9429, 132.5561),
    "N.NAE17": (31.7484, 132.4602), "N.NAE18": (31.3256, 131.7281),
    "N.NBE01": (33.2770, 134.3310), "N.NBE02": (33.0371, 134.2809),
    "N.NBE03": (32.8219, 134.0795), "N.NBE04": (32.9192, 133.6611),
    "N.NBE05": (32.5604, 133.7211), "N.NBE06": (32.4456, 134.0502),
    "N.NBE07": (32.2196, 133.9560), "N.NBE08": (32.1551, 133.7177),
    "N.NBE09": (31.9977, 133.3759), "N.NBE10": (32.1490, 133.2199),
    "N.NBE11": (32.4758, 133.4332), "N.NBE12": (32.3797, 133.1779),
    "N.NBE13": (32.3314, 132.8255), "N.NBE14": (32.4520, 132.5221),
    "N.NBE15": (32.3444, 132.2392), "N.NBE16": (31.9702, 132.1595),
    "N.NBE17": (31.7707, 132.0585), "N.NBE18": (31.6569, 131.7726),
}


class SnetConnector(DataSourceConnector):
    """S-net 海底测站数据连接器。

    下载 MSIL 瓦片 PNG，连同测站坐标一起 emit 原始数据。
    """

    REQUEST_TIMEOUT: float = 15.0

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__("snet", parent)
        self._timer: Optional[QTimer] = None
        self._stations: list[dict] = []
        self._poll_lock = threading.Lock()

    # ── 生命周期 ──

    def start(self) -> None:
        super().start()
        self._load_stations()
        self._set_status("connecting", "等待首次轮询 S-net")

        self._timer = QTimer(self)
        self._timer.setInterval(SNET_UPDATE_INTERVAL * 1000)
        self._timer.timeout.connect(self._poll)
        self._timer.start()

        self._poll()

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        self._set_status("disconnected", "手动停止")
        super().stop()

    # ── 内部 ──

    def _load_stations(self) -> None:
        """加载测站列表（坐标 + 瓦片像素位置）。"""
        base = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..",
            "resources", "geojson",
        )
        json_path = os.path.join(base, "ObsPoints.json")

        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                for tile_name in ("y11", "y12"):
                    points = data["tiles"]["z5"]["x28"][tile_name]
                    for pt in points:
                        name = pt["name"]
                        lat, lon = SNET_REAL_COORDS.get(name, (0, 0))
                        self._stations.append({
                            "name": name, "lat": lat, "lon": lon,
                            "tile": tile_name, "x": pt["x"], "y": pt["y"],
                        })
                logger.info("[snet] 从 ObsPoints.json 加载 %d 个测站", len(self._stations))
                return
            except Exception as e:
                logger.warning("[snet] 加载 ObsPoints.json 失败: %s", e)

        # 回退：仅用内置坐标
        for name, (lat, lon) in SNET_REAL_COORDS.items():
            self._stations.append({
                "name": name, "lat": lat, "lon": lon,
                "tile": "", "x": 0, "y": 0,
            })
        logger.info("[snet] 使用内置坐标，共 %d 个测站", len(self._stations))

    def _poll(self) -> None:
        """触发一次异步瓦片下载（非阻塞）。"""
        if not self._running:
            return
        if not self._poll_lock.acquire(blocking=False):
            return

        thread = threading.Thread(
            target=self._do_poll,
            daemon=True,
            name="snet-poll",
        )
        thread.start()

    def _do_poll(self) -> None:
        """后台线程：下载瓦片并 emit 原始数据。"""
        if not self._running:
            self._poll_lock.release()
            return

        now_utc = datetime.utcnow()
        data_time = now_utc - timedelta(seconds=SNET_GET_DELAY)
        data_time = data_time.replace(second=0, microsecond=0)
        time_str = data_time.strftime("%Y%m%d%H%M00")

        tiles = {}
        for name, filename in SNET_TILE_NAMES.items():
            if not self._running:
                self._poll_lock.release()
                return
            url = SNET_TILE_URL.format(time=time_str, tile=filename)
            try:
                resp = requests.get(url, timeout=self.REQUEST_TIMEOUT)
                resp.raise_for_status()
                tiles[name] = resp.content  # raw PNG bytes
            except requests.RequestException as e:
                logger.warning("[snet] 瓦片 %s 下载失败: %s", name, e)

        if len(tiles) < len(SNET_TILE_NAMES):
            self._set_status("error", "瓦片下载不完整")
            self._poll_lock.release()
            return

        self._set_status("connected", "正常")
        self._emit_raw({
            "type": "tile_data",
            "timestamp": time_str,
            "tiles": tiles,
            "stations": self._stations,
        })
        self._poll_lock.release()
