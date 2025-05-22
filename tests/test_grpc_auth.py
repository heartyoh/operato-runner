import pytest
import asyncio
import grpc
from api.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from proto import executor_pb2, executor_pb2_grpc
from main import main as runner_main
import multiprocessing
import time
from datetime import timedelta

GRPC_PORT = 50551

# gRPC 서버를 별도 프로세스로 실행 (테스트 격리)
def start_server():
    import sys
    sys.argv = ["main.py", f"--grpc-port={GRPC_PORT}", "--no-rest"]
    asyncio.run(runner_main())

@pytest.fixture(scope="module", autouse=True)
def grpc_server():
    proc = multiprocessing.Process(target=start_server)
    proc.start()
    time.sleep(2)  # 서버 기동 대기
    yield
    proc.terminate()
    proc.join()

@pytest.mark.asyncio
async def test_execute_with_valid_token(grpc_server):
    token = create_access_token({"sub": "admin", "scopes": ["execute:all", "modules:read", "modules:write"]})
    async with grpc.aio.insecure_channel(f"localhost:{GRPC_PORT}") as channel:
        stub = executor_pb2_grpc.ExecutorStub(channel)
        metadata = [("authorization", f"Bearer {token}")]
        req = executor_pb2.ExecRequest(module="mod", json_input="{}")
        try:
            await stub.Execute(req, metadata=metadata, timeout=3)
        except grpc.aio.AioRpcError as e:
            assert False, f"Should not raise: {e}"

@pytest.mark.asyncio
async def test_execute_without_token(grpc_server):
    async with grpc.aio.insecure_channel(f"localhost:{GRPC_PORT}") as channel:
        stub = executor_pb2_grpc.ExecutorStub(channel)
        req = executor_pb2.ExecRequest(module="mod", json_input="{}")
        with pytest.raises(grpc.aio.AioRpcError) as e:
            await stub.Execute(req, timeout=3)
        assert e.value.code() == grpc.StatusCode.UNAUTHENTICATED

@pytest.mark.asyncio
async def test_execute_with_invalid_token(grpc_server):
    async with grpc.aio.insecure_channel(f"localhost:{GRPC_PORT}") as channel:
        stub = executor_pb2_grpc.ExecutorStub(channel)
        metadata = [("authorization", "Bearer invalidtoken")]
        req = executor_pb2.ExecRequest(module="mod", json_input="{}")
        with pytest.raises(grpc.aio.AioRpcError) as e:
            await stub.Execute(req, metadata=metadata, timeout=3)
        assert e.value.code() == grpc.StatusCode.UNAUTHENTICATED

@pytest.mark.asyncio
async def test_execute_with_insufficient_scope(grpc_server):
    token = create_access_token({"sub": "user", "scopes": ["modules:read"]})
    async with grpc.aio.insecure_channel(f"localhost:{GRPC_PORT}") as channel:
        stub = executor_pb2_grpc.ExecutorStub(channel)
        metadata = [("authorization", f"Bearer {token}")]
        req = executor_pb2.ExecRequest(module="mod", json_input="{}")
        with pytest.raises(grpc.aio.AioRpcError) as e:
            await stub.Execute(req, metadata=metadata, timeout=3)
        assert e.value.code() == grpc.StatusCode.PERMISSION_DENIED

@pytest.mark.asyncio
async def test_listmodules_with_read_scope(grpc_server):
    token = create_access_token({"sub": "user", "scopes": ["modules:read"]})
    async with grpc.aio.insecure_channel(f"localhost:{GRPC_PORT}") as channel:
        stub = executor_pb2_grpc.ExecutorStub(channel)
        metadata = [("authorization", f"Bearer {token}")]
        req = executor_pb2.ListModulesRequest()
        await stub.ListModules(req, metadata=metadata, timeout=3)

@pytest.mark.asyncio
async def test_registermodule_without_write_scope(grpc_server):
    token = create_access_token({"sub": "user", "scopes": ["modules:read"]})
    async with grpc.aio.insecure_channel(f"localhost:{GRPC_PORT}") as channel:
        stub = executor_pb2_grpc.ExecutorStub(channel)
        metadata = [("authorization", f"Bearer {token}")]
        req = executor_pb2.RegisterModuleRequest(name="mod", env="inline", code="def handler(x): return x", path="", version="0.1.0", tags=[])
        with pytest.raises(grpc.aio.AioRpcError) as e:
            await stub.RegisterModule(req, metadata=metadata, timeout=3)
        assert e.value.code() == grpc.StatusCode.PERMISSION_DENIED 