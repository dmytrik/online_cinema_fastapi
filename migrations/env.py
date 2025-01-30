from core import engine, Base

connectable = engine

def run_migrations_online():
    from alembic import context
    config = context.config
    target_metadata = Base.metadata

    async def run():
        async with connectable.connect() as connection:
            async with connection.begin():
                context.run_migrations()

    run()
