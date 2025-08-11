import os
import subprocess
import tempfile
import json
import time
import logging
import importlib.util
from executors.base import Executor
from models import ExecRequest, ExecResult

def log_module_action(module_name, version, action, message):
    logging.info(f"[{module_name}][v{version}][{action}] {message}")

class UvExecutor(Executor):
    def __init__(self, uv_path="module_envs", module_registry=None):
        # 절대 경로로 변환
        self.uv_path = os.path.abspath(uv_path)
        self.module_registry = module_registry
        os.makedirs(self.uv_path, exist_ok=True)

    async def validate(self, module_name: str) -> bool:
        # 절대 경로 사용
        module_dir = os.path.join(self.uv_path, module_name)
        return os.path.exists(module_dir)

    async def execute(self, request: ExecRequest) -> ExecResult:
        start_time = time.time()
        module_name = request.module
        module = await self.module_registry.get_module(module_name)
        
        # 절대 경로로 모듈과 uv 가상환경 경로 설정
        module_dir = os.path.join(self.uv_path, module_name)
        uv_dir = os.path.join(module_dir, "uv")
        
        # uv 가상환경 python 경로 (절대 경로)
        python_bin = os.path.join(uv_dir, "bin", "python")
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as input_file:
            json.dump(request.input_json, input_file)
            input_path = input_file.name
        output_path = tempfile.mktemp(suffix='.json')
        
        # Python 스크립트 작성 (절대 경로 사용)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
            script_content = f"""
import json
import sys
import os
import importlib.util

# 모듈 디렉토리를 Python 경로에 추가 (절대 경로)
sys.path.insert(0, r'{module_dir}')

# 모듈의 __main__.py에서 main 함수 import (절대 경로)
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

        # 환경변수 주입 및 .env 파일 생성 (절대 경로)
        env = os.environ.copy()
        env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        if hasattr(module, 'env_vars') and module.env_vars:
            env_dict = {e.key: e.value for e in module.env_vars}
            env.update(env_dict)
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
            # 임시 파일들 정리
            try:
                os.unlink(input_path)
                os.unlink(output_path)
                os.unlink(script_path)
                if env_path and os.path.exists(env_path):
                    os.unlink(env_path)
            except:
                pass
                
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