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
        
        # 각 실행마다 고유한 작업 디렉토리 생성
        execution_work_dir = tempfile.mkdtemp(prefix=f"exec_{module_name}_{int(time.time())}_")
        
        # 입력 파일 생성 (작업 디렉토리 내에)
        input_path = os.path.join(execution_work_dir, "input.json")
        with open(input_path, 'w') as f:
            # 표준 API: work_directory 제공
            enhanced_input = request.input_json.copy()
            enhanced_input["work_directory"] = execution_work_dir
            enhanced_input["temp_directory"] = execution_work_dir
            json.dump(enhanced_input, f)
        
        # 출력 파일 경로 (작업 디렉토리 내에)
        output_path = os.path.join(execution_work_dir, "output.json")
        
        # 모듈 경로 획득
        module_path = ""
        if self.module_registry:
            module = await self.module_registry.get_module(module_name)
            if module and module.path:
                module_path = module.path
        # 환경변수 주입 및 .env 파일 생성
        env = os.environ.copy()
        if hasattr(module, 'env_vars') and module.env_vars:
            env_dict = {e.key: e.value for e in module.env_vars}
            env.update(env_dict)
            env_path = os.path.join(os.path.dirname(module_path), '.env')
            with open(env_path, 'w') as f:
                for k, v in env_dict.items():
                    f.write(f"{k}={v}\n")
        else:
            env_path = None

        try:
            # 명령어 구성
            cmd = [
                "conda", "run", "-n", module_name,
                "python", "-c",
                f"import json; import sys; import importlib.util; "
                f"sys.path.append('{os.path.dirname(module_path)}'); "
                f"spec = importlib.util.spec_from_file_location('module_main', '{os.path.join(module_path, '__main__.py')}'); "
                f"module_main = importlib.util.module_from_spec(spec); "
                f"spec.loader.exec_module(module_main); "
                f"main = module_main.main; "
                f"with open('{input_path}', 'r') as f: input_data = json.load(f); "
                f"result = main(input_data); "
                f"with open('{output_path}', 'w') as f: json.dump(result, f)"
            ]
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, 
                                   cwd=execution_work_dir, env=env)
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
            if env_path and os.path.exists(env_path):
                try:
                    os.unlink(env_path)
                except:
                    pass
        duration = time.time() - start_time
        return ExecResult(
            result_json=result_json,
            exit_code=exit_code,
            stderr=stderr,
            stdout=stdout,
            duration=duration,
            work_directory=execution_work_dir
        )

    async def cleanup(self) -> None:
        pass

    @property
    def executor_type(self) -> str:
        return "conda" 