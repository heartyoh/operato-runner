import pytest
from models import Module, ExecRequest, ExecResult
from datetime import datetime
from pydantic import ValidationError

# 1. Module 모델 테스트
def test_module_creation():
    m = Module(name="testmod", env="inline", code="print('hi')", version="1.0.0", tags=["test"])
    assert m.name == "testmod"
    assert m.env == "inline"
    assert m.code == "print('hi')"
    assert m.version == "1.0.0"
    assert m.tags == ["test"]
    assert isinstance(m.created_at, datetime)
    assert str(m).startswith("Module(testmod, inline")

def test_module_validation_error():
    with pytest.raises(ValidationError):
        Module(name=123, env=456)  # 잘못된 타입

def test_module_json_serialization():
    m = Module(name="mod", env="venv")
    data = m.json()
    m2 = Module.parse_raw(data)
    assert m2.name == "mod"
    assert m2.env == "venv"

def test_module_default_values():
    m = Module(name="mod2", env="docker")
    assert m.version == "0.1.0"
    assert m.tags == []

# 2. ExecRequest 테스트
def test_exec_request_creation():
    req = ExecRequest(module="mod", input_json={"x": 1})
    assert req.module == "mod"
    assert req.input_json["x"] == 1

def test_exec_request_validation_error():
    with pytest.raises(ValidationError):
        ExecRequest(module=123, input_json="notadict")

# 3. ExecResult 테스트
def test_exec_result_creation():
    res = ExecResult(result_json={"y": 2}, exit_code=0, duration=1.23)
    assert res.result_json["y"] == 2
    assert res.exit_code == 0
    assert res.duration == 1.23
    assert res.stderr is None

def test_exec_result_validation_error():
    with pytest.raises(ValidationError):
        ExecResult(result_json="notadict", exit_code="fail", duration="fast") 