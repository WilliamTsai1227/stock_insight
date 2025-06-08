import psycopg2
from psycopg2 import pool
import os
from dotenv import load_dotenv
import time
from contextlib import contextmanager

load_dotenv()

class PostgreSQLConnectionPool:
    _instance = None
    _pool = None
    _max_retries = 3
    _retry_delay = 1  # 秒

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PostgreSQLConnectionPool, cls).__new__(cls)
            cls._instance._initialize_pool()
        return cls._instance

    def _initialize_pool(self):
        if self._pool is None:
            try:
                self._pool = pool.SimpleConnectionPool(
                    minconn=5,  # 增加最小連接數
                    maxconn=50,  # 增加最大連接數
                    host=os.getenv('PostgreSQL_DB_HOST', 'localhost'),
                    database=os.getenv('PostgreSQL_DB_NAME', 'stock_insight'),
                    user=os.getenv('PostgreSQL_DB_USER'),
                    password=os.getenv('PostgreSQL_DB_PASSWORD'),
                    port=os.getenv('PostgreSQL_DB_PORT', '5432'),
                    connect_timeout=10  # 添加連接超時時間
                )
            except Exception as e:
                print(f"Error creating connection pool: {e}")
                raise

    @contextmanager
    def get_connection(self):
        """
        從連接池獲取一個連接，使用上下文管理器確保連接被正確釋放
        """
        conn = None
        retries = 0
        while retries < self._max_retries:
            try:
                if self._pool is None:
                    self._initialize_pool()
                conn = self._pool.getconn()
                try:
                    yield conn
                finally:
                    if conn is not None:
                        self.release_connection(conn)
                break
            except pool.PoolError as e:
                retries += 1
                if retries == self._max_retries:
                    raise Exception(f"Connection pool exhausted after {self._max_retries} retries: {str(e)}")
                time.sleep(self._retry_delay)

    def release_connection(self, conn):
        """
        釋放連接回連接池
        """
        if self._pool is not None:
            try:
                self._pool.putconn(conn)
            except Exception as e:
                print(f"Error releasing connection: {e}")

    def close_all(self):
        """
        關閉所有連接
        """
        if self._pool is not None:
            try:
                self._pool.closeall()
            except Exception as e:
                print(f"Error closing all connections: {e}")

# 創建一個全局的連接池實例
postgresql_pool = PostgreSQLConnectionPool() 