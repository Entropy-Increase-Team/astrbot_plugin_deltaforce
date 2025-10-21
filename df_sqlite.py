import aiosqlite, os
from astrbot.api import logger

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
                await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_data (
                    user INTEGER PRIMARY KEY NOT NULL,
                    selection INTEGER NOT NULL,
                    token TEXT(36)
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