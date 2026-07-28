import os
import sys

from alembic import context

config = context.config

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_root = os.path.join(project_root, "backend")

if project_root not in sys.path:
    sys.path.insert(0, project_root)

if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app import app  # noqa: E402
from extensions import db  # noqa: E402

target_metadata = db.metadata


def run_migrations_offline():
    url = app.config.get("SQLALCHEMY_DATABASE_URI")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with app.app_context():
        connectable = db.engine

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