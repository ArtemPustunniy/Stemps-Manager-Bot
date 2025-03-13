import asyncio
from .redis_client import get_redis_client
from .checker import check_for_updates


async def main():
    print("📡 Запуск мониторинга Google Таблиц всех менеджеров...")
    redis_client = await get_redis_client()

    while True:
        await check_for_updates(redis_client)
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())