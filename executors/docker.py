import os
import tempfile
import json
import time
import shutil
import docker
from executors.base import Executor
from models import ExecRequest, ExecResult
from module_registry import ModuleRegistry

class DockerExecutor(Executor):
    def __init__(self, module_registry: ModuleRegistry = None, base_image="python:3.10-slim"):
        self.client = docker.from_env()
        self.base_image = base_image
        self.module_registry = module_registry

    async def validate(self, module_name: str) -> bool:
        try:
            self.client.ping()
            # 실제로는 module_registry에서 env 체크 필요
            if self.module_registry:
                module = await self.module_registry.get_module(module_name)
                return module and module.env == "docker"
            return True
        except Exception:
            return False

    async def execute(self, request: ExecRequest) -> ExecResult:
        start_time = time.time()
        module_name = request.module
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, "input.json")
        with open(input_path, "w") as f:
            json.dump(request.input_json, f)
        output_path = os.path.join(temp_dir, "output.json")
        # artifact 기반 이미지 주소 사용
        image_ref = None
        if self.module_registry:
            module = await self.module_registry.get_module(module_name)
            if module and getattr(module, "artifact_type", None) == "docker":
                image_ref = getattr(module, "artifact_uri", None)
        if not image_ref:
            return ExecResult(
                result_json={},
                exit_code=1,
                stderr="docker artifact_uri가 지정되지 않았습니다.",
                stdout="",
                duration=0
            )
        script_path = os.path.join(temp_dir, "script.py")
        with open(script_path, "w") as f:
            f.write("import json\n")
            f.write("import sys\n")
            f.write(f"sys.path.insert(0, '{temp_dir}')\n")
            f.write("from handler import handler\n")
            f.write("with open('/data/input.json', 'r') as f:\n")
            f.write("    input_data = json.load(f)\n")
            f.write("result = handler(input_data)\n")
            f.write("with open('/data/output.json', 'w') as f:\n")
            f.write("    json.dump(result, f)\n")
        container = None
        try:
            # 이미지 pull (최초 실행 시)
            self.client.images.pull(image_ref)
            container = self.client.containers.run(
                image_ref,
                command=["python", "/data/script.py"],
                volumes={temp_dir: {"bind": "/data", "mode": "rw"}},
                detach=True,
                mem_limit="512m",
                cpu_period=100000,
                cpu_quota=50000,
                network_mode="none"
            )
            exit_code = container.wait(timeout=60)["StatusCode"]
            logs = container.logs(stdout=True, stderr=True).decode("utf-8")
            stdout = ""
            stderr = ""
            if exit_code == 0:
                stdout = logs
            else:
                stderr = logs
            if os.path.exists(output_path):
                with open(output_path, "r") as f:
                    result_json = json.load(f)
            else:
                result_json = {}
        except docker.errors.ContainerError as e:
            exit_code = e.exit_status
            stderr = str(e)
            stdout = ""
            result_json = {}
        except Exception as e:
            exit_code = 1
            stderr = f"Error executing module: {str(e)}"
            stdout = ""
            result_json = {}
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            shutil.rmtree(temp_dir, ignore_errors=True)
        duration = time.time() - start_time
        return ExecResult(
            result_json=result_json,
            exit_code=exit_code,
            stderr=stderr,
            stdout=stdout,
            duration=duration
        )

    async def cleanup(self) -> None:
        try:
            containers = self.client.containers.list(all=True, filters={"label": "operato-runner"})
            for container in containers:
                container.remove(force=True)
        except Exception:
            pass

    @property
    def executor_type(self) -> str:
        return "docker" 