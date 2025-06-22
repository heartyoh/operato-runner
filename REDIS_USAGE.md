# Redis 사용 가이드

이 문서는 Operato Runner에서 Redis를 사용하는 방법을 설명합니다.

## 📋 개요

Redis는 Operato Runner에서 다음과 같은 용도로 사용됩니다:

- **캐싱**: 자주 조회되는 데이터의 성능 향상
- **세션 관리**: 사용자 세션 정보 저장
- **실시간 통계**: 모듈 실행 통계 및 메트릭
- **임시 데이터**: 일시적인 데이터 저장

## 🚀 빠른 시작

### 1. Docker Compose로 Redis 시작

```bash
# 전체 서비스 시작 (Redis 포함)
docker-compose up -d

# Redis만 시작
docker-compose up -d redis
```

### 2. Redis 연결 확인

```bash
# Redis 컨테이너 상태 확인
docker-compose ps redis

# Redis CLI 접속
docker exec -it operato-redis redis-cli

# 헬스체크 API 호출
curl http://localhost:8000/api/health/redis
```

## 🔧 기본 사용법

### Redis 클라이언트 사용

```python
from utils.redis_client import redis_client

# 연결
await redis_client.connect()

# 기본 작업
await redis_client.set("key", "value", expire=3600)  # 1시간 만료
value = await redis_client.get("key")
exists = await redis_client.exists("key")
await redis_client.delete("key")

# 연결 해제
await redis_client.disconnect()
```

### 해시 작업

```python
# 해시 설정
await redis_client.hset("user:123", "name", "John")
await redis_client.hset("user:123", "email", "john@example.com")

# 해시 조회
name = await redis_client.hget("user:123", "name")
all_data = await redis_client.hgetall("user:123")
```

## 🎯 캐싱 패턴

### 1. 함수 결과 캐싱

```python
from utils.redis_client import cache_result

@cache_result(expire=300, key_prefix="modules")
async def get_module_info(module_name: str):
    # DB에서 모듈 정보 조회
    return {"name": module_name, "version": "1.0.0"}

# 사용
result = await get_module_info("spec-matching")
```

### 2. 캐시 무효화

```python
from utils.redis_client import invalidate_cache

@invalidate_cache("modules:*")
async def update_module(module_name: str, data: dict):
    # 모듈 업데이트 로직
    return {"status": "updated"}

# 사용
await update_module("spec-matching", {"version": "1.1.0"})
```

## 📊 세션 관리

### 사용자 세션 저장

```python
async def create_user_session(user_id: int, user_data: dict):
    session_key = f"session:{user_id}"
    session_data = {
        "user_id": user_id,
        "username": user_data["username"],
        "roles": user_data["roles"],
        "login_time": datetime.now().isoformat()
    }

    # 세션 저장 (1시간 만료)
    await redis_client.set(session_key, session_data, expire=3600)
    return session_key

async def get_user_session(user_id: int):
    session_key = f"session:{user_id}"
    return await redis_client.get(session_key)

async def extend_session(user_id: int, hours: int = 2):
    session_key = f"session:{user_id}"
    await redis_client.expire(session_key, hours * 3600)

async def delete_session(user_id: int):
    session_key = f"session:{user_id}"
    await redis_client.delete(session_key)
```

## 📈 실시간 통계

### 모듈 실행 통계

```python
async def increment_module_execution(module_name: str):
    """모듈 실행 횟수 증가"""
    key = f"stats:modules:{module_name}:executions"
    current = await redis_client.get(key) or "0"
    new_count = int(current) + 1
    await redis_client.set(key, str(new_count), expire=86400)  # 24시간
    return new_count

async def get_module_stats(module_name: str):
    """모듈 통계 조회"""
    stats = {}

    # 실행 횟수
    executions = await redis_client.get(f"stats:modules:{module_name}:executions") or "0"
    stats["executions"] = int(executions)

    # 평균 실행 시간
    avg_time = await redis_client.get(f"stats:modules:{module_name}:avg_time") or "0"
    stats["avg_execution_time"] = float(avg_time)

    return stats

async def record_execution_time(module_name: str, execution_time: float):
    """실행 시간 기록"""
    key = f"stats:modules:{module_name}:avg_time"
    current_avg = await redis_client.get(key) or "0"
    current_avg = float(current_avg)

    # 간단한 이동 평균 계산
    new_avg = (current_avg * 0.9) + (execution_time * 0.1)
    await redis_client.set(key, str(new_avg), expire=86400)
```

## 🔍 모니터링 및 디버깅

### Redis 상태 확인

```bash
# Redis 컨테이너 로그 확인
docker-compose logs redis

# Redis 메모리 사용량 확인
docker exec -it operato-redis redis-cli info memory

# Redis 키 개수 확인
docker exec -it operato-redis redis-cli dbsize

# 특정 패턴의 키 조회
docker exec -it operato-redis redis-cli keys "modules:*"
```

### API 헬스체크

