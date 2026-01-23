"""
每日密码推送
对应 JS: apps/push/Task.js
默认 cron: 0 8 * * * (每天8点)
"""
import asyncio
from typing import Dict, List, Any, TYPE_CHECKING

from astrbot.api import logger
from astrbot.core.message.components import Plain
from astrbot.core.message.message_event_result import MessageChain

if TYPE_CHECKING:
    from astrbot.api.star import Context
    from ..df_api import DeltaForceAPI


class DailyKeywordPush:
    """每日密码推送"""
    
    JOB_ID = "delta_force_daily_keyword"
    DEFAULT_CRON = "0 8 * * *"  # 每天8点
    
    def __init__(self, context: "Context", api: "DeltaForceAPI", config: Dict[str, Any]):
        self.context = context
        self.api = api
        self.config = config
    
    @property
    def enabled(self) -> bool:
        return self.config.get("push_daily_keyword_enabled", False)
    
    @property
    def cron(self) -> str:
        return self.config.get("push_daily_keyword_cron", self.DEFAULT_CRON)
    
    @property
    def push_groups(self) -> List[str]:
        groups_str = self.config.get("push_daily_keyword_groups", "")
        if not groups_str:
            return []
        return [g.strip() for g in groups_str.split(",") if g.strip()]
    
    @property
    def push_privates(self) -> List[str]:
        # 私聊推送暂不支持，返回空列表
        return []
    
    def reload_config(self, config: Dict[str, Any]):
        """重新加载配置"""
        self.config = config
    
    async def execute(self):
        """执行每日密码推送"""
        # 重新读取配置检查是否启用
        if not self.enabled:
            return
        
        logger.info("[三角洲] 开始执行每日密码推送...")
        
        try:
            result = await self.api.get_daily_keyword()
            
            if not result.get("success") and result.get("code") != 0:
                logger.error(f"[三角洲] 获取每日密码失败: {result.get('msg', '未知错误')}")
                return
            
            data = result.get("data", {})
            keyword_list = data.get("list", [])
            
            if not keyword_list:
                logger.info("[三角洲] 今日暂无每日密码数据")
                return
            
            # 构建消息
            lines = ["📋【每日密码】"]
            for item in keyword_list:
                map_name = item.get("mapName", "未知地图")
                secret = item.get("secret", "未知")
                if secret and str(secret).isdigit():
                    secret = str(secret).zfill(4)
                lines.append(f"📍【{map_name}】: {secret}")
            
            message = "\n".join(lines)
            
            # 推送到群
            await self._push_to_targets(message)
            
            logger.info(f"[三角洲] 每日密码推送完成，共 {len(keyword_list)} 条")
            
        except Exception as e:
            logger.error(f"[三角洲] 每日密码推送异常: {e}")
    
    async def _push_to_targets(self, message: str):
        """推送消息到目标"""
        chain = MessageChain([Plain(message)])
        
        # 推送到群
        for group_id in self.push_groups:
            try:
                # 构建 unified_msg_origin 格式
                # AstrBot 的 UMO 格式通常是 "platform_name:group:group_id" 或类似格式
                # 这里需要根据实际配置的平台来构建
                umo = f"aiocqhttp:group:{group_id}"
                await self.context.send_message(session=umo, message_chain=chain)
                logger.debug(f"[三角洲] 推送每日密码到群 {group_id} 成功")
                await asyncio.sleep(1)  # 避免发送过快
            except Exception as e:
                logger.error(f"[三角洲] 推送每日密码到群 {group_id} 失败: {e}")
        
        # 推送到私聊
        for user_id in self.push_privates:
            try:
                umo = f"aiocqhttp:private:{user_id}"
                await self.context.send_message(session=umo, message_chain=chain)
                logger.debug(f"[三角洲] 推送每日密码到用户 {user_id} 成功")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"[三角洲] 推送每日密码到用户 {user_id} 失败: {e}")
    
    def toggle_group(self, group_id: str, enable: bool) -> tuple[bool, str]:
        """
        开关群推送
        
        Returns:
            (成功与否, 消息)
        """
        group_id = str(group_id)
        
        # 获取当前群列表
        groups = self.push_groups.copy()
        
        if enable:
            if group_id in groups:
                return False, "本群已开启每日密码推送"
            groups.append(group_id)
            # 更新配置
            self.config["push_daily_keyword_groups"] = ",".join(groups)
            self.config["push_daily_keyword_enabled"] = True  # 有群订阅就启用
            msg = "已开启本群每日密码推送"
        else:
            if group_id not in groups:
                return False, "本群尚未开启每日密码推送"
            groups.remove(group_id)
            # 更新配置
            self.config["push_daily_keyword_groups"] = ",".join(groups)
            msg = "已关闭本群每日密码推送"
        
        return True, msg
