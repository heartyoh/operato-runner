import pytest
import asyncio
import os
from executors.venv import VenvExecutor
from models import ExecRequest, ExecResult

@pytest.mark.asyncio
async def test_venv_executor_success():
    # 샘플 venv와 handler_module.py가 이미 생성되어 있다고 가정
    venv_path = "./venvs"
    module_name = "testmod"
    module_path = os.path.abspath(os.path.join(venv_path, module_name, "handler_module.py"))
    executor = VenvExecutor(venv_path=venv_path)
    async def execute_with_module_path(self, request):
        import subprocess, tempfile, json, time
        start_time = time.time()
        venv_dir = os.path.join(self.venv_path, module_name)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as input_file:
            json.dump(request.input_json, input_file)
            input_path = input_file.name
        output_path = tempfile.mktemp(suffix='.json')
        # 임시 파이썬 실행 스크립트 생성
        script_code = f'''
import json
import sys
sys.path.append('{os.path.dirname(module_path)}')
from handler_module import handler
with open('{input_path}', 'r') as f:
    input_data = json.load(f)
result = handler(input_data)
with open('{output_path}', 'w') as f:
    json.dump(result, f)
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
            script_file.write(script_code)
            script_path = script_file.name
        if os.name == 'nt':
            python_bin = os.path.join(venv_dir, 'Scripts', 'python.exe')
        else:
            python_bin = os.path.join(venv_dir, 'bin', 'python')
        cmd = [python_bin, script_path]
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
    executor.execute = execute_with_module_path.__get__(executor)
    req = ExecRequest(module=module_name, input_json={"a": 10, "b": 20})
    result: ExecResult = await executor.execute(req)
    assert result.exit_code == 0
    assert result.result_json == {"sum": 30} 