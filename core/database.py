import mysql.connector
from mysql.connector import Error
from config.settings import settings
from loguru import logger
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = mysql.connector.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_DATABASE,
            user=settings.DB_USERNAME,
            password=settings.DB_PASSWORD,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            autocommit=False  # Kita manual commit
        )
        yield conn
    except Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()