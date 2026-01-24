import aiosqlite, os, json
from pathlib import Path
from astrbot.api import logger
from typing import Dict, List, Any, Optional

class DeltaForceSQLiteManager:
    def __init__(self, db_path=None):
        if not db_path:
            # 使用推荐的数据存储路径
            self.data_dir = Path("data/plugin_data/astrbot_plugin_deltaforce")
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = self.data_dir / "users.db"
        else:
            self.db_path = Path(db_path)

    async def initialize_table(self):
        """初始化数据库表"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                # 1. 用户数据表 (按照推荐 schema: user_id, data, updated_at)
                # 使用 JSON blob 存储数据
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    data TEXT,
                    updated_at INTEGER
                )
                ''')
                
                # 兼容旧代码，不建议使用，这里保留是为了避免重写 place_push_subscriptions 和 broadcast_history
                # 如果完全迁移，应将这些表也迁移到 users 表的 data 字段中，但为了稳定性，暂且保留独立表
                
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
                logger.info(f"数据库初始化成功: {self.db_path}")
                return True
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            return False
    
    async def upsert_user(self, user: int, selection: int, token: str = None) -> bool:
        """
        异步插入或更新用户数据
        使用新的 users 表结构存储
        """
        try:
            user_id = str(user)
            import time
            current_time = int(time.time())
            
            # 读取旧数据（如果只是更新selection）
            # 由于 upsert_user 参数没有包含所有可能的 data 字段，我们需要先读取
            # 但这里我们主要存储 selection 和 token
            
            # 使用 upsert 语法
            data_dict = {"selection": selection}
            if token:
                data_dict["token"] = token
            
            async with aiosqlite.connect(self.db_path) as conn:
                # 先尝试读取现有数据，以合并而不是覆盖（如果未来有更多字段）
                cursor = await conn.execute("SELECT data FROM users WHERE user_id=?", (user_id,))
                row = await cursor.fetchone()
                
                existing_data = {}
                if row and row[0]:
                    try:
                        existing_data = json.loads(row[0])
                    except:
                        pass
                
                # 合并数据
                existing_data.update(data_dict)
                final_json = json.dumps(existing_data)
                
                await conn.execute("""
                INSERT INTO users (user_id, data, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    data=excluded.data,
                    updated_at=excluded.updated_at
                """, (user_id, final_json, current_time))
                
                await conn.commit()
                logger.info(f"用户 {user} 数据保存成功")
                return True
        except Exception as e:
            logger.error(f"数据库错误 (upsert_user): {e}")
            return False
    
    async def get_user(self, user: int) -> tuple:
        """
        异步查询用户数据
        从 data JSON 中提取 selection 和 token
        返回: (selection, token)
        """
        try:
            user_id = str(user)
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute(
                    "SELECT data FROM users WHERE user_id = ?",
                    (user_id,)
                )
                row = await cursor.fetchone()
                
                if row and row[0]:
                    try:
                        data = json.loads(row[0])
                        selection = data.get("selection", 0)
                        token = data.get("token")
                        return (selection, token)
                    except Exception as e:
                        logger.error(f"解析用户数据失败: {e}")
                        return None
                return None
        except Exception as e:
            logger.error(f"查询错误: {e}")
            return None

    async def delete_user(self, user: int) -> bool:
        """删除用户数据"""
        try:
            user_id = str(user)
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
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