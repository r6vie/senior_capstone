import asyncio
from database import database_connection

async def main():
    async with database_connection() as db:
        print((await db.connections.delete_many({})).deleted_count, "requests deleted")
        print((await db.messages.delete_many({})).deleted_count, "messages deleted")
        print((await db.notifications.delete_many({})).deleted_count, "email records deleted")

asyncio.run(main())