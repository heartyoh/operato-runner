import os
import subprocess
import tempfile
import json
import time
from executors.base import Executor
from models import ExecRequest, ExecResult
from module_registry import ModuleRegistry

class CondaExecutor(Executor):
    def __init__(self, module_registry: ModuleRegistry = None):
        self.module_registry = module_registry

    async def validate(self, module_name: str) -> bool:
        # 모듈이 존재하고 env가 'conda'인지, conda 환경이 존재하는지 확인
        try:
            # conda 설치 확인
            subprocess.run(["conda", "--version"], check=True, capture_output=True)
            # 환경 목록 확인
            result = subprocess.run(
                ["conda", "env", "list", "--json"],
                check=True,
                capture_output=True,
                text=True
            )
            envs = json.loads(result.stdout)["envs"]
            # 환경 이름이 모듈 이름과 일치하는지 확인
            return any(env.endswith(module_name) for env in envs)
        except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
            return False

    async def execute(self, request: ExecRequest) -> ExecResult:
        start_time = time.time()
        module_name = request.module
        
        # 입력 파일 생성 - NamedTemporaryFile 사용
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as input_file:
            json.dump(request.input_json, input_file)
            input_path = input_file.name
        
        # 출력 파일 경로만 확보 (파일은 미리 생성하지 않음)
        output_path = tempfile.mktemp(suffix='.json')
        
        # 모듈 경로 획득
        module_path = ""
        if self.module_registry:
            module = await self.module_registry.get_module(module_name)
            if module and module.path:
                module_path = module.path
        # 명령어 구성
        cmd = [
            "conda", "run", "-n", module_name,
            "python", "-c",
            f"import json; import sys; sys.path.append('{os.path.dirname(module_path)}'); "
            f"from {os.path.basename(module_path).replace('.py', '')} import handler; "
            f"with open('{input_path}', 'r') as f: input_data = json.load(f); "
            f"result = handler(input_data); "
            f"with open('{output_path}', 'w') as f: json.dump(result, f)"
        ]
        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            result_json = {}
            if process.returncode == 0:
                try:
                    with open(output_path, 'r') as f:
                        result_json = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading output file: {str(e)}")
                    result_json = {}
            exit_code = process.returncode
            stderr = process.stderr
            stdout = process.stdout
        except subprocess.TimeoutExpired:
            exit_code = 124
            stderr = "Execution timed out after 60 seconds"
            stdout = ""
            result_json = {}
        except Exception as e:
            exit_code = 1
            stderr = f"Error executing module: {str(e)}"
            stdout = ""
            result_json = {}
        finally:
            try:
                if os.path.exists(input_path):
                    os.unlink(input_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)
            except Exception as e:
                print(f"Error cleaning up temporary files: {str(e)}")
        duration = time.time() - start_time
        return ExecResult(
            result_json=result_json,
            exit_code=exit_code,
            stderr=stderr,
            stdout=stdout,
            duration=duration
        )

    async def cleanup(self) -> None:
        pass

    @property
    def executor_type(self) -> str:
        return "conda" 