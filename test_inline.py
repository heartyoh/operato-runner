import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from executor_manager import ExecutorManager
from module_registry import ModuleRegistry
from core.db import get_db, init_engine
from executors.inline import InlineExecutor

async def test_inline_executor():
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
            
            # 테스트 모듈 가져오기
            module = await mr.get_module('test_module')
            print(f"모듈 찾음: {module.name if module else 'None'}")
            
            if module:
                # ExecutorManager 생성
                em = ExecutorManager(mr)
                print("ExecutorManager 생성 완료")
                
                # Inline executor 등록
                inline_executor = InlineExecutor(mr)
                em.register_executor('inline', inline_executor)
                print("Inline executor 등록 완료")
                
                # 모듈 실행 테스트
                from models import ExecRequest
                request = ExecRequest(
                    module=module.name,
                    input_json={'test': 'data'}
                )
                
                result = await em.execute(request)
                print(f"실행 결과: {result}")
            
            break  # 한 번만 실행
            
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_inline_executor()) 