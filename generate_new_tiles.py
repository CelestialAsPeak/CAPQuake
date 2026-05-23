"""
generate_new_tiles.py
最终版：经纬度网格修复、多线程加速、边界无乱飞。
"""
import os
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pygame
from shapely.geometry import box, Point, Polygon, MultiPolygon
from shapely.validation import make_valid
from topojson_decoder import decode_topojson

# ==================== 配置 ====================
OUTPUT_DIR = r"C:\Users\ZhuanZ.DESKTOP-PH97BKO\Desktop\CAPQuake\Newtile"
ZOOM_LEVELS = range(0, 4)
TILE_SIZE = 4096

OCEAN_COLOR = (6, 6, 6)
LAND_COLOR = (40, 38, 38)
RED_COLOR = (200, 100, 100)
GRAY_COLOR = (135, 135, 137)

LINE_WIDTH_RED = 2
LINE_WIDTH_GRAY = 1

GRID_COARSE_STEP = 100.0
GRID_FINE_STEP = 20.0
GRID_COARSE_COLOR = (200, 100, 100)
GRID_FINE_COLOR = (180, 180, 180)
GRID_LINE_WIDTH = 1

WORLD_PATH = r"C:\Users\ZhuanZ.DESKTOP-PH97BKO\Desktop\CAPQuake\map\World.json"
CN_PROVINCE_TOPO = r"C:\Users\ZhuanZ.DESKTOP-PH97BKO\Desktop\CAPQuake\topojson\cn.province.topo.json"
CN_CITY_TOPO = r"C:\Users\ZhuanZ.DESKTOP-PH97BKO\Desktop\CAPQuake\topojson\cn.eew.topo.json"
JP_PREF_TOPO = r"C:\Users\ZhuanZ.DESKTOP-PH97BKO\Desktop\CAPQuake\topojson\jp.pref.topo.json"
JP_EEW_TOPO = r"C:\Users\ZhuanZ.DESKTOP-PH97BKO\Desktop\CAPQuake\topojson\jp.eew.topo.json"
KR_EEW_TOPO = r"C:\Users\ZhuanZ.DESKTOP-PH97BKO\Desktop\CAPQuake\topojson\kr.eew.topo.json"
BOUNDARIES_JS = r"C:\Users\ZhuanZ.DESKTOP-PH97BKO\AppData\Local\OXWU\resources\app\app\js\boundaries.js"

SIMPLIFY_RATIO_WORLD = 0.8
SIMPLIFY_RATIO_PROVINCE = 0.6
SIMPLIFY_RATIO_CITY = 0.3
SIMPLIFY_RATIO_TOWN = 0.15
SIMPLIFY_RATIO_TAIWAN_COUNTY = 0.6

MAX_WORKERS = 8

# ==================== 数据加载 ====================
def load_geojson(path):
    if not os.path.exists(path):
        print(f"警告：文件不存在 {path}")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    from shapely.geometry import shape as shapely_shape
    polygons = []
    for feat in data.get('features', []):
        geom = feat.get('geometry')
        if geom:
            try:
                s = shapely_shape(geom)
                if not s.is_valid:
                    s = make_valid(s)
                if not s.is_empty:
                    polygons.append(s)
            except:
                pass
    return polygons

def load_topojson(path, simplify=1.0):
    if not os.path.exists(path):
        print(f"警告：文件不存在 {path}")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        topo = json.load(f)
    return decode_topojson(topo, simplify_ratio=simplify)

def load_boundaries_js(filepath):
    if not os.path.exists(filepath):
        print(f"警告：boundaries.js 不存在 {filepath}")
        return None, None, None
    with open(filepath, 'rb') as f:
        raw = f.read()
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    content = raw.decode('utf-8')
    start = content.find('{')
    end = content.rfind('}')
    if start == -1 or end == -1:
        raise ValueError("未找到 JSON 部分")
    json_str = content[start:end+1]
    for key in ('towns', 'counties', 'foreigns'):
        json_str = json_str.replace(f'{key}:', f'"{key}":')
    json_str = json_str.rstrip(';')
    data = json.loads(json_str)
    return data.get('towns'), data.get('counties'), data.get('foreigns')

