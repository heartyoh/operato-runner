"""
Redis 사용 예제

이 파일은 Operato Runner에서 Redis를 사용하는 다양한 방법을 보여줍니다.
"""

import asyncio
from utils.redis_client import redis_client, cache_result, invalidate_cache

# 1. 기본 Redis 작업 예제
async def basic_redis_example():
    """기본 Redis 작업 예제"""
    print("=== 기본 Redis 작업 예제 ===")
    
    # 연결 확인
    is_connected = await redis_client.is_connected()
    print(f"Redis 연결 상태: {is_connected}")
    
    if not is_connected:
        print("Redis에 연결할 수 없습니다.")
        return
    
    # 키-값 설정
    await redis_client.set("user:1", {"name": "John", "email": "john@example.com"}, expire=3600)
    print("사용자 정보 캐시 저장")
    
    # 값 조회
    user_data = await redis_client.get("user:1")
    print(f"사용자 정보 조회: {user_data}")
    
    # 만료 시간 확인
    ttl = await redis_client.ttl("user:1")
    print(f"남은 시간: {ttl}초")
    
    # 키 존재 확인
    exists = await redis_client.exists("user:1")
    print(f"키 존재 여부: {exists}")
    
    # 키 삭제
    await redis_client.delete("user:1")
    print("키 삭제 완료")

# 2. 해시 작업 예제
async def hash_redis_example():
    """Redis 해시 작업 예제"""
    print("\n=== Redis 해시 작업 예제 ===")
    
    # 해시 설정
    await redis_client.hset("module:spec-matching", "version", "1.0.0")
    await redis_client.hset("module:spec-matching", "status", "active")
    await redis_client.hset("module:spec-matching", "last_updated", "2024-01-01")
    print("모듈 정보 해시 저장")
    
    # 개별 해시 값 조회
    version = await redis_client.hget("module:spec-matching", "version")
    status = await redis_client.hget("module:spec-matching", "status")
    print(f"모듈 버전: {version}")
    print(f"모듈 상태: {status}")
    
    # 전체 해시 조회
    module_info = await redis_client.hgetall("module:spec-matching")
    print(f"전체 모듈 정보: {module_info}")
    
    # 해시 삭제
    await redis_client.delete("module:spec-matching")
    print("해시 삭제 완료")

# 3. 캐싱 데코레이터 예제
@cache_result(expire=300, key_prefix="modules")
async def get_module_info(module_name: str):
    """모듈 정보를 가져오는 함수 (캐싱 적용)"""
    # 실제로는 DB에서 조회하는 로직
    print(f"DB에서 모듈 정보 조회: {module_name}")
    await asyncio.sleep(1)  # DB 조회 시뮬레이션
    return {
        "name": module_name,
        "version": "1.0.0",
        "status": "active",
        "description": f"{module_name} 모듈 정보"
    }

@invalidate_cache("modules:*")
async def update_module_info(module_name: str, new_info: dict):
    """모듈 정보 업데이트 (캐시 무효화)"""
    print(f"모듈 정보 업데이트: {module_name}")
    # 실제로는 DB 업데이트 로직
    await asyncio.sleep(0.5)
    return {"status": "updated"}

async def caching_example():
    """캐싱 데코레이터 사용 예제"""
    print("\n=== 캐싱 데코레이터 예제 ===")
    
    # 첫 번째 호출 (캐시 미스)
    print("첫 번째 호출:")
    result1 = await get_module_info("spec-matching")
    print(f"결과: {result1}")
    
    # 두 번째 호출 (캐시 히트)
    print("\n두 번째 호출 (캐시 히트):")
    result2 = await get_module_info("spec-matching")
    print(f"결과: {result2}")
    
    # 모듈 정보 업데이트 (캐시 무효화)
    print("\n모듈 정보 업데이트:")
    await update_module_info("spec-matching", {"version": "1.1.0"})
    
    # 세 번째 호출 (캐시 무효화 후 다시 DB 조회)
    print("\n세 번째 호출 (캐시 무효화 후):")
    result3 = await get_module_info("spec-matching")
    print(f"결과: {result3}")

# 4. 세션 관리 예제
async def session_management_example():
    """세션 관리 예제"""
    print("\n=== 세션 관리 예제 ===")
    
    # 사용자 세션 저장
    session_data = {
        "user_id": 123,
        "username": "admin",
        "roles": ["admin", "user"],
        "login_time": "2024-01-01T10:00:00Z"
    }
    
    session_key = f"session:{session_data['user_id']}"
    await redis_client.set(session_key, session_data, expire=3600)
    print(f"사용자 세션 저장: {session_key}")
    
    # 세션 조회
    retrieved_session = await redis_client.get(session_key)
    print(f"세션 조회: {retrieved_session}")
    
    # 세션 만료 시간 연장
    await redis_client.expire(session_key, 7200)  # 2시간으로 연장
    ttl = await redis_client.ttl(session_key)
    print(f"세션 만료 시간 연장: {ttl}초")
    
    # 세션 삭제 (로그아웃)
    await redis_client.delete(session_key)
    print("세션 삭제 (로그아웃)")

# 5. 실시간 통계 예제
async def realtime_stats_example():
    """실시간 통계 예제"""
    print("\n=== 실시간 통계 예제 ===")
    
    # 모듈 실행 횟수 증가
    await redis_client.hset("stats:modules", "spec-matching", "0")
    
    for i in range(5):
        # 실행 횟수 증가
        current_count = await redis_client.hget("stats:modules", "spec-matching")
        new_count = int(current_count or 0) + 1
        await redis_client.hset("stats:modules", "spec-matching", str(new_count))
        print(f"모듈 실행 횟수: {new_count}")
        await asyncio.sleep(0.1)
    
    # 전체 통계 조회
    stats = await redis_client.hgetall("stats:modules")
    print(f"전체 모듈 통계: {stats}")
    
    # 통계 초기화
    await redis_client.delete("stats:modules")
    print("통계 초기화")

async def main():
    """메인 함수"""
    print("🚀 Redis 사용 예제 시작")
    
    try:
        # Redis 연결
        await redis_client.connect()
        
        # 예제 실행
        await basic_redis_example()
        await hash_redis_example()
        await caching_example()
        await session_management_example()
        await realtime_stats_example()
        
    except Exception as e:
        print(f"오류 발생: {e}")
    
    finally:
        # Redis 연결 해제
        await redis_client.disconnect()
        print("\n✅ Redis 사용 예제 완료")

if __name__ == "__main__":
    asyncio.run(main()) 