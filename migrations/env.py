"""Запуск миграций Alembic. Адрес БД — из DATABASE_URL, как и у приложения."""
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLAlchemy 2.1 по умолчанию берёт для postgresql:// драйвер psycopg (v3),
# поэтому явно указываем psycopg2 — тот же драйвер, что у приложения
DATABASE_URL = os.environ["DATABASE_URL"].replace(
    "postgresql://", "postgresql+psycopg2://", 1)


def run_migrations_offline():
    """alembic upgrade head --sql: только вывести SQL, без подключения к БД."""
    context.configure(url=DATABASE_URL, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Обычный режим: изменения схемы выполняются в одной транзакции."""
    engine = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, transactional_ddl=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
