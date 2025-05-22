import os
import subprocess
import tempfile
import json
import time
from executors.base import Executor
from module_models import ExecRequest, ExecResult

class VenvExecutor(Executor):
    def __init__(self, venv_path="./venvs", module_registry=None):
        self.venv_path = venv_path
        self.module_registry = module_registry
        os.makedirs(venv_path, exist_ok=True)

    async def validate(self, module_name: str) -> bool:
        venv_dir = os.path.join(self.venv_path, module_name)
        return os.path.exists(venv_dir)

    async def execute(self, request: ExecRequest) -> ExecResult:
        start_time = time.time()
        module_name = request.module
        module = self.module_registry.get_module(module_name)
        if not module or not module.path:
            return ExecResult(
                result_json={},
                exit_code=1,
                stderr=f"Module path not found for {module_name}",
                stdout="",
                duration=0
            )
            
        # 가상환경과 모듈 경로 설정
        venv_dir = os.path.join(self.venv_path, module_name)
        module_dir = venv_dir  # 모듈이 있는 디렉토리는 가상환경 디렉토리와 동일
        
        # Python 실행 파일 경로
        if os.name == 'nt':
            python_bin = os.path.join(venv_dir, 'Scripts', 'python.exe')
        else:
            python_bin = os.path.join(venv_dir, 'bin', 'python')
            
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as input_file:
            json.dump(request.input_json, input_file)
            input_path = input_file.name
        output_path = tempfile.mktemp(suffix='.json')
            
        # Python 스크립트 작성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
            script_content = f"""
import json
import sys
import os

# 모듈 디렉토리를 Python 경로에 추가
sys.path.insert(0, '{module_dir}')

# 모듈 임포트 및 실행
from {module_name.replace('-', '_')} import handler

with open('{input_path}', 'r') as f:
    input_data = json.load(f)

result = handler(input_data)

with open('{output_path}', 'w') as f:
    json.dump(result, f)
"""
            script_file.write(script_content)
            script_path = script_file.name

        try:
            process = subprocess.run(
                [python_bin, script_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    result_json = json.load(f)
            else:
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
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
            if os.path.exists(script_path):
                os.unlink(script_path)
                
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
        return "venv" 