import os
import subprocess
import tempfile
import json
import time
import logging
from executors.base import Executor
from models import ExecRequest, ExecResult

def log_module_action(module_name, version, action, message):
    logging.info(f"[{module_name}][v{version}][{action}] {message}")

class VenvExecutor(Executor):
    def __init__(self, venv_path="module_envs", module_registry=None):
        # 절대 경로로 변환
        self.venv_path = os.path.abspath(venv_path)
        self.module_registry = module_registry
        os.makedirs(self.venv_path, exist_ok=True)

    async def validate(self, module_name: str) -> bool:
        # 절대 경로 사용
        venv_dir = os.path.join(self.venv_path, module_name, "venv")
        return os.path.exists(venv_dir)

    async def execute(self, request: ExecRequest) -> ExecResult:
        start_time = time.time()
        module_name = request.module
        module = await self.module_registry.get_module(module_name)
        
        # 절대 경로로 가상환경과 모듈 경로 설정
        venv_dir = os.path.join(self.venv_path, module_name, "venv")
        module_dir = os.path.join(self.venv_path, module_name)
        
        # 각 실행마다 고유한 작업 디렉토리 생성
        execution_work_dir = tempfile.mkdtemp(prefix=f"exec_{module_name}_{int(time.time())}_")
        
        # Python 실행 파일 경로 (절대 경로)
        if os.name == 'nt':
            python_bin = os.path.join(venv_dir, 'Scripts', 'python.exe')
        else:
            python_bin = os.path.join(venv_dir, 'bin', 'python')
            
        # 임시 파일 생성 (작업 디렉토리 내에)
        input_path = os.path.join(execution_work_dir, "input.json")
        with open(input_path, 'w') as f:
            # 표준 API: work_directory 제공
            enhanced_input = request.input_json.copy()
            enhanced_input["work_directory"] = execution_work_dir
            enhanced_input["temp_directory"] = execution_work_dir
            json.dump(enhanced_input, f)
            
        output_path = os.path.join(execution_work_dir, "output.json")
            
        # Python 스크립트 작성 (절대 경로 사용)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
            script_content = f"""
import json
import sys
import os

# 모듈 디렉토리를 Python 경로에 추가 (절대 경로)
sys.path.insert(0, r'{module_dir}')

# 모듈의 __main__.py에서 main 함수 import
import importlib.util
spec = importlib.util.spec_from_file_location("module_main", os.path.join(r'{module_dir}', '__main__.py'))
module_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module_main)
main = module_main.main

with open(r'{input_path}', 'r') as f:
    input_data = json.load(f)

result = main(input_data)

with open(r'{output_path}', 'w') as f:
    json.dump(result, f)
"""
            script_file.write(script_content)
            script_path = script_file.name

        # 환경변수 주입 및 .env 파일 생성
        env = os.environ.copy()
        env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        # module.env_vars는 relationship으로 리스트 형태
        if hasattr(module, 'env_vars') and module.env_vars:
            env_dict = {e.key: e.value for e in module.env_vars}
            env.update(env_dict)
            # .env 파일 생성 (절대 경로)
            env_path = os.path.join(module_dir, '.env')
            with open(env_path, 'w') as f:
                for k, v in env_dict.items():
                    f.write(f"{k}={v}\n")
        else:
            env_path = None

        try:
            process = subprocess.run(
                [python_bin, script_path],
                capture_output=True,
                text=True,
                timeout=3600,
                cwd=execution_work_dir,  # 격리된 작업 디렉토리에서 실행
                env=env
            )
            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    result_json = json.load(f)
            else:
                result_json = {}
            exit_code = process.returncode
            stderr = process.stderr
            stdout = process.stdout
            log_module_action(module_name, getattr(module, 'version', 'unknown'), "execute", f"실행 완료 (exit_code={exit_code})")
        except subprocess.TimeoutExpired:
            exit_code = 124
            stderr = "Execution timed out after 60 seconds"
            stdout = ""
            result_json = {}
            log_module_action(module_name, getattr(module, 'version', 'unknown'), "execute", "실행 타임아웃")
        except Exception as e:
            exit_code = 1
            stderr = f"Error executing module: {str(e)}"
            stdout = ""
            result_json = {}
            log_module_action(module_name, getattr(module, 'version', 'unknown'), "execute", f"실행 에러: {str(e)}")
        finally:
            # 스크립트 파일은 별도 위치에 있으므로 개별 삭제
            try:
                os.unlink(script_path)
            except:
                pass
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
        return "venv" 