def load_all_data():
    print("加载世界数据...")
    world = load_geojson(WORLD_PATH)
    print(f"  世界数据: {len(world)} 个多边形")
    print("加载省界...")
    cn_prov = load_topojson(CN_PROVINCE_TOPO, SIMPLIFY_RATIO_PROVINCE)
    print(f"  中国省界: {len(cn_prov)} 个多边形")
    jp_prov = load_topojson(JP_PREF_TOPO, SIMPLIFY_RATIO_PROVINCE)
    print(f"  日本省界: {len(jp_prov)} 个多边形")
    kr_prov = load_topojson(KR_EEW_TOPO, SIMPLIFY_RATIO_PROVINCE)
    print(f"  韩国省界: {len(kr_prov)} 个多边形")
    print("加载市/乡镇...")
    cn_city = load_topojson(CN_CITY_TOPO, SIMPLIFY_RATIO_CITY)
    print(f"  中国市界: {len(cn_city)} 个多边形")
    jp_small = load_topojson(JP_EEW_TOPO, SIMPLIFY_RATIO_CITY)
    print(f"  日本小区域: {len(jp_small)} 个多边形")
    print("加载台湾数据...")
    towns_topo, counties_topo, foreigns_topo = load_boundaries_js(BOUNDARIES_JS)
    tw_towns = []
    tw_counties = []
    if towns_topo:
        tw_towns = decode_topojson(towns_topo, simplify_ratio=SIMPLIFY_RATIO_TOWN)
        print(f"  台湾乡镇: {len(tw_towns)} 个多边形")
    if counties_topo:
        tw_counties += decode_topojson(counties_topo, simplify_ratio=SIMPLIFY_RATIO_TAIWAN_COUNTY)
    if foreigns_topo:
        tw_counties += decode_topojson(foreigns_topo, simplify_ratio=SIMPLIFY_RATIO_TAIWAN_COUNTY)
    print(f"  台湾县市+离岛: {len(tw_counties)} 个多边形")
    return {
        'world': world,
        'cn_prov': cn_prov,
        'jp_prov': jp_prov,
        'kr_prov': kr_prov,
        'cn_city': cn_city,
        'jp_small': jp_small,
        'tw_counties': tw_counties,
        'tw_towns': tw_towns,
    }

DATA = None

# ==================== 绘图辅助 ====================
def draw_grid_lines(surf, lon_min, lon_max, lat_min, lat_max):
    step = int(GRID_FINE_STEP)
    # 修复跨180度经线的情况
    if lon_min > lon_max:
        lon_min -= 360

    for lon in range(math.floor(lon_min / step) * step,
                     math.ceil(lon_max / step) * step + 1, step):
        if lon < lon_min or lon > lon_max:
            continue
        color = GRID_COARSE_COLOR if lon % GRID_COARSE_STEP == 0 else GRID_FINE_COLOR
        display_lon = lon if lon <= lon_max else lon + 360
        x = int((display_lon - lon_min) / (lon_max - lon_min) * TILE_SIZE)
        pygame.draw.line(surf, color, (x, 0), (x, TILE_SIZE), GRID_LINE_WIDTH)

    for lat in range(math.floor(lat_min / step) * step,
                     math.ceil(lat_max / step) * step + 1, step):
        if lat < lat_min or lat > lat_max:
            continue
        color = GRID_COARSE_COLOR if lat % GRID_COARSE_STEP == 0 else GRID_FINE_COLOR
        y = int((lat_max - lat) / (lat_max - lat_min) * TILE_SIZE)
        pygame.draw.line(surf, color, (0, y), (TILE_SIZE, y), GRID_LINE_WIDTH)

def draw_polygon_filled(surf, polygon, color, project):
    outer = [project(x, y) for x, y in polygon.exterior.coords]
    if len(outer) >= 3:
        pygame.draw.polygon(surf, color, outer)
    for interior in polygon.interiors:
        inner = [project(x, y) for x, y in interior.coords]
        if len(inner) >= 3:
            pygame.draw.polygon(surf, OCEAN_COLOR, inner)

def draw_filled_polygons(surf, polys, color, bbox, project):
    tile_poly = box(*bbox)
    for poly in polys:
        if not poly.is_valid:
            continue
        if not tile_poly.intersects(poly):
            continue
        inter = poly.intersection(tile_poly)
        if inter.is_empty:
            continue
        if inter.geom_type == 'Polygon':
            draw_polygon_filled(surf, inter, color, project)
        elif inter.geom_type == 'MultiPolygon':
            for ip in inter.geoms:
                draw_polygon_filled(surf, ip, color, project)

