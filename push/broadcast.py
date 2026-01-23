"""
广播通知系统
对应 JS: apps/push/Notification.js
管理员向指定群组发送广播消息

实现思路：
1. 仅限管理员使用
2. 支持向多个群发送消息
3. 记录广播历史
"""
import asyncio
from typing import Dict, List, Any, TYPE_CHECKING

from astrbot.api import logger
from astrbot.core.message.components import Plain
from astrbot.core.message.message_event_result import MessageChain

if TYPE_CHECKING:
    from astrbot.api.star import Context
    from ..df_sqlite import DeltaForceSQLiteManager


class BroadcastSystem:
    """广播通知系统"""
    
    def __init__(
        self, 
        context: "Context", 
        db_manager: "DeltaForceSQLiteManager",
        config: Dict[str, Any]
    ):
        self.context = context
        self.db_manager = db_manager
        self.config = config
    
    def reload_config(self, config: Dict[str, Any]):
        """重新加载配置"""
        self.config = config
    
    @property
    def admin_users(self) -> List[str]:
        """获取管理员用户列表"""
        admin_str = self.config.get("broadcast_admin_users", "")
        if not admin_str:
            return []
        return [u.strip() for u in admin_str.split(",") if u.strip()]
    
    @property
    def default_targets(self) -> List[Dict[str, str]]:
        """获取默认广播目标"""
        targets_str = self.config.get("broadcast_default_targets", "")
        if not targets_str:
            return []
        # 解析格式: group_id1,group_id2 -> [{"type": "group", "id": "xxx"}]
        return [{"type": "group", "id": t.strip()} for t in targets_str.split(",") if t.strip()]
    
    def is_admin(self, user_id: str) -> bool:
        """检查用户是否为管理员"""
        return str(user_id) in [str(u) for u in self.admin_users]
    
    async def broadcast(
        self,
        sender_id: str,
        message: str,
        targets: List[Dict[str, str]] = None,
        delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        发送广播消息
        
        Args:
            sender_id: 发送者ID
            message: 广播内容
            targets: 目标列表 [{"type": "group", "id": "xxx", "platform": "aiocqhttp"}]
            delay: 发送间隔（秒）
        
        Returns:
            {"success": bool, "success_count": int, "fail_count": int, "details": list}
        """
        if not self.is_admin(sender_id):
            return {
                "success": False,
                "message": "❌ 您没有广播权限",
                "success_count": 0,
                "fail_count": 0
            }
        
        if not message:
            return {
                "success": False,
                "message": "❌ 广播内容不能为空",
                "success_count": 0,
                "fail_count": 0
            }
        
        # 使用指定目标或默认目标
        broadcast_targets = targets or self.default_targets
        
        if not broadcast_targets:
            return {
                "success": False,
                "message": "❌ 未配置广播目标",
                "success_count": 0,
                "fail_count": 0
            }
        
        success_count = 0
        fail_count = 0
        details = []
        
        # 构建消息链
        chain = MessageChain([
            Plain(f"📢 系统通知\n\n{message}")
        ])
        
        for target in broadcast_targets:
            target_type = target.get("type", "group")
            target_id = target.get("id")
            platform = target.get("platform", "aiocqhttp")
            
            if not target_id:
                fail_count += 1
                details.append({"target": target, "success": False, "error": "目标ID为空"})
                continue
            
            try:
                # 构建 unified_msg_origin
                umo = f"{platform}:{target_type}:{target_id}"
                
                await self.context.send_message(session=umo, message_chain=chain)
                
                success_count += 1
                details.append({"target": target_id, "success": True})
                logger.info(f"[三角洲] 广播发送成功: {target_id}")
                
            except Exception as e:
                fail_count += 1
                details.append({"target": target_id, "success": False, "error": str(e)})
                logger.error(f"[三角洲] 广播发送失败 {target_id}: {e}")
            
            # 发送间隔，避免风控
            if delay > 0:
                await asyncio.sleep(delay)
        
        # 保存广播历史
        target_ids = [t.get("id", "") for t in broadcast_targets]
        await self.db_manager.save_broadcast_history(
            sender_id=sender_id,
            message=message,
            targets=target_ids,
            success_count=success_count,
            fail_count=fail_count
        )
        
        return {
            "success": success_count > 0,
            "message": f"✅ 广播完成\n成功: {success_count} 个\n失败: {fail_count} 个",
            "success_count": success_count,
            "fail_count": fail_count,
            "details": details
        }
    
    async def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取广播历史"""
        return await self.db_manager.get_broadcast_history(limit)
    
    async def broadcast_to_single(
        self,
        sender_id: str,
        message: str,
        target_type: str,
        target_id: str,
        platform: str = "aiocqhttp"
    ) -> Dict[str, Any]:
        """
        向单个目标发送广播
        
        Args:
            sender_id: 发送者ID
            message: 广播内容
            target_type: 目标类型 (group/private)
            target_id: 目标ID
            platform: 平台
        
        Returns:
            结果字典
        """
        target = {
            "type": target_type,
            "id": target_id,
            "platform": platform
        }
        return await self.broadcast(
            sender_id=sender_id,
            message=message,
            targets=[target],
            delay=0
        )
