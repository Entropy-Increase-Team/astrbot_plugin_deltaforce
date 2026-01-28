"""
数据查询处理器
包含：个人数据、流水记录、战绩记录、地图统计等
"""
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp
from datetime import datetime
from .base import BaseHandler
from ..utils.render import Render


class DataHandler(BaseHandler):
    """数据查询处理器"""

    # 段位分数映射
    SOL_RANK_THRESHOLDS = [
        (0, '青铜 V'), (100, '青铜 IV'), (200, '青铜 III'), (300, '青铜 II'), (400, '青铜 I'),
        (500, '白银 V'), (650, '白银 IV'), (800, '白银 III'), (950, '白银 II'), (1100, '白银 I'),
        (1250, '黄金 V'), (1450, '黄金 IV'), (1650, '黄金 III'), (1850, '黄金 II'), (2050, '黄金 I'),
        (2250, '铂金 V'), (2500, '铂金 IV'), (2750, '铂金 III'), (3000, '铂金 II'), (3250, '铂金 I'),
        (3500, '钻石 V'), (3800, '钻石 IV'), (4100, '钻石 III'), (4400, '钻石 II'), (4700, '钻石 I'),
        (5000, '黑鹰 V'), (5400, '黑鹰 IV'), (5800, '黑鹰 III'), (6200, '黑鹰 II'), (6600, '黑鹰 I'),
        (7000, '三角洲巅峰'),
    ]
    
    TDM_RANK_THRESHOLDS = [
        (0, '列兵 V'), (100, '列兵 IV'), (200, '列兵 III'), (300, '列兵 II'), (400, '列兵 I'),
        (500, '上等兵 V'), (650, '上等兵 IV'), (800, '上等兵 III'), (950, '上等兵 II'), (1100, '上等兵 I'),
        (1250, '军士长 V'), (1450, '军士长 IV'), (1650, '军士长 III'), (1850, '军士长 II'), (2050, '军士长 I'),
        (2250, '尉官 V'), (2500, '尉官 IV'), (2750, '尉官 III'), (3000, '尉官 II'), (3250, '尉官 I'),
        (3500, '校官 V'), (3800, '校官 IV'), (4100, '校官 III'), (4400, '校官 II'), (4700, '校官 I'),
        (5000, '将军 V'), (5400, '将军 IV'), (5800, '将军 III'), (6200, '将军 II'), (6600, '将军 I'),
        (7000, '统帅'),
    ]

    # 硬编码地图ID映射（作为兜底）
    MAP_ID_MAPPING = {
        "101": "零号大坝-常规", "102": "零号大坝-机密", "103": "零号大坝-绝密",
        "201": "长弓溪谷-常规", "202": "长弓溪谷-机密", "203": "长弓溪谷-绝密",
        "301": "航天基地-常规", "302": "航天基地-机密", "303": "航天基地-绝密",
        "401": "巴克什-常规", "402": "巴克什-机密", "403": "巴克什-绝密",
        "1101": "零号大坝-全面", "1201": "长弓溪谷-全面", "1301": "攀升", "1401": "裂痕",
        "2002": "堑壕战", "2007": "全面-攀升", "5001": "临界点",
        # 兼容用户已知的奇怪ID
        "1981": "航天基地-常规", "1121": "零号大坝-常规", "154": "巴克什-常规",
        "121": "零号大坝-常规", "54": "巴克什-常规",
        # 更多映射可自行补充，优先尝试使用 search_object 接口或 ID 直接显示
    }

    def _format_price(self, price):
        """格式化金钱"""
        if not price:
            return '-'
        try:
            num = float(price)
            if num >= 1000000000:
                return f"{num / 1000000000:.2f}B"
            elif num >= 1000000:
                return f"{num / 1000000:.2f}M"
            elif num >= 1000:
                return f"{num / 1000:.1f}K"
            else:
                return f"{int(num)}"
        except:
            return str(price)

    def _format_kd(self, kd):
        """格式化KD"""
        if kd is None:
            return '-'
        try:
            return f"{float(kd) / 100:.2f}"
        except:
            return '-'
            
    def _format_rate(self, rate):
        """格式化百分比 (输入可能是整数如 2500 表示 25.00%)"""
        if rate is None:
            return '-'
        try:
            # 假设输入是放大100倍的整数
            if float(rate) > 1: 
                return f"{float(rate)/100:.1f}%"
            # 如果输入已经是小数
            return f"{float(rate)*100:.1f}%"
        except:
            return '-'

    async def _get_object_names(self, ids: list) -> dict:
        """批量获取物品名称"""
        if not ids:
            return {}
        try:
            # 去重
            ids = list(set(str(i) for i in ids))
            # 批量查询
            res = await self.api.search_object(object_ids=",".join(ids))
            name_map = {}
            if self.is_success(res):
                keywords = res.get("data", {}).get("keywords", [])
                for item in keywords:
                    name_map[str(item.get("objectID"))] = item.get("name") or item.get("objectName")
            return name_map
        except Exception as e:
            return {}

    def get_rank_by_score(self, score: int, mode: str = 'sol') -> str:
        """根据分数获取段位名称"""
        try:
            score = int(score) if score else 0
        except:
            return '未定级'
        
        thresholds = self.SOL_RANK_THRESHOLDS if mode == 'sol' else self.TDM_RANK_THRESHOLDS
        rank_name = '未定级'
        for threshold, name in thresholds:
            if score >= threshold:
                rank_name = name
            else:
                break
        return rank_name

    async def get_personal_data(self, event: AstrMessageEvent, args: str = ""):
        """个人数据查询"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        # 解析参数
        mode = ""
        season = "7"
        if args:
            parts = args.strip().split()
            for part in parts:
                part_lower = part.lower()
                if part_lower in ["烽火", "烽火地带", "sol", "摸金"]:
                    mode = "sol"
                elif part_lower in ["全面", "全面战场", "战场", "mp"]:
                    mode = "mp"
                elif part_lower in ["all", "全部"]:
                    season = "all"
                elif part.isdigit():
                    season = part

        yield self.chain_reply(event, "正在查询个人数据，请稍候...")

        result = await self.api.get_personal_data(frameworkToken=token, mode=mode, season=season)
        if not result:
            yield self.chain_reply(event, "查询数据失败，请检查网络或联系管理员")
            return

        if not self.is_success(result):
            yield self.chain_reply(event, f"查询数据失败：{self.get_error_msg(result)}")
            return

        # 解析数据
        sol_detail = None
        mp_detail = None

        if mode:
            single_data = result.get("data", {}).get("data", {}).get("data", {})
            sol_detail = single_data.get("solDetail")
            mp_detail = single_data.get("mpDetail")
        else:
            all_data = result.get("data", {})
            sol_data = all_data.get("sol", {}).get("data", {}).get("data", {})
            mp_data = all_data.get("mp", {}).get("data", {}).get("data", {})
            sol_detail = sol_data.get("solDetail")
            mp_detail = mp_data.get("mpDetail")

        if not sol_detail and not mp_detail:
            yield self.chain_reply(event, "暂未查询到该账号的游戏数据")
            return

        # ---------------- 数据预处理 ----------------
        
        # 1. 批量查询物品名称 (收藏品、武器)
        query_ids = set()
        if sol_detail:
            for item in sol_detail.get('redList', []) or []:
                if item.get('objectID'): query_ids.add(item['objectID'])
            for item in sol_detail.get('gunPlayList', []) or []:
                if item.get('objectID'): query_ids.add(item['objectID'])
        
        name_map = await self._get_object_names(list(query_ids))

        # 2. 处理烽火地带数据
        processed_sol = None
        if sol_detail and (not mode or mode == "sol"):
            processed_sol = sol_detail.copy()
            # 格式化基础数据
            processed_sol['totalGainedPriceFormatted'] = self._format_price(sol_detail.get('totalGainedPrice'))
            processed_sol['redTotalMoneyStr'] = self._format_price(sol_detail.get('redTotalMoney') or sol_detail.get('totalMoney')) # 兼容字段
            processed_sol['kdRatio'] = self._format_kd(sol_detail.get('kdRatio')) # 原始数据可能是整数(放大100倍)或小数
            
            # TS 模板兼容别名
            processed_sol['totalEscape'] = sol_detail.get('escapeGames', 0)
            processed_sol['totalFight'] = sol_detail.get('totalGames', 0)
            processed_sol['totalKill'] = sol_detail.get('totalKills', 0)
            processed_sol['userRank'] = sol_detail.get('userRank', '-')
            processed_sol['lowKD'] = self._format_kd(sol_detail.get('lowKillDeathRatio'))
            processed_sol['medKD'] = self._format_kd(sol_detail.get('medKillDeathRatio'))
            processed_sol['highKD'] = self._format_kd(sol_detail.get('highKillDeathRatio'))
            
            processed_sol['headshotRate'] = self._format_rate(sol_detail.get('headshotRate'))
            processed_sol['escapeRate'] = self._format_rate(sol_detail.get('escapeRate'))
            processed_sol['totalGameTime'] = self.format_duration(sol_detail.get('totalDuration', 0))
            
            # 处理地图列表
            raw_map_list = sol_detail.get('mapList', []) or []
            # 丰富地图信息
            enriched_maps = []
            for m in raw_map_list:
                map_id = str(m.get('mapID'))
                # 优先查表以确保名称格式统一（包含难度后缀），否则使用 API 返回的名称
                map_name = self.MAP_ID_MAPPING.get(map_id) or m.get('mapName') or f"未知地图({map_id})"
                # 分组基准名 (去除后缀)
                import re
                base_map_name = re.sub(r'-?(常规|机密|绝密|水淹|适应|前夜|永夜|终夜|普通|困难|极限)$', '', map_name)
                
                enriched_maps.append({
                    **m,
                    'mapName': map_name,
                    'baseMapName': base_map_name,
                    'mapImage': Render.get_map_image(map_name, 'sol') or "",
                })
            
            # 分组
            map_groups = {}
            # 固定排序
            map_order = ['零号大坝', '长弓溪谷', '巴克什', '航天基地', '潮汐监狱']
            for m in enriched_maps:
                base = m['baseMapName']
                if base not in map_groups:
                    map_groups[base] = []
                map_groups[base].append(m)
            
            final_map_list = []
            # 先按固定顺序添加存在的组
            for base in map_order:
                if base in map_groups:
                    group_maps = map_groups[base]
                    # 组内按场次降序
                    group_maps.sort(key=lambda x: x.get('totalCount', 0), reverse=True)
                    final_map_list.append({'baseMapName': base, 'maps': group_maps})
                    del map_groups[base]
            
            # 添加剩余的组
            for base, maps in map_groups.items():
                maps.sort(key=lambda x: x.get('totalCount', 0), reverse=True)
                final_map_list.append({'baseMapName': base, 'maps': maps})
                
            # 合并仅包含单张地图的组，减少行数以避免渲染过长
            merged_map_list = []
            pending_single_groups = []

            def flush_pending():
                nonlocal pending_single_groups
                if len(pending_single_groups) > 1:
                    merged_maps = []
                    for group in pending_single_groups:
                        merged_maps.extend(group.get('maps', []))
                    merged_map_list.append({'baseMapName': 'merged', 'maps': merged_maps})
                elif len(pending_single_groups) == 1:
                    merged_map_list.append(pending_single_groups[0])
                pending_single_groups = []

            for group in final_map_list:
                if len(group.get('maps', [])) == 1:
                    pending_single_groups.append(group)
                else:
                    flush_pending()
                    merged_map_list.append(group)
            flush_pending()

            processed_sol['mapList'] = merged_map_list

            # 处理武器列表
            raw_guns = sol_detail.get('gunPlayList', []) or []
            processed_guns = []
            for g in raw_guns:
                oid = str(g.get('objectID'))
                name = name_map.get(oid) or f"武器({oid})"
                processed_guns.append({
                    **g,
                    'weaponName': name,
                    'imageUrl': f"https://playerhub.df.qq.com/playerhub/60004/object/{oid}.png",
                    'totalPriceFormatted': self._format_price(g.get('totalPrice')),
                    'fightCount': g.get('fightCount', 0),
                    'escapeCount': g.get('escapeCount', 0),
                })
            # 按收益降序取前10
            processed_guns.sort(key=lambda x: x.get('totalPrice', 0) or 0, reverse=True)
            processed_sol['gunPlayList'] = processed_guns[:10]

            # 处理收藏品 (兼容 TS 逻辑：取前10)
            raw_reds = sol_detail.get('redCollectionDetail', []) or sol_detail.get('redList', []) or []
            processed_reds = []
            for r in raw_reds:
                oid = str(r.get('objectID'))
                name = name_map.get(oid) or f"物品({oid})"
                price = r.get('price') or r.get('totalPrice') or 0
                processed_reds.append({
                    **r,
                    'name': name,
                    'objectName': name, # TS 字段
                    'imageUrl': f"https://playerhub.df.qq.com/playerhub/60004/object/{oid}.png",
                    'count': r.get('count', r.get('totalCount', 0)),
                    'price': self._format_price(price),
                    'priceFormatted': self._format_price(price), # TS 字段
                    '_raw_price': float(price) if price else 0
                })
            # 按价格降序
            processed_reds.sort(key=lambda x: x['_raw_price'], reverse=True)
            # 取前10
            processed_sol['redList'] = processed_reds[:10]
            processed_sol['redCollectionList'] = processed_reds[:10]

        # 3. 处理全面战场数据
        processed_mp = None
        if mp_detail and (not mode or mode == "mp"):
            processed_mp = mp_detail.copy()
            processed_mp['winRatio'] = processed_mp.get('winRate') # 兼容字段名
            processed_mp['totalScoreStr'] = self._format_price(mp_detail.get('totalScore')) 
            processed_mp['avgKillPerMinuteFormatted'] = f"{float(mp_detail.get('avgKillPerMinute', 0))/100:.2f}"
            processed_mp['avgScorePerMinuteFormatted'] = f"{float(mp_detail.get('avgScorePerMinute', 0))/100:.2f}"
            processed_mp['totalGameTime'] = self.format_duration(mp_detail.get('totalDuration', 0), 'minutes')
            
            # TS 模板兼容别名
            processed_mp['totalFight'] = mp_detail.get('totalGames', 0)
            processed_mp['totalWin'] = mp_detail.get('winGames', 0)
            processed_mp['totalVehicleKill'] = mp_detail.get('vehicleKills', 0) # API key might vary, assuming vehicleKills or checking?
            # Actually standard API: vehicleKills?
            # Let's check get_record or similar? 
            # Assuming 'vehicleKills' or 'totalVehicleKills'. 
            # If not sure, use safe get.
            processed_mp['totalVehicleKill'] = mp_detail.get('vehicleKills') or mp_detail.get('totalVehicleKills', 0)
            processed_mp['totalVehicleDestroyed'] = mp_detail.get('vehicleDestroyed') or mp_detail.get('totalVehicleDestroyed', 0)

            # 处理地图
            raw_mp_maps = mp_detail.get('mapList', []) or []
            processed_mp_maps = []
            for m in raw_mp_maps:
                map_id = str(m.get('mapID'))
                map_name = m.get('mapName') or self.MAP_ID_MAPPING.get(map_id) or f"未知地图({map_id})"
                processed_mp_maps.append({
                    **m,
                    'mapName': map_name,
                    'mapImage': Render.get_map_image(map_name, 'mp') or "",
                })
            processed_mp_maps.sort(key=lambda x: x.get('totalCount', 0), reverse=True)
            processed_mp['mapList'] = processed_mp_maps[:10]


        # 准备渲染数据
        render_data = {
            'backgroundImage': Render.get_background_image(),
            'season': season if season != 'all' else '全部',
            'mode': mode,
            'userName': result.get("roleInfo", {}).get("charac_name", "未知战士"),
            'userAvatar': result.get("roleInfo", {}).get("picurl") or f"http://q.qlogo.cn/headimg_dl?dst_uin={event.get_sender_id()}&spec=640",
            'qqAvatarUrl': f"http://q.qlogo.cn/headimg_dl?dst_uin={event.get_sender_id()}&spec=640",
            'currentDate': datetime.fromtimestamp(event.message_obj.timestamp).strftime("%Y-%m-%d") if hasattr(event.message_obj, 'timestamp') and isinstance(event.message_obj.timestamp, (int, float)) else (event.message_obj.timestamp.strftime("%Y-%m-%d") if hasattr(event.message_obj, 'timestamp') and hasattr(event.message_obj.timestamp, 'strftime') else ""),
            
            'solDetail': processed_sol,
            'mpDetail': processed_mp,
            
            # 烽火地带段位
            'solRank': self.get_rank_by_score(sol_detail.get('rankPoint', 0), 'sol') if sol_detail else '-',
            'solRankImage': Render.get_rank_image(
                self.get_rank_by_score(sol_detail.get('rankPoint', 0), 'sol'), 'sol'
            ) if sol_detail else None,
            
            # 全面战场段位
            'mpRank': self.get_rank_by_score(mp_detail.get('rankPoint', 0), 'tdm') if mp_detail else '-',
            'mpRankImage': Render.get_rank_image(
                self.get_rank_by_score(mp_detail.get('rankPoint', 0), 'tdm'), 'mp'
            ) if mp_detail else None,
        }

        # 尝试渲染图片
        fallback_text = self._build_personal_data_text(season, mode, sol_detail, mp_detail)

        yield await self.render_and_reply(
            event,
            'personalData/personalData.html',
            render_data,
            fallback_text=fallback_text,
            width=2000
        )

    def _build_personal_data_text(self, season, mode, sol_detail, mp_detail):
        """构建纯文本个人数据（渲染失败时的回退）"""
        output_lines = ["📊【个人数据统计】📊"]
        output_lines.append(f"赛季: {season if season != 'all' else '全部'}")
        output_lines.append("━━━━━━━━━━━━━━━")

        # 烽火地带数据
        if sol_detail and (not mode or mode == "sol"):
            output_lines.append("")
            output_lines.append("🔥【烽火地带】")
            output_lines.append(f"  对局数: {sol_detail.get('totalGames', 0)}")
            output_lines.append(f"  撤离数: {sol_detail.get('escapeGames', 0)}")
            output_lines.append(f"  撤离率: {sol_detail.get('escapeRate', '0%')}")
            output_lines.append(f"  击杀数: {sol_detail.get('totalKills', 0)}")
            output_lines.append(f"  死亡数: {sol_detail.get('totalDeaths', 0)}")
            output_lines.append(f"  KD比: {sol_detail.get('kdRatio', '0')}")
            output_lines.append(f"  爆头率: {sol_detail.get('headshotRate', '0%')}")
            output_lines.append(f"  伤害输出: {sol_detail.get('totalDamage', 0)}")
            output_lines.append(f"  游戏时长: {self.format_duration(sol_detail.get('totalDuration', 0))}")

        # 全面战场数据
        if mp_detail and (not mode or mode == "mp"):
            output_lines.append("")
            output_lines.append("⚔️【全面战场】")
            output_lines.append(f"  对局数: {mp_detail.get('totalGames', 0)}")
            output_lines.append(f"  胜场数: {mp_detail.get('winGames', 0)}")
            output_lines.append(f"  胜率: {mp_detail.get('winRate', '0%')}")
            output_lines.append(f"  击杀数: {mp_detail.get('totalKills', 0)}")
            output_lines.append(f"  死亡数: {mp_detail.get('totalDeaths', 0)}")
            output_lines.append(f"  KD比: {mp_detail.get('kdRatio', '0')}")
            output_lines.append(f"  助攻数: {mp_detail.get('totalAssists', 0)}")
            output_lines.append(f"  伤害输出: {mp_detail.get('totalDamage', 0)}")
            output_lines.append(f"  游戏时长: {self.format_duration(mp_detail.get('totalDuration', 0), 'minutes')}")

        return "\n".join(output_lines)

    async def get_flows(self, event: AstrMessageEvent, args: str = ""):
        """流水记录查询"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        # 解析参数
        type_map = {"设备": 1, "道具": 2, "货币": 3}
        flow_type = 1  # 默认设备
        page = 1

        if args:
            parts = args.strip().split()
            for part in parts:
                if part in type_map:
                    flow_type = type_map[part]
                elif part.isdigit():
                    page = int(part)

        type_names = {1: "设备", 2: "道具", 3: "货币"}
        yield self.chain_reply(event, f"正在查询{type_names[flow_type]}流水记录，请稍候...")

        result = await self.api.get_flows(frameworkToken=token, flow_type=flow_type, page=page)
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取流水记录失败：{self.get_error_msg(result)}")
            return

        data = result.get("data", [])
        if not data:
            yield self.chain_reply(event, "暂无流水记录")
            return

        first_data = data[0] if isinstance(data, list) else data

        # 准备渲染数据
        render_data = {
            'backgroundImage': Render.get_background_image(),
            'typeName': type_names[flow_type],
            'typeValue': flow_type,
            'page': page,
        }

        if flow_type == 1:
            # 设备登录记录
            login_arr = first_data.get("LoginArr", [])
            render_data['playerInfo'] = {
                'vRoleName': first_data.get('vRoleName', '未知'),
                'Level': first_data.get('Level', '未知'),
                'loginDay': first_data.get('loginDay', '未知'),
            }
            render_data['totalCount'] = len(login_arr)
            
            # 处理登录列 - 分成5列显示
            login_records = []
            for idx, record in enumerate(login_arr[:20], 1):
                login_records.append({
                    'index': idx,
                    'indtEventTime': record.get('indtEventTime', '未知'),
                    'outdtEventTime': record.get('outdtEventTime', '未知'),
                    'vClientIP': record.get('vClientIP', '未知'),
                    'SystemHardware': record.get('SystemHardware', '未知'),
                })
            # 将记录分成5列
            columns_count = 5
            items_per_column = (len(login_records) + columns_count - 1) // columns_count
            login_columns = []
            for i in range(columns_count):
                start = i * items_per_column
                end = start + items_per_column
                if start < len(login_records):
                    login_columns.append(login_records[start:end])
            render_data['loginColumns'] = login_columns
            
            # 统计设备和IP
            device_stats = {}
            ip_stats = {}
            for record in login_arr:
                device = record.get('SystemHardware', '未知')
                ip = record.get('vClientIP', '未知')
                device_stats[device] = device_stats.get(device, 0) + 1
                ip_stats[ip] = ip_stats.get(ip, 0) + 1
            
            render_data['deviceStats'] = [{'name': k, 'count': v} for k, v in sorted(device_stats.items(), key=lambda x: -x[1])[:5]]
            render_data['ipStats'] = [{'ip': k, 'count': v} for k, v in sorted(ip_stats.items(), key=lambda x: -x[1])[:5]]

        elif flow_type == 2:
            # 道具记录
            item_arr = first_data.get("itemArr", [])
            item_records = []
            for idx, record in enumerate(item_arr[:20], 1):
                count = record.get('iCount', 0)
                item_records.append({
                    'index': idx,
                    'dtEventTime': record.get('dtEventTime', '未知'),
                    'Name': record.get('iItemID', '未知'),
                    'Reason': self.decode_url(record.get("vReason", "")),
                    'changeType': 'positive' if count >= 0 else 'negative',
                    'AddOrReduce': f"+{count}" if count >= 0 else str(count),
                })
            # 将记录分成5列
            columns_count = 5
            items_per_column = (len(item_records) + columns_count - 1) // columns_count
            item_columns = []
            for i in range(columns_count):
                start = i * items_per_column
                end = start + items_per_column
                if start < len(item_records):
                    item_columns.append(item_records[start:end])
            render_data['itemColumns'] = item_columns

        elif flow_type == 3:
            # 货币记录
            money_arr = first_data.get("iMoneyArr", [])
            money_records = []
            for idx, record in enumerate(money_arr[:20], 1):
                change = record.get('iChange', 0)
                money_records.append({
                    'index': idx,
                    'dtEventTime': record.get('dtEventTime', '未知'),
                    'Reason': self.decode_url(record.get("vReason", "")),
                    'changeType': 'positive' if change >= 0 else 'negative',
                    'AddOrReduce': f"+{change}" if change >= 0 else str(change),
                    'leftMoney': record.get('iMoney', 0),
                })
            # 将记录分成5列
            columns_count = 5
            items_per_column = (len(money_records) + columns_count - 1) // columns_count
            money_columns = []
            for i in range(columns_count):
                start = i * items_per_column
                end = start + items_per_column
                if start < len(money_records):
                    money_columns.append(money_records[start:end])
            render_data['moneyColumns'] = money_columns

        yield await self.render_and_reply(
            event,
            'flows/flows.html',
            render_data,
            fallback_text=self._build_flows_text(first_data, flow_type, page),
            width=2200,
            height=900
        )

    def _build_flows_text(self, first_data, flow_type, page):
        """构建纯文本流水记录（渲染失败时的回退）"""
        type_names = {1: "设备", 2: "道具", 3: "货币"}
        output_lines = [f"📜【{type_names[flow_type]}流水记录】第{page}页"]
        output_lines.append("━━━━━━━━━━━━━━━")

        if flow_type == 1:
            login_arr = first_data.get("LoginArr", [])
            if first_data.get("vRoleName"):
                output_lines.append(f"角色: {first_data.get('vRoleName', '未知')}")
                output_lines.append(f"等级: {first_data.get('Level', '未知')}")
                output_lines.append(f"登录天数: {first_data.get('loginDay', '未知')}")
                output_lines.append("")

            if login_arr:
                for i, record in enumerate(login_arr[:10], 1):
                    output_lines.append(f"【{i}】")
                    output_lines.append(f"  登入: {record.get('indtEventTime', '未知')}")
                    output_lines.append(f"  登出: {record.get('outdtEventTime', '未知')}")
                    output_lines.append(f"  IP: {record.get('vClientIP', '未知')}")
                    output_lines.append(f"  设备: {record.get('SystemHardware', '未知')}")
                if len(login_arr) > 10:
                    output_lines.append(f"\n... 共 {len(login_arr)} 条记录")
            else:
                output_lines.append("暂无登录记录")

        elif flow_type == 2:
            item_arr = first_data.get("itemArr", [])
            if item_arr:
                for i, record in enumerate(item_arr[:10], 1):
                    reason = self.decode_url(record.get("vReason", ""))
                    output_lines.append(f"【{i}】{reason}")
                    output_lines.append(f"  物品ID: {record.get('iItemID', '未知')}")
                    output_lines.append(f"  数量: {record.get('iCount', 0)}")
                    output_lines.append(f"  时间: {record.get('dtEventTime', '未知')}")
                if len(item_arr) > 10:
                    output_lines.append(f"\n... 共 {len(item_arr)} 条记录")
            else:
                output_lines.append("暂无道具记录")

        elif flow_type == 3:
            money_arr = first_data.get("iMoneyArr", [])
            if money_arr:
                for i, record in enumerate(money_arr[:10], 1):
                    reason = self.decode_url(record.get("vReason", ""))
                    output_lines.append(f"【{i}】{reason}")
                    output_lines.append(f"  货币类型: {record.get('iMoneyType', '未知')}")
                    output_lines.append(f"  变化量: {record.get('iChange', 0)}")
                    output_lines.append(f"  当前余额: {record.get('iMoney', 0)}")
                    output_lines.append(f"  时间: {record.get('dtEventTime', '未知')}")
                if len(money_arr) > 10:
                    output_lines.append(f"\n... 共 {len(money_arr)} 条记录")
            else:
                output_lines.append("暂无货币记录")

        return "\n".join(output_lines)

    async def get_record(self, event: AstrMessageEvent, args: str = ""):
        """战绩记录查询"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        # 解析参数 (4: 烽火地带, 5: 全面战场)
        mode_type = 4  # 默认烽火地带
        page = 1

        if args:
            parts = args.strip().split()
            for part in parts:
                part_lower = part.lower()
                if part_lower in ["烽火", "烽火地带", "sol", "摸金"]:
                    mode_type = 4
                elif part_lower in ["全面", "全面战场", "战场", "mp"]:
                    mode_type = 5
                elif part.isdigit():
                    page = int(part)

        mode_names = {4: "烽火地带", 5: "全面战场"}
        yield self.chain_reply(event, f"正在查询{mode_names[mode_type]}战绩记录，请稍候...")

        result = await self.api.get_record(frameworkToken=token, mode_type=mode_type, page=page)
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取战绩记录失败：{self.get_error_msg(result)}")
            return

        data = result.get("data", {})
        records = data.get("list", [])
        
        if not records:
            yield self.chain_reply(event, "暂无战绩记录")
            return

        # 处理战绩数据用于渲染
        processed_records = []
        for record in records[:10]:
            processed_records.append({
                'mapName': record.get("mapName", "未知地图"),
                'isEscape': record.get("isEscape", False),
                'resultText': "撤离" if record.get("isEscape") else "阵亡",
                'kills': record.get("kills", 0),
                'damage': record.get("damage", 0),
                'duration': self.format_duration(record.get("duration", 0)),
                'playTime': record.get("playTime", "未知时间"),
                'headshots': record.get("headshots", 0),
                'assists': record.get("assists", 0),
            })

        render_data = {
            'backgroundImage': Render.get_background_image(),
            'modeType': mode_names[mode_type],
            'modeName': mode_names[mode_type],
            'page': page,
            'records': processed_records,
            'totalRecords': len(records),
        }

        # 尝试渲染图片
        yield await self.render_and_reply(
            event,
            'record/record.html',
            render_data,
            fallback_text=self._build_record_text(mode_names[mode_type], page, records),
            width=600,
            height=1000
        )

    def _build_record_text(self, mode_name, page, records):
        """构建纯文本战绩（渲染失败时的回退）"""
        output_lines = [f"🎯【{mode_name}战绩】第{page}页"]
        output_lines.append("━━━━━━━━━━━━━━━")

        for i, record in enumerate(records[:5], 1):
            map_name = record.get("mapName", "未知地图")
            result_text = "撤离" if record.get("isEscape") else "阵亡"
            kills = record.get("kills", 0)
            damage = record.get("damage", 0)
            duration = self.format_duration(record.get("duration", 0))
            play_time = record.get("playTime", "未知时间")

            output_lines.append(f"")
            output_lines.append(f"【{i}】{map_name}")
            output_lines.append(f"  结果: {result_text} | 击杀: {kills}")
            output_lines.append(f"  伤害: {damage} | 时长: {duration}")
            output_lines.append(f"  时间: {play_time}")

        if len(records) > 5:
            output_lines.append(f"\n... 本页共 {len(records)} 条记录")

        return "\n".join(output_lines)

    async def get_collection(self, event: AstrMessageEvent):
        """藏品查询"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        yield self.chain_reply(event, "正在查询藏品信息，请稍候...")

        result = await self.api.get_collection(frameworkToken=token)
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取藏品信息失败：{self.get_error_msg(result)}")
            return

        data = result.get("data", {})
        if not data:
            yield self.chain_reply(event, "暂无藏品信息")
            return

        # 统计信息
        total_count = data.get("totalCount", 0)
        red_count = data.get("redCount", 0)
        collections = data.get("list", [])

        # 品质等级映射
        quality_map = {
            '传说': 5, '史诗': 4, '稀有': 3, '精良': 2, '普通': 1,
            'legendary': 5, 'epic': 4, 'rare': 3, 'uncommon': 2, 'common': 1
        }
        
        # 按类别分组藏品
        categories_dict = {}
        quality_stats = {'5': 0, '4': 0, '3': 0, '2': 0, '1': 0}
        
        for item in collections[:50]:  # 限制数量
            category_name = item.get("category", "其他") or "其他"
            rarity = item.get("rarity", "普通") or "普通"
            quality_level = quality_map.get(rarity.lower(), quality_map.get(rarity, 1))
            quality_stats[str(quality_level)] = quality_stats.get(str(quality_level), 0) + 1
            
            if category_name not in categories_dict:
                categories_dict[category_name] = {
                    'name': category_name,
                    'bgImage': 'default',
                    'items': []
                }
            
            categories_dict[category_name]['items'].append({
                'id': item.get("id", ""),
                'name': item.get("name", "未知"),
                'imageUrl': item.get("imageUrl", ""),
                'qualityLevel': quality_level,
                'category': category_name,
            })
        
        # 转换为列表格式
        categories = list(categories_dict.values())
        quality_stats_list = [
            {'level': k, 'count': v} for k, v in quality_stats.items() if v > 0
        ]

        render_data = {
            'backgroundImage': Render.get_background_image(),
            'totalCount': total_count,
            'typeName': '全部藏品',
            'categories': categories,
            'qualityStats': quality_stats_list,
            'redCount': red_count,
        }

        # 尝试渲染图片
        yield await self.render_and_reply(
            event,
            'collection/collection.html',
            render_data,
            fallback_text=self._build_collection_text(total_count, red_count, collections),
            width=1200,
            height=800
        )

    def _build_collection_text(self, total_count, red_count, collections):
        """构建纯文本藏品信息（渲染失败时的回退）"""
        output_lines = ["🏆【藏品信息】🏆"]
        output_lines.append("━━━━━━━━━━━━━━━")
        output_lines.append(f"总藏品数: {total_count}")
        output_lines.append(f"大红藏品: {red_count}")

        if collections:
            output_lines.append("")
            output_lines.append("📦 最近获得:")
            for item in collections[:10]:
                name = item.get("name", "未知")
                rarity = item.get("rarity", "普通")
                get_time = item.get("getTime", "")
                output_lines.append(f"  【{rarity}】{name}")
                if get_time:
                    output_lines.append(f"    获得时间: {get_time}")

            if len(collections) > 10:
                output_lines.append(f"\n... 共 {len(collections)} 件藏品")

        return "\n".join(output_lines)

    async def get_operators(self, event: AstrMessageEvent, name: str = ""):
        """干员信息查询"""
        yield self.chain_reply(event, "正在查询干员信息，请稍候...")

        result = await self.api.get_operators()
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取干员信息失败：{self.get_error_msg(result)}")
            return

        operators = result.get("data", [])
        if not operators:
            yield self.chain_reply(event, "未找到任何干员信息")
            return

        # 如果指定了名称，进行筛选
        if name:
            name = name.strip()
            matched = [op for op in operators if 
                       name in (op.get("operator", "") or "") or 
                       name in (op.get("fullName", "") or "") or
                       (op.get("operator", "") or "") in name or
                       (op.get("fullName", "") or "") in name]
            
            if not matched:
                yield self.chain_reply(event, f"未找到干员「{name}」的信息，请检查干员名称是否正确")
                return

            # 优先完全匹配
            operator = next((op for op in matched if 
                           op.get("operator") == name or op.get("fullName") == name), matched[0])

            if len(matched) > 1:
                names_str = "、".join([op.get("operator", "") or op.get("fullName", "") for op in matched[:5]])
                yield self.chain_reply(event, f"找到多个匹配的干员：{names_str}，将显示第一个匹配结果")

            # 准备渲染数据
            render_data = {
                'operatorPic': operator.get('avatar', '') or operator.get('operatorPic', ''),
                'operator': operator,
                'operatorName': operator.get('operator', '未知'),
                'fullName': operator.get('fullName', '未知'),
                'armyType': operator.get('armyType', '未知'),
                'armyTypeDesc': operator.get('armyTypeDesc', '无'),
                'abilitiesList': operator.get('abilitiesList', []),
                'avatar': operator.get('avatar', ''),
                'showDetail': True,
            }

            # 尝试渲染图片
            yield await self.render_and_reply(
                event,
                'operator/operator.html',
                render_data,
                fallback_text=self._build_operator_detail_text(operator),
                width=1200,
                height=800
            )
        else:
            # 显示干员列表 - 按兵种分类
            by_type = {}
            for op in operators:
                army_type = op.get("armyType", "其他")
                if army_type not in by_type:
                    by_type[army_type] = []
                by_type[army_type].append(op)

            render_data = {
                'backgroundImage': Render.get_background_image(),
                'totalCount': len(operators),
                'operatorsByType': by_type,
                'showDetail': False,
            }

            yield await self.render_and_reply(
                event,
                'operator/operator.html',
                render_data,
                fallback_text=self._build_operator_list_text(operators, by_type),
                width=1200,
                height=800
            )

    def _build_operator_detail_text(self, operator):
        """构建纯文本干员详情（渲染失败时的回退）"""
        output_lines = [f"👤【干员详情】"]
        output_lines.append("━━━━━━━━━━━━━━━")
        output_lines.append(f"名称: {operator.get('operator', '未知')}")
        output_lines.append(f"全名: {operator.get('fullName', '未知')}")
        output_lines.append(f"兵种: {operator.get('armyType', '未知')}")
        output_lines.append(f"描述: {operator.get('armyTypeDesc', '无')}")

        abilities = operator.get("abilitiesList", [])
        if abilities:
            output_lines.append("")
            output_lines.append("🎯 技能列表:")
            for ability in abilities:
                ability_name = ability.get("abilityName", "未知技能")
                ability_type = ability.get("abilityTypeCN", "") or ability.get("abilityType", "")
                ability_desc = ability.get("abilityDesc", "")
                output_lines.append(f"  【{ability_type}】{ability_name}")
                if ability_desc:
                    output_lines.append(f"    {ability_desc[:50]}{'...' if len(ability_desc) > 50 else ''}")

        return "\n".join(output_lines)

    def _build_operator_list_text(self, operators, by_type):
        """构建纯文本干员列表（渲染失败时的回退）"""
        output_lines = ["👥【干员列表】"]
        output_lines.append("━━━━━━━━━━━━━━━")
        output_lines.append(f"共 {len(operators)} 名干员")
        output_lines.append("")

        for army_type, ops in by_type.items():
            output_lines.append(f"【{army_type}】")
            names = [op.get("operator", "未知") for op in ops]
            output_lines.append(f"  {', '.join(names)}")

        output_lines.append("")
        output_lines.append("💡 使用 /三角洲 干员 <名称> 查看详情")

        return "\n".join(output_lines)
