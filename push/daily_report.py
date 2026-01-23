"""
日报自动推送
对应 JS: apps/push/DailyPush.js
默认 cron: 0 10 * * * (每天10点)
"""
import asyncio
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, TYPE_CHECKING
from urllib.parse import unquote

from astrbot.api import logger
from astrbot.core.message.components import Plain, Image
from astrbot.core.message.message_event_result import MessageChain

if TYPE_CHECKING:
    from astrbot.api.star import Context
    from ..df_api import DeltaForceAPI
    from ..df_sqlite import DeltaForceSQLiteManager

from ..utils.render import Render


class DailyReportPush:
    """日报自动推送"""
    
    JOB_ID = "delta_force_daily_report"
    DEFAULT_CRON = "0 10 * * *"  # 每天10点
    
    def __init__(self, context: "Context", api: "DeltaForceAPI", 
                 db: "DeltaForceSQLiteManager", config: Dict[str, Any]):
        self.context = context
        self.api = api
        self.db = db
        self.config = config
    
    @property
    def enabled(self) -> bool:
        return self.config.get("push_daily_report_enabled", False)
    
    @property
    def cron(self) -> str:
        return self.config.get("push_daily_report_cron", self.DEFAULT_CRON)
    
    def reload_config(self, config: Dict[str, Any]):
        """重新加载配置"""
        self.config = config
    
    def _decode_user_info(self, s: str) -> str:
        """解码用户信息"""
        try:
            return unquote(s or "")
        except:
            return s or ""
    
    def _format_number(self, num) -> str:
        """格式化数字"""
        if num is None:
            return "0"
        try:
            return f"{int(num):,}"
        except:
            return str(num)
    
    async def execute(self):
        """执行日报推送"""
        if not self.enabled:
            return
        
        logger.info("[三角洲] 开始执行日报推送...")
        
        try:
            # 获取订阅了日报推送的用户
            subscribed_users = self._get_subscribed_users()
            
            if not subscribed_users:
                logger.info("[三角洲] 没有用户订阅日报推送")
                return
            
            for platform_id, user_config in subscribed_users.items():
                await self._push_user_daily_report(platform_id, user_config)
                await asyncio.sleep(2)  # 避免请求过快
            
            logger.info(f"[三角洲] 日报推送完成，共处理 {len(subscribed_users)} 个用户")
            
        except Exception as e:
            logger.error(f"[三角洲] 日报推送异常: {e}")
    
    def _get_subscribed_users(self) -> Dict[str, Dict]:
        """获取订阅了日报推送的用户"""
        users = {}
        for key, value in self._push_config.items():
            # 用户ID是数字字符串
            if key.isdigit() and isinstance(value, dict):
                if value.get("enabled") and value.get("push_to", {}).get("group"):
                    users[key] = value
        return users
    
    async def _push_user_daily_report(self, platform_id: str, user_config: Dict):
        """为单个用户推送日报"""
        try:
            # 获取用户 token
            token = await self.db.get_active_token(platform_id)
            if not token:
                logger.warn(f"[日报推送] 用户 {platform_id} 未绑定token，跳过")
                return
            
            # 获取昨天的日期
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_str = yesterday.strftime("%Y%m%d")
            
            # 获取日报数据
            result = await self.api.get_daily_record(token, "", yesterday_str)
            
            if not result.get("success") or not result.get("data"):
                logger.warn(f"[日报推送] 用户 {platform_id} 获取日报失败: {result.get('msg', '未知错误')}")
                return
            
            data = result.get("data", {})
            sol_data = data.get("sol", {}).get("data", {}).get("data", {}).get("solDetail")
            mp_data = data.get("mp", {}).get("data", {}).get("data", {}).get("mpDetail")
            
            if not sol_data and not mp_data:
                logger.info(f"[日报推送] 用户 {platform_id} 无日报数据，跳过")
                return
            
            # 获取用户昵称
            user_name = user_config.get("nickname", platform_id)
            try:
                info_result = await self.api.get_personal_info(token)
                if info_result.get("data"):
                    user_data = info_result["data"].get("userData", {})
                    role_info = info_result.get("roleInfo", {})
                    name = self._decode_user_info(user_data.get("charac_name") or role_info.get("charac_name"))
                    if name:
                        user_name = name
            except:
                pass
            
            # 构建消息（优先图片，回退文本）
            image_bytes = await self._render_daily_report(user_name, sol_data, mp_data, yesterday)
            fallback_message = self._build_daily_report_message(user_name, sol_data, mp_data, yesterday)
            
            # 推送到群
            push_groups = user_config.get("push_to", {}).get("group", [])
            await self._push_to_groups(image_bytes, fallback_message, push_groups)
            
        except Exception as e:
            logger.error(f"[日报推送] 用户 {platform_id} 推送失败: {e}")
    
    def _build_daily_report_message(self, user_name: str, sol_data: Dict, 
                                     mp_data: Dict, date: datetime) -> str:
        """构建日报消息"""
        date_str = date.strftime("%Y-%m-%d")
        lines = [f"📊【{user_name} 的日报】", f"📅 {date_str}", ""]
        
        # 烽火地带数据
        if sol_data and sol_data.get("recentGainDate"):
            lines.append("🔥【烽火地带】")
            lines.append(f"  对局数: {sol_data.get('totalMatch', 0)}")
            lines.append(f"  撤离数: {sol_data.get('totalEscape', 0)}")
            lines.append(f"  击杀数: {sol_data.get('totalKill', 0)}")
            lines.append(f"  收益: {self._format_number(sol_data.get('totalGain', 0))}")
            
            # 最佳战绩
            best = sol_data.get("bestMatch")
            if best:
                lines.append(f"  🏆 最佳: 击杀{best.get('killNum', 0)} 收益{self._format_number(best.get('gain', 0))}")
            lines.append("")
        
        # 全面战场数据
        if mp_data and mp_data.get("recentDate"):
            lines.append("⚔️【全面战场】")
            lines.append(f"  对局数: {mp_data.get('totalFightNum', 0)}")
            lines.append(f"  胜场数: {mp_data.get('totalWinNum', 0)}")
            lines.append(f"  击杀数: {mp_data.get('totalKillNum', 0)}")
            lines.append(f"  积分: {self._format_number(mp_data.get('totalScore', 0))}")
            
            # 最佳战绩
            best = mp_data.get("bestMatch")
            if best:
                result = "胜利" if best.get("isWinner") else "失败"
                lines.append(f"  🏆 最佳: {result} 击杀{best.get('killNum', 0)} 积分{self._format_number(best.get('score', 0))}")
            lines.append("")
        
        if len(lines) <= 3:
            lines.append("暂无对局数据")
        
        return "\n".join(lines)
    
    async def _render_daily_report(self, user_name: str, sol_data: Dict, 
                                    mp_data: Dict, date: datetime) -> bytes:
        """渲染日报为图片"""
        try:
            date_str = date.strftime("%Y-%m-%d")
            
            render_data = {
                'backgroundImage': Render.get_background_image(),
                'userName': user_name,
                'dateStr': date_str,
                'reportType': 'daily',
                # 烽火地带数据
                'solData': {
                    'hasData': bool(sol_data and sol_data.get("recentGainDate")),
                    'totalMatch': sol_data.get('totalMatch', 0) if sol_data else 0,
                    'totalEscape': sol_data.get('totalEscape', 0) if sol_data else 0,
                    'totalKill': sol_data.get('totalKill', 0) if sol_data else 0,
                    'totalGain': self._format_number(sol_data.get('totalGain', 0)) if sol_data else '0',
                    'bestMatch': sol_data.get('bestMatch') if sol_data else None,
                } if sol_data else None,
                # 全面战场数据
                'mpData': {
                    'hasData': bool(mp_data and mp_data.get("recentDate")),
                    'totalFightNum': mp_data.get('totalFightNum', 0) if mp_data else 0,
                    'totalWinNum': mp_data.get('totalWinNum', 0) if mp_data else 0,
                    'totalKillNum': mp_data.get('totalKillNum', 0) if mp_data else 0,
                    'totalScore': self._format_number(mp_data.get('totalScore', 0)) if mp_data else '0',
                    'bestMatch': mp_data.get('bestMatch') if mp_data else None,
                } if mp_data else None,
            }
            
            return await Render.render_to_image(
                'dailyReport/dailyReport.html',
                render_data,
                width=800,
                height=600
            )
        except Exception as e:
            logger.error(f"[日报推送] 渲染图片失败: {e}")
            return None
    
    async def _push_to_groups(self, image_bytes: bytes, fallback_message: str, groups: List[str]):
        """推送到群"""
        # 优先使用图片，失败则使用文本
        if image_bytes:
            b64_image = base64.b64encode(image_bytes).decode('utf-8')
            chain = MessageChain([Image.fromBase64(b64_image)])
        else:
            chain = MessageChain([Plain(fallback_message)])
        
        for group_id in groups:
            try:
                umo = f"aiocqhttp:group:{group_id}"
                await self.context.send_message(session=umo, message_chain=chain)
                logger.debug(f"[三角洲] 推送日报到群 {group_id} 成功")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"[三角洲] 推送日报到群 {group_id} 失败: {e}")
    
    def toggle_user_push(self, platform_id: str, group_id: str, enable: bool, 
                         nickname: str = "") -> tuple[bool, str]:
        """
        开关用户的日报推送
        
        Args:
            platform_id: 用户平台ID
            group_id: 推送到的群ID
            enable: 开启或关闭
            nickname: 用户昵称(可选)
        
        Returns:
            (成功与否, 消息)
        """
        platform_id = str(platform_id)
        group_id = str(group_id)
        
        if "push_daily_report" not in self.config:
            self.config["push_daily_report"] = {
                "enabled": False,
                "cron": self.DEFAULT_CRON
            }
        
        push_config = self.config["push_daily_report"]
        
        if platform_id not in push_config:
            push_config[platform_id] = {
                "enabled": False,
                "nickname": nickname or platform_id,
                "push_to": {"group": []}
            }
        
        user_config = push_config[platform_id]
        groups = user_config.get("push_to", {}).get("group", [])
        groups = [str(g) for g in groups]
        
        if enable:
            if group_id in groups:
                return False, "已开启日报推送到此群"
            groups.append(group_id)
            user_config["enabled"] = True
            push_config["enabled"] = True  # 有人订阅就启用
            if nickname:
                user_config["nickname"] = nickname
            msg = "已开启日报推送"
        else:
            if group_id not in groups:
                return False, "尚未开启日报推送到此群"
            groups.remove(group_id)
            if not groups:
                user_config["enabled"] = False
            msg = "已关闭日报推送"
        
        user_config["push_to"] = {"group": groups}
        self._push_config = push_config
        
        return True, msg
