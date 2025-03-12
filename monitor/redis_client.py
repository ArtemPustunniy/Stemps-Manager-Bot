import aioredis


async def get_redis_client():
    return await aioredis.create_redis_pool("redis://localhost")