def draw_world_boundary(surf, polys, bbox, project):
    tile_poly = box(*bbox)
    for poly in polys:
        if not poly.is_valid:
            continue
        if not tile_poly.intersects(poly):
            continue
        if poly.geom_type == 'MultiPolygon':
            sub_polys = list(poly.geoms)
        else:
            sub_polys = [poly]
        for sub in sub_polys:
            coords = sub.exterior.coords
            pts = [project(x, y) for x, y in coords]
            if len(pts) >= 2:
                pygame.draw.lines(surf, RED_COLOR, True, pts, LINE_WIDTH_RED)

def draw_admin_lines(surf, polys, color, width, project):
    for poly in polys:
        if not poly.is_valid:
            continue
        if poly.is_empty:
            continue
        if poly.geom_type == 'MultiPolygon':
            sub_polys = list(poly.geoms)
        elif poly.geom_type == 'Polygon':
            sub_polys = [poly]
        else:
            continue
        for sub in sub_polys:
            coords = list(sub.exterior.coords)
            if len(coords) < 2:
                continue
            for i in range(len(coords) - 1):
                x1, y1 = project(coords[i][0], coords[i][1])
                x2, y2 = project(coords[i+1][0], coords[i+1][1])
                if 0 < x1 < TILE_SIZE and 0 < y1 < TILE_SIZE and 0 < x2 < TILE_SIZE and 0 < y2 < TILE_SIZE:
                    pygame.draw.line(surf, color, (x1, y1), (x2, y2), width)

# ==================== 瓦片生成 ====================
def generate_tile(args):
    z, x, y = args
    z_std = z + 2
    lon_min = x / 2 ** z_std * 360 - 180
    lon_max = (x + 1) / 2 ** z_std * 360 - 180
    lat_max = 90 - y / 2 ** z_std * 180
    lat_min = 90 - (y + 1) / 2 ** z_std * 180
    bbox = (lon_min, lat_min, lon_max, lat_max)

    def project(lon, lat):
        px = (lon - lon_min) / (lon_max - lon_min) * TILE_SIZE
        py = (lat_max - lat) / (lat_max - lat_min) * TILE_SIZE
        return int(px), int(py)

    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(OCEAN_COLOR)

    global DATA
    show_detail = (z >= 2)

    # 1. 填充陆地
    try:
        draw_filled_polygons(surf, DATA['world'], LAND_COLOR, bbox, project)
    except Exception:
        pass

    # 2. 世界海岸线
    try:
        draw_world_boundary(surf, DATA['world'], bbox, project)
    except Exception:
        pass

    # 3. 灰色行政边界
    if show_detail:
        for polys, color, width in [
            (DATA['cn_city'], GRAY_COLOR, LINE_WIDTH_GRAY),
            (DATA['jp_small'], GRAY_COLOR, LINE_WIDTH_GRAY),
            (DATA['tw_towns'], GRAY_COLOR, LINE_WIDTH_GRAY)
        ]:
            try:
                draw_admin_lines(surf, polys, color, width, project)
            except Exception:
                pass

    # 4. 红色省级边界
    for polys in [
        DATA['cn_prov'],
        DATA['jp_prov'],
        DATA['kr_prov']
    ]:
        try:
            draw_admin_lines(surf, polys, RED_COLOR, LINE_WIDTH_RED, project)
        except Exception:
            pass

    if show_detail:
        try:
            draw_admin_lines(surf, DATA['tw_counties'], RED_COLOR, LINE_WIDTH_RED, project)
        except Exception:
            pass

    # 5. 经纬网（最上层）
    draw_grid_lines(surf, lon_min, lon_max, lat_min, lat_max)

    tile_dir = os.path.join(OUTPUT_DIR, str(z), str(x))
    os.makedirs(tile_dir, exist_ok=True)
    pygame.image.save(surf, os.path.join(tile_dir, f"{y}.png"))

def main():
    pygame.init()
    print("加载数据...")
    data = load_all_data()
    global DATA
    DATA = data
    print("数据加载完成，开始生成瓦片...")

    tasks = []
    for z in ZOOM_LEVELS:
        max_coord = 2 ** (z + 2)
        for x in range(max_coord):
            for y in range(max_coord):
                tasks.append((z, x, y))

    total = len(tasks)
    print(f"共 {total} 个瓦片")
    start = time.time()
    done = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(generate_tile, task): task for task in tasks}
        for future in as_completed(futures):
            done += 1
            if done % 50 == 0 or done == total:
                print(f"已完成 {done}/{total}")

    print(f"全部完成，耗时 {time.time()-start:.1f} 秒")
    pygame.quit()

if __name__ == "__main__":
    main()