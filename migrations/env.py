from alembic import context
from sqlalchemy import create_engine
from core.database import Base
from core.config import settings

connectable = create_engine(settings.DATABASE_URL_SYNC)

def run_migrations_online():
    config = context.config
    target_metadata = Base.metadata

    with connectable.connect() as connection:
        with connection.begin():
            context.configure(connection=connection, target_metadata=target_metadata)
            context.run_migrations()
