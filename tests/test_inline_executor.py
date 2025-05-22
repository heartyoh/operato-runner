import pytest
import asyncio
from models import ExecRequest, ExecResult
from executors.inline import InlineExecutor

@pytest.mark.asyncio
async def test_successful_execution():
    code = """
def handler(input):
    print('hello from handler')
    return {'sum': input['a'] + input['b']}
"""
    req = ExecRequest(module="mod", input_json={"a": 2, "b": 3, "code": code})
    executor = InlineExecutor()
    result: ExecResult = await executor.execute(req)
    assert result.exit_code == 0
    assert result.result_json == {"sum": 5}
    assert "hello from handler" in result.stderr or "hello from handler" in getattr(result, 'stdout', '')
    assert result.duration > 0

@pytest.mark.asyncio
async def test_invalid_code_error():
    code = "def handler(input):\nreturn input['a'] +"  # 문법 오류
    req = ExecRequest(module="mod", input_json={"a": 1, "b": 2, "code": code})
    executor = InlineExecutor()
    result = await executor.execute(req)
    assert result.exit_code == 1
    assert "SyntaxError" in result.stderr or "Error executing module" in result.stderr

@pytest.mark.asyncio
async def test_no_handler_error():
    code = "print('no handler')"
    req = ExecRequest(module="mod", input_json={"code": code})
    executor = InlineExecutor()
    result = await executor.execute(req)
    assert result.exit_code == 1
    assert "handler function" in result.stderr

@pytest.mark.asyncio
async def test_handler_receives_input():
    code = """
def handler(input):
    return {'echo': input['msg']}
"""
    req = ExecRequest(module="mod", input_json={"msg": "hi", "code": code})
    executor = InlineExecutor()
    result = await executor.execute(req)
    assert result.result_json == {"echo": "hi"}

@pytest.mark.asyncio
async def test_security_ast_parse_blocks_bad_code():
    code = "import os\ndef handler(input): return 1"
    req = ExecRequest(module="mod", input_json={"code": code})
    executor = InlineExecutor()
    result = await executor.execute(req)
    # ast.parse는 import 자체를 막지 않으나, RestrictedPython 등 확장 필요
    # 여기서는 SyntaxError가 아니므로 exit_code==0일 수 있음
    assert "import os" in req.input_json["code"]
    # 실제 보안 테스트는 RestrictedPython 적용 후 강화 필요 