import os
import subprocess
import tempfile
import json
import time
from executors.base import Executor
from models import ExecRequest, ExecResult

class VenvExecutor(Executor):
    def __init__(self, venv_path="./venvs"):
        self.venv_path = venv_path
        os.makedirs(venv_path, exist_ok=True)

    async def validate(self, module_name: str) -> bool:
        venv_dir = os.path.join(self.venv_path, module_name)
        return os.path.exists(venv_dir)

    async def execute(self, request: ExecRequest) -> ExecResult:
        start_time = time.time()
        module_name = request.module
        venv_dir = os.path.join(self.venv_path, module_name)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as input_file:
            json.dump(request.input_json, input_file)
            input_path = input_file.name
        output_path = tempfile.mktemp(suffix='.json')
        module_path = ""  # 실제 구현에서는 ModuleRegistry에서 받아야 함
        if os.name == 'nt':
            python_bin = os.path.join(venv_dir, 'Scripts', 'python.exe')
        else:
            python_bin = os.path.join(venv_dir, 'bin', 'python')
        cmd = [
            python_bin,
            '-c',
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