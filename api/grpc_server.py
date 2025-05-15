import json
import grpc
from concurrent import futures
from typing import Any
import asyncio
from proto import executor_pb2, executor_pb2_grpc
from models import Module, ExecRequest as ModelExecRequest
from module_registry import ModuleRegistry
from executor_manager import ExecutorManager
from api.auth import get_current_user, User, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError

# --- gRPC JWT 인증 인터셉터 ---
class JwtAuthInterceptor(grpc.aio.ServerInterceptor):
    async def intercept_service(self, continuation, handler_call_details):
        # 메타데이터에서 authorization 추출
        metadata = dict(handler_call_details.invocation_metadata)
        token = None
        auth_header = metadata.get('authorization')
        if auth_header and auth_header.lower().startswith('bearer '):
            token = auth_header[7:]
        if not token:
            def unauthenticated_behavior(request, context):
                context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Missing JWT token')
            return grpc.aio.unary_unary_rpc_method_handler(unauthenticated_behavior)
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get('sub')
            scopes = payload.get('scopes', [])
            if not username:
                raise JWTError('No subject in token')
            user = User(username=username, scopes=scopes)
        except JWTError as e:
            def unauthenticated_behavior(request, context):
                context.abort(grpc.StatusCode.UNAUTHENTICATED, f'Invalid JWT: {str(e)}')
            return grpc.aio.unary_unary_rpc_method_handler(unauthenticated_behavior)
        # 인증 성공: context에 user 주입
        handler = await continuation(handler_call_details)
        async def new_behavior(request, context):
            context.user = user
            return await handler.unary_unary(request, context)
        return grpc.aio.unary_unary_rpc_method_handler(new_behavior)

# --- 권한 체크 함수 ---
def require_scope(context, required_scope):
    user = getattr(context, 'user', None)
    if not user or required_scope not in user.scopes:
        context.abort(grpc.StatusCode.PERMISSION_DENIED, f"Not enough permissions. Required scope: {required_scope}")

class ExecutorServicer(executor_pb2_grpc.ExecutorServicer):
    def __init__(self, module_registry: ModuleRegistry, executor_manager: ExecutorManager):
        self.module_registry = module_registry
        self.executor_manager = executor_manager

    async def Execute(self, request, context):
        # 실행 권한 체크
        user = getattr(context, 'user', None)
        if not user or (('execute:all' not in user.scopes) and ('execute:limited' not in user.scopes)):
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Not enough permissions. Required scope: execute:all or execute:limited")
        try:
            input_json = json.loads(request.json_input)
        except json.JSONDecodeError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid JSON input")
            return executor_pb2.ExecResponse()
        exec_request = ModelExecRequest(
            module=request.module,
            input_json=input_json
        )
        result = await self.executor_manager.execute(exec_request)
        return executor_pb2.ExecResponse(
            result=json.dumps(result.result_json),
            exit_code=result.exit_code,
            stderr=result.stderr,
            stdout=result.stdout,
            duration=result.duration
        )

    async def ListModules(self, request, context):
        require_scope(context, "modules:read")
        modules = self.module_registry.list_modules()
        response = executor_pb2.ListModulesResponse()
        for module in modules:
            module_info = executor_pb2.ModuleInfo(
                name=module.name,
                env=module.env,
                version=module.version,
                created_at=module.created_at.isoformat(),
                tags=module.tags
            )
            response.modules.append(module_info)
        return response

    async def GetModule(self, request, context):
        require_scope(context, "modules:read")
        module = self.module_registry.get_module(request.name)
        if not module:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Module '{request.name}' not found")
            return executor_pb2.ModuleInfo()
        return executor_pb2.ModuleInfo(
            name=module.name,
            env=module.env,
            version=module.version,
            created_at=module.created_at.isoformat(),
            tags=module.tags
        )

    async def RegisterModule(self, request, context):
        require_scope(context, "modules:write")
        if not request.code and not request.path:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Either code or path must be provided")
            return executor_pb2.ModuleInfo()
        module = Module(
            name=request.name,
            env=request.env,
            code=request.code if request.code else None,
            path=request.path if request.path else None,
            version=request.version if request.version else "0.1.0",
            tags=list(request.tags)
        )
        self.module_registry.register_module(module)
        return executor_pb2.ModuleInfo(
            name=module.name,
            env=module.env,
            version=module.version,
            created_at=module.created_at.isoformat(),
            tags=module.tags
        )

    async def DeleteModule(self, request, context):
        require_scope(context, "modules:write")
        success = self.module_registry.delete_module(request.name)
        if not success:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Module '{request.name}' not found")
        return executor_pb2.DeleteModuleResponse(success=success)

def serve(module_registry: ModuleRegistry, executor_manager: ExecutorManager, port=50051):
    # --- 인터셉터 등록 ---
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10), interceptors=[JwtAuthInterceptor()])
    executor_pb2_grpc.add_ExecutorServicer_to_server(
        ExecutorServicer(module_registry, executor_manager),
        server
    )
    server.add_insecure_port(f'[::]:{port}')
    return server 