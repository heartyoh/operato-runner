import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 기존 경로에 프로젝트 루트 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

# models 전체 import (모든 테이블 인식)
from src.models.base import Base
from src.models.user import User
from src.models.module import Module
from src.models.role import Role
from src.models.deployment import Deployment
from src.models.version import Version
from src.models.audit_log import AuditLog

from src.core.db import sync_engine

target_metadata = Base.metadata

# DB URL을 .env에서 읽어오도록 설정  
from dotenv import load_dotenv
load_dotenv(override=True)
import os
from alembic import context
config = context.config

def convert_to_sync_url(async_url):
    """비동기 URL을 동기 URL로 변환"""
    if not async_url:
        return 'sqlite:///./app.db'
    
    # 드라이버 매핑
    driver_mappings = {
        '+asyncpg': '+psycopg2',      # PostgreSQL
        '+aiosqlite': '',             # SQLite  
        '+aiomysql': '+pymysql',      # MySQL
        '+asyncmy': '+pymysql'        # MySQL alternative
    }
    
    sync_url = async_url
    for async_driver, sync_driver in driver_mappings.items():
        if async_driver in sync_url:
            sync_url = sync_url.replace(async_driver, sync_driver)
            break
    
    return sync_url

# DATABASE_URL을 동기 버전으로 변환
async_database_url = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///./app.db')
database_url = convert_to_sync_url(async_database_url)
config.set_main_option('sqlalchemy.url', database_url)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = sync_engine
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
