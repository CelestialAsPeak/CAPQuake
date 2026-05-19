╔══════════════════════════════════════════════════════════════════════════════╗
║             CAPQuakeQt  数据层连接器 API 说明                            ║
║             data/connectors/ — 共 15 个连接器                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
一、WebSocket 实时流（3个）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. fan  —  FAN Studio 全数据
─────────────────────────────────────────────────────────────────────────────
   URL:        wss://ws.fanstudio.tech/all          (主)
               wss://ws.fanstudio.hk/all          (HK 备用)
   来源:       FAN Studio (第三方地震数据聚合平台)
   数据内容:   全球地震情报 + EEW 预警（JMA/CWA/CEA 等）+ 测站数据
   协议:       WebSocket，连接后发 {"type":"query"} 即可开始接收
   旧版对比:   功能不变，新架构用统一 Connector 接口 + 多 URL 故障转移

2. wolfx  —  Wolfx EEW 预警
─────────────────────────────────────────────────────────────────────────────
   URL:        wss://ws-api.wolfx.jp/all_eew
   来源:       Wolfx Japan
   数据内容:   JMA EEW, CENC EEW, CWA EEW, SC EEW, FJ EEW（5 子源）
   协议:       WebSocket，连接后发 query_jmaeew / query_sceew 等订阅
   旧版对比:   功能不变，新增自动重连 + 连接状态上报

3. p2p  —  P2PQuake 地震情報
─────────────────────────────────────────────────────────────────────────────
   URL:        wss://api.p2pquake.net/v2/ws
   来源:       P2PQuake (日本)
   数据内容:   日本地震情報 (code 551) + 緊急地震速報 (code 556) + 海嘯 (code 552)
   协议:       WebSocket，发送 "ping" 保活
   旧版对比:   功能不变

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
二、HTTP 轮询（9个）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. usgs  —  USGS 全球地震（每小时）
─────────────────────────────────────────────────────────────────────────────
   URL:        https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson
   来源:       USGS (美国地质调查局)
   轮询间隔:   30 秒
   数据内容:   过去一小时的全球地震（GeoJSON FeatureCollection）
   旧版对比:   功能不变

5. usgs-weekly  —  USGS 全球地震周报 ★ 新增
─────────────────────────────────────────────────────────────────────────────
   URL:        https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson
   来源:       USGS
   轮询间隔:   300 秒（5 分钟）
   数据内容:   过去一周 M≥2.5 的全球地震列表
   旧版对比:   Pygame 版没有，CAPQuakeProK 有

6. cenc  —  CENC 中国地震列表
─────────────────────────────────────────────────────────────────────────────
   URL:        https://api.wolfx.jp/cenc_eqlist.json
   来源:       Wolfx 代转发 CENC（中国地震台网中心）
   轮询间隔:   30 秒
   数据内容:   中国及邻区地震事件列表
   旧版对比:   功能不变

7. jma  —  JMA 日本地震列表
─────────────────────────────────────────────────────────────────────────────
   URL:        https://api.wolfx.jp/jma_eqlist.json
   来源:       Wolfx 代转发 JMA（日本气象厅）
   轮询间隔:   30 秒
   数据内容:   日本及周边地震事件列表（含震度信息）
   旧版对比:   功能不变

8. kmoni  —  NIED Kmoni 最新震源 ★ 新增
─────────────────────────────────────────────────────────────────────────────
   URL:        http://www.kmoni.bosai.go.jp/webservice/server/pros/latest.json
   来源:       NIED（日本防灾科学技术研究所）強震モニタ
   轮询间隔:   30 秒
   数据内容:   日本最新震源信息（包含震源坐标、深度、震级等）
   旧版对比:   Pygame 版没有，CAPQuakeProK 有但未活跃使用

9. p2p-history  —  P2P 地震历史 ★ 新增
─────────────────────────────────────────────────────────────────────────────
   URL:        https://api.p2pquake.net/v2/history?codes=551&limit=50
   来源:       P2PQuake
   轮询间隔:   30 秒
   数据内容:   最近 50 条日本地震情报（code 551）
   旧版对比:   Pygame 版有（作为 P2P HTTP 备用），原分离为独立连接器

10. p2p-tsunami  —  P2P 海啸预报 ★ 新增
─────────────────────────────────────────────────────────────────────────────
   URL:         https://api.p2pquake.net/v2/history?codes=552&limit=1
   来源:        P2PQuake
   轮询间隔:    60 秒
   数据内容:    最新海啸预报（code 552）
   旧版对比:    Pygame 版有但默认禁用；CAPQuakeProK 有

