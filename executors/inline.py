import ast
import sys
from io import StringIO
import time
from executors.base import Executor
from models import ExecRequest, ExecResult, Version, Deployment
import json
import os
from sqlalchemy.future import select

class InlineExecutor(Executor):
    def __init__(self, module_registry=None):
        self.module_registry = module_registry

    @property
    def executor_type(self) -> str:
        return "inline"

    async def validate(self, module_name: str) -> bool:
        # 실제 구현에서는 ModuleRegistry 연동 필요, 여기서는 항상 True
        return True

    async def execute(self, request: ExecRequest) -> ExecResult:
        start_time = time.time()
        # 모듈 레지스트리에서 코드 가져오기
        code = None
        print(f"DEBUG: module_registry 존재 여부: {self.module_registry is not None}", file=sys.stderr)
        print(f"DEBUG: request.module: {getattr(request, 'module', None)}", file=sys.stderr)
        
        if self.module_registry is not None and hasattr(request, 'module'):
            module_obj = await self.module_registry.get_module(request.module)
            print(f"DEBUG: module_registry.get_module 결과: {module_obj}", file=sys.stderr)
            if module_obj:
                try:
                    # AsyncSession 추출 (module_registry가 가지고 있는 db 세션 활용)
                    db = getattr(self.module_registry, 'db', None)
                    if db is not None:
                        # 활성화된 Deployment 찾기
                        result = await db.execute(
                            select(Deployment, Version)
                            .join(Version, Deployment.version_id == Version.id)
                            .where(Deployment.module_id == module_obj.id, Deployment.status == "active")
                        )
                        row = result.first()
                        if row and hasattr(row[1], 'code'):
                            code = row[1].code
                            print(f"DEBUG: 활성화된 버전에서 코드 가져옴, 길이: {len(code) if code else 0}", file=sys.stderr)
                    if not code and getattr(module_obj, 'code', None):
                        code = module_obj.code
                        print(f"DEBUG: 모듈에서 코드 가져옴(백업), 길이: {len(code) if code else 0}", file=sys.stderr)
                except Exception as e:
                    print(f"DEBUG: 활성화 버전 코드 조회 오류: {e}", file=sys.stderr)
                    if getattr(module_obj, 'code', None):
                        code = module_obj.code
        if not code:
            code = request.input_json.get("code", "")
            print(f"DEBUG: input_json에서 코드 가져옴, 길이: {len(code) if code else 0}", file=sys.stderr)
        old_stdout, old_stderr = sys.stdout, sys.stderr
        stdout_capture, stderr_capture = StringIO(), StringIO()
        sys.stdout, sys.stderr = stdout_capture, stderr_capture
        result_json = {}
        exit_code = 0
        env_vars = None  # 초기화
        env_path = None  # 초기화
        try:
            # 환경변수 주입 (os.environ만 사용, .env 파일 생성 X)
            original_env = os.environ.copy()
            if module_obj:
                try:
                    env_vars = getattr(module_obj, 'env_vars', None)
                    if env_vars:
                        for env_var in env_vars:
                            key = getattr(env_var, 'key', None)
                            value = getattr(env_var, 'value', None)
                            if key and value is not None:
                                os.environ[key] = str(value)
                    else:
                        env_vars = None
                except Exception as e:
                    env_vars = None
            else:
                env_vars = None
            
            # 샌드박싱: 문법 및 위험 코드 체크 (RestrictedPython 등은 추후)
            ast.parse(code)
            input_obj = request.input_json
            if isinstance(input_obj, str):
                try:
                    input_obj = json.loads(input_obj)
                except Exception:
                    input_obj = {}
            
            # 사용자 코드를 함수로 감싸기 (return 문 사용 가능하게, 들여쓰기 오류 방지)
            wrapped_code = f"""
def inline_main(input_data):
{chr(10).join(('    ' + line if line.strip() else '    ') for line in code.split(chr(10)))}
    return None  # 기본 반환값

# 함수 실행
result = inline_main({repr(input_obj)})
"""
            
            namespace = {"input": input_obj}
            exec(wrapped_code, namespace)
            
            # 결과 반환
            if "result" in namespace and namespace["result"] is not None:
                result_json = namespace["result"]
            elif stdout_capture.getvalue():
                result_json = {"stdout": stdout_capture.getvalue()}
            else:
                result_json = {}
        except Exception as e:
            exit_code = 1
            print(f"Error executing module: {str(e)}", file=sys.stderr)
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
            # 환경변수 복원
            try:
                if env_vars:
                    os.environ.clear()
                    os.environ.update(original_env)
            except Exception as e:
                print(f"DEBUG: 환경변수 복원 오류: {e}", file=sys.stderr)
        duration = time.time() - start_time
        
        # result_json이 dict가 아닌 경우 적절히 변환
        if not isinstance(result_json, dict):
            if result_json is None:
                result_json = {}
            else:
                result_json = {"result": result_json}
        
        return ExecResult(
            result_json=result_json,
            exit_code=exit_code,
            stderr=stderr_capture.getvalue(),
            stdout=stdout_capture.getvalue(),
            duration=duration
        )

    async def cleanup(self) -> None:
        pass 