# redis_service.py
import json
import redis
from django.conf import settings
from typing import Any, Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
    
    def set_data(self, key: str, data: Any, expire: int = None) -> bool:
        """
        Store data in Redis
        
        Args:
            key: Redis key
            data: Data to store (will be JSON serialized)
            expire: Expiration time in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Serialize data to JSON
            json_data = json.dumps(data, ensure_ascii=False)
            
            # Store in Redis
            result = self.redis_client.set(key, json_data)
            
            # Set expiration if provided
            if expire and result:
                self.redis_client.expire(key, expire)
            
            logger.info(f"Successfully stored data in Redis: {key}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error storing data in Redis key {key}: {e}")
            return False
    
    def get_data(self, key: str) -> Optional[Any]:
        """
        Retrieve data from Redis
        
        Args:
            key: Redis key
            
        Returns:
            Deserialized data or None if not found/error
        """
        try:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving data from Redis key {key}: {e}")
            return None
    
    def get_multiple_data(self, keys: List[str]) -> Dict[str, Any]:
        """
        Retrieve multiple keys from Redis efficiently
        
        Args:
            keys: List of Redis keys
            
        Returns:
            Dictionary with key-value pairs
        """
        try:
            if not keys:
                return {}
            
            # Use pipeline for efficiency
            pipeline = self.redis_client.pipeline()
            for key in keys:
                pipeline.get(key)
            
            results = pipeline.execute()
            
            data_dict = {}
            for i, key in enumerate(keys):
                if results[i]:
                    try:
                        data_dict[key] = json.loads(results[i])
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON data for key {key}")
                        data_dict[key] = None
                else:
                    data_dict[key] = None
            
            return data_dict
            
        except Exception as e:
            logger.error(f"Error retrieving multiple keys from Redis: {e}")
            return {}
    
    def delete_data(self, key: str) -> bool:
        """
        Delete data from Redis
        
        Args:
            key: Redis key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.redis_client.delete(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")
            return False
    
    def key_exists(self, key: str) -> bool:
        """
        Check if key exists in Redis
        
        Args:
            key: Redis key
            
        Returns:
            bool: True if exists, False otherwise
        """
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Error checking key existence {key}: {e}")
            return False
    
    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """
        Get keys matching a pattern
        
        Args:
            pattern: Redis key pattern (e.g., "odds:*")
            
        Returns:
            List of matching keys
        """
        try:
            return self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Error getting keys by pattern {pattern}: {e}")
            return []

# Create singleton instance
redis_service = RedisService()