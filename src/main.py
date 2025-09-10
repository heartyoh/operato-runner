import asyncio
import argparse
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from core.db import init_engine, get_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from module_registry import ModuleRegistry
from executor_manager import ExecutorManager
from executors.inline import InlineExecutor
from executors.venv import VenvExecutor
from executors.conda import CondaExecutor
from executors.docker import DockerExecutor
from executors.uv import UvExecutor
from api.rest import app as rest_app
from api.grpc_server import serve as serve_grpc
from utils.redis_client import redis_client
from utils.file_storage import start_cleanup_scheduler
import uvicorn

async def main():
    parser = argparse.ArgumentParser(description="Operato Runner")
    parser.add_argument("--rest-port", type=int, default=8000, help="REST API port")
    parser.add_argument("--grpc-port", type=int, default=50051, help="gRPC server port")
    parser.add_argument("--venv-path", default="./runtime/module_envs", help="Path to virtual environments")
    parser.add_argument("--no-rest", action="store_true", help="Disable REST API")
    parser.add_argument("--no-grpc", action="store_true", help="Disable gRPC server")
    parser.add_argument("--no-redis", action="store_true", help="Disable Redis")
    args = parser.parse_args()

    # Redis 비활성화 설정
    if args.no_redis:
        os.environ['REDIS_ENABLED'] = 'false'

    # DB 엔진 초기화
    init_engine()
    async_session = get_sessionmaker()

    # Redis 연결 초기화 (조건부)
    if redis_client.enabled:
        await redis_client.connect()
        # 연결 상태 확인
        if await redis_client.is_connected():
            print("✅ Redis 연결됨")
        else:
            print("⚠️  Redis 연결 실패 - 캐싱 기능 사용 불가")
    else:
        print("⚠️  Redis 비활성화됨 - 캐싱 기능 사용 불가")

    async with async_session() as db:
        module_registry = ModuleRegistry(db)
        executor_manager = ExecutorManager(module_registry, max_workers=4)
        executor_manager.venv_path = args.venv_path  # venv_path 정보 저장
        executor_manager.register_executor("inline", InlineExecutor(module_registry))
        executor_manager.register_executor("venv", VenvExecutor(venv_path=args.venv_path, module_registry=module_registry))
        executor_manager.register_executor("conda", CondaExecutor(module_registry))
        
        # Docker executor 등록 (사용 가능한 경우에만)
        try:
            executor_manager.register_executor("docker", DockerExecutor(module_registry))
            print("✅ Docker executor 등록됨")
        except Exception as e:
            print(f"⚠️  Docker executor 등록 실패: {e}")
            print("⚠️  Docker 관련 기능 사용 불가")
        
        executor_manager.register_executor("uv", UvExecutor(uv_path=args.venv_path, module_registry=module_registry))

        # FastAPI 앱에 context 주입
        rest_app.state.module_registry = module_registry
        rest_app.state.executor_manager = executor_manager

        grpc_server = None
        grpc_task = None
        rest_task = None
        cleanup_task = None

        try:
            # 파일 정리 스케줄러 시작
            cleanup_task = asyncio.create_task(start_cleanup_scheduler())
            loop = asyncio.get_running_loop()
            if not args.no_grpc:
                grpc_server = serve_grpc(module_registry, executor_manager, port=args.grpc_port)
                await grpc_server.start()
                print(f"gRPC server started on port {args.grpc_port}")
                grpc_task = loop.create_task(grpc_server.wait_for_termination())

            if not args.no_rest:
                config = uvicorn.Config(rest_app, host="0.0.0.0", port=args.rest_port, log_level="info")
                server = uvicorn.Server(config)
                rest_task = loop.create_task(server.serve())
                print(f"REST API started on port {args.rest_port}")

            tasks = [t for t in [grpc_task, rest_task, cleanup_task] if t is not None]
            if tasks:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        except KeyboardInterrupt:
            print("Shutting down servers...")
            if grpc_server:
                await grpc_server.stop(0)
                await grpc_server.wait_for_termination()
            for t in [grpc_task, rest_task, cleanup_task]:
                if t is not None and not t.done():
                    t.cancel()
            await asyncio.sleep(0.1)
        finally:
            # Redis 연결 해제 (조건부)
            if redis_client.enabled and await redis_client.is_connected():
                await redis_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 