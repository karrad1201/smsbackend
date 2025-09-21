from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import re

from src.infrastructure.database.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def replace_env_vars(url):

    def replace_match(match):
        var_name = match.group(1)
        return os.getenv(var_name, '')

    return re.sub(r'\$\{([^}]+)\}', replace_match, url)


target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    url = replace_env_vars(url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    if 'sqlalchemy.url' in configuration:
        configuration['sqlalchemy.url'] = replace_env_vars(configuration['sqlalchemy.url'])

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()