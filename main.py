"""
三角洲行动 AstrBot 插件
主入口文件 - 负责命令注册和路由
"""
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api import AstrBotConfig

from .df_api import DeltaForceAPI
from .df_sqlite import DeltaForceSQLiteManager
from .handlers import (
    InfoHandler, AccountHandler, DataHandler, ToolsHandler, 
    SystemHandler, EntertainmentHandler, VoiceHandler, 
    MusicHandler, RoomHandler, SolutionHandler, CalculatorHandler,
    PushHandler
)

# 推送模块 (可选依赖)
try:
    from .push import (
        PushScheduler, DailyKeywordPush, DailyReportPush, WeeklyReportPush,
        PlaceTaskPush, BroadcastSystem
    )
    HAS_PUSH_MODULE = True
except ImportError:
    HAS_PUSH_MODULE = False
    logger.warning("推送模块未能加载，定时推送功能不可用")


# 子命令路由表: 当用户发送 "三角洲 xxx" (带空格) 时, 通过此表路由到对应的 handler 方法
# 格式: "子命令关键词": ("handler属性名", "方法名", 是否传递参数)
_CMD_ROUTES = {
    # 帮助
    "帮助": ("system_handler", "show_help", False),
    "菜单": ("system_handler", "show_help", False),
    # 账号 - 登录
    "CK登录": ("account_handler", "login_by_qq_ck", True),
    "Cookie登录": ("account_handler", "login_by_qq_ck", True),
    "ck登录": ("account_handler", "login_by_qq_ck", True),
    "QQ登录": ("account_handler", "login_by_qq", False),
    "登录": ("account_handler", "login_by_qq", False),
    "微信登录": ("account_handler", "login_by_wechat", False),
    "安全中心登录": ("account_handler", "login_by_qqsafe", False),
    "WeGame登录": ("account_handler", "login_by_wegame", False),
    "WG登录": ("account_handler", "login_by_wegame", False),
    "WeGame领奖": ("account_handler", "wegame_claim_gift", False),
    "WG领奖": ("account_handler", "wegame_claim_gift", False),
    "每日领奖": ("account_handler", "wegame_claim_gift", False),
    "wegame礼包": ("account_handler", "wegame_claim_gift", False),
    "账号列表": ("account_handler", "list_account", False),
    "账号管理": ("account_handler", "list_account", False),
    "QQ刷新": ("account_handler", "refresh_qq", False),
    "刷新QQ": ("account_handler", "refresh_qq", False),
    "微信刷新": ("account_handler", "refresh_wechat", False),
    "刷新微信": ("account_handler", "refresh_wechat", False),
    "QQ授权登录": ("account_handler", "login_qq_oauth", True),
    "qqoauth": ("account_handler", "login_qq_oauth", True),
    "微信授权登录": ("account_handler", "login_wechat_oauth", True),
    "wechatoauth": ("account_handler", "login_wechat_oauth", True),
    # 信息查询
    "货币": ("info_handler", "get_money", False),
    "余额": ("info_handler", "get_money", False),
    "金币": ("info_handler", "get_money", False),
    "信息": ("info_handler", "get_personal_info", False),
    "个人信息": ("info_handler", "get_personal_info", False),
    "我的信息": ("info_handler", "get_personal_info", False),
    "UID": ("info_handler", "get_uid", False),
    "uid": ("info_handler", "get_uid", False),
    "每日密码": ("info_handler", "get_daily_keyword", False),
    "今日密码": ("info_handler", "get_daily_keyword", False),
    "违规历史": ("info_handler", "get_ban_history", False),
    "封禁历史": ("info_handler", "get_ban_history", False),
    "干员列表": ("info_handler", "get_operator_list", True),
    "所有干员": ("info_handler", "get_operator_list", True),
    "特勤处状态": ("info_handler", "get_place_status", False),
    "特勤状态": ("info_handler", "get_place_status", False),
    "特勤处信息": ("info_handler", "get_place_info", True),
    "特勤信息": ("info_handler", "get_place_info", True),
    "出红记录": ("info_handler", "get_red_collection", False),
    "红色记录": ("info_handler", "get_red_collection", False),
    "红装记录": ("info_handler", "get_red_collection", False),
    "健康状态": ("info_handler", "get_game_health", False),
    "游戏健康": ("info_handler", "get_game_health", False),
    "用户统计": ("info_handler", "get_user_stats", False),
    "统计": ("info_handler", "get_user_stats", False),
    # 数据查询
    "数据": ("data_handler", "get_personal_data", True),
    "data": ("data_handler", "get_personal_data", True),
    "个人数据": ("data_handler", "get_personal_data", True),
    "流水": ("data_handler", "get_flows", True),
    "flows": ("data_handler", "get_flows", True),
    "战绩": ("data_handler", "get_record", True),
    "record": ("data_handler", "get_record", True),
    "记录": ("data_handler", "get_record", True),
    "藏品": ("data_handler", "get_collection", False),
    "collection": ("data_handler", "get_collection", False),
    "收藏": ("data_handler", "get_collection", False),
    "干员": ("data_handler", "get_operators", True),
    "operator": ("data_handler", "get_operators", True),
    # 工具查询
    "搜索": ("tools_handler", "search_object", True),
    "search": ("tools_handler", "search_object", True),
    "查找": ("tools_handler", "search_object", True),
    "价格": ("tools_handler", "get_current_price", True),
    "price": ("tools_handler", "get_current_price", True),
    "物价": ("tools_handler", "get_current_price", True),
    "材料价格": ("tools_handler", "get_material_price", True),
    "材料": ("tools_handler", "get_material_price", True),
    "material": ("tools_handler", "get_material_price", True),
    "利润排行": ("tools_handler", "get_profit_rank", True),
    "利润榜": ("tools_handler", "get_profit_rank", True),
    "profit": ("tools_handler", "get_profit_rank", True),
    "地图统计": ("tools_handler", "get_map_stats", True),
    "mapstats": ("tools_handler", "get_map_stats", True),
    "地图数据": ("tools_handler", "get_map_stats", True),
    "物品列表": ("tools_handler", "get_object_list", True),
    "itemlist": ("tools_handler", "get_object_list", True),
    "物品": ("tools_handler", "get_object_list", True),
    "大红收藏": ("tools_handler", "get_red_collection", True),
    "大红藏品": ("tools_handler", "get_red_collection", True),
    "红色收藏": ("tools_handler", "get_red_collection", True),
    "最高利润": ("tools_handler", "get_max_profit", True),
    "利润V2": ("tools_handler", "get_max_profit", True),
    "maxprofit": ("tools_handler", "get_max_profit", True),
    "特勤处利润": ("tools_handler", "get_special_ops_profit", True),
    "特勤利润": ("tools_handler", "get_special_ops_profit", True),
    "文章列表": ("tools_handler", "get_article_list", False),
    "文章": ("tools_handler", "get_article_list", False),
    "文章详情": ("tools_handler", "get_article_detail", True),
    "文章内容": ("tools_handler", "get_article_detail", True),
    "官方改枪码": ("tools_handler", "get_official_solution_list", False),
    "官方方案": ("tools_handler", "get_official_solution_list", False),
    "官方改枪码列表": ("tools_handler", "get_official_solution_list", False),
    "官方改枪码详情": ("tools_handler", "get_official_solution_detail", True),
    "官方方案详情": ("tools_handler", "get_official_solution_detail", True),
    "价格历史": ("tools_handler", "get_price_history", True),
    "历史价格": ("tools_handler", "get_price_history", True),
    "利润历史": ("tools_handler", "get_profit_history", True),
    "历史利润": ("tools_handler", "get_profit_history", True),
    # 系统
    "服务器状态": ("system_handler", "get_server_health", False),
    "状态": ("system_handler", "get_server_health", False),
    "health": ("system_handler", "get_server_health", False),
    "更新日志": ("system_handler", "get_changelog", False),
    "changelog": ("system_handler", "get_changelog", False),
    "插件状态": ("system_handler", "get_plugin_status", False),
    "插件信息": ("system_handler", "get_plugin_status", False),
    "订阅战绩": ("system_handler", "subscribe_record", True),
    "战绩订阅": ("system_handler", "subscribe_record", True),
    "取消订阅": ("system_handler", "unsubscribe_record", False),
    "取消战绩订阅": ("system_handler", "unsubscribe_record", False),
    "订阅状态": ("system_handler", "get_subscription_status", False),
    "查看订阅": ("system_handler", "get_subscription_status", False),
    # 娱乐 - TTS
    "tts状态": ("entertainment_handler", "get_tts_health", False),
    "TTS状态": ("entertainment_handler", "get_tts_health", False),
    "tts角色列表": ("entertainment_handler", "get_tts_presets", False),
    "TTS角色列表": ("entertainment_handler", "get_tts_presets", False),
    "tts角色详情": ("entertainment_handler", "get_tts_preset_detail", True),
    "TTS角色详情": ("entertainment_handler", "get_tts_preset_detail", True),
    "tts": ("entertainment_handler", "tts_synthesize", True),
    "TTS": ("entertainment_handler", "tts_synthesize", True),
    "语音合成": ("entertainment_handler", "tts_synthesize", True),
    "tts上传": ("entertainment_handler", "download_last_tts", False),
    "TTS上传": ("entertainment_handler", "download_last_tts", False),
    "tts下载": ("entertainment_handler", "download_last_tts", False),
    # 娱乐 - AI
    "ai预设列表": ("entertainment_handler", "get_ai_presets", False),
    "AI预设列表": ("entertainment_handler", "get_ai_presets", False),
    "ai锐评": ("entertainment_handler", "get_ai_commentary", True),
    "AI锐评": ("entertainment_handler", "get_ai_commentary", True),
    "ai评价": ("entertainment_handler", "get_ai_commentary", True),
    # 娱乐 - 报告
    "日报": ("entertainment_handler", "get_daily_report", True),
    "daily": ("entertainment_handler", "get_daily_report", True),
    "每日报告": ("entertainment_handler", "get_daily_report", True),
    "周报": ("entertainment_handler", "get_weekly_report", True),
    "weekly": ("entertainment_handler", "get_weekly_report", True),
    "每周报告": ("entertainment_handler", "get_weekly_report", True),
    "昨日收益": ("entertainment_handler", "get_yesterday_profit", True),
    "昨日物资": ("entertainment_handler", "get_yesterday_profit", True),
    # 语音
    "语音": ("voice_handler", "send_voice", True),
    "游戏语音": ("voice_handler", "send_voice", True),
    "语音角色": ("voice_handler", "get_voice_characters", True),
    "语音角色列表": ("voice_handler", "get_voice_characters", True),
    "语音标签": ("voice_handler", "get_voice_tags", True),
    "语音标签列表": ("voice_handler", "get_voice_tags", True),
    "语音分类": ("voice_handler", "get_voice_categories", False),
    "语音分类列表": ("voice_handler", "get_voice_categories", False),
    "语音统计": ("voice_handler", "get_voice_stats", False),
    "语音数据": ("voice_handler", "get_voice_stats", False),
    # 音乐
    "鼠鼠音乐": ("music_handler", "send_music", True),
    "播放音乐": ("music_handler", "send_music", True),
    "音乐列表": ("music_handler", "get_music_list", True),
    "鼠鼠音乐列表": ("music_handler", "get_music_list", True),
    "鼠鼠歌单": ("music_handler", "get_playlist", True),
    "歌单": ("music_handler", "get_playlist", True),
    "点歌": ("music_handler", "select_music_by_number", True),
    "听": ("music_handler", "select_music_by_number", True),
    "播放": ("music_handler", "select_music_by_number", True),
    "歌词": ("music_handler", "get_lyrics", False),
    "鼠鼠歌词": ("music_handler", "get_lyrics", False),
    "鼠鼠语音": ("music_handler", "send_voice", False),
    # 房间
    "房间列表": ("room_handler", "get_room_list", True),
    "开黑列表": ("room_handler", "get_room_list", True),
    "创建房间": ("room_handler", "create_room", True),
    "开房间": ("room_handler", "create_room", True),
    "加入房间": ("room_handler", "join_room", True),
    "进入房间": ("room_handler", "join_room", True),
    "退出房间": ("room_handler", "quit_room", True),
    "离开房间": ("room_handler", "quit_room", True),
    "房间信息": ("room_handler", "get_room_info", True),
    "房间详情": ("room_handler", "get_room_info", True),
    "房间标签": ("room_handler", "get_room_tags", False),
    "开黑标签": ("room_handler", "get_room_tags", False),
    "房间地图列表": ("room_handler", "get_room_maps", False),
    "房间地图": ("room_handler", "get_room_maps", False),
    "踢出成员": ("room_handler", "kick_member", True),
    "踢人": ("room_handler", "kick_member", True),
    # 改枪方案
    "改枪码列表": ("solution_handler", "get_solution_list", True),
    "改枪方案列表": ("solution_handler", "get_solution_list", True),
    "改枪码详情": ("solution_handler", "get_solution_detail", True),
    "改枪方案详情": ("solution_handler", "get_solution_detail", True),
    "上传改枪码": ("solution_handler", "upload_solution", True),
    "分享改枪码": ("solution_handler", "upload_solution", True),
    "上传方案": ("solution_handler", "upload_solution", True),
    "删除改枪码": ("solution_handler", "delete_solution", True),
    "删除方案": ("solution_handler", "delete_solution", True),
    "收藏改枪码": ("solution_handler", "collect_solution", True),
    "收藏方案": ("solution_handler", "collect_solution", True),
    "取消收藏改枪码": ("solution_handler", "discollect_solution", True),
    "取消收藏方案": ("solution_handler", "discollect_solution", True),
    "改枪码收藏列表": ("solution_handler", "get_collect_list", True),
    "我的收藏方案": ("solution_handler", "get_collect_list", True),
    # 计算器
    "修甲": ("calculator_handler", "quick_repair", True),
    "修理": ("calculator_handler", "quick_repair", True),
    "维修计算": ("calculator_handler", "quick_repair", True),
    "伤害": ("calculator_handler", "quick_damage", True),
    "伤害计算": ("calculator_handler", "quick_damage", True),
    "dmg": ("calculator_handler", "quick_damage", True),
    "战场伤害": ("calculator_handler", "battlefield_damage", True),
    "战场计算": ("calculator_handler", "battlefield_damage", True),
    "mp伤害": ("calculator_handler", "battlefield_damage", True),
    "战备": ("calculator_handler", "readiness", True),
    "战备计算": ("calculator_handler", "readiness", True),
    "配装计算": ("calculator_handler", "readiness", True),
    "计算帮助": ("calculator_handler", "calc_help", True),
    "计算器帮助": ("calculator_handler", "calc_help", True),
    "计算映射表": ("calculator_handler", "mapping_table", True),
    "映射表": ("calculator_handler", "mapping_table", True),
}

