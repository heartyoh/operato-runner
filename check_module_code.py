import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from module_registry import ModuleRegistry
from core.db import get_db, init_engine

async def check_module_code():
    try:
        # DB 엔진 초기화
        init_engine()
        print("DB 엔진 초기화 완료")
        
        # DB 세션 생성
        async for db in get_db():
            print("DB 세션 생성 완료")
            
            # ModuleRegistry 생성
            mr = ModuleRegistry(db)
            print("ModuleRegistry 생성 완료")
            
            # inline-01 모듈 가져오기
            module = await mr.get_module('inline-01')
            if module:
                print(f"[현재 적용 모듈] 이름: {module.name}, 버전: {getattr(module, 'version', '?')}")
                print(f"코드:")
                print("=" * 50)
                print(module.code)
                print("=" * 50)
                # 모든 버전 출력
                if hasattr(module, 'versions'):
                    print("[모든 버전 코드]")
                    for v in module.versions:
                        print(f"버전: {getattr(v, 'version', '?')}")
                        print("-" * 40)
                        print(getattr(v, 'code', '코드 없음'))
                        print("-" * 40)
                else:
                    print("versions 속성이 없습니다.")
            else:
                print("inline-01 모듈을 찾을 수 없습니다.")
            
            break
            
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_module_code()) 