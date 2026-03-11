"""
系统处理器
包含：帮助、服务器状态、订阅管理等
"""
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp
from .base import BaseHandler
from .help_data import HELP_CFG, HELP_LIST
from ..utils.render import Render


class SystemHandler(BaseHandler):
    """系统处理器"""

    def _process_icon(self, icon_id):
        if not icon_id:
            return None
        try:
            val = int(icon_id)
            x = (val - 1) % 10
            y = (val - x - 1) // 10
            # Icon size 50px
            return f"background-position: -{x * 50}px -{y * 50}px;"
        except (ValueError, TypeError):
            return None

    def _process_groups(self, groups):
        processed = []
        for g in groups:
            new_group = g.copy()
            if "list" in new_group:
                new_list = []
                for item in new_group["list"]:
                    new_item = item.copy()
                    if "icon" in new_item:
                         css = self._process_icon(new_item["icon"])
                         if css:
                             new_item["css"] = css
                             new_item["icon"] = "" # Clear icon text if using sprite
                    new_list.append(new_item)
                new_group["list"] = new_list
            processed.append(new_group)
        return processed

    async def show_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        # Load config and list
        help_cfg = HELP_CFG.copy()
        help_list = HELP_LIST
        
        # Process groups
        top_full = []
        bottom_full = []
        
        if "fullWidth" in help_list:
            for group in help_list["fullWidth"]:
                if group.get("order", 0) < 50:
                    top_full.append(group)
                else:
                    bottom_full.append(group)

        top_groups = self._process_groups(top_full)
        bottom_groups = self._process_groups(bottom_full)
        left_groups = self._process_groups(help_list.get("left", []))
        right_groups = self._process_groups(help_list.get("right", []))

        # Background logic
        from pathlib import Path
        resources_path = Render.get_resources_dir()
        bg_path = resources_path / "help" / "imgs" / "default" / "bg.jpg"
        bg_uri = bg_path.as_uri()
        
        # Icon Sprite Logic
        icon_path = resources_path / "help" / "imgs" / "default" / "icon.png"
        icon_uri = icon_path.as_uri()

        style = f"""
        :root {{
            --bg-url: url('{bg_uri}');
            --container-bg-url: url('{bg_uri}');
            --icon-url: url('{icon_uri}');
            --primary-color: #ceb78b;
            --desc-color: #eee;
        }}
        body, .container {{
            background-color: #222 !important; 
        }}
        .cont-box {{
             background: rgba(255, 255, 255, 0.1) !important;
             backdrop-filter: blur(10px);
             -webkit-backdrop-filter: blur(10px);
        }}
        """
        
        render_data = {
            'helpCfg': help_cfg,
            'style': style,
            'bgType': ' default',
            'twoColumnLayout': True,
            'topFullWidthGroups': top_groups,
            'bottomFullWidthGroups': bottom_groups,
            'leftGroups': left_groups,
            'rightGroups': right_groups,
        }
        
        yield await self.render_and_reply(
            event,
            'help/index.html',
            render_data,
            fallback_text=self._build_help_text(),
            width=1000,
            height=4000
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

        sender_id = str(event.get_sender_id())
        self.logger.info(
            "战绩订阅身份上下文: sender_id=%s client_id=%s active_account_checked=%s",
            sender_id,
            self.api.clientid,
            bool(token),
        )
        result = await self.api.subscribe_record(
            platform_id=sender_id,
            client_id=self.api.clientid,
            subscription_type=subscription_type
        )

        if self.is_success(result):
            type_names = {"sol": "烽火地带", "mp": "全面战场", "both": "全部模式"}
            verify_result = await self.api.get_record_subscription(
                platform_id=sender_id,
                client_id=self.api.clientid
            )
            verify_data = verify_result.get("data", {}) if isinstance(verify_result, dict) else {}

            if self.is_success(verify_result) and verify_data and verify_data.get("enabled", False):
                confirmed_type = verify_data.get("subscriptionType", subscription_type)
                lines = [
                    "✅ 战绩订阅成功！",
                    f"订阅类型：{type_names.get(confirmed_type, confirmed_type)}",
                    "",
                    "战绩将在对局结束后自动推送",
                    "说明：当前插件按机器人用户维度发起订阅，切换游戏账号不会创建新的订阅记录",
                ]
                yield self.chain_reply(event, "\n".join(lines))
                return

            subscribe_meta = result.get("_requestMeta", {}) if isinstance(result, dict) else {}
            verify_meta = verify_result.get("_requestMeta", {}) if isinstance(verify_result, dict) else {}
            self.logger.warning(
                "战绩订阅回查未确认: sender_id=%s client_id=%s requested_type=%s subscribe_meta=%s verify_meta=%s verify_result=%s",
                sender_id,
                self.api.clientid,
                subscription_type,
                subscribe_meta,
                verify_meta,
                verify_result,
            )

            lines = [
                "⚠️ 订阅接口已返回成功，但暂时未确认订阅状态已经生效。",
                f"请求的订阅类型：{type_names.get(subscription_type, subscription_type)}",
                "",
                "请稍后再次发送 /三角洲订阅状态 确认。",
                "说明：当前插件按机器人用户维度发起订阅，切换游戏账号不会创建新的订阅记录。",
            ]
            if subscribe_meta.get("baseURL") and verify_meta.get("baseURL") and subscribe_meta.get("baseURL") != verify_meta.get("baseURL"):
                lines.append("提示：本次订阅与回查命中了不同后端节点，可能存在状态同步延迟。")
            yield self.chain_reply(event, "\n".join(lines))
        else:
            yield self.chain_reply(event, f"❌ 订阅失败：{self.get_error_msg(result)}")

    async def unsubscribe_record(self, event: AstrMessageEvent):
        """取消订阅战绩"""
        result = await self.api.unsubscribe_record(
            platform_id=str(event.get_sender_id()),
            client_id=self.api.clientid
        )

        if self.is_success(result):
            yield self.chain_reply(event, "✅ 已取消战绩订阅")
        else:
            yield self.chain_reply(event, f"❌ 取消订阅失败：{self.get_error_msg(result)}")

    async def get_subscription_status(self, event: AstrMessageEvent):
        """查询订阅状态"""
        result = await self.api.get_record_subscription(
            platform_id=str(event.get_sender_id()),
            client_id=self.api.clientid
        )

        if not self.is_success(result):
            yield self.chain_reply(event, f"❌ 查询失败：{self.get_error_msg(result)}")
            return

        data = result.get("data", {})
        if not data or not data.get("enabled", False):
            yield self.chain_reply(
                event,
                "📡 当前未订阅战绩推送\n\n使用 /三角洲 订阅战绩 开启订阅\n如果刚刚完成订阅却仍显示未订阅，可能是后端状态同步延迟，请稍后重试。"
            )
            return

        sub_type = data.get("subscriptionType", "both")
        type_names = {"sol": "烽火地带", "mp": "全面战场", "both": "全部模式"}
        
        lines = [
            "📡【战绩订阅状态】",
            f"状态：✅ 已订阅",
            f"类型：{type_names.get(sub_type, sub_type)}",
            "说明：当前插件按机器人用户维度发起订阅，切换游戏账号不会创建新的订阅记录"
        ]
        
        if data.get("createdAt"):
            lines.append(f"订阅时间：{data['createdAt']}")

        yield self.chain_reply(event, "\n".join(lines))

    async def get_changelog(self, event: AstrMessageEvent):
        """获取更新日志（管理员）"""
        changelog = """📝【三角洲插件更新日志】
━━━━━━━━━━━━━━━━━━━━

📦 v0.3.1 (当前版本)
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
            f"📦 插件版本: v0.3.1",
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