_DIGIT_VALIDATE_ROUTES = {
    "解绑": ("account_handler", "unbind_account", "解绑"),
    "账号解绑": ("account_handler", "unbind_account", "解绑"),
    "删除": ("account_handler", "delete_account", "删除"),
    "账号删除": ("account_handler", "delete_account", "删除"),
    "切换": ("account_handler", "switch_account", "切换"),
    "账号切换": ("account_handler", "switch_account", "切换"),
}

_VOTE_ROUTES = {
    "改枪码点赞": True,
    "方案点赞": True,
    "改枪码点踩": False,
    "方案点踩": False,
}

_PUSH_ROUTES = {
    "开启每日密码推送": ("toggle_daily_keyword", True),
    "开启密码推送": ("toggle_daily_keyword", True),
    "关闭每日密码推送": ("toggle_daily_keyword", False),
    "关闭密码推送": ("toggle_daily_keyword", False),
    "开启日报推送": ("toggle_daily_report", True),
    "订阅日报": ("toggle_daily_report", True),
    "关闭日报推送": ("toggle_daily_report", False),
    "取消订阅日报": ("toggle_daily_report", False),
    "开启周报推送": ("toggle_weekly_report", True),
    "订阅周报": ("toggle_weekly_report", True),
    "关闭周报推送": ("toggle_weekly_report", False),
    "取消订阅周报": ("toggle_weekly_report", False),
    "推送状态": ("get_push_status", None),
    "定时任务状态": ("get_push_status", None),
}

_PLACE_PUSH_ROUTES = {
    "开启特勤处推送", "订阅特勤处",
    "关闭特勤处推送", "取消订阅特勤处",
}

_BROADCAST_ROUTES = {
    "广播": "send",
    "系统通知": "send",
    "广播历史": "history",
    "通知历史": "history",
}


@register(
    "astrbot_plugin_deltaforce",
    "EntropyIncrease",
    "三角洲行动 AstrBot 插件",
    "0.2.0",
    "https://github.com/Entropy-Increase-Team/astrbot_plugin_deltaforce",
)
class DeltaForce(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.context = context
        self.config = config
        self.token = config.get("token", "")
        self.clientid = config.get("clientid", "")
        
        self.api_mode = config.get("api_mode", "auto")
        try:
            self.api_timeout = max(1, int(config.get("api_timeout", 30)))
        except (TypeError, ValueError):
            self.api_timeout = 30
        try:
            self.api_retry_count = max(0, min(int(config.get("api_retry_count", 3)), 10))
        except (TypeError, ValueError):
            self.api_retry_count = 3
        
        try:
            # 初始化 API 和数据库
            self.api = DeltaForceAPI(
                token=self.token, 
                clientid=self.clientid,
                api_mode=self.api_mode,
                timeout=self.api_timeout,
                retry_count=self.api_retry_count
            )
            self.db_manager = DeltaForceSQLiteManager()
            
            # 初始化各处理器
            self.info_handler = InfoHandler(self.api, self.db_manager)
            self.account_handler = AccountHandler(self.api, self.db_manager)
            self.data_handler = DataHandler(self.api, self.db_manager)
            self.tools_handler = ToolsHandler(self.api, self.db_manager)
            self.system_handler = SystemHandler(self.api, self.db_manager)
            self.entertainment_handler = EntertainmentHandler(self.api, self.db_manager)
            self.voice_handler = VoiceHandler(self.api, self.db_manager)
            self.music_handler = MusicHandler(self.api, self.db_manager)
            self.room_handler = RoomHandler(self.api, self.db_manager)
            self.solution_handler = SolutionHandler(self.api, self.db_manager)
            self.calculator_handler = CalculatorHandler(self.api, self.db_manager)
            
            # 推送模块 (可选)
            self.scheduler = None
            self.daily_keyword_push = None
            self.daily_report_push = None
            self.weekly_report_push = None
            self.place_task_push = None
            self.broadcast_system = None
            self.push_handler = None
        except Exception as e:
            logger.error(f"三角洲插件初始化失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 重新抛出异常，或者保持部分功能可用
            # 这里我们选择打印堆栈，以便排查 list index out of range 具体位置
            raise e

    async def initialize(self):
        """插件初始化"""
        try:
            success = await self.db_manager.initialize_table()
            if success:
                logger.info("三角洲插件数据库初始化完成")
            else:
                logger.error("三角洲插件数据库初始化失败")
            
            # 初始化推送模块
            await self._init_push_module()
            
        except Exception as e:
            logger.error(f"插件初始化失败: {e}")
    
    async def _init_push_module(self):
        """初始化推送模块"""
        if not HAS_PUSH_MODULE:
            return
        
        try:
            # 创建调度器
            self.scheduler = PushScheduler()
            await self.scheduler.initialize()
            
            # 创建推送实例
            self.daily_keyword_push = DailyKeywordPush(self.context, self.api, self.config)
            self.daily_report_push = DailyReportPush(self.context, self.api, self.db_manager, self.config)
            self.weekly_report_push = WeeklyReportPush(self.context, self.api, self.db_manager, self.config)
            
            # 创建特勤处推送实例
            self.place_task_push = PlaceTaskPush(self.context, self.api, self.db_manager, self.config)
            
            # 创建广播系统实例
            self.broadcast_system = BroadcastSystem(self.context, self.db_manager, self.config)
            
            # 创建推送处理器
            self.push_handler = PushHandler(
                self.api, self.db_manager, self.scheduler,
                self.daily_keyword_push, self.daily_report_push, self.weekly_report_push,
                self.config
            )
            
            # 启动调度器
            await self.scheduler.start()
            
            # 启动特勤处推送后台任务
            await self.place_task_push.start()
            
            # 注册已启用的推送任务
            if self.daily_keyword_push.enabled:
                self.scheduler.add_job(
                    self.daily_keyword_push.JOB_ID,
                    self.daily_keyword_push.execute,
                    self.daily_keyword_push.cron
                )
            if self.daily_report_push.enabled:
                self.scheduler.add_job(
                    self.daily_report_push.JOB_ID,
                    self.daily_report_push.execute,
                    self.daily_report_push.cron
                )
            if self.weekly_report_push.enabled:
                self.scheduler.add_job(
                    self.weekly_report_push.JOB_ID,
                    self.weekly_report_push.execute,
                    self.weekly_report_push.cron
                )
            
            logger.info("三角洲推送模块初始化完成")
            
        except Exception as e:
            logger.error(f"推送模块初始化失败: {e}")

    # ==================== 空格兼容分发器 ====================

    @filter.command("三角洲", alias={"洲"})
    async def delta_dispatch(self, event: AstrMessageEvent, rest: str = ""):
        """处理 '三角洲 xxx' 格式的带空格指令，路由到对应的 handler"""
        # AstrBot 按空格分割参数，rest 只收到第一个词，后续参数丢失
        # 从 event.message_str 提取完整剩余文本
        try:
            full_msg = event.message_str.strip()
            for prefix in ["三角洲", "洲"]:
                idx = full_msg.find(prefix)
                if idx >= 0:
                    rest = full_msg[idx + len(prefix):].strip()
                    break
        except Exception:
            pass

        if not rest.strip():
            async for result in self.system_handler.show_help(event):
                yield result
            return

        parts = rest.strip().split(maxsplit=1)
        sub_cmd = parts[0]
        sub_args = parts[1] if len(parts) > 1 else ""

        # 1) 需要数字验证的子命令 (解绑/删除/切换)
        if sub_cmd in _DIGIT_VALIDATE_ROUTES:
            handler_attr, method_name, action_name = _DIGIT_VALIDATE_ROUTES[sub_cmd]
            if not sub_args:
                yield event.plain_result(f"请输入要{action_name}的账号序号")
                return
            if not sub_args.strip().isdigit():
                yield event.plain_result("请输入有效的账号序号（正整数）")
                return
            handler = getattr(self, handler_attr)
            method = getattr(handler, method_name)
            async for result in method(event, int(sub_args)):
                yield result
            return

        # 2) 改枪方案投票
        if sub_cmd in _VOTE_ROUTES:
            is_upvote = _VOTE_ROUTES[sub_cmd]
            async for result in self.solution_handler.vote_solution(event, sub_args, is_upvote):
                yield result
            return

        # 3) 推送开关指令
        if sub_cmd in _PUSH_ROUTES:
            if not self.push_handler:
                yield event.plain_result("推送功能未初始化")
                return
            method_name, toggle = _PUSH_ROUTES[sub_cmd]
            method = getattr(self.push_handler, method_name)
            if toggle is not None:
                async for result in method(event, toggle):
                    yield result
            else:
                async for result in method(event):
                    yield result
            return

        # 4) 特勤处推送
        if sub_cmd in _PLACE_PUSH_ROUTES:
            if not self.place_task_push:
                yield event.plain_result("推送功能未初始化")
                return
            user_id = str(event.get_sender_id())
            if sub_cmd in ("开启特勤处推送", "订阅特勤处"):
                user_data = await self.db_manager.get_user(int(user_id))
                if not user_data or not user_data[1]:
                    yield event.plain_result("请先登录账号后再开启特勤处推送")
                    return
                token = user_data[1]
                umo = event.unified_msg_origin
                umo_parts = umo.split(":") if umo else []
                platform = umo_parts[0] if len(umo_parts) > 0 else "aiocqhttp"
                target_type = umo_parts[1] if len(umo_parts) > 1 else "private"
                target_id = umo_parts[2] if len(umo_parts) > 2 else user_id
                success, message = await self.place_task_push.subscribe(
                    user_id=user_id, token=token,
                    target_type=target_type, target_id=target_id, platform=platform
                )
                yield event.plain_result(message)
            else:
                umo = event.unified_msg_origin
                umo_parts = umo.split(":") if umo else []
                target_type = umo_parts[1] if len(umo_parts) > 1 else "private"
                target_id = umo_parts[2] if len(umo_parts) > 2 else user_id
                success, message = await self.place_task_push.unsubscribe(
                    user_id=user_id, target_type=target_type, target_id=target_id
                )
                yield event.plain_result(message)
            return

        # 5) 广播
        if sub_cmd in _BROADCAST_ROUTES:
            action = _BROADCAST_ROUTES[sub_cmd]
            if not self.broadcast_system:
                yield event.plain_result("广播功能未初始化")
                return
            if action == "send":
                if not sub_args:
                    yield event.plain_result("请输入广播内容\n用法: /三角洲广播 <消息内容>")
                    return
                sender_id = event.get_sender_id()
                broadcast_result = await self.broadcast_system.broadcast(sender_id, sub_args)
                yield event.plain_result(broadcast_result.get("message", "广播发送失败"))
            else:
                sender_id = event.get_sender_id()
                if not self.broadcast_system.is_admin(sender_id):
                    yield event.plain_result("您没有权限查看广播历史")
                    return
                history = await self.broadcast_system.get_history(10)
                if not history:
                    yield event.plain_result("暂无广播历史")
                    return
                import time
                lines = ["最近广播记录\n"]
                for i, record in enumerate(history, 1):
                    timestamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(record["created_at"]))
                    msg_preview = record["message"][:30] + "..." if len(record["message"]) > 30 else record["message"]
                    lines.append(f"{i}. [{timestamp}] {msg_preview}")
                    lines.append(f"   成功: {record['success_count']} | 失败: {record['fail_count']}")
                yield event.plain_result("\n".join(lines))
            return

        # 6) 通用路由表
        route = _CMD_ROUTES.get(sub_cmd)
        if route:
            handler_attr, method_name, pass_args = route
            handler = getattr(self, handler_attr)
            method = getattr(handler, method_name)
            if pass_args:
                async for result in method(event, sub_args):
                    yield result
            else:
                async for result in method(event):
                    yield result
            return

        yield event.plain_result(f"未知指令: {sub_cmd}\n发送 '三角洲帮助' 查看可用指令")

    # ==================== 帮助命令 ====================

    @filter.command("三角洲帮助", alias={"洲帮助", "三角洲菜单", "洲菜单"})
    async def show_help(self, event: AstrMessageEvent, message: str = ""):
        """显示帮助菜单"""
        async for result in self.system_handler.show_help(event):
            yield result

    # ==================== 账号管理命令 ====================

    @filter.command("三角洲CK登录", alias={"洲CK登录", "三角洲Cookie登录", "三角洲ck登录"})
    async def login_by_qq_ck(self, event: AstrMessageEvent, cookie: str = None):
        """QQ Cookie 登录"""
        async for result in self.account_handler.login_by_qq_ck(event, cookie):
            yield result

    @filter.command("三角洲QQ登录", alias={"洲QQ登录", "三角洲登录", "洲登录"})
    async def login_by_qq(self, event: AstrMessageEvent, _extra: str = ""):
        """QQ 二维码登录"""
        async for result in self.account_handler.login_by_qq(event):
            yield result

    @filter.command("三角洲微信登录", alias={"洲微信登录"})
    async def login_by_wechat(self, event: AstrMessageEvent, _extra: str = ""):
        """微信二维码登录"""
        async for result in self.account_handler.login_by_wechat(event):
            yield result

    @filter.command("三角洲安全中心登录", alias={"洲安全中心登录"})
    async def login_by_qqsafe(self, event: AstrMessageEvent, _extra: str = ""):
        """QQ安全中心登录"""
        async for result in self.account_handler.login_by_qqsafe(event):
            yield result

    @filter.command("三角洲WeGame登录", alias={"洲WeGame登录", "三角洲WG登录", "洲WG登录"})
    async def login_by_wegame(self, event: AstrMessageEvent, _extra: str = ""):
        """WeGame 登录"""
        async for result in self.account_handler.login_by_wegame(event):
            yield result

    @filter.command("三角洲WeGame领奖", alias={"洲WeGame领奖", "三角洲WG领奖", "洲WG领奖", "三角洲每日领奖", "三角洲wegame礼包"})
    async def wegame_claim_gift(self, event: AstrMessageEvent, _extra: str = ""):
        """WeGame 每日领奖"""
        async for result in self.account_handler.wegame_claim_gift(event):
            yield result

    @filter.command("三角洲账号列表", alias={"洲账号列表", "三角洲账号管理", "洲账号管理"})
    async def list_account(self, event: AstrMessageEvent, _extra: str = ""):
        """查看账号列表"""
        async for result in self.account_handler.list_account(event):
            yield result

    @filter.command("三角洲解绑", alias={"洲解绑", "三角洲账号解绑"})
    async def unbind_account(self, event: AstrMessageEvent, value: str = ""):
        """解绑账号"""
        if not value:
            yield event.plain_result("请输入要解绑的账号序号")
            return
        if not value.strip().isdigit():
            yield event.plain_result("请输入有效的账号序号（正整数）")
            return
        async for result in self.account_handler.unbind_account(event, int(value)):
            yield result

    @filter.command("三角洲删除", alias={"洲删除", "三角洲账号删除"})
    async def delete_account(self, event: AstrMessageEvent, value: str = ""):
        """删除账号（仅支持QQ/微信）"""
        if not value:
            yield event.plain_result("请输入要删除的账号序号")
            return
        if not value.strip().isdigit():
            yield event.plain_result("请输入有效的账号序号（正整数）")
            return
        async for result in self.account_handler.delete_account(event, int(value)):
            yield result

    @filter.command("三角洲切换", alias={"洲切换", "三角洲账号切换"})
    async def switch_account(self, event: AstrMessageEvent, value: str = ""):
        """切换账号"""
        if not value:
            yield event.plain_result("请输入要切换的账号序号")
            return
        if not value.strip().isdigit():
            yield event.plain_result("请输入有效的账号序号（正整数）")
            return
        async for result in self.account_handler.switch_account(event, int(value)):
            yield result

    @filter.command("三角洲QQ刷新", alias={"洲QQ刷新", "三角洲刷新QQ"})
    async def refresh_qq(self, event: AstrMessageEvent, _extra: str = ""):
        """刷新QQ登录"""
        async for result in self.account_handler.refresh_qq(event):
            yield result

    @filter.command("三角洲微信刷新", alias={"洲微信刷新", "三角洲刷新微信"})
    async def refresh_wechat(self, event: AstrMessageEvent, _extra: str = ""):
        """刷新微信登录"""
        async for result in self.account_handler.refresh_wechat(event):
            yield result

    @filter.command("三角洲QQ授权登录", alias={"洲QQ授权登录", "三角洲qqoauth"})
    async def login_qq_oauth(self, event: AstrMessageEvent, auth_url: str = None):
        """QQ OAuth 授权登录"""
        async for result in self.account_handler.login_qq_oauth(event, auth_url):
            yield result

    @filter.command("三角洲微信授权登录", alias={"洲微信授权登录", "三角洲wechatoauth"})
    async def login_wechat_oauth(self, event: AstrMessageEvent, auth_url: str = None):
        """微信 OAuth 授权登录"""
        async for result in self.account_handler.login_wechat_oauth(event, auth_url):
            yield result

    # ==================== 信息查询命令 ====================

    @filter.command("三角洲货币", alias={"洲货币", "三角洲余额", "三角洲金币"})
    async def get_money(self, event: AstrMessageEvent, _extra: str = ""):
        """查询货币信息"""
        async for result in self.info_handler.get_money(event):
            yield result

    @filter.command("三角洲信息", alias={"洲信息", "三角洲个人信息", "三角洲我的信息"})
    async def get_personal_info(self, event: AstrMessageEvent, _extra: str = ""):
        """查询个人信息"""
        async for result in self.info_handler.get_personal_info(event):
            yield result

    @filter.command("三角洲UID", alias={"洲UID", "三角洲uid", "洲uid"})
    async def get_uid(self, event: AstrMessageEvent, _extra: str = ""):
        """查询UID"""
        async for result in self.info_handler.get_uid(event):
            yield result

    @filter.command("三角洲每日密码", alias={"洲每日密码", "三角洲今日密码", "洲今日密码"})
    async def get_daily_keyword(self, event: AstrMessageEvent, _extra: str = ""):
        """获取每日密码"""
        async for result in self.info_handler.get_daily_keyword(event):
            yield result

    @filter.command("三角洲违规历史", alias={"洲违规历史", "三角洲封禁历史"})
    async def get_ban_history(self, event: AstrMessageEvent, _extra: str = ""):
        """查询违规历史"""
        async for result in self.info_handler.get_ban_history(event):
            yield result

    @filter.command("三角洲干员列表", alias={"洲干员列表", "三角洲所有干员"})
    async def get_operator_list(self, event: AstrMessageEvent, args: str = ""):
        """查询干员列表"""
        async for result in self.info_handler.get_operator_list(event, args):
            yield result

    @filter.command("三角洲特勤处状态", alias={"洲特勤处状态", "三角洲特勤状态"})
    async def get_place_status(self, event: AstrMessageEvent, _extra: str = ""):
        """查询特勤处状态"""
        async for result in self.info_handler.get_place_status(event):
            yield result

    @filter.command("三角洲特勤处信息", alias={"洲特勤处信息", "三角洲特勤信息"})
    async def get_place_info(self, event: AstrMessageEvent, place_name: str = ""):
        """查询特勤处详情"""
        async for result in self.info_handler.get_place_info(event, place_name):
            yield result

    @filter.command("三角洲出红记录", alias={"洲出红记录", "三角洲红色记录", "三角洲红装记录"})
    async def get_red_collection(self, event: AstrMessageEvent, _extra: str = ""):
        """查询出红记录"""
        async for result in self.info_handler.get_red_collection(event):
            yield result

    @filter.command("三角洲健康状态", alias={"洲健康状态", "三角洲游戏健康"})
    async def get_game_health(self, event: AstrMessageEvent, _extra: str = ""):
        """查询游戏健康状态"""
        async for result in self.info_handler.get_game_health(event):
            yield result

    @filter.command("三角洲用户统计", alias={"洲用户统计", "三角洲统计"})
    async def get_user_stats(self, event: AstrMessageEvent, _extra: str = ""):
        """查询用户统计"""
        async for result in self.info_handler.get_user_stats(event):
            yield result

    # ==================== 数据查询命令 ====================

    @filter.command("三角洲数据", alias={"洲数据", "三角洲data", "三角洲个人数据"})
    async def get_personal_data(self, event: AstrMessageEvent, args: str = ""):
        """查询个人数据"""
        async for result in self.data_handler.get_personal_data(event, args):
            yield result

    @filter.command("三角洲流水", alias={"洲流水", "三角洲flows"})
    async def get_flows(self, event: AstrMessageEvent, args: str = ""):
        """查询流水记录"""
        async for result in self.data_handler.get_flows(event, args):
            yield result

    @filter.command("三角洲战绩", alias={"洲战绩", "三角洲record", "三角洲记录"})
    async def get_record(self, event: AstrMessageEvent, args: str = ""):
        """查询战绩记录"""
        async for result in self.data_handler.get_record(event, args):
            yield result

    @filter.command("三角洲藏品", alias={"洲藏品", "三角洲collection", "三角洲收藏"})
    async def get_collection(self, event: AstrMessageEvent, _extra: str = ""):
        """查询藏品信息"""
        async for result in self.data_handler.get_collection(event):
            yield result

    @filter.command("三角洲干员", alias={"洲干员", "三角洲operator"})
    async def get_operators(self, event: AstrMessageEvent, name: str = ""):
        """查询干员信息"""
        async for result in self.data_handler.get_operators(event, name):
            yield result

    # ==================== 工具查询命令 ====================

    @filter.command("三角洲搜索", alias={"洲搜索", "三角洲search", "三角洲查找"})
    async def search_object(self, event: AstrMessageEvent, keyword: str = ""):
        """搜索物品"""
        async for result in self.tools_handler.search_object(event, keyword):
            yield result

    @filter.command("三角洲价格", alias={"洲价格", "三角洲price", "三角洲物价"})
    async def get_current_price(self, event: AstrMessageEvent, query: str = ""):
        """查询物品价格"""
        async for result in self.tools_handler.get_current_price(event, query):
            yield result

    @filter.command("三角洲材料价格", alias={"洲材料价格", "三角洲材料", "三角洲material"})
    async def get_material_price(self, event: AstrMessageEvent, query: str = ""):
        """查询材料价格"""
        async for result in self.tools_handler.get_material_price(event, query):
            yield result

    @filter.command("三角洲利润排行", alias={"洲利润排行", "三角洲利润榜", "三角洲profit"})
    async def get_profit_rank(self, event: AstrMessageEvent, args: str = ""):
        """查询利润排行"""
        async for result in self.tools_handler.get_profit_rank(event, args):
            yield result

    @filter.command("三角洲地图统计", alias={"洲地图统计", "三角洲mapstats", "三角洲地图数据"})
    async def get_map_stats(self, event: AstrMessageEvent, args: str = ""):
        """查询地图统计"""
        async for result in self.tools_handler.get_map_stats(event, args):
            yield result

    @filter.command("三角洲物品列表", alias={"洲物品列表", "三角洲itemlist", "三角洲物品"})
    async def get_object_list(self, event: AstrMessageEvent, args: str = ""):
        """查询物品列表"""
        async for result in self.tools_handler.get_object_list(event, args):
            yield result

    @filter.command("三角洲大红收藏", alias={"洲大红收藏", "三角洲大红藏品", "三角洲红色收藏"})
    async def get_red_collection_season(self, event: AstrMessageEvent, args: str = ""):
        """查询大红收藏"""
        async for result in self.tools_handler.get_red_collection(event, args):
            yield result

    @filter.command("三角洲最高利润", alias={"洲最高利润", "三角洲利润V2", "三角洲maxprofit"})
    async def get_max_profit(self, event: AstrMessageEvent, args: str = ""):
        """查询最高利润排行V2"""
        async for result in self.tools_handler.get_max_profit(event, args):
            yield result

    @filter.command("三角洲特勤处利润", alias={"洲特勤处利润", "三角洲特勤利润"})
    async def get_special_ops_profit(self, event: AstrMessageEvent, args: str = ""):
        """查询特勤处利润总览"""
        async for result in self.tools_handler.get_special_ops_profit(event, args):
            yield result

    @filter.command("三角洲文章列表", alias={"洲文章列表", "三角洲文章"})
    async def get_article_list(self, event: AstrMessageEvent, _extra: str = ""):
        """获取文章列表"""
        async for result in self.tools_handler.get_article_list(event):
            yield result

    @filter.command("三角洲文章详情", alias={"洲文章详情", "三角洲文章内容"})
    async def get_article_detail(self, event: AstrMessageEvent, thread_id: str = ""):
        """获取文章详情"""
        async for result in self.tools_handler.get_article_detail(event, thread_id):
            yield result

    @filter.command("三角洲官方改枪码", alias={"洲官方改枪码", "三角洲官方方案", "三角洲官方改枪码列表"})
    async def get_official_solution_list(self, event: AstrMessageEvent, _extra: str = ""):
        """获取官方改枪方案列表"""
        async for result in self.tools_handler.get_official_solution_list(event):
            yield result

    @filter.command("三角洲官方改枪码详情", alias={"洲官方改枪码详情", "三角洲官方方案详情"})
    async def get_official_solution_detail(self, event: AstrMessageEvent, solution_id: str = ""):
        """获取官方改枪方案详情"""
        async for result in self.tools_handler.get_official_solution_detail(event, solution_id):
            yield result

    # ==================== 系统命令 ====================

    @filter.command("三角洲服务器状态", alias={"洲服务器状态", "三角洲状态", "三角洲health"})
    async def get_server_health(self, event: AstrMessageEvent, _extra: str = ""):
        """查询服务器状态"""
        async for result in self.system_handler.get_server_health(event):
            yield result

    # ==================== 管理员命令 ====================

    @filter.command("三角洲更新日志", alias={"洲更新日志", "三角洲changelog"})
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def get_changelog(self, event: AstrMessageEvent, _extra: str = ""):
        """查看更新日志（管理员）"""
        async for result in self.system_handler.get_changelog(event):
            yield result

    @filter.command("三角洲插件状态", alias={"洲插件状态", "三角洲插件信息"})
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def get_plugin_status(self, event: AstrMessageEvent, _extra: str = ""):
        """查看插件状态（管理员）"""
        async for result in self.system_handler.get_plugin_status(event):
            yield result

    @filter.command("三角洲订阅战绩", alias={"洲订阅战绩", "三角洲战绩订阅"})
    async def subscribe_record(self, event: AstrMessageEvent, sub_type: str = ""):
        """订阅战绩推送"""
        async for result in self.system_handler.subscribe_record(event, sub_type):
            yield result

    @filter.command("三角洲取消订阅", alias={"洲取消订阅", "三角洲取消战绩订阅"})
    async def unsubscribe_record(self, event: AstrMessageEvent, _extra: str = ""):
        """取消战绩订阅"""
        async for result in self.system_handler.unsubscribe_record(event):
            yield result

    @filter.command("三角洲订阅状态", alias={"洲订阅状态", "三角洲查看订阅"})
    async def get_subscription_status(self, event: AstrMessageEvent, _extra: str = ""):
        """查看订阅状态"""
        async for result in self.system_handler.get_subscription_status(event):
            yield result

    # ==================== 娱乐功能命令 ====================

    @filter.command("三角洲tts状态", alias={"洲tts状态", "三角洲TTS状态"})
    async def get_tts_health(self, event: AstrMessageEvent, _extra: str = ""):
        """查询TTS服务状态"""
        async for result in self.entertainment_handler.get_tts_health(event):
            yield result

    @filter.command("三角洲tts角色列表", alias={"洲tts角色列表", "三角洲TTS角色列表"})
    async def get_tts_presets(self, event: AstrMessageEvent, _extra: str = ""):
        """获取TTS角色预设列表"""
        async for result in self.entertainment_handler.get_tts_presets(event):
            yield result

    @filter.command("三角洲tts角色详情", alias={"洲tts角色详情", "三角洲TTS角色详情"})
    async def get_tts_preset_detail(self, event: AstrMessageEvent, character_id: str = ""):
        """获取TTS角色预设详情"""
        async for result in self.entertainment_handler.get_tts_preset_detail(event, character_id):
            yield result

    @filter.command("三角洲tts", alias={"洲tts", "三角洲TTS", "三角洲语音合成"})
    async def tts_synthesize(self, event: AstrMessageEvent, args: str = ""):
        """TTS语音合成"""
        async for result in self.entertainment_handler.tts_synthesize(event, args):
            yield result

    @filter.command("三角洲tts上传", alias={"洲tts上传", "三角洲TTS上传", "三角洲tts下载"})
    async def download_last_tts(self, event: AstrMessageEvent, _extra: str = ""):
        """下载上次合成的TTS语音"""
        async for result in self.entertainment_handler.download_last_tts(event):
            yield result

    @filter.command("三角洲ai预设列表", alias={"洲ai预设列表", "三角洲AI预设列表"})
    async def get_ai_presets(self, event: AstrMessageEvent, _extra: str = ""):
        """获取AI预设列表"""
        async for result in self.entertainment_handler.get_ai_presets(event):
            yield result

    @filter.command("三角洲ai锐评", alias={"洲ai锐评", "三角洲AI锐评", "三角洲ai评价"})
    async def get_ai_commentary(self, event: AstrMessageEvent, args: str = ""):
        """AI锐评战绩"""
        async for result in self.entertainment_handler.get_ai_commentary(event, args):
            yield result

    @filter.command("三角洲日报", alias={"洲日报", "三角洲daily", "三角洲每日报告"})
    async def get_daily_report(self, event: AstrMessageEvent, args: str = ""):
        """获取日报"""
        async for result in self.entertainment_handler.get_daily_report(event, args):
            yield result

    @filter.command("三角洲周报", alias={"洲周报", "三角洲weekly", "三角洲每周报告"})
    async def get_weekly_report(self, event: AstrMessageEvent, args: str = ""):
        """获取周报"""
        async for result in self.entertainment_handler.get_weekly_report(event, args):
            yield result

    @filter.command("三角洲昨日收益", alias={"洲昨日收益", "三角洲昨日物资"})
    async def get_yesterday_profit(self, event: AstrMessageEvent, args: str = ""):
        """获取昨日收益"""
        async for result in self.entertainment_handler.get_yesterday_profit(event, args):
            yield result

    # ==================== 语音功能命令 ====================

    @filter.command("三角洲语音", alias={"洲语音", "三角洲游戏语音"})
    async def send_voice(self, event: AstrMessageEvent, args: str = ""):
        """发送游戏语音"""
        async for result in self.voice_handler.send_voice(event, args):
            yield result

    @filter.command("三角洲语音角色", alias={"洲语音角色", "三角洲语音角色列表"})
    async def get_voice_characters(self, event: AstrMessageEvent, args: str = ""):
        """获取语音角色列表"""
        async for result in self.voice_handler.get_voice_characters(event, args):
            yield result

    @filter.command("三角洲语音标签", alias={"洲语音标签", "三角洲语音标签列表"})
    async def get_voice_tags(self, event: AstrMessageEvent, args: str = ""):
        """获取语音标签列表"""
        async for result in self.voice_handler.get_voice_tags(event, args):
            yield result

    @filter.command("三角洲语音分类", alias={"洲语音分类", "三角洲语音分类列表"})
    async def get_voice_categories(self, event: AstrMessageEvent, _extra: str = ""):
        """获取语音分类列表"""
        async for result in self.voice_handler.get_voice_categories(event):
            yield result

    @filter.command("三角洲语音统计", alias={"洲语音统计", "三角洲语音数据"})
    async def get_voice_stats(self, event: AstrMessageEvent, _extra: str = ""):
        """获取语音统计数据"""
        async for result in self.voice_handler.get_voice_stats(event):
            yield result

    # ==================== 音乐功能命令 ====================

    @filter.command("三角洲鼠鼠音乐", alias={"洲鼠鼠音乐", "三角洲播放音乐"})
    async def send_music(self, event: AstrMessageEvent, args: str = ""):
        """播放鼠鼠音乐"""
        async for result in self.music_handler.send_music(event, args):
            yield result

    @filter.command("三角洲音乐列表", alias={"洲音乐列表", "三角洲鼠鼠音乐列表"})
    async def get_music_list(self, event: AstrMessageEvent, args: str = ""):
        """获取音乐列表"""
        async for result in self.music_handler.get_music_list(event, args):
            yield result

    @filter.command("三角洲鼠鼠歌单", alias={"洲鼠鼠歌单", "三角洲歌单"})
    async def get_playlist(self, event: AstrMessageEvent, args: str = ""):
        """获取鼠鼠歌单"""
        async for result in self.music_handler.get_playlist(event, args):
            yield result

    @filter.command("三角洲点歌", alias={"洲点歌", "三角洲听", "三角洲播放", "点歌"})
    async def select_music_by_number(self, event: AstrMessageEvent, number: str = ""):
        """点歌 - 通过序号选择音乐"""
        async for result in self.music_handler.select_music_by_number(event, number):
            yield result

    @filter.command("三角洲歌词", alias={"洲歌词", "三角洲鼠鼠歌词"})
    async def get_lyrics(self, event: AstrMessageEvent, _extra: str = ""):
        """获取歌词"""
        async for result in self.music_handler.get_lyrics(event):
            yield result

    @filter.command("三角洲鼠鼠语音", alias={"洲鼠鼠语音"})
    async def send_shushu_voice(self, event: AstrMessageEvent, _extra: str = ""):
        """发送鼠鼠语音"""
        async for result in self.music_handler.send_voice(event):
            yield result

    # ==================== 开黑房间命令 ====================

    @filter.command("三角洲房间列表", alias={"洲房间列表", "三角洲开黑列表"})
    async def get_room_list(self, event: AstrMessageEvent, args: str = ""):
        """获取开黑房间列表"""
        async for result in self.room_handler.get_room_list(event, args):
            yield result

    @filter.command("三角洲创建房间", alias={"洲创建房间", "三角洲开房间"})
    async def create_room(self, event: AstrMessageEvent, args: str = ""):
        """创建开黑房间"""
        async for result in self.room_handler.create_room(event, args):
            yield result

    @filter.command("三角洲加入房间", alias={"洲加入房间", "三角洲进入房间"})
    async def join_room(self, event: AstrMessageEvent, room_id: str = ""):
        """加入开黑房间"""
        async for result in self.room_handler.join_room(event, room_id):
            yield result

    @filter.command("三角洲退出房间", alias={"洲退出房间", "三角洲离开房间"})
    async def quit_room(self, event: AstrMessageEvent, room_id: str = ""):
        """退出开黑房间"""
        async for result in self.room_handler.quit_room(event, room_id):
            yield result

    @filter.command("三角洲房间信息", alias={"洲房间信息", "三角洲房间详情"})
    async def get_room_info(self, event: AstrMessageEvent, room_id: str = ""):
        """获取房间信息"""
        async for result in self.room_handler.get_room_info(event, room_id):
            yield result

    @filter.command("三角洲房间标签", alias={"洲房间标签", "三角洲开黑标签"})
    async def get_room_tags(self, event: AstrMessageEvent, _extra: str = ""):
        """获取房间标签列表"""
        async for result in self.room_handler.get_room_tags(event):
            yield result

    @filter.command("三角洲房间地图列表", alias={"洲房间地图列表", "三角洲房间地图"})
    async def get_room_maps(self, event: AstrMessageEvent, _extra: str = ""):
        """获取房间地图列表"""
        async for result in self.room_handler.get_room_maps(event):
            yield result

    @filter.command("三角洲踢出成员", alias={"洲踢出成员", "三角洲踢人"})
    async def kick_member(self, event: AstrMessageEvent, args: str = ""):
        """踢出房间成员"""
        async for result in self.room_handler.kick_member(event, args):
            yield result

    # ==================== 改枪方案命令 ====================

    @filter.command("三角洲改枪码列表", alias={"洲改枪码列表", "三角洲改枪方案列表"})
    async def get_solution_list(self, event: AstrMessageEvent, args: str = ""):
        """获取改枪方案列表"""
        async for result in self.solution_handler.get_solution_list(event, args):
            yield result

    @filter.command("三角洲改枪码详情", alias={"洲改枪码详情", "三角洲改枪方案详情"})
    async def get_solution_detail(self, event: AstrMessageEvent, solution_id: str = ""):
        """获取改枪方案详情"""
        async for result in self.solution_handler.get_solution_detail(event, solution_id):
            yield result

    @filter.command("三角洲上传改枪码", alias={"洲上传改枪码", "三角洲分享改枪码", "三角洲上传方案"})
    async def upload_solution(self, event: AstrMessageEvent, args: str = ""):
        """上传改枪方案"""
        async for result in self.solution_handler.upload_solution(event, args):
            yield result

    @filter.command("三角洲改枪码点赞", alias={"洲改枪码点赞", "三角洲方案点赞"})
    async def upvote_solution(self, event: AstrMessageEvent, solution_id: str = ""):
        """给改枪方案点赞"""
        async for result in self.solution_handler.vote_solution(event, solution_id, True):
            yield result

    @filter.command("三角洲改枪码点踩", alias={"洲改枪码点踩", "三角洲方案点踩"})
    async def downvote_solution(self, event: AstrMessageEvent, solution_id: str = ""):
        """给改枪方案点踩"""
        async for result in self.solution_handler.vote_solution(event, solution_id, False):
            yield result

    @filter.command("三角洲删除改枪码", alias={"洲删除改枪码", "三角洲删除方案"})
    async def delete_solution(self, event: AstrMessageEvent, solution_id: str = ""):
        """删除改枪方案"""
        async for result in self.solution_handler.delete_solution(event, solution_id):
            yield result

    @filter.command("三角洲收藏改枪码", alias={"洲收藏改枪码", "三角洲收藏方案"})
    async def collect_solution(self, event: AstrMessageEvent, solution_id: str = ""):
        """收藏改枪方案"""
        async for result in self.solution_handler.collect_solution(event, solution_id):
            yield result

    @filter.command("三角洲取消收藏改枪码", alias={"洲取消收藏改枪码", "三角洲取消收藏方案"})
    async def discollect_solution(self, event: AstrMessageEvent, solution_id: str = ""):
        """取消收藏改枪方案"""
        async for result in self.solution_handler.discollect_solution(event, solution_id):
            yield result

    @filter.command("三角洲改枪码收藏列表", alias={"洲改枪码收藏列表", "三角洲我的收藏方案"})
    async def get_collect_list(self, event: AstrMessageEvent, args: str = ""):
        """获取收藏的改枪方案"""
        async for result in self.solution_handler.get_collect_list(event, args):
            yield result

    # ==================== 计算器命令 ====================

    @filter.command("三角洲修甲", alias={"洲修甲", "三角洲修理", "三角洲维修计算"})
    async def calc_repair(self, event: AstrMessageEvent, args: str = ""):
        """快捷维修计算"""
        async for result in self.calculator_handler.quick_repair(event, args):
            yield result

    @filter.command("三角洲伤害", alias={"洲伤害", "三角洲伤害计算", "三角洲dmg"})
    async def calc_damage(self, event: AstrMessageEvent, args: str = ""):
        """快捷伤害计算"""
        async for result in self.calculator_handler.quick_damage(event, args):
            yield result

    @filter.command("三角洲战场伤害", alias={"洲战场伤害", "三角洲战场计算", "三角洲mp伤害"})
    async def calc_battlefield_damage(self, event: AstrMessageEvent, args: str = ""):
        """战场伤害计算"""
        async for result in self.calculator_handler.battlefield_damage(event, args):
            yield result

    @filter.command("三角洲战备", alias={"洲战备", "三角洲战备计算", "三角洲配装计算"})
    async def calc_readiness(self, event: AstrMessageEvent, args: str = ""):
        """战备计算"""
        async for result in self.calculator_handler.readiness(event, args):
            yield result

    @filter.command("三角洲计算帮助", alias={"洲计算帮助", "三角洲计算器帮助"})
    async def show_calc_help(self, event: AstrMessageEvent, args: str = ""):
        """显示计算帮助"""
        async for result in self.calculator_handler.calc_help(event, args):
            yield result

    @filter.command("三角洲计算映射表", alias={"洲计算映射表", "三角洲映射表"})
    async def show_mapping_table(self, event: AstrMessageEvent, args: str = ""):
        """显示计算映射表"""
        async for result in self.calculator_handler.mapping_table(event, args):
            yield result

    # ==================== 推送命令 ====================

    @filter.command("三角洲开启每日密码推送", alias={"洲开启每日密码推送", "三角洲开启密码推送"})
    async def enable_daily_keyword_push(self, event: AstrMessageEvent, _extra: str = ""):
        """开启每日密码推送"""
        if not self.push_handler:
            yield event.plain_result("推送功能未初始化")
            return
        async for result in self.push_handler.toggle_daily_keyword(event, True):
            yield result

    @filter.command("三角洲关闭每日密码推送", alias={"洲关闭每日密码推送", "三角洲关闭密码推送"})
    async def disable_daily_keyword_push(self, event: AstrMessageEvent, _extra: str = ""):
        """关闭每日密码推送"""
        if not self.push_handler:
            yield event.plain_result("推送功能未初始化")
            return
        async for result in self.push_handler.toggle_daily_keyword(event, False):
            yield result

    @filter.command("三角洲开启日报推送", alias={"洲开启日报推送", "三角洲订阅日报"})
    async def enable_daily_report_push(self, event: AstrMessageEvent, _extra: str = ""):
        """开启日报推送"""
        if not self.push_handler:
            yield event.plain_result("推送功能未初始化")
            return
        async for result in self.push_handler.toggle_daily_report(event, True):
            yield result

    @filter.command("三角洲关闭日报推送", alias={"洲关闭日报推送", "三角洲取消订阅日报"})
    async def disable_daily_report_push(self, event: AstrMessageEvent, _extra: str = ""):
        """关闭日报推送"""
        if not self.push_handler:
            yield event.plain_result("推送功能未初始化")
            return
        async for result in self.push_handler.toggle_daily_report(event, False):
            yield result

    @filter.command("三角洲开启周报推送", alias={"洲开启周报推送", "三角洲订阅周报"})
    async def enable_weekly_report_push(self, event: AstrMessageEvent, _extra: str = ""):
        """开启周报推送"""
        if not self.push_handler:
            yield event.plain_result("推送功能未初始化")
            return
        async for result in self.push_handler.toggle_weekly_report(event, True):
            yield result

    @filter.command("三角洲关闭周报推送", alias={"洲关闭周报推送", "三角洲取消订阅周报"})
    async def disable_weekly_report_push(self, event: AstrMessageEvent, _extra: str = ""):
        """关闭周报推送"""
        if not self.push_handler:
            yield event.plain_result("推送功能未初始化")
            return
        async for result in self.push_handler.toggle_weekly_report(event, False):
            yield result

    @filter.command("三角洲推送状态", alias={"洲推送状态", "三角洲定时任务状态"})
    async def get_push_status(self, event: AstrMessageEvent, _extra: str = ""):
        """查询推送状态"""
        if not self.push_handler:
            yield event.plain_result("推送功能未初始化")
            return
        async for result in self.push_handler.get_push_status(event):
            yield result

    # ==================== 特勤处推送命令 ====================

    @filter.command("三角洲开启特勤处推送", alias={"洲开启特勤处推送", "三角洲订阅特勤处"})
    async def enable_place_task_push(self, event: AstrMessageEvent, _extra: str = ""):
        """开启特勤处制造完成推送"""
        if not self.place_task_push:
            yield event.plain_result("推送功能未初始化")
            return
        
        user_id = str(event.get_sender_id())
        user_data = await self.db_manager.get_user(int(user_id))
        
        if not user_data or not user_data[1]:
            yield event.plain_result("请先登录账号后再开启特勤处推送")
            return
        
        token = user_data[1]
        
        # 解析 unified_msg_origin 获取推送目标信息
        umo = event.unified_msg_origin
        # umo 格式: platform:type:id 例如 aiocqhttp:group:123456
        parts = umo.split(":") if umo else []
        platform = parts[0] if len(parts) > 0 else "aiocqhttp"
        target_type = parts[1] if len(parts) > 1 else "private"
        target_id = parts[2] if len(parts) > 2 else user_id
        
        success, message = await self.place_task_push.subscribe(
            user_id=user_id,
            token=token,
            target_type=target_type,
            target_id=target_id,
            platform=platform
        )
        
        yield event.plain_result(message)

    @filter.command("三角洲关闭特勤处推送", alias={"洲关闭特勤处推送", "三角洲取消订阅特勤处"})
    async def disable_place_task_push(self, event: AstrMessageEvent, _extra: str = ""):
        """关闭特勤处制造完成推送"""
        if not self.place_task_push:
            yield event.plain_result("推送功能未初始化")
            return
        
        user_id = str(event.get_sender_id())
        # 解析 unified_msg_origin
        umo = event.unified_msg_origin
        parts = umo.split(":") if umo else []
        target_type = parts[1] if len(parts) > 1 else "private"
        target_id = parts[2] if len(parts) > 2 else user_id
        
        success, message = await self.place_task_push.unsubscribe(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id
        )
        
        yield event.plain_result(message)

    # ==================== 广播命令 ====================

    @filter.command("三角洲广播", alias={"洲广播", "三角洲系统通知"})
    async def send_broadcast(self, event: AstrMessageEvent, message: str = ""):
        """发送广播消息（仅管理员）"""
        if not self.broadcast_system:
            yield event.plain_result("广播功能未初始化")
            return
        
        if not message:
            yield event.plain_result("请输入广播内容\n用法: /三角洲广播 <消息内容>")
            return
        
        sender_id = event.get_sender_id()
        result = await self.broadcast_system.broadcast(sender_id, message)
        
        yield event.plain_result(result.get("message", "广播发送失败"))

    @filter.command("三角洲广播历史", alias={"洲广播历史", "三角洲通知历史"})
    async def get_broadcast_history(self, event: AstrMessageEvent, _extra: str = ""):
        """查看广播历史（仅管理员）"""
        if not self.broadcast_system:
            yield event.plain_result("广播功能未初始化")
            return
        
        sender_id = event.get_sender_id()
        if not self.broadcast_system.is_admin(sender_id):
            yield event.plain_result("❌ 您没有权限查看广播历史")
            return
        
        history = await self.broadcast_system.get_history(10)
        
        if not history:
            yield event.plain_result("暂无广播历史")
            return
        
        import time
        lines = ["📋 最近广播记录\n"]
        for i, record in enumerate(history, 1):
            timestamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(record["created_at"]))
            msg_preview = record["message"][:30] + "..." if len(record["message"]) > 30 else record["message"]
            lines.append(f"{i}. [{timestamp}] {msg_preview}")
            lines.append(f"   成功: {record['success_count']} | 失败: {record['fail_count']}")
        
        yield event.plain_result("\n".join(lines))

    # ==================== 价格历史命令 ====================

    @filter.command("三角洲价格历史", alias={"洲价格历史", "三角洲历史价格"})
    async def get_price_history(self, event: AstrMessageEvent, query: str = ""):
        """查询物品价格历史"""
        async for result in self.tools_handler.get_price_history(event, query):
            yield result

    @filter.command("三角洲利润历史", alias={"洲利润历史", "三角洲历史利润"})
    async def get_profit_history(self, event: AstrMessageEvent, query: str = ""):
        """查询物品利润历史"""
        async for result in self.tools_handler.get_profit_history(event, query):
            yield result

    # ==================== 生命周期 ====================

    async def terminate(self):
        """插件销毁"""
        # 关闭推送调度器
        if self.scheduler:
            await self.scheduler.shutdown()
        # 关闭特勤处推送
        if self.place_task_push:
            await self.place_task_push.stop()
        logger.info("三角洲插件已终止")
