"""
特勤处制造完成推送
对应 JS: apps/push/PlaceTask.js
使用定时轮询检查制造状态，完成后推送通知

实现思路（参考早柚核心适配器）：
1. 使用 asyncio.create_task 启动后台轮询任务
2. 使用 context.send_message 主动推送消息
3. 使用数据库存储订阅信息和任务状态
"""
import asyncio
import time
from typing import Dict, List, Any, Optional, TYPE_CHECKING

from astrbot.api import logger
from astrbot.core.message.components import Plain, At
from astrbot.core.message.message_event_result import MessageChain

if TYPE_CHECKING:
    from astrbot.api.star import Context
    from ..df_api import DeltaForceAPI
    from ..df_sqlite import DeltaForceSQLiteManager


class PlaceTaskPush:
    """特勤处制造完成推送"""
    
    JOB_ID = "delta_force_place_task"
    POLL_INTERVAL = 60  # 轮询间隔（秒）
    SCHEDULE_INTERVAL = 300  # 调度间隔（秒）
    
    def __init__(
        self, 
        context: "Context", 
        api: "DeltaForceAPI", 
        db_manager: "DeltaForceSQLiteManager",
        config: Dict[str, Any]
    ):
        self.context = context
        self.api = api
        self.db_manager = db_manager
        self.config = config
        
        # 存储待推送的任务 {user_id: {place_id: {finish_time, object_name, push_targets}}}
        self.scheduled_tasks: Dict[str, Dict[str, Dict]] = {}
        
        # 已通知过期的用户，避免重复通知
        self.notified_expired: set = set()
        
        # 后台任务
        self._poll_task: Optional[asyncio.Task] = None
        self._push_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    @property
    def enabled(self) -> bool:
        return self.config.get("push_place_task_enabled", True)
    
    def reload_config(self, config: Dict[str, Any]):
        """重新加载配置"""
        self.config = config
    
    async def start(self):
        """启动后台任务"""
        if self._is_running:
            return
        
        self._is_running = True
        
        # 启动轮询调度任务
        self._poll_task = asyncio.create_task(self._poll_and_schedule_loop())
        
        # 启动推送检查任务
        self._push_task = asyncio.create_task(self._check_and_push_loop())
        
        logger.info("[三角洲] 特勤处推送后台任务已启动")
    
    async def stop(self):
        """停止后台任务"""
        self._is_running = False
        
        if self._poll_task:
            self._poll_task.cancel()
        if self._push_task:
            self._push_task.cancel()
        
        logger.info("[三角洲] 特勤处推送后台任务已停止")
    
    async def _poll_and_schedule_loop(self):
        """低频轮询调度器 - 从API同步状态并调度任务"""
        while self._is_running:
            try:
                if self.enabled:
                    await self._poll_and_schedule()
            except Exception as e:
                logger.error(f"[三角洲] 特勤处调度器异常: {e}")
            
            await asyncio.sleep(self.SCHEDULE_INTERVAL)
    
    async def _check_and_push_loop(self):
        """高频推送器 - 检查到期任务并推送"""
        while self._is_running:
            try:
                if self.enabled:
                    await self._check_and_push()
            except Exception as e:
                logger.error(f"[三角洲] 特勤处推送器异常: {e}")
            
            await asyncio.sleep(10)  # 每10秒检查一次
    
    async def _poll_and_schedule(self):
        """从API同步状态并调度任务"""
        # 获取所有启用推送的用户
        subscriptions = await self.db_manager.get_place_push_subscriptions()
        
        for sub in subscriptions:
            user_id = sub.get("user_id")
            token = sub.get("token")
            push_targets = sub.get("push_targets", [])
            
            if not token or not push_targets:
                continue
            
            try:
                result = await self.api.get_place_status(token)
                
                # API 返回格式: {code: 0, data: {...}} 或 {code: xxx, msg: "..."}
                if result.get("code") != 0:
                    # 检查是否为登录失效 (ret: 101)
                    data = result.get("data", {})
                    if isinstance(data, dict) and data.get("ret") == 101:
                        await self._handle_token_expired(user_id, push_targets)
                    continue
                
                # 清除过期通知标记
                self.notified_expired.discard(user_id)
                
                data = result.get("data", {})
                places = data.get("places", []) if isinstance(data, dict) else []
                
                if user_id not in self.scheduled_tasks:
                    self.scheduled_tasks[user_id] = {}
                
                current_tasks = set()
                
                for place in places:
                    place_id = place.get("id")
                    left_time = place.get("leftTime", 0)
                    object_detail = place.get("objectDetail", {})
                    
                    if not object_detail or left_time <= 0:
                        continue
                    
                    current_tasks.add(place_id)
                    finish_time = time.time() + left_time
                    
                    # 添加或更新任务
                    self.scheduled_tasks[user_id][place_id] = {
                        "finish_time": finish_time,
                        "object_name": object_detail.get("objectName", "未知物品"),
                        "push_targets": push_targets,
                        "user_id": user_id
                    }
                
                # 清理已不存在的任务
                for place_id in list(self.scheduled_tasks[user_id].keys()):
                    if place_id not in current_tasks:
                        del self.scheduled_tasks[user_id][place_id]
                
            except Exception as e:
                logger.error(f"[三角洲] 获取用户 {user_id} 特勤处状态失败: {e}")
            
            await asyncio.sleep(2)  # 避免请求过快
    
    async def _check_and_push(self):
        """检查到期任务并推送"""
        current_time = time.time()
        
        for user_id, tasks in list(self.scheduled_tasks.items()):
            for place_id, task in list(tasks.items()):
                if task["finish_time"] <= current_time:
                    # 任务完成，推送通知
                    await self._push_completion(
                        user_id=task["user_id"],
                        object_name=task["object_name"],
                        push_targets=task["push_targets"]
                    )
                    
                    # 删除已推送的任务
                    del self.scheduled_tasks[user_id][place_id]
    
    async def _push_completion(self, user_id: str, object_name: str, push_targets: List[Dict]):
        """推送制造完成通知"""
        message = f"您的 {object_name} 已在特勤处生产完成！"
        
        for target in push_targets:
            target_type = target.get("type", "group")
            target_id = target.get("id")
            platform = target.get("platform", "aiocqhttp")
            
            if not target_id:
                continue
            
            try:
                # 构建消息链（带At）
                chain = MessageChain([
                    At(qq=user_id),
                    Plain(f" {message}")
                ])
                
                # 构建 unified_msg_origin
                umo = f"{platform}:{target_type}:{target_id}"
                
                await self.context.send_message(session=umo, message_chain=chain)
                logger.info(f"[三角洲] 特勤处推送成功: {user_id} -> {target_id}")
                
            except Exception as e:
                logger.error(f"[三角洲] 特勤处推送失败: {e}")
    
    async def _handle_token_expired(self, user_id: str, push_targets: List[Dict]):
        """处理token过期"""
        if user_id in self.notified_expired:
            return
        
        self.notified_expired.add(user_id)
        
        message = "您的三角洲行动登录已过期，特勤处推送功能已暂停。\n请使用 /三角洲 登录 重新登录以恢复推送功能。"
        
        for target in push_targets:
            target_type = target.get("type", "group")
            target_id = target.get("id")
            platform = target.get("platform", "aiocqhttp")
            
            if not target_id:
                continue
            
            try:
                chain = MessageChain([
                    At(qq=user_id),
                    Plain(f" {message}")
                ])
                
                umo = f"{platform}:{target_type}:{target_id}"
                await self.context.send_message(session=umo, message_chain=chain)
                
            except Exception as e:
                logger.error(f"[三角洲] 发送token过期通知失败: {e}")
    
    async def subscribe(self, user_id: str, token: str, target_type: str, target_id: str, platform: str = "aiocqhttp") -> tuple[bool, str]:
        """
        订阅特勤处推送
        
        Args:
            user_id: 用户ID
            token: 用户token
            target_type: 推送目标类型 (group/private)
            target_id: 推送目标ID
            platform: 平台类型
        
        Returns:
            (成功与否, 消息)
        """
        try:
            push_target = {
                "type": target_type,
                "id": target_id,
                "platform": platform
            }
            
            success = await self.db_manager.add_place_push_subscription(
                user_id=user_id,
                token=token,
                push_target=push_target
            )
            
            if success:
                # 启用推送
                self._push_config["enabled"] = True
                return True, "✅ 已开启特勤处制造完成推送\n制造完成后将在本群通知您"
            else:
                return False, "订阅失败，请稍后重试"
                
        except Exception as e:
            logger.error(f"[三角洲] 订阅特勤处推送失败: {e}")
            return False, f"订阅失败: {e}"
    
    async def unsubscribe(self, user_id: str, target_type: str, target_id: str) -> tuple[bool, str]:
        """
        取消订阅特勤处推送
        
        Args:
            user_id: 用户ID
            target_type: 推送目标类型
            target_id: 推送目标ID
        
        Returns:
            (成功与否, 消息)
        """
        try:
            success = await self.db_manager.remove_place_push_subscription(
                user_id=user_id,
                target_type=target_type,
                target_id=target_id
            )
            
            if success:
                # 清理内存中的任务
                if user_id in self.scheduled_tasks:
                    del self.scheduled_tasks[user_id]
                return True, "✅ 已关闭特勤处制造完成推送"
            else:
                return False, "您尚未开启特勤处推送"
                
        except Exception as e:
            logger.error(f"[三角洲] 取消订阅特勤处推送失败: {e}")
            return False, f"取消订阅失败: {e}"
