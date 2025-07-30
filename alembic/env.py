# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Импортируем модели
from database.models import Base
from database.config import setting

# this is the Alembic Config object
config = context.config

# Интерпретируем конфигурационный файл, если он есть
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Устанавливаем target_metadata
target_metadata = Base.metadata

# ВАЖНО: Используем синхронный драйвер для Alembic
db_url = setting.get_db_url().replace('mysql+aiomysql://', 'mysql+pymysql://')
config.set_main_option('sqlalchemy.url', db_url)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
    # ВАЖНО: Используем синхронный engine для Alembic
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()