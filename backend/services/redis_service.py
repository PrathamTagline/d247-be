# backend/services/redis_service.py
import redis
import json
import os

# Connect to Redis (you can also use env variables for host/port/db)
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=True  # ensures returned values are strings
)

def set_data(key: str, value: dict, expire: int = 60):
    """
    Store dict as JSON in Redis
    """
    redis_client.set(key, json.dumps(value), ex=expire)


def get_data(key: str):
    """
    Get dict from Redis
    """
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None


def delete_data(key: str):
    """
    Delete key from Redis
    """
    redis_client.delete(key)