11. wolfx-http  —  Wolfx EEW HTTP 备用 ★ 新增
─────────────────────────────────────────────────────────────────────────────
   子源 URLs:
     JMA:   https://api.wolfx.jp/jma_eew.json
     SC:    https://api.wolfx.jp/sc_eew.json
     CENC:  https://api.wolfx.jp/cenc_eew.json
     FJ:    https://api.wolfx.jp/fj_eew.json
     CWA:   https://api.wolfx.jp/cwa_eew.json
   来源:        Wolfx Japan
   轮询间隔:    30 秒（全部轮询一次）
   数据内容:   5 个 EEW 子源的 JSON 数据，WS 断连时作为备用
   旧版对比:   Pygame 版有（WolfxHttpFetcher），独立为连接器

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
三、测站监控（3个）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

12. nied  —  NIED 強震モニタ（Yahoo 日本）
─────────────────────────────────────────────────────────────────────────────
   URL:        https://weather-kyoshin.east.edge.storage-yahoo.jp/SiteList/sitelist.json
               https://weather-kyoshin.west.edge.storage-yahoo.jp/RealTimeData/{date}/{time}.json
   来源:       NIED / LY Corporation (Yahoo Japan)
   轮询间隔:   5 秒
   数据内容:   日本全国约 1000 个地震观测点的实时震度
   旧版对比:   功能不变

13. kma-station  —  KMA 韩国测站 ★ 改进
─────────────────────────────────────────────────────────────────────────────
   URL:        wss://ws.fanstudio.tech/kma-station    (主)
               wss://ws.fanstudio.hk/kma-station    (HK 备用)
   来源:       FAN Studio 转发 KMA（韩国气象厅）
   数据内容:   韩国地震观测站列表 + 实时 MMI 数据
   旧版对比:   Pygame 版无此连接器；CAPQuakeProK 有。新增 HK 备用 URL

14. snet  —  S-net 日本海底测站
─────────────────────────────────────────────────────────────────────────────
   URL:        https://www.msil.go.jp/data/tiles/smoni/tileimage/{time}/{time}/5/28/{tile}.png
   来源:       MSIL (日本海上自卫队)
   轮询间隔:   60 秒
   数据内容:   S-net 海底地震计 tile 图片（解析 RGB 获得震度值）
   旧版对比:   功能不变。CAPQuakeProK 没有此源

15. palert  —  P-Alert 台湾测站
─────────────────────────────────────────────────────────────────────────────
   URL:        https://palert.earth.sinica.edu.tw/graphql/
   来源:       中央研究院地球科学研究所（台湾）
   轮询间隔:   3 秒
   数据内容:   台湾 P-Alert 地震预警站的实时 PGA 值（约 600 站）
   旧版对比:   功能不变。CAPQuakeProK 没有此源

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
四、新架构对比 Pygame 版改进
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 统一接口：所有连接器继承 DataSourceConnector ABC
   - 标准化 start/stop/restart 生命周期
   - 统一信号 raw_data / status_changed
   - 统一状态机 connecting → connected → disconnected → error

2. 新增功能：
   - WebSocket 多 URL 故障转移（主 URL 断连自动切备用）
   - 线性退避重连（3s→4s→...→10s→切 URL）
   - 连接超时检测（10 秒无响应主动断开）
   - 心跳自动回复（如 Wolfx 的 pong）
   - HTTP 4xx/5xx 区分处理（4xx 不重试）
   - 每种连接器独立状态上报

3. 新增数据源（Pygame 版没有的）：
   - usgs-weekly（USGS 周报）
   - kmoni（NIED Kmoni 最新震源）
   - kma-station（KMA 韩国测站 WebSocket）

4. 删除的旧源：
   - kmoni-eew（端点永久 404）

5. 三项目对比表：

   数据源                我们的Qt     Pygame版    CAPQuakeProK
   ─────────────────────────────────────────────────────────
   FAN WS                   ✅          ✅          ✅
   Wolfx WS                 ✅          ✅          ✅
   Wolfx HTTP               ✅          ✅          ❌
   P2P WS                   ✅          ✅          ✅
   P2P 历史(code 551)       ✅          ✅          ✅
   P2P 海啸(code 552)       ✅          ❌(禁用)    ✅
   USGS 每小时              ✅          ✅          ❌
   USGS 周报                ✅          ❌          ✅
   CENC 列表                ✅          ✅          ✅(通过FAN)
   JMA 列表                 ✅          ✅          ✅(通过P2P)
   NIED Kmoni               ✅          ❌          ✅(不活跃)
   NIED 测站(Yahoo)         ✅          ✅          ✅
   KMA 测站 WS              ✅          ❌          ✅
   S-net                    ✅          ✅          ❌
   P-Alert                  ✅          ✅          ❌
   kmoni-eew                ❌(删)      ❌          ❌(死端点)

   总计: 15 连接器，全部 15 个通过测试（10 秒内至少收到一次数据）。