```bash
# Redis 연결 상태 확인
curl http://localhost:8000/api/health/redis

# 전체 서비스 상태 확인
curl http://localhost:8000/api/health
```

## 🛠️ 고급 사용법

### 1. 배치 작업

```python
async def batch_cache_operations():
    """배치 캐싱 작업"""
    operations = []

    # 여러 모듈 정보를 한 번에 캐싱
    modules = ["spec-matching", "data-processor", "ml-pipeline"]
    for module in modules:
        operations.append(
            redis_client.set(f"module:{module}", {"name": module, "status": "active"})
        )

    # 병렬로 실행
    await asyncio.gather(*operations)
```

### 2. 조건부 캐싱

```python
async def get_cached_or_fetch(key: str, fetch_func, expire: int = 300):
    """캐시된 값이 있으면 반환, 없으면 함수 실행 후 캐싱"""
    cached = await redis_client.get(key)
    if cached is not None:
        return cached

    # 캐시 미스 - 함수 실행
    result = await fetch_func()
    await redis_client.set(key, result, expire)
    return result
```

### 3. 캐시 계층

```python
async def get_module_with_cache(module_name: str):
    """캐시 계층을 사용한 모듈 정보 조회"""

    # 1단계: 메모리 캐시 (Redis)
    cache_key = f"module:{module_name}"
    cached = await redis_client.get(cache_key)
    if cached:
        return cached

    # 2단계: 데이터베이스 조회
    from models.module import Module
    from sqlalchemy.future import select

    async with get_db() as db:
        result = await db.execute(
            select(Module).where(Module.name == module_name)
        )
        module = result.scalars().first()

        if module:
            module_data = {
                "name": module.name,
                "version": module.version,
                "status": "active" if module.is_active else "inactive"
            }

            # Redis에 캐싱 (5분)
            await redis_client.set(cache_key, module_data, expire=300)
            return module_data

    return None
```

## 🔒 보안 고려사항

### 1. 민감한 데이터 처리

```python
# 민감한 데이터는 암호화 후 저장
import hashlib

async def store_sensitive_data(key: str, data: dict):
    """민감한 데이터 암호화 저장"""
    # 실제로는 더 강력한 암호화 사용
    encrypted_data = hashlib.sha256(str(data).encode()).hexdigest()
    await redis_client.set(f"encrypted:{key}", encrypted_data, expire=1800)  # 30분
```

### 2. 접근 제어

```python
async def validate_session(session_id: str, required_roles: list):
    """세션 유효성 검증"""
    session = await redis_client.get(f"session:{session_id}")
    if not session:
        return False

    user_roles = session.get("roles", [])
    return any(role in user_roles for role in required_roles)
```

## 📚 예제 실행

### Redis 사용 예제 실행

```bash
# 예제 파일 실행
python examples/redis_usage.py
```

### 예제 결과

```
🚀 Redis 사용 예제 시작
=== 기본 Redis 작업 예제 ===
Redis 연결 상태: True
사용자 정보 캐시 저장
사용자 정보 조회: {'name': 'John', 'email': 'john@example.com'}
남은 시간: 3599초
키 존재 여부: True
키 삭제 완료

=== Redis 해시 작업 예제 ===
모듈 정보 해시 저장
모듈 버전: 1.0.0
모듈 상태: active
전체 모듈 정보: {'version': '1.0.0', 'status': 'active', 'last_updated': '2024-01-01'}
해시 삭제 완료

=== 캐싱 데코레이터 예제 ===
첫 번째 호출:
DB에서 모듈 정보 조회: spec-matching
결과: {'name': 'spec-matching', 'version': '1.0.0', 'status': 'active', 'description': 'spec-matching 모듈 정보'}

두 번째 호출 (캐시 히트):
결과: {'name': 'spec-matching', 'version': '1.0.0', 'status': 'active', 'description': 'spec-matching 모듈 정보'}

✅ Redis 사용 예제 완료
```

## 🐛 문제 해결

### 일반적인 문제들

1. **Redis 연결 실패**

   ```bash
   # Redis 컨테이너 상태 확인
   docker-compose ps redis

   # Redis 로그 확인
   docker-compose logs redis

   # 네트워크 연결 확인
   docker exec -it operato-backend ping redis
   ```

2. **메모리 부족**

   ```bash
   # Redis 메모리 사용량 확인
   docker exec -it operato-redis redis-cli info memory

   # 오래된 키 삭제
   docker exec -it operato-redis redis-cli --scan --pattern "*" | head -100 | xargs redis-cli del
   ```

3. **성능 문제**

   ```bash
   # Redis 성능 통계 확인
   docker exec -it operato-redis redis-cli info stats

   # 느린 쿼리 로그 확인
   docker exec -it operato-redis redis-cli slowlog get 10
   ```

## 📖 추가 자료

- [Redis 공식 문서](https://redis.io/documentation)
- [aioredis 문서](https://aioredis.readthedocs.io/)
- [Redis 데이터 타입](https://redis.io/topics/data-types)
- [Redis 명령어 참조](https://redis.io/commands)
