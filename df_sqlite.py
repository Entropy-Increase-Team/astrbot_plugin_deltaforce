import aiosqlite, os, json
from astrbot.api import logger
from typing import Dict, List, Any, Optional

class DeltaForceSQLiteManager:
    def __init__(self, db_path=None):
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        if not db_path:
            self.db_path = os.path.join(self.plugin_dir, 'df.db')
        else:
            self.db_path = db_path

    async def initialize_table(self):
        """初始化数据库表"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                # 用户数据表
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_data (
                    user INTEGER PRIMARY KEY NOT NULL,
                    selection INTEGER NOT NULL,
                    token TEXT(36)
                )
                ''')
                
                # 特勤处推送订阅表
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS place_push_subscriptions (
                    user_id TEXT PRIMARY KEY NOT NULL,
                    token TEXT NOT NULL,
                    push_targets TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
                ''')
                
                # 广播消息历史表
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS broadcast_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    targets TEXT NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    created_at INTEGER NOT NULL
                )
                ''')
                
                await conn.commit()
                logger.info("数据库表初始化成功")
                return True
        except Exception as e:
            logger.error(f"数据库表初始化失败: {e}")
            return False
    
    async def upsert_user(self, user: int, selection: int, token: str = None) -> bool:
        """异步插入或更新用户数据"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                if token:
                    await conn.execute(
                        "INSERT OR REPLACE INTO user_data (user, selection, token) VALUES (?, ?, ?)",
                        (user, selection, token)
                    )
                else:
                    await conn.execute(
                        "INSERT OR REPLACE INTO user_data (user, selection) VALUES (?, ?)",
                        (user, selection)
                    )
                await conn.commit()
                logger.info(f"用户 {user} 数据保存成功")
                return True
        except Exception as e:
            logger.error(f"数据库错误: {e}")
            return False
    
    async def get_user(self, user: int) -> tuple:
        """异步查询用户数据"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute(
                    "SELECT selection, token FROM user_data WHERE user = ?",
                    (user,)
                )
                result = await cursor.fetchone()
                return result
        except Exception as e:
            logger.error(f"查询错误: {e}")
            return None

    async def delete_user(self, user: int) -> bool:
        """删除用户数据"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("DELETE FROM user_data WHERE user = ?", (user,))
                await conn.commit()
                logger.info(f"用户 {user} 数据删除成功")
                return True
        except Exception as e:
            logger.error(f"删除错误: {e}")
            return False

    # ==================== 特勤处推送订阅 ====================
    
    async def add_place_push_subscription(
        self, 
        user_id: str, 
        token: str, 
        push_target: Dict[str, str]
    ) -> bool:
        """添加或更新特勤处推送订阅"""
        try:
            import time
            current_time = int(time.time())
            
            async with aiosqlite.connect(self.db_path) as conn:
                # 检查是否已存在
                cursor = await conn.execute(
                    "SELECT push_targets FROM place_push_subscriptions WHERE user_id = ?",
                    (user_id,)
                )
                result = await cursor.fetchone()
                
                if result:
                    # 更新现有订阅
                    existing_targets = json.loads(result[0])
                    
                    # 检查目标是否已存在
                    target_exists = any(
                        t.get("type") == push_target.get("type") and 
                        t.get("id") == push_target.get("id")
                        for t in existing_targets
                    )
                    
                    if not target_exists:
                        existing_targets.append(push_target)
                    
                    await conn.execute(
                        """UPDATE place_push_subscriptions 
                           SET token = ?, push_targets = ?, updated_at = ?
                           WHERE user_id = ?""",
                        (token, json.dumps(existing_targets), current_time, user_id)
                    )
                else:
                    # 创建新订阅
                    await conn.execute(
                        """INSERT INTO place_push_subscriptions 
                           (user_id, token, push_targets, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (user_id, token, json.dumps([push_target]), current_time, current_time)
                    )
                
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"添加特勤处推送订阅失败: {e}")
            return False
    
    async def remove_place_push_subscription(
        self, 
        user_id: str, 
        target_type: str = None, 
        target_id: str = None
    ) -> bool:
        """移除特勤处推送订阅"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                if target_type and target_id:
                    # 移除特定目标
                    cursor = await conn.execute(
                        "SELECT push_targets FROM place_push_subscriptions WHERE user_id = ?",
                        (user_id,)
                    )
                    result = await cursor.fetchone()
                    
                    if not result:
                        return False
                    
                    existing_targets = json.loads(result[0])
                    updated_targets = [
                        t for t in existing_targets 
                        if not (t.get("type") == target_type and t.get("id") == target_id)
                    ]
                    
                    if len(updated_targets) == 0:
                        # 如果没有剩余目标，删除整条记录
                        await conn.execute(
                            "DELETE FROM place_push_subscriptions WHERE user_id = ?",
                            (user_id,)
                        )
                    else:
                        import time
                        await conn.execute(
                            """UPDATE place_push_subscriptions 
                               SET push_targets = ?, updated_at = ?
                               WHERE user_id = ?""",
                            (json.dumps(updated_targets), int(time.time()), user_id)
                        )
                else:
                    # 移除所有订阅
                    await conn.execute(
                        "DELETE FROM place_push_subscriptions WHERE user_id = ?",
                        (user_id,)
                    )
                
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"移除特勤处推送订阅失败: {e}")
            return False
    
    async def get_place_push_subscriptions(self) -> List[Dict[str, Any]]:
        """获取所有特勤处推送订阅"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute(
                    "SELECT user_id, token, push_targets FROM place_push_subscriptions"
                )
                results = await cursor.fetchall()
                
                return [
                    {
                        "user_id": row[0],
                        "token": row[1],
                        "push_targets": json.loads(row[2])
                    }
                    for row in results
                ]
        except Exception as e:
            logger.error(f"获取特勤处推送订阅失败: {e}")
            return []
    
    async def get_user_place_push_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户的特勤处推送订阅"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute(
                    "SELECT user_id, token, push_targets FROM place_push_subscriptions WHERE user_id = ?",
                    (user_id,)
                )
                result = await cursor.fetchone()
                
                if result:
                    return {
                        "user_id": result[0],
                        "token": result[1],
                        "push_targets": json.loads(result[2])
                    }
                return None
        except Exception as e:
            logger.error(f"获取用户特勤处推送订阅失败: {e}")
            return None

    # ==================== 广播历史 ====================
    
    async def save_broadcast_history(
        self, 
        sender_id: str, 
        message: str, 
        targets: List[str],
        success_count: int = 0,
        fail_count: int = 0
    ) -> bool:
        """保存广播历史"""
        try:
            import time
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute(
                    """INSERT INTO broadcast_history 
                       (sender_id, message, targets, success_count, fail_count, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (sender_id, message, json.dumps(targets), success_count, fail_count, int(time.time()))
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"保存广播历史失败: {e}")
            return False
    
    async def get_broadcast_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取广播历史"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute(
                    """SELECT id, sender_id, message, targets, success_count, fail_count, created_at 
                       FROM broadcast_history 
                       ORDER BY created_at DESC 
                       LIMIT ?""",
                    (limit,)
                )
                results = await cursor.fetchall()
                
                return [
                    {
                        "id": row[0],
                        "sender_id": row[1],
                        "message": row[2],
                        "targets": json.loads(row[3]),
                        "success_count": row[4],
                        "fail_count": row[5],
                        "created_at": row[6]
                    }
                    for row in results
                ]
        except Exception as e:
            logger.error(f"获取广播历史失败: {e}")
            return []