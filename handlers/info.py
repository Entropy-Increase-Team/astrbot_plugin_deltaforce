"""
信息查询处理器
包含：货币查询、个人信息、UID查询、违规历史等
"""
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp
from .base import BaseHandler
from ..utils.render import Render


class InfoHandler(BaseHandler):
    """信息查询处理器"""

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

    async def get_money(self, event: AstrMessageEvent):
        """货币查询"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return
        
        result = await self.api.get_money(frameworkToken=token)
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取货币信息失败：{self.get_error_msg(result)}")
            return
        
        data = result.get("data", [])
        if not data:
            yield self.chain_reply(event, "未查询到任何货币信息")
            return
        
        output_lines = ["💰【货币信息】💰"]
        for item in data:
            name = item.get("name", "未知")
            total = item.get("totalMoney", 0)
            total_formatted = f"{total:,}" if isinstance(total, int) else str(total)
            output_lines.append(f"  {name}: {total_formatted}")
        
        yield self.chain_reply(event, "\n".join(output_lines))

    async def get_personal_info(self, event: AstrMessageEvent):
        """个人信息查询"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return
        
        yield self.chain_reply(event, "正在查询个人信息，请稍候...")
        
        result = await self.api.get_personal_info(frameworkToken=token)
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取个人信息失败：{self.get_error_msg(result)}")
            return
        
        # 兼容两种数据结构：
        # 旧格式：{"code": 0, "data": {...}, "roleInfo": {...}}
        # 新格式：{"success": true, "data": {"userData": {...}, "roleInfo": {...}}}
        data = result.get("data", {})
        role_info = result.get("roleInfo") or data.get("roleInfo", {})
        if not data and not role_info:
            yield self.chain_reply(event, "未查询到个人信息")
            return
        
        # 解析用户数据
        user_data = data.get("userData", {})
        career_data = data.get("careerData", {})
        
        # URL 解码昵称
        nick_name = self.decode_url(
            user_data.get("charac_name", "") or role_info.get("charac_name", "") or "未知"
        )
        uid = role_info.get("uid", "未知")
        level = role_info.get("level", "-")
        tdm_level = role_info.get("tdmlevel", "-")
        
        # 账号状态
        is_ban = "封禁" if role_info.get("isbanuser") == "1" else "正常"
        is_ban_speak = "禁言" if role_info.get("isbanspeak") == "1" else "正常"
        is_adult = "已成年" if role_info.get("adultstatus") == "0" else "未成年"
        
        # 资产计算
        prop_capital = float(role_info.get("propcapital", 0) or 0)
        haf_coin = float(role_info.get("hafcoinnum", 0) or 0)
        total_assets = (prop_capital + haf_coin) / 1000000
        
        # 段位信息
        sol_rank_point = career_data.get("rankpoint", 0)
        tdm_rank_point = career_data.get("tdmrankpoint", 0)
        sol_rank = self.get_rank_by_score(sol_rank_point, 'sol') if sol_rank_point else '-'
        tdm_rank = self.get_rank_by_score(tdm_rank_point, 'tdm') if tdm_rank_point else '-'
        sol_rank_image = Render.get_rank_image(sol_rank, 'sol')
        tdm_rank_image = Render.get_rank_image(tdm_rank, 'mp')
        
        # 时间格式化
        register_time = self.format_timestamp(role_info.get("register_time", 0))
        last_login_time = self.format_timestamp(role_info.get("lastlogintime", 0))
        
        # 格式化哈夫币
        haf_coin_str = f"{int(haf_coin):,}" if haf_coin > 0 else "-"
        total_assets_str = f"{total_assets:.2f}M" if total_assets > 0 else "-"
        
        # 用户头像 URL
        pic_url = user_data.get("pic_url", "") or f"http://q.qlogo.cn/headimg_dl?dst_uin={event.get_sender_id()}&spec=640&img_type=jpg"
        
        # 准备渲染数据
        render_data = {
            # 背景图片
            'backgroundImage': Render.get_background_image(),
            # 用户基础信息
            'userName': nick_name,
            'userAvatar': pic_url,
            'userId': uid,
            'registerTime': register_time,
            'lastLoginTime': last_login_time,
            'accountStatus': f"账号封禁: {is_ban} | 禁言: {is_ban_speak} | 防沉迷: {is_adult}",
            # 烽火地带信息
            'solLevel': level,
            'solRankName': sol_rank,
            'solRankImage': sol_rank_image,
            'solTotalFight': career_data.get("soltotalfght", "-"),
            'solTotalEscape': career_data.get("solttotalescape", "-"),
            'solEscapeRatio': career_data.get("solescaperatio", "-"),
            'solTotalKill': career_data.get("soltotalkill", "-"),
            'solDuration': self.format_duration(career_data.get("solduration", 0)),
            # 全面战场信息
            'tdmLevel': tdm_level,
            'tdmRankName': tdm_rank,
            'tdmRankImage': tdm_rank_image,
            'tdmTotalFight': career_data.get("tdmtotalfight", "-"),
            'tdmTotalWin': career_data.get("totalwin", "-"),
            'tdmWinRatio': career_data.get("tdmsuccessratio", "-"),
            'tdmTotalKill': career_data.get("tdmtotalkill", "-"),
            'tdmDuration': self.format_duration(career_data.get("tdmduration", 0), "minutes"),
            # 资产信息
            'hafCoin': haf_coin_str,
            'totalAssets': total_assets_str,
        }
        
        # 尝试渲染图片
        yield await self.render_and_reply(
            event,
            'userInfo/userInfo.html',
            render_data,
            fallback_text=self._build_personal_info_text(
                nick_name, uid, is_ban, is_ban_speak, total_assets,
                level, career_data, tdm_level
            ),
            width=1365,
            height=640
        )

    def _build_personal_info_text(
        self, nick_name, uid, is_ban, is_ban_speak, total_assets,
        level, career_data, tdm_level
    ):
        """构建纯文本个人信息（渲染失败时的回退）"""
        return "\n".join([
            f"🎮【{nick_name}】个人信息",
            f"━━━━━━━━━━━━━━━",
            f"📋 UID: {uid}",
            f"📊 账号状态: {is_ban} | 禁言: {is_ban_speak}",
            f"💰 总资产: {total_assets:.2f}M",
            f"",
            f"🔥【烽火地带】等级 {level}",
            f"  对局: {career_data.get('soltotalfght', '-')} | 撤离: {career_data.get('solttotalescape', '-')}",
            f"  撤离率: {career_data.get('solescaperatio', '-')} | 击杀: {career_data.get('soltotalkill', '-')}",
            f"  游戏时长: {self.format_duration(career_data.get('solduration', 0))}",
            f"",
            f"⚔️【全面战场】等级 {tdm_level}",
            f"  对局: {career_data.get('tdmtotalfight', '-')} | 胜场: {career_data.get('totalwin', '-')}",
            f"  胜率: {career_data.get('tdmsuccessratio', '-')} | 击杀: {career_data.get('tdmtotalkill', '-')}",
            f"  游戏时长: {self.format_duration(career_data.get('tdmduration', 0), 'minutes')}",
        ])

    async def get_uid(self, event: AstrMessageEvent):
        """UID查询"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return
        
        result = await self.api.get_personal_info(frameworkToken=token)
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取UID失败：{self.get_error_msg(result)}")
            return
        
        # 兼容两种数据结构
        data = result.get("data", {})
        role_info = result.get("roleInfo") or data.get("roleInfo", {})
        if not role_info:
            yield self.chain_reply(event, "未查询到角色信息")
            return
        
        nick_name = self.decode_url(role_info.get("charac_name", "") or "未知")
        uid = role_info.get("uid", "未知")
        
        yield self.chain_reply(event, f"昵称: {nick_name}\nUID: {uid}")

    async def get_ban_history(self, event: AstrMessageEvent):
        """违规历史查询"""
        token, error = await self.get_qqsafe_token(event)
        if error:
            yield self.chain_reply(event, error)
            return
        
        result = await self.api.get_ban_history(frameworkToken=token)
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取违规历史失败：{self.get_error_msg(result)}")
            return
        
        ban_data = result.get("data", [])
        if not ban_data:
            yield self.chain_reply(event, "🎉 恭喜！暂无违规记录")
            return
        
        nodes = []
        nodes.append(Comp.Plain("【违规历史记录】\n\n"))
        
        for i, ban_record in enumerate(ban_data, 1):
            start_time = self.format_timestamp(ban_record.get("start_stmp", 0))
            cheat_time = self.format_timestamp(ban_record.get("cheat_date", 0))
            duration = self.format_ban_duration(ban_record.get("duration", 0))
            
            content_lines = [
                f"🚫 第 {i} 条违规记录",
                f"📱 游戏: {ban_record.get('game_name', '未知游戏')}",
                f"📝 类型: {ban_record.get('type', '未知类型')}",
                f"❓ 原因: {ban_record.get('reason', '未知原因')}",
                f"📋 描述: {ban_record.get('strategy_desc', '无描述')}",
                f"⏰ 开始时间: {start_time}",
                f"🕒 违规时间: {cheat_time}" if cheat_time != "未知时间" else "",
                f"⏱️ 持续时间: {duration}",
                f"🎮 游戏ID: {ban_record.get('game_id', '未知')}",
                f"🌐 区域: {ban_record.get('zone', '全区')}",
                "─" * 20,
                "\n"
            ]
            content_lines = [line for line in content_lines if line]
            nodes.append(Comp.Plain("\n".join(content_lines)))
        
        yield event.chain_result([Comp.Node(
            uin=str(event.get_sender_id()),
            name=event.get_sender_name(),
            content=nodes
        )])

    async def get_daily_keyword(self, event: AstrMessageEvent):
        """每日密码查询"""
        result = await self.api.get_daily_keyword()
        if not result.get("success", False):
            error_msg = result.get("message", "未知错误")
            yield self.chain_reply(event, f"获取每日密码失败：{error_msg}")
            return
        
        data = result.get("data", {})
        maps_list = data.get("list", [])
        if not maps_list:
            yield self.chain_reply(event, "今日暂无密码信息")
            return
        
        output_lines = ["🗝️【每日密码】🗝️"]
        for map_info in maps_list:
            map_name = map_info.get("mapName", "未知地图")
            secret = map_info.get("secret", "未知")
            if secret and secret.isdigit():
                secret = secret.zfill(4)
            output_lines.append(f"📍【{map_name}】: {secret}")
        
        request_info = data.get("requestInfo", {})
        timestamp = request_info.get("timestamp", "")
        if timestamp:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%m-%d %H:%M")
                output_lines.append(f"\n⏰ 更新时间: {time_str}")
            except:
                pass
        
        yield self.chain_reply(event, "\n".join(output_lines))

    async def get_operator_list(self, event: AstrMessageEvent):
        """干员列表查询"""
        result = await self.api.get_operators()
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取干员列表失败：{self.get_error_msg(result)}")
            return

        operators = result.get("data", [])
        if not operators:
            yield self.chain_reply(event, "未查询到任何干员信息")
            return

        # 根据ID前缀判断兵种
        def get_army_type(op_id):
            op_id = int(op_id) if str(op_id).isdigit() else 0
            if 10000 <= op_id < 20000:
                return "突击"
            elif 20000 <= op_id < 30000:
                return "支援"
            elif 30000 <= op_id < 40000:
                return "工程"
            elif 40000 <= op_id < 50000:
                return "侦察"
            return "未知"

        # 按兵种分组
        grouped = {}
        for op in operators:
            army_type = op.get("armyType") or get_army_type(op.get("id", 0))
            if army_type not in grouped:
                grouped[army_type] = []
            grouped[army_type].append(op)

        # 按固定顺序排序
        order = ["突击", "工程", "支援", "侦察"]
        sorted_types = sorted(grouped.keys(), key=lambda x: order.index(x) if x in order else 999)

        lines = [f"👥【干员列表】共 {len(operators)} 个干员", ""]
        for army_type in sorted_types:
            ops = grouped[army_type]
            lines.append(f"【{army_type}】({len(ops)}人)")
            for op in ops:
                name = op.get("name") or op.get("operator") or op.get("fullName") or "未知"
                lines.append(f"  • {name}")
            lines.append("")

        yield self.chain_reply(event, "\n".join(lines).strip())

    async def get_place_status(self, event: AstrMessageEvent):
        """特勤处状态查询"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        result = await self.api.get_place_status(token)
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取特勤处状态失败：{self.get_error_msg(result)}")
            return

        data = result.get("data", {})
        places = data.get("places", [])
        stats = data.get("stats", {})

        if not places:
            yield self.chain_reply(event, "未查询到特勤处设施信息")
            return

        # 处理时间格式
        for place in places:
            left_time = place.get("leftTime", 0)
            if left_time and isinstance(left_time, (int, float)):
                h = int(left_time) // 3600
                m = (int(left_time) % 3600) // 60
                s = int(left_time) % 60
                place["timeFormatted"] = f"{h}时{m}分{s}秒"
            else:
                place["timeFormatted"] = "N/A"

        render_data = {
            'backgroundImage': Render.get_background_image(),
            'places': places,
            'stats': stats,
            'totalCount': stats.get('total', len(places)),
            'producingCount': stats.get('producing', 0),
            'idleCount': stats.get('idle', 0),
        }

        yield await self.render_and_reply(
            event,
            'placeInfo/placeInfo.html',
            render_data,
            fallback_text=self._build_place_status_text(places, stats),
            width=1700,
            height=1000
        )

    def _build_place_status_text(self, places, stats):
        """构建纯文本特勤处状态（渲染失败时的回退）"""
        lines = [
            "🏭【特勤处状态】",
            f"总设施: {stats.get('total', 0)} | 生产中: {stats.get('producing', 0)} | 闲置: {stats.get('idle', 0)}",
            "━━━━━━━━━━━━━━━━━━━━"
        ]

        for place in places:
            place_name = place.get("placeName", "未知设施")
            level = place.get("level", "?")
            status = place.get("status", "未知")
            
            if place.get("objectDetail"):
                obj_name = place["objectDetail"].get("objectName", "未知物品")
                time_str = place.get("timeFormatted", "N/A")
                lines.append(f"🔨 {place_name} (Lv.{level})")
                lines.append(f"   生产中: {obj_name}")
                lines.append(f"   剩余: {time_str}")
            else:
                lines.append(f"💤 {place_name} (Lv.{level}) - {status}")

        return "\n".join(lines)

    async def get_place_info(self, event: AstrMessageEvent, args: str = ""):
        """特勤处信息查询"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        # 设施类型映射
        place_map = {
            "仓库": "storage", "指挥中心": "control", "工作台": "workbench",
            "技术中心": "tech", "靶场": "shoot", "训练中心": "training",
            "制药台": "pharmacy", "防具台": "armory", "收藏室": "collect",
            "潜水中心": "diving"
        }

        if not args or args.strip() == "":
            place_names = "、".join(place_map.keys())
            yield self.chain_reply(event, f"请指定设施类型\n用法：/三角洲 特勤处信息 <设施名>\n支持：{place_names}")
            return

        parts = args.strip().split()
        place_name = parts[0]
        target_level = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

        place_type = place_map.get(place_name, "")
        if not place_type and place_name.lower() != "all":
            yield self.chain_reply(event, f"❌ 未知设施类型: {place_name}")
            return

        result = await self.api.get_place_info(token, place_type if place_name.lower() != "all" else "")
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取特勤处信息失败：{self.get_error_msg(result)}")
            return

        data = result.get("data", {})
        places = data.get("places", [])
        if not places:
            yield self.chain_reply(event, "未查询到特勤处信息")
            return

        lines = [f"🏭【特勤处信息 - {place_name}】", ""]
        for place in places:
            level = place.get("level", "?")
            if target_level and int(level) != target_level:
                continue
            
            lines.append(f"📍 等级 {level}")
            if place.get("upgradeItems"):
                lines.append("  升级需要:")
                for item in place["upgradeItems"][:5]:
                    lines.append(f"    • {item.get('name', '未知')} x{item.get('count', 0)}")
            if place.get("unlockItems"):
                lines.append("  解锁配方:")
                for item in place["unlockItems"][:5]:
                    lines.append(f"    • {item.get('name', '未知')}")
            lines.append("")

        yield self.chain_reply(event, "\n".join(lines).strip() if len(lines) > 2 else "未找到匹配的等级信息")

    async def get_red_collection(self, event: AstrMessageEvent):
        """出红记录查询"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        result = await self.api.get_red_list(token)
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取出红记录失败：{self.get_error_msg(result)}")
            return

        data = result.get("data", {})
        records = data.get("list", [])
        if not records:
            yield self.chain_reply(event, "📭 暂无藏品解锁记录")
            return

        total_value = data.get("totalValue", 0)
        
        # 处理记录格式
        processed_records = []
        for record in records[:15]:
            name = record.get("objectName", "未知物品")
            price = record.get("price", 0)
            unlock_time = record.get("unlockTime", "")
            if unlock_time:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(unlock_time.replace('Z', '+00:00'))
                    time_str = dt.strftime("%m-%d %H:%M")
                except:
                    time_str = unlock_time[:10] if unlock_time else "未知"
            else:
                time_str = "未知"
            
            processed_records.append({
                'objectName': name,
                'objectImage': record.get('objectImage', ''),
                'price': int(price) if price else 0,
                'time': time_str,
                'map': record.get('map', ''),
            })

        render_data = {
            'backgroundImage': Render.get_background_image(),
            'records': processed_records,
            'totalValue': int(total_value) if total_value else 0,
            'userName': '玩家',
            'page': 1,
            'totalRecords': len(records),
        }

        yield await self.render_and_reply(
            event,
            'redRecord/redRecord.html',
            render_data,
            fallback_text=self._build_red_collection_text(records, total_value),
            width=1250,
            height=1000
        )

    def _build_red_collection_text(self, records, total_value):
        """构建纯文本出红记录（渲染失败时的回退）"""
        lines = [
            "🎁【藏品解锁记录】",
            f"总价值：￥{float(total_value):,.0f}",
            "━━━━━━━━━━━━━━━━━━━━"
        ]

        for i, record in enumerate(records[:15], 1):
            name = record.get("objectName", "未知物品")
            price = record.get("price", 0)
            unlock_time = record.get("unlockTime", "")
            if unlock_time:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(unlock_time.replace('Z', '+00:00'))
                    time_str = dt.strftime("%m-%d %H:%M")
                except:
                    time_str = unlock_time[:10] if unlock_time else "未知"
            else:
                time_str = "未知"
            lines.append(f"{i}. {name} ￥{float(price):,.0f} ({time_str})")

        if len(records) > 15:
            lines.append(f"... 等共 {len(records)} 条记录")

        return "\n".join(lines)

    async def get_game_health(self, event: AstrMessageEvent):
        """游戏健康状态查询"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        result = await self.api.get_game_health(token)
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取健康状态失败：{self.get_error_msg(result)}")
            return

        data = result.get("data", [])
        if not data or not data[0]:
            yield self.chain_reply(event, "未查询到健康状态信息")
            return

        health_data = data[0]
        healthy_detail = health_data.get("healthyDetail", {})
        if not healthy_detail:
            yield self.chain_reply(event, "未查询到健康状态详情")
            return

        debuff_list = healthy_detail.get("deBuffList", [])
        buff_list = healthy_detail.get("buffList", [])

        # 处理负面状态：合并同一部位的状态到同一卡片
        processed_debuff_list = []
        if debuff_list:
            for area_group in debuff_list:
                area = area_group.get("area", "未知部位")
                statuses = area_group.get("list", [])
                # 每2个状态合并成一个卡片组
                for i in range(0, len(statuses), 2):
                    group_statuses = statuses[i:i+2]
                    processed_debuff_list.append({
                        "area": area,
                        "list": group_statuses,
                        "isMerged": len(group_statuses) == 2
                    })

        # 准备渲染数据
        render_data = {
            'deBuffList': processed_debuff_list,
            'buffList': buff_list or []
        }

        # 尝试渲染图片
        yield await self.render_and_reply(
            event,
            'healthInfo/healthInfo.html',
            render_data,
            fallback_text=self._build_health_text(debuff_list, buff_list),
            width=1000,
            height=800
        )

    def _build_health_text(self, debuff_list, buff_list):
        """构建纯文本健康状态（渲染失败时的回退）"""
        lines = ["🏥【健康状态】", ""]

        if debuff_list:
            lines.append("❌ 负面状态:")
            for area_group in debuff_list:
                area = area_group.get("area", "未知部位")
                statuses = area_group.get("list", [])
                for status in statuses:
                    name = status.get("name") or status.get("title") or "未知"
                    desc = status.get("desc") or status.get("effect") or ""
                    lines.append(f"  • [{area}] {name}")
                    if desc:
                        lines.append(f"    {desc[:30]}...")
            lines.append("")

        if buff_list:
            lines.append("✅ 正面状态:")
            for buff_group in buff_list:
                for buff in buff_group.get("list", []):
                    name = buff.get("name") or buff.get("title") or "未知"
                    lines.append(f"  • {name}")

        if not debuff_list and not buff_list:
            lines.append("✨ 状态良好，无异常")

        return "\n".join(lines)

    async def get_user_stats(self, event: AstrMessageEvent):
        """用户统计（管理员功能）"""
        # 此功能需要管理员权限，由调用方检查
        result = await self.api.get_user_stats()
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取统计失败：{self.get_error_msg(result)}")
            return

        access_level = result.get("accessLevel", "user")
        data = result.get("data", {})

        if access_level == "admin":
            users = data.get("users", {})
            api_info = data.get("api", {})
            subscription = data.get("subscription", {})
            
            lines = [
                "📊【全站用户统计】",
                f"权限级别：超级管理员",
                "",
                "👥 用户统计",
                f"  总用户数: {users.get('total', 0)}",
                f"  邮箱已验证: {users.get('emailVerified', 0)}",
                "",
                "🔑 API密钥统计",
                f"  总密钥数: {api_info.get('totalKeys', 0)}",
                f"  活跃密钥: {api_info.get('activeKeys', 0)}",
                "",
                "💎 订阅统计",
                f"  专业用户: {subscription.get('proUsers', 0)}",
                f"  免费用户: {subscription.get('freeUsers', 0)}"
            ]
        else:
            user_info = data.get("userInfo", {})
            lines = [
                "📊【个人统计信息】",
                f"总账号数: {user_info.get('totalAccounts', 0)}",
                f"已绑定: {user_info.get('boundAccounts', 0)}",
                f"未绑定: {user_info.get('unboundAccounts', 0)}"
            ]

        yield self.chain_reply(event, "\n".join(lines))
