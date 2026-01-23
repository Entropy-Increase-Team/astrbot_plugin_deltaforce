"""
推送命令处理器
处理推送开关、状态查询等命令
"""
from typing import Dict, Any, TYPE_CHECKING

from astrbot.api.event import AstrMessageEvent
from .base import BaseHandler

if TYPE_CHECKING:
    from ..push import PushScheduler, DailyKeywordPush, DailyReportPush, WeeklyReportPush


class PushHandler(BaseHandler):
    """推送命令处理器"""
    
    def __init__(self, api, db_manager, scheduler: "PushScheduler" = None,
                 daily_keyword: "DailyKeywordPush" = None,
                 daily_report: "DailyReportPush" = None,
                 weekly_report: "WeeklyReportPush" = None,
                 config: Dict[str, Any] = None):
        super().__init__(api, db_manager)
        self.scheduler = scheduler
        self.daily_keyword = daily_keyword
        self.daily_report = daily_report
        self.weekly_report = weekly_report
        self.config = config or {}
    
    def _save_config(self):
        """保存配置"""
        if hasattr(self.config, 'save_config'):
            self.config.save_config()
    
    def _is_group_message(self, event: AstrMessageEvent) -> bool:
        """判断是否是群消息"""
        umo = event.unified_msg_origin or ""
        return "group" in umo.lower()
    
    def _get_platform_id(self, event: AstrMessageEvent) -> int:
        """获取平台用户ID"""
        return event.get_sender_id()
    
    def _get_nickname(self, event: AstrMessageEvent) -> str:
        """获取用户昵称"""
        try:
            return event.get_sender_name() or ""
        except:
            return ""
    
    async def toggle_daily_keyword(self, event: AstrMessageEvent, enable: bool):
        """开关每日密码推送（群维度）"""
        if not self._is_group_message(event):
            yield self.chain_reply(event, "该指令只能在群聊中使用")
            return
        
        # 检查管理员权限
        if not await self._is_group_admin(event):
            yield self.chain_reply(event, "抱歉，只有群管理员才能操作哦~")
            return
        
        if not self.daily_keyword:
            yield self.chain_reply(event, "推送功能未初始化")
            return
        
        group_id = self._get_group_id(event)
        success, msg = self.daily_keyword.toggle_group(group_id, enable)
        
        if success:
            self._save_config()
            # 更新调度任务
            if self.scheduler and enable:
                self.scheduler.add_job(
                    self.daily_keyword.JOB_ID,
                    self.daily_keyword.execute,
                    self.daily_keyword.cron
                )
        
        yield self.chain_reply(event, msg)
    
    async def toggle_daily_report(self, event: AstrMessageEvent, enable: bool):
        """开关日报推送（用户维度）"""
        if not self._is_group_message(event):
            yield self.chain_reply(event, "该指令只能在群聊中使用")
            return
        
        if not self.daily_report:
            yield self.chain_reply(event, "推送功能未初始化")
            return
        
        # 获取用户token检查是否已绑定
        platform_id = self._get_platform_id(event)
        token, error = await self.get_active_token(event)
        if not token:
            yield self.chain_reply(event, error or "您尚未绑定账号，请先使用 /三角洲登录 进行绑定")
            return
        
        group_id = self._get_group_id(event)
        nickname = self._get_nickname(event)
        
        success, msg = self.daily_report.toggle_user_push(platform_id, group_id, enable, nickname)
        
        if success:
            self._save_config()
            if self.scheduler and enable:
                self.scheduler.add_job(
                    self.daily_report.JOB_ID,
                    self.daily_report.execute,
                    self.daily_report.cron
                )
        
        yield self.chain_reply(event, msg)
    
    async def toggle_weekly_report(self, event: AstrMessageEvent, enable: bool):
        """开关周报推送（用户维度）"""
        if not self._is_group_message(event):
            yield self.chain_reply(event, "该指令只能在群聊中使用")
            return
        
        if not self.weekly_report:
            yield self.chain_reply(event, "推送功能未初始化")
            return
        
        # 获取用户token检查是否已绑定
        platform_id = self._get_platform_id(event)
        token, error = await self.get_active_token(event)
        if not token:
            yield self.chain_reply(event, error or "您尚未绑定账号，请先使用 /三角洲登录 进行绑定")
            return
        
        group_id = self._get_group_id(event)
        nickname = self._get_nickname(event)
        
        success, msg = self.weekly_report.toggle_user_push(platform_id, group_id, enable, nickname)
        
        if success:
            self._save_config()
            if self.scheduler and enable:
                self.scheduler.add_job(
                    self.weekly_report.JOB_ID,
                    self.weekly_report.execute,
                    self.weekly_report.cron
                )
        
        yield self.chain_reply(event, msg)
    
    async def get_push_status(self, event: AstrMessageEvent):
        """查询推送状态"""
        lines = ["📋【推送状态】", ""]
        
        # 调度器状态
        if self.scheduler:
            status = "运行中" if self.scheduler.is_running else "已停止"
            lines.append(f"🔄 调度器: {status}")
            lines.append("")
            
            # 各任务状态
            jobs = self.scheduler.get_job_status()
            if jobs:
                lines.append("📌 定时任务:")
                for job in jobs:
                    lines.append(f"  • {job['name']}")
                    lines.append(f"    下次执行: {job['next_run']}")
            else:
                lines.append("📌 暂无定时任务")
        else:
            lines.append("⚠️ 推送调度器未初始化")
        
        lines.append("")
        
        # 每日密码推送状态
        if self.daily_keyword:
            status = "✅ 已启用" if self.daily_keyword.enabled else "❌ 未启用"
            lines.append(f"📅 每日密码推送: {status}")
            if self.daily_keyword.push_groups:
                lines.append(f"   推送群: {len(self.daily_keyword.push_groups)}个")
        
        # 日报推送状态
        if self.daily_report:
            status = "✅ 已启用" if self.daily_report.enabled else "❌ 未启用"
            lines.append(f"📊 日报推送: {status}")
        
        # 周报推送状态
        if self.weekly_report:
            status = "✅ 已启用" if self.weekly_report.enabled else "❌ 未启用"
            lines.append(f"📈 周报推送: {status}")
        
        yield self.chain_reply(event, "\n".join(lines))
    
    async def _is_group_admin(self, event: AstrMessageEvent) -> bool:
        """检查是否是群管理员"""
        # 简化实现：检查 AstrBot 的权限系统
        try:
            # 检查是否是 master（通过 role 属性或其他方式）
            if hasattr(event, 'role') and event.role in ['admin', 'owner']:
                return True
            # 尝试检查 sender 的角色
            if hasattr(event, 'sender') and hasattr(event.sender, 'role'):
                return event.sender.role in ['admin', 'owner']
            # 默认允许（宽松模式）
            return True
        except:
            return True
    
    def _get_group_id(self, event: AstrMessageEvent) -> str:
        """获取群ID"""
        try:
            # 从 unified_msg_origin 解析
            umo = event.unified_msg_origin or ""
            if "group:" in umo:
                return umo.split("group:")[-1].split(":")[0]
            # 尝试从 message_obj 获取
            if hasattr(event, 'message_obj') and hasattr(event.message_obj, 'group_id'):
                return str(event.message_obj.group_id)
        except:
            pass
        return ""
