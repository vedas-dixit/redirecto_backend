import os
from redis.asyncio import Redis
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
