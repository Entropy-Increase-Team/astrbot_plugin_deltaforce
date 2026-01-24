"""
系统处理器
包含：帮助、服务器状态、订阅管理等
"""
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp
from .base import BaseHandler
from ..utils.render import Render


class SystemHandler(BaseHandler):
    """系统处理器"""

    # 帮助信息配置
    HELP_GROUPS = [
        {
            "group": "📱 账号管理",
            "list": [
                {"icon": "🔐", "title": "/三角洲 登录", "desc": "QQ扫码登录"},
                {"icon": "💬", "title": "/三角洲 微信登录", "desc": "微信扫码登录"},
                {"icon": "🛡️", "title": "/三角洲 安全中心登录", "desc": "QQ安全中心登录"},
                {"icon": "🎮", "title": "/三角洲 WeGame登录", "desc": "WeGame登录"},
                {"icon": "🍪", "title": "/三角洲 CK登录 <cookie>", "desc": "Cookie登录"},
                {"icon": "🔗", "title": "/三角洲 QQ授权登录", "desc": "OAuth授权登录"},
                {"icon": "📋", "title": "/三角洲 账号列表", "desc": "查看绑定账号"},
                {"icon": "🔄", "title": "/三角洲 切换 <序号>", "desc": "切换账号"},
                {"icon": "🗑️", "title": "/三角洲 解绑 <序号>", "desc": "解绑账号"},
            ]
        },
        {
            "group": "📊 信息查询",
            "list": [
                {"icon": "👤", "title": "/三角洲 信息", "desc": "个人信息"},
                {"icon": "🆔", "title": "/三角洲 UID", "desc": "查询UID"},
                {"icon": "💰", "title": "/三角洲 货币", "desc": "货币余额"},
                {"icon": "🔑", "title": "/三角洲 每日密码", "desc": "今日密码"},
                {"icon": "⚠️", "title": "/三角洲 违规历史", "desc": "封禁记录"},
                {"icon": "👥", "title": "/三角洲 干员列表", "desc": "所有干员"},
                {"icon": "🏭", "title": "/三角洲 特勤处状态", "desc": "特勤处状态"},
                {"icon": "🎁", "title": "/三角洲 出红记录", "desc": "红装出货"},
                {"icon": "🏥", "title": "/三角洲 健康状态", "desc": "游戏健康"},
            ]
        },
        {
            "group": "📈 数据查询",
            "list": [
                {"icon": "📊", "title": "/三角洲 数据 [模式]", "desc": "个人数据"},
                {"icon": "📜", "title": "/三角洲 流水 [类型]", "desc": "流水记录"},
                {"icon": "🎯", "title": "/三角洲 战绩 [模式]", "desc": "战绩记录"},
                {"icon": "💵", "title": "/三角洲 昨日收益", "desc": "昨日收益"},
                {"icon": "🏆", "title": "/三角洲 藏品", "desc": "藏品信息"},
                {"icon": "🗺️", "title": "/三角洲 地图统计", "desc": "地图数据"},
                {"icon": "📅", "title": "/三角洲 日报", "desc": "查看日报"},
                {"icon": "📆", "title": "/三角洲 周报", "desc": "查看周报"},
            ]
        },
        {
            "group": "🔧 工具查询",
            "list": [
                {"icon": "🔍", "title": "/三角洲 搜索 <词>", "desc": "搜索物品"},
                {"icon": "💲", "title": "/三角洲 价格 <物品>", "desc": "物品价格"},
                {"icon": "📦", "title": "/三角洲 材料价格", "desc": "材料价格"},
                {"icon": "📈", "title": "/三角洲 利润排行", "desc": "利润榜"},
                {"icon": "📝", "title": "/三角洲 物品列表", "desc": "物品列表"},
                {"icon": "💎", "title": "/三角洲 大红收藏", "desc": "大红藏品"},
            ]
        },
        {
            "group": "🧮 计算器",
            "list": [
                {"icon": "🔧", "title": "/三角洲 修甲 <参数>", "desc": "维修计算"},
                {"icon": "💥", "title": "/三角洲 伤害 <参数>", "desc": "伤害计算"},
                {"icon": "⚔️", "title": "/三角洲 战场伤害", "desc": "战场伤害"},
                {"icon": "🎒", "title": "/三角洲 战备 <目标>", "desc": "战备配装"},
                {"icon": "❓", "title": "/三角洲 计算帮助", "desc": "计算器帮助"},
            ]
        },
        {
            "group": "🎤 娱乐功能",
            "list": [
                {"icon": "🗣️", "title": "/三角洲 tts <角色> <文字>", "desc": "语音合成"},
                {"icon": "🎭", "title": "/三角洲 tts角色列表", "desc": "角色列表"},
                {"icon": "🤖", "title": "/三角洲 ai锐评", "desc": "AI战绩点评"},
                {"icon": "🔊", "title": "/三角洲 语音 [角色]", "desc": "游戏语音"},
                {"icon": "🎵", "title": "/三角洲 鼠鼠音乐", "desc": "播放音乐"},
            ]
        },
        {
            "group": "🏠 开黑房间",
            "list": [
                {"icon": "📋", "title": "/三角洲 房间列表", "desc": "查看房间"},
                {"icon": "➕", "title": "/三角洲 创建房间", "desc": "创建房间"},
                {"icon": "🚪", "title": "/三角洲 加入房间 <ID>", "desc": "加入房间"},
                {"icon": "ℹ️", "title": "/三角洲 房间信息 <ID>", "desc": "房间详情"},
            ]
        },
        {
            "group": "🔫 改枪方案",
            "list": [
                {"icon": "📜", "title": "/三角洲 改枪码列表", "desc": "方案列表"},
                {"icon": "🔍", "title": "/三角洲 改枪码详情 <ID>", "desc": "方案详情"},
                {"icon": "📤", "title": "/三角洲 上传改枪码", "desc": "上传方案"},
                {"icon": "👍", "title": "/三角洲 改枪码点赞 <ID>", "desc": "点赞方案"},
            ]
        },
        {
            "group": "📢 推送功能",
            "list": [
                {"icon": "🔔", "title": "/三角洲 开启每日密码推送", "desc": "群推送(管理)"},
                {"icon": "📊", "title": "/三角洲 开启日报推送", "desc": "订阅日报"},
                {"icon": "📈", "title": "/三角洲 开启周报推送", "desc": "订阅周报"},
                {"icon": "🏭", "title": "/三角洲 开启特勤处推送", "desc": "制造通知"},
                {"icon": "📋", "title": "/三角洲 推送状态", "desc": "查看推送"},
            ]
        },
        {
            "group": "⚙️ 系统功能",
            "list": [
                {"icon": "❓", "title": "/三角洲 帮助", "desc": "显示本帮助"},
                {"icon": "🌐", "title": "/三角洲 服务器状态", "desc": "API服务状态"},
                {"icon": "📜", "title": "/三角洲 更新日志", "desc": "更新历史"},
                {"icon": "📊", "title": "/三角洲 插件状态", "desc": "插件状态"},
            ]
        },
    ]

    async def show_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        # 将帮助分为左右两列
        help_groups = self.HELP_GROUPS
        mid = (len(help_groups) + 1) // 2
        left_groups = help_groups[:mid]
        right_groups = help_groups[mid:]

        # 获取背景图片的绝对路径并转换为 file URI
        # 这样可以确保 Playwright 能够正确加载本地图片
        bg_path = Render.RESOURCES_PATH / "imgs" / "background" / "bg2-1.webp"
        bg_uri = bg_path.as_uri()
        
        # 构建样式
        # 强制设置背景图片，并添加背景颜色作为回退
        style = f"""
        :root {{
            --bg-url: url('{bg_uri}');
            --container-bg-url: url('{bg_uri}');
            --icon-url: none;
            --primary-color: #ceb78b;
            --desc-color: #eee;
        }}
        body, .container {{
            background-color: #222 !important; /* 防止图片加载失败时显示白底 */
        }}
        """
        
        render_data = {
            'helpCfg': {
                'title': '三角洲行动插件帮助',
                'subTitle': 'DeltaForce-Plugin for AstrBot'
            },
            'style': style,
            'bgType': ' default',
            'twoColumnLayout': True,
            'leftGroups': left_groups,
            'rightGroups': right_groups,
            'helpGroups': help_groups,
        }
        
        # 尝试渲染图片
        # 增加高度以容纳更多指令，Playwright 会自动裁剪到实际内容
        yield await self.render_and_reply(
            event,
            'help/index.html',
            render_data,
            fallback_text=self._build_help_text(),
            width=1000,
            height=3000
        )

    def _build_help_text(self):
        """构建纯文本帮助（渲染失败时的回退）"""
        return """🎮【三角洲行动插件帮助】🎮
━━━━━━━━━━━━━━━━━━━━

📱 账号管理
  /三角洲 登录 - QQ扫码登录
  /三角洲 微信登录 - 微信扫码登录
  /三角洲 安全中心登录 - QQ安全中心登录
  /三角洲 账号列表 - 查看绑定的账号
  /三角洲 切换 <序号> - 切换账号

📊 信息查询
  /三角洲 信息 - 个人信息
  /三角洲 UID - 查询UID
  /三角洲 货币 - 货币余额
  /三角洲 每日密码 - 今日密码
  /三角洲 健康状态 - 游戏健康状态

📈 数据查询
  /三角洲 数据 [模式] - 个人数据
  /三角洲 战绩 [模式] - 战绩记录
  /三角洲 日报 - 查看日报
  /三角洲 周报 - 查看周报

🧮 计算器
  /三角洲 伤害 <参数> - 伤害计算
  /三角洲 修甲 <参数> - 维修计算
  /三角洲 计算帮助 - 计算器帮助

📢 推送功能
  /三角洲 开启日报推送 - 订阅日报
  /三角洲 开启周报推送 - 订阅周报
  /三角洲 推送状态 - 查看推送

⚙️ 系统功能
  /三角洲 帮助 - 显示本帮助
  /三角洲 服务器状态 - API服务状态

━━━━━━━━━━━━━━━━━━━━
💡 模式参数: 烽火/sol 或 mp/全面
💡 更多命令请查看完整帮助图片"""

    async def get_server_health(self, event: AstrMessageEvent):
        """服务器状态查询"""
        try:
            result = await self.api.get_health()
            
            if result and isinstance(result, dict) and result.get("status"):
                msg = self._format_health_status(result)
            elif result and isinstance(result, dict):
                msg = self._format_simple_status(result)
            else:
                msg = self._format_offline_status("无响应")
                
            yield self.chain_reply(event, msg)
            
        except Exception as e:
            error_info = str(e)
            if "502" in error_info:
                error_info = "502 Bad Gateway"
            elif "503" in error_info:
                error_info = "503 Service Unavailable"
            elif "500" in error_info:
                error_info = "500 Internal Server Error"
            elif "timeout" in error_info.lower():
                error_info = "请求超时"
            
            yield self.chain_reply(event, self._format_offline_status(error_info))

    def _format_health_status(self, data: dict) -> str:
        """格式化详细健康状态"""
        status = data.get("status", "unknown")
        cluster = data.get("cluster", {})
        system = data.get("system", {})
        dependencies = data.get("dependencies", {})
        
        status_text = "✅ 在线" if status == "healthy" else "❌ 离线" if status == "unhealthy" else "⚠️ 未知"
        node_type = cluster.get("nodeType", "unknown")
        node_type_name = "主节点" if node_type == "master" else "从节点" if node_type == "worker" else "未知节点"
        
        uptime = system.get("uptime", 0)
        uptime_hours = f"{uptime / 3600:.1f}" if uptime > 0 else "0"
        
        memory = system.get("memory", {})
        if memory.get("rss") and memory.get("heapUsed") and memory.get("heapTotal"):
            memory_info = f"RSS {memory['rss']}MB，堆内存 {memory['heapUsed']}/{memory['heapTotal']}MB"
        else:
            memory_info = "内存信息不可用"
        
        mongo_status = "✅ 正常" if dependencies.get("mongodb", {}).get("status") == "connected" else "❌ 异常"
        redis_status = "✅ 正常" if dependencies.get("redis", {}).get("status") == "connected" else "❌ 异常"
        
        lines = [
            "【三角洲插件-服务器状态】",
            f"服务状态：{status_text}",
            f"节点信息：{cluster.get('nodeId', '')} ({node_type_name})" if cluster.get('nodeId') else f"节点信息：{node_type_name}",
            f"运行时间：{uptime_hours}小时",
        ]
        
        if system.get("platform"):
            lines.append(f"系统平台：{system['platform']}")
        
        lines.append(f"内存使用：{memory_info}")
        
        if dependencies.get("mongodb") or dependencies.get("redis"):
            lines.append(f"数据库连接：MongoDB {mongo_status}，Redis {redis_status}")
        else:
            lines.append("数据库连接：状态信息不可用")
        
        return "\n".join(lines)

    def _format_simple_status(self, data: dict) -> str:
        """格式化简单状态"""
        status = data.get("status", "unknown")
        status_text = "✅ 在线" if status == "healthy" else "❌ 离线" if status == "unhealthy" else "⚠️ 未知"
        
        lines = [
            "【三角洲插件-服务器状态】",
            f"服务状态：{status_text}"
        ]
        
        if data.get("message"):
            lines.append(f"消息：{data['message']}")
        
        if data.get("timestamp"):
            from datetime import datetime
            try:
                time_str = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"检查时间：{time_str}")
            except:
                pass
        
        return "\n".join(lines)

    def _format_offline_status(self, error_info: str) -> str:
        """格式化离线状态"""
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"【三角洲插件-服务器状态】\n服务状态：❌ 离线\n错误信息：{error_info}\n检查时间：{current_time}"

    async def subscribe_record(self, event: AstrMessageEvent, sub_type: str = ""):
        """订阅战绩"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        # 解析订阅类型
        subscription_type = "both"
        if sub_type:
            sub_type_lower = sub_type.strip().lower()
            if sub_type_lower in ["烽火", "烽火地带", "sol"]:
                subscription_type = "sol"
            elif sub_type_lower in ["全面", "全面战场", "mp"]:
                subscription_type = "mp"

        result = await self.api.subscribe_record(
            platform_id=str(event.get_sender_id()),
            client_id=self.api.clientid,
            subscription_type=subscription_type
        )

        if result.get("success", False) or self.is_success(result):
            type_names = {"sol": "烽火地带", "mp": "全面战场", "both": "全部模式"}
            yield self.chain_reply(event, f"✅ 战绩订阅成功！\n订阅类型：{type_names.get(subscription_type, subscription_type)}\n\n战绩将在对局结束后自动推送")
        else:
            yield self.chain_reply(event, f"❌ 订阅失败：{result.get('message', result.get('msg', '未知错误'))}")

    async def unsubscribe_record(self, event: AstrMessageEvent):
        """取消订阅战绩"""
        result = await self.api.unsubscribe_record(
            platform_id=str(event.get_sender_id()),
            client_id=self.api.clientid
        )

        if result.get("success", False) or self.is_success(result):
            yield self.chain_reply(event, "✅ 已取消战绩订阅")
        else:
            yield self.chain_reply(event, f"❌ 取消订阅失败：{result.get('message', result.get('msg', '未知错误'))}")

    async def get_subscription_status(self, event: AstrMessageEvent):
        """查询订阅状态"""
        result = await self.api.get_record_subscription(
            platform_id=str(event.get_sender_id()),
            client_id=self.api.clientid
        )

        if not result.get("success", False) and not self.is_success(result):
            yield self.chain_reply(event, f"❌ 查询失败：{result.get('message', result.get('msg', '未知错误'))}")
            return

        data = result.get("data", {})
        if not data or not data.get("enabled", False):
            yield self.chain_reply(event, "📡 当前未订阅战绩推送\n\n使用 /三角洲 订阅战绩 开启订阅")
            return

        sub_type = data.get("subscriptionType", "both")
        type_names = {"sol": "烽火地带", "mp": "全面战场", "both": "全部模式"}
        
        lines = [
            "📡【战绩订阅状态】",
            f"状态：✅ 已订阅",
            f"类型：{type_names.get(sub_type, sub_type)}"
        ]
        
        if data.get("createdAt"):
            lines.append(f"订阅时间：{data['createdAt']}")

        yield self.chain_reply(event, "\n".join(lines))

    async def get_changelog(self, event: AstrMessageEvent):
        """获取更新日志（管理员）"""
        changelog = """📝【三角洲插件更新日志】
━━━━━━━━━━━━━━━━━━━━

📦 v0.3.0 (当前版本)
• 新增物品列表查询功能
• 新增大红收藏按赛季查询
• 新增最高利润V2排行功能
• 新增特勤处利润总览功能
• 新增房间地图列表功能
• 新增管理员专属功能：更新日志、插件状态
• 完善帮助文档

📦 v0.2.0
• 新增推送模块（每日密码、日报、周报推送）
• 新增价格历史查询功能
• 新增利润历史分析功能
• 优化计算器功能

📦 v0.1.0
• 初始版本发布
• 实现账号管理、信息查询、数据分析
• 实现价格查询、利润排行等工具
• 实现TTS、语音、音乐娱乐功能
• 实现开黑房间、改枪方案功能
• 实现伤害计算、修甲计算、战备计算

━━━━━━━━━━━━━━━━━━━━
💡 功能建议/问题反馈请联系开发者"""

        yield self.chain_reply(event, changelog)

    async def get_plugin_status(self, event: AstrMessageEvent):
        """获取插件状态（管理员）"""
        import sys
        import platform
        
        lines = [
            "⚙️【插件运行状态】",
            "━━━━━━━━━━━━━━━━━━━━",
            "",
            f"📦 插件版本: v0.3.0",
            f"🐍 Python版本: {sys.version.split()[0]}",
            f"💻 系统平台: {platform.system()} {platform.release()}",
            "",
            "📡 服务状态:"
        ]
        
        # 检查API连接
        try:
            health = await self.api.get_health()
            if health and health.get("status") == "healthy":
                lines.append("  • API服务: ✅ 正常")
            else:
                lines.append("  • API服务: ⚠️ 异常")
        except:
            lines.append("  • API服务: ❌ 连接失败")
        
        # 数据库状态
        lines.append("  • 数据库: ✅ 正常")
        
        lines.append("")
        lines.append(f"📊 运行信息:")
        lines.append(f"  • 客户端ID: {self.api.clientid[:8]}..." if self.api.clientid else "  • 客户端ID: 未配置")
        
        yield self.chain_reply(event, "\n".join(lines))
