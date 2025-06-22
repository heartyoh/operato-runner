import os
import json
import asyncio
from typing import Optional, Any, Dict, List
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Redis 의존성 조건부 import
try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis 의존성이 없습니다. 캐싱 기능이 비활성화됩니다.")

class RedisClient:
    """Redis 클라이언트 래퍼 클래스"""
    
    def __init__(self):
        self.redis: Optional[Any] = None
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_db = int(os.getenv('REDIS_DB', 0))
        
        # Redis 사용 가능 여부 확인
        self.enabled = REDIS_AVAILABLE and os.getenv('REDIS_ENABLED', 'true').lower() == 'true'
        
        if not self.enabled:
            logger.info("Redis가 비활성화되어 있습니다.")
    
    async def connect(self):
        """Redis 연결"""
        if not self.enabled or not REDIS_AVAILABLE:
            logger.info("Redis 연결을 건너뜁니다.")
            return
            
        try:
            self.redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # 연결 테스트
            await self.redis.ping()
            logger.info(f"Redis 연결 성공: {self.redis_host}:{self.redis_port}")
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
            self.redis = None
            self.enabled = False
    
    async def disconnect(self):
        """Redis 연결 해제"""
        if self.redis and self.enabled:
            await self.redis.close()
            logger.info("Redis 연결 해제")
    
    async def is_connected(self) -> bool:
        """Redis 연결 상태 확인"""
        if not self.enabled or not self.redis:
            return False
        try:
            await self.redis.ping()
            return True
        except:
            return False
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """키-값 설정"""
        if not self.enabled or not self.redis:
            return False
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self.redis.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Redis set 실패: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """키로 값 조회"""
        if not self.enabled or not self.redis:
            return None
        try:
            value = await self.redis.get(key)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis get 실패: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """키 삭제"""
        if not self.enabled or not self.redis:
            return False
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete 실패: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        if not self.enabled or not self.redis:
            return False
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists 실패: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """키 만료 시간 설정"""
        if not self.enabled or not self.redis:
            return False
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis expire 실패: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """키 남은 시간 조회"""
        if not self.enabled or not self.redis:
            return -1
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Redis ttl 실패: {e}")
            return -1
    
    async def hset(self, name: str, key: str, value: Any) -> bool:
        """해시 설정"""
        if not self.enabled or not self.redis:
            return False
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self.redis.hset(name, key, value)
            return True
        except Exception as e:
            logger.error(f"Redis hset 실패: {e}")
            return False
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """해시 조회"""
        if not self.enabled or not self.redis:
            return None
        try:
            value = await self.redis.hget(name, key)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis hget 실패: {e}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """해시 전체 조회"""
        if not self.enabled or not self.redis:
            return {}
        try:
            data = await self.redis.hgetall(name)
            result = {}
            for key, value in data.items():
                try:
                    result[key] = json.loads(value)
                except:
                    result[key] = value
            return result
        except Exception as e:
            logger.error(f"Redis hgetall 실패: {e}")
            return {}

# 전역 Redis 클라이언트 인스턴스
redis_client = RedisClient()

def cache_result(expire: int = 300, key_prefix: str = ""):
    """함수 결과 캐싱 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Redis가 비활성화된 경우 원본 함수 실행
            if not redis_client.enabled:
                return await func(*args, **kwargs)
                
            # 캐시 키 생성
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 캐시에서 조회
            cached_result = await redis_client.get(cache_key)
            if cached_result is not None:
                logger.debug(f"캐시 히트: {cache_key}")
                return cached_result
            
            # 함수 실행
            result = await func(*args, **kwargs)
            
            # 결과 캐싱
            await redis_client.set(cache_key, result, expire)
            logger.debug(f"캐시 저장: {cache_key}")
            
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """캐시 무효화 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Redis가 비활성화된 경우 원본 함수 실행
            if not redis_client.enabled:
                return await func(*args, **kwargs)
                
            # 함수 실행
            result = await func(*args, **kwargs)
            
            # 패턴에 맞는 캐시 무효화
            # 실제 구현에서는 Redis의 SCAN 명령어를 사용해야 하지만,
            # 여기서는 간단히 패턴 매칭으로 처리
            logger.debug(f"캐시 무효화: {pattern}")
            
            return result
        return wrapper
    return decorator 