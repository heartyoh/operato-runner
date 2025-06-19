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

class UvExecutor(Executor):
    def __init__(self, uv_path="module_envs", module_registry=None):
        self.uv_path = uv_path
        self.module_registry = module_registry
        os.makedirs(uv_path, exist_ok=True)

    async def validate(self, module_name: str) -> bool:
        uv_dir = os.path.join(self.uv_path, module_name, "uv")
        return os.path.exists(uv_dir)

    async def execute(self, request: ExecRequest) -> ExecResult:
        start_time = time.time()
        module_name = request.module
        module = await self.module_registry.get_module(module_name)
        
        uv_dir = os.path.join(self.uv_path, module_name, "uv")
        module_dir = os.path.join(self.uv_path, module_name)
        
        # uv 가상환경 python 경로
        python_bin = os.path.join(uv_dir, "bin", "python")
        
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
sys.path.insert(0, '{module_dir}')
from handler import handler
with open('{input_path}', 'r') as f:
    input_data = json.load(f)
result = handler(input_data)
with open('{output_path}', 'w') as f:
    json.dump(result, f)
"""
            script_file.write(script_content)
            script_path = script_file.name

        try:
            env = os.environ.copy()
            env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
            process = subprocess.run(
                [python_bin, script_path],
                capture_output=True,
                text=True,
                timeout=60,
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
        return "uv" 