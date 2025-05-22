import ast
import sys
from io import StringIO
import time
from executors.base import Executor
from module_models import ExecRequest, ExecResult

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
        if self.module_registry is not None and hasattr(request, 'module'):
            module_obj = self.module_registry.get_module(request.module)
            if module_obj and getattr(module_obj, 'code', None):
                code = module_obj.code
        if not code:
            code = request.input_json.get("code", "")
        old_stdout, old_stderr = sys.stdout, sys.stderr
        stdout_capture, stderr_capture = StringIO(), StringIO()
        sys.stdout, sys.stderr = stdout_capture, stderr_capture
        result_json = {}
        exit_code = 0
        try:
            # 샌드박싱: 문법 및 위험 코드 체크 (RestrictedPython 등은 추후)
            ast.parse(code)
            namespace = {"input": request.input_json}
            exec(code, namespace)
            if "handler" in namespace and callable(namespace["handler"]):
                handler_result = namespace["handler"](request.input_json)
                if not isinstance(handler_result, dict):
                    handler_result = {"result": handler_result}
                result_json = handler_result
            else:
                raise ValueError("Module must define a handler function")
        except Exception as e:
            exit_code = 1
            print(f"Error executing module: {str(e)}", file=sys.stderr)
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
        duration = time.time() - start_time
        return ExecResult(
            result_json=result_json,
            exit_code=exit_code,
            stderr=stderr_capture.getvalue(),
            stdout=stdout_capture.getvalue(),
            duration=duration
        )

    async def cleanup(self) -> None:
        pass 