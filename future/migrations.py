import argparse
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from star.database import Database
from star.models import Model



# Generated by Django 3.2.4 on 2021-09-10 13:59

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    # 0004_auto_20210910_1359.py
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("monitor", "0003_index"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditindicator",
            name="json_data",
            field=models.JSONField(null=True, verbose_name="Optional JSON data"),
        ),
        migrations.AlterField(
            model_name="auditindicator",
            name="bank",
            field=models.CharField(max_length=5, null=True),
        ),
        migrations.AlterField(
            model_name="auditindicator",
            name="vycode",
            field=models.CharField(max_length=10, null=True),
        ),
    ]





"""
# 000_migrations
CREATE TABLE schema_migrations (
    version VARCHAR(255) PRIMARY KEY
);

# 001_initial
from future.models import Model

async def upgrade(engine):
    # Assuming `Model.metadata` includes all your model's metadata
    # Use SQLAlchemy's `create_all` to create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)

async def downgrade(engine):
    # This will drop all tables; use with caution
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)


"""

# Function to initialize the database engine
def init_engine():
    db = Database(driver="mysql", host="10.0.0.69", port=3306, username="user", password="lol123", database="test", options="")
    return create_async_engine(db._build_engine_url(), echo=True)

# Migration actions
async def upgrade(engine, version):
    migration = __import__(f"migrations.{version}", fromlist=['upgrade'])
    await migration.upgrade(engine)
    async with engine.begin() as conn:
        await conn.execute("INSERT INTO schema_migrations (version) VALUES (:version)", {'version': version})

async def downgrade(engine, version):
    migration = __import__(f"migrations.{version}", fromlist=['downgrade'])
    await migration.downgrade(engine)
    async with engine.begin() as conn:
        await conn.execute("DELETE FROM schema_migrations WHERE version = :version", {'version': version})

async def create_all(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)

async def drop_all(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)

# Main function to handle CLI arguments
def main():
    parser = argparse.ArgumentParser(description="Manage database migrations")
    parser.add_argument("command", choices=["upgrade", "downgrade", "create", "drop"], help="Migration command to execute")
    parser.add_argument("version", nargs='?', help="Migration version to apply")
    args = parser.parse_args()

    engine = init_engine()

    if args.command == "create":
        asyncio.run(create_all(engine))
    elif args.command == "drop":
        asyncio.run(drop_all(engine))
    elif args.command == "upgrade":
        asyncio.run(upgrade(engine, args.version))
    elif args.command == "downgrade":
        asyncio.run(downgrade(engine, args.version))

if __name__ == "__main__":
    main()