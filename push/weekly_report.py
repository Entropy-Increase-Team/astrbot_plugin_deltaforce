"""
周报自动推送
对应 JS: apps/push/WeeklyPush.js
默认 cron: 0 10 * * 1 (每周一10点)
"""
import asyncio
import base64
from datetime import datetime
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


class WeeklyReportPush:
    """周报自动推送"""
    
    JOB_ID = "delta_force_weekly_report"
    DEFAULT_CRON = "0 10 * * 1"  # 每周一10点
    
    def __init__(self, context: "Context", api: "DeltaForceAPI", 
                 db: "DeltaForceSQLiteManager", config: Dict[str, Any]):
        self.context = context
        self.api = api
        self.db = db
        self.config = config
    
    @property
    def enabled(self) -> bool:
        return self.config.get("push_weekly_report_enabled", False)
    
    @property
    def cron(self) -> str:
        return self.config.get("push_weekly_report_cron", self.DEFAULT_CRON)
    
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
    
    def _format_duration(self, seconds) -> str:
        """格式化时长"""
        if not seconds:
            return "0分钟"
        try:
            seconds = int(seconds)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if hours > 0:
                return f"{hours}小时{minutes}分钟"
            return f"{minutes}分钟"
        except:
            return "0分钟"
    
    async def execute(self):
        """执行周报推送"""
        if not self.enabled:
            return
        
        logger.info("[三角洲] 开始执行周报推送...")
        
        try:
            # 获取订阅了周报推送的用户
            subscribed_users = self._get_subscribed_users()
            
            if not subscribed_users:
                logger.info("[三角洲] 没有用户订阅周报推送")
                return
            
            for platform_id, user_config in subscribed_users.items():
                await self._push_user_weekly_report(platform_id, user_config)
                await asyncio.sleep(2)
            
            logger.info(f"[三角洲] 周报推送完成，共处理 {len(subscribed_users)} 个用户")
            
        except Exception as e:
            logger.error(f"[三角洲] 周报推送异常: {e}")
    
    def _get_subscribed_users(self) -> Dict[str, Dict]:
        """获取订阅了周报推送的用户"""
        users = {}
        for key, value in self._push_config.items():
            if key.isdigit() and isinstance(value, dict):
                if value.get("enabled") and value.get("push_to", {}).get("group"):
                    users[key] = value
        return users
    
    async def _push_user_weekly_report(self, platform_id: str, user_config: Dict):
        """为单个用户推送周报"""
        try:
            # 获取用户 token
            token = await self.db.get_active_token(platform_id)
            if not token:
                logger.warn(f"[周报推送] 用户 {platform_id} 未绑定token，跳过")
                return
            
            # 获取周报数据
            result = await self.api.get_weekly_record(token, "", True)
            
            if not result.get("success") or not result.get("data"):
                logger.warn(f"[周报推送] 用户 {platform_id} 获取周报失败: {result.get('msg', '未知错误')}")
                return
            
            data = result.get("data", {})
            sol_data = data.get("sol", {}).get("data", {}).get("data")
            mp_data = data.get("mp", {}).get("data", {}).get("data")
            
            if not sol_data and not mp_data:
                logger.info(f"[周报推送] 用户 {platform_id} 无周报数据，跳过")
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
            image_bytes = await self._render_weekly_report(user_name, sol_data, mp_data)
            fallback_message = self._build_weekly_report_message(user_name, sol_data, mp_data)
            
            # 推送到群
            push_groups = user_config.get("push_to", {}).get("group", [])
            await self._push_to_groups(image_bytes, fallback_message, push_groups)
            
        except Exception as e:
            logger.error(f"[周报推送] 用户 {platform_id} 推送失败: {e}")
    
    def _build_weekly_report_message(self, user_name: str, sol_data: Dict, 
                                      mp_data: Dict) -> str:
        """构建周报消息"""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        
        lines = [f"📊【{user_name} 的周报】", f"📅 截至 {date_str}", ""]
        
        # 烽火地带数据
        if sol_data:
            lines.append("🔥【烽火地带】")
            lines.append(f"  总对局: {sol_data.get('total_loginnum', 0)}")
            lines.append(f"  总撤离: {sol_data.get('total_escapenum', 0)}")
            lines.append(f"  总击杀: {sol_data.get('total_killnum', 0)}")
            lines.append(f"  总收益: {self._format_number(sol_data.get('total_Gain', 0))}")
            lines.append(f"  游戏时长: {self._format_duration(sol_data.get('total_time', 0))}")
            
            # 撤离率
            total_games = int(sol_data.get('total_loginnum', 0) or 0)
            total_escape = int(sol_data.get('total_escapenum', 0) or 0)
            if total_games > 0:
                escape_rate = (total_escape / total_games) * 100
                lines.append(f"  撤离率: {escape_rate:.1f}%")
            
            # 队友信息
            teammates = sol_data.get("teammates", [])
            if teammates:
                lines.append(f"  本周队友: {len(teammates)}人")
            lines.append("")
        
        # 全面战场数据
        if mp_data:
            lines.append("⚔️【全面战场】")
            lines.append(f"  总对局: {mp_data.get('total_inum', 0)}")
            lines.append(f"  总胜场: {mp_data.get('total_win_inum', 0)}")
            lines.append(f"  总击杀: {mp_data.get('total_killnum', 0)}")
            lines.append(f"  总死亡: {mp_data.get('total_deathnum', 0)}")
            lines.append(f"  总助攻: {mp_data.get('total_assistnum', 0)}")
            lines.append(f"  总积分: {self._format_number(mp_data.get('total_scorenum', 0))}")
            lines.append(f"  游戏时长: {self._format_duration(mp_data.get('total_time', 0))}")
            
            # 胜率和KD
            total_games = int(mp_data.get('total_inum', 0) or 0)
            total_wins = int(mp_data.get('total_win_inum', 0) or 0)
            total_kills = int(mp_data.get('total_killnum', 0) or 0)
            total_deaths = int(mp_data.get('total_deathnum', 0) or 0)
            
            if total_games > 0:
                win_rate = (total_wins / total_games) * 100
                lines.append(f"  胜率: {win_rate:.1f}%")
            
            if total_deaths > 0:
                kd = total_kills / total_deaths
                lines.append(f"  KD: {kd:.2f}")
            
            # 队友信息
            teammates = mp_data.get("teammates", [])
            if teammates:
                lines.append(f"  本周队友: {len(teammates)}人")
            lines.append("")
        
        if len(lines) <= 3:
            lines.append("暂无对局数据")
        
        return "\n".join(lines)
    
    async def _render_weekly_report(self, user_name: str, sol_data: Dict, 
                                     mp_data: Dict) -> bytes:
        """渲染周报为图片"""
        try:
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            
            render_data = {
                'backgroundImage': Render.get_background_image(),
                'userName': user_name,
                'dateStr': date_str,
                'reportType': 'weekly',
                # 烽火地带数据
                'solData': {
                    'hasData': bool(sol_data),
                    'totalLoginNum': sol_data.get('total_loginnum', 0) if sol_data else 0,
                    'totalEscapeNum': sol_data.get('total_escapenum', 0) if sol_data else 0,
                    'totalKillNum': sol_data.get('total_killnum', 0) if sol_data else 0,
                    'totalGain': self._format_number(sol_data.get('total_Gain', 0)) if sol_data else '0',
                    'totalTime': self._format_duration(sol_data.get('total_time', 0)) if sol_data else '0分钟',
                    'teammates': sol_data.get('teammates', []) if sol_data else [],
                } if sol_data else None,
                # 全面战场数据
                'mpData': {
                    'hasData': bool(mp_data),
                    'totalINum': mp_data.get('total_inum', 0) if mp_data else 0,
                    'totalWinINum': mp_data.get('total_win_inum', 0) if mp_data else 0,
                    'totalKillNum': mp_data.get('total_killnum', 0) if mp_data else 0,
                    'totalDeathNum': mp_data.get('total_deathnum', 0) if mp_data else 0,
                    'totalAssistNum': mp_data.get('total_assistnum', 0) if mp_data else 0,
                    'totalScoreNum': self._format_number(mp_data.get('total_scorenum', 0)) if mp_data else '0',
                    'totalTime': self._format_duration(mp_data.get('total_time', 0)) if mp_data else '0分钟',
                    'teammates': mp_data.get('teammates', []) if mp_data else [],
                } if mp_data else None,
            }
            
            return await Render.render_to_image(
                'weeklyReport/weeklyReport.html',
                render_data,
                width=2000,
                height=3000
            )
        except Exception as e:
            logger.error(f"[周报推送] 渲染图片失败: {e}")
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
                logger.debug(f"[三角洲] 推送周报到群 {group_id} 成功")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"[三角洲] 推送周报到群 {group_id} 失败: {e}")
    
    def toggle_user_push(self, platform_id: str, group_id: str, enable: bool, 
                         nickname: str = "") -> tuple[bool, str]:
        """
        开关用户的周报推送
        """
        platform_id = str(platform_id)
        group_id = str(group_id)
        
        if "push_weekly_report" not in self.config:
            self.config["push_weekly_report"] = {
                "enabled": False,
                "cron": self.DEFAULT_CRON
            }
        
        push_config = self.config["push_weekly_report"]
        
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
                return False, "已开启周报推送到此群"
            groups.append(group_id)
            user_config["enabled"] = True
            push_config["enabled"] = True
            if nickname:
                user_config["nickname"] = nickname
            msg = "已开启周报推送"
        else:
            if group_id not in groups:
                return False, "尚未开启周报推送到此群"
            groups.remove(group_id)
            if not groups:
                user_config["enabled"] = False
            msg = "已关闭周报推送"
        
        user_config["push_to"] = {"group": groups}
        self._push_config = push_config
        
        return True, msg
