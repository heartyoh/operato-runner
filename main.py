import asyncio
import argparse
import uvicorn
from module_registry import ModuleRegistry
from executor_manager import ExecutorManager
from executors.inline import InlineExecutor
from executors.venv import VenvExecutor
from executors.conda import CondaExecutor
from executors.docker import DockerExecutor
from api.rest import app as rest_app
from api.grpc_server import serve as serve_grpc

async def main():
    parser = argparse.ArgumentParser(description="Operato Runner")
    parser.add_argument("--config", default="./modules.yaml", help="Path to modules configuration file")
    parser.add_argument("--rest-port", type=int, default=8000, help="REST API port")
    parser.add_argument("--grpc-port", type=int, default=50051, help="gRPC server port")
    parser.add_argument("--venv-path", default="./venvs", help="Path to virtual environments")
    parser.add_argument("--no-rest", action="store_true", help="Disable REST API")
    parser.add_argument("--no-grpc", action="store_true", help="Disable gRPC server")
    args = parser.parse_args()

    module_registry = ModuleRegistry(config_path=args.config)
    executor_manager = ExecutorManager(module_registry)
    executor_manager.register_executor("inline", InlineExecutor(module_registry))
    executor_manager.register_executor("venv", VenvExecutor(venv_path=args.venv_path, module_registry=module_registry))
    executor_manager.register_executor("conda", CondaExecutor(module_registry))
    executor_manager.register_executor("docker", DockerExecutor(module_registry))

    # FastAPI 앱에 context 주입
    rest_app.state.module_registry = module_registry
    rest_app.state.executor_manager = executor_manager

    grpc_server = None
    grpc_task = None
    rest_task = None

    try:
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

        tasks = [t for t in [grpc_task, rest_task] if t is not None]
        if tasks:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    except KeyboardInterrupt:
        print("Shutting down servers...")
        if grpc_server:
            await grpc_server.stop(0)
            await grpc_server.wait_for_termination()
        for t in [grpc_task, rest_task]:
            if t is not None and not t.done():
                t.cancel()
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main()) 