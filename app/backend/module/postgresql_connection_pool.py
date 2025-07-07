import asyncpg
import os
from dotenv import load_dotenv
import asyncio # For asynchronous operations
from contextlib import asynccontextmanager

load_dotenv()

class AsyncPostgreSQLConnectionPool:
    _instance = None
    _pool = None

    def __new__(cls):
        # 實作單例模式，確保只有一個連線池實例
        if cls._instance is None:
            cls._instance = super(AsyncPostgreSQLConnectionPool, cls).__new__(cls)
        return cls._instance

    async def initialize_pool(self):
        # 惰性初始化連線池，確保只在第一次需要時建立
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    host=os.getenv('PostgreSQL_DB_HOST', 'localhost'),
                    database=os.getenv('PostgreSQL_DB_NAME', 'stock_insight'),
                    user=os.getenv('PostgreSQL_DB_USER'),
                    password=os.getenv('PostgreSQL_DB_PASSWORD'),
                    port=os.getenv('PostgreSQL_DB_PORT', '5432'),
                    min_size=5,  # 最小連線數
                    max_size=50, # 最大連線數
                    timeout=10,  # 獲取連線的超時時間（秒）
                    command_timeout=60 # 單一命令的超時時間（秒）
                )
            except Exception as e:
                print(f"Error creating async connection pool: {e}")
                raise
    @asynccontextmanager
    async def get_connection(self):
        """
        提供 async context manager 取得/釋放連線
        用法: async with postgresql_pool.connection() as conn:
        """
        if self._pool is None:
            await self.initialize_pool()
        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            await self._pool.release(conn)


    async def close_all(self):
        """
        異步關閉所有連接
        """
        if self._pool is not None:
            try:
                await self._pool.close()
            except Exception as e:
                print(f"Error closing all async connections: {e}")
            finally:
                self._pool = None # 清除池實例



# 創建一個全局的連線池實例 (但此時尚未初始化)
# 初始化會在第一次 get_connection() 時執行
postgresql_pool = AsyncPostgreSQLConnectionPool()