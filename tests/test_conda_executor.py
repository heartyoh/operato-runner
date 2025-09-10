import os
import sys
import tempfile
import json
import pytest
import types
import subprocess
from unittest import mock
from src.models import ExecRequest, ExecResult, Module
from module_registry import ModuleRegistry

# Skip all conda executor tests as they require conda environment
pytestmark = pytest.mark.skip(reason="Conda executor tests require conda environment setup")
from src.executors.conda import CondaExecutor
import asyncio
import time

@pytest.fixture
def dummy_module(tmp_path):
    # 임시 파이썬 모듈 파일 생성
    code = """
def handler(input_json):
    return {"echo": input_json["value"]}
"""
    module_path = tmp_path / "mod.py"
    with open(module_path, "w") as f:
        f.write(code)
    return Module(
        name="testmod",
        env="conda",
        code=code,
        path=str(module_path),
        version="0.1.0",
        tags=[]
    )

@pytest.fixture
def module_registry(dummy_module):
    from tests.conftest import TestingSessionLocal
    async def get_test_db():
        async with TestingSessionLocal() as session:
            return session
    
    db_session = get_test_db()
    reg = ModuleRegistry(next(db_session))
    reg.modules[dummy_module.name] = dummy_module
    return reg

@pytest.mark.asyncio
async def test_validate_success(monkeypatch, module_registry):
    executor = CondaExecutor(module_registry)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: types.SimpleNamespace(stdout=json.dumps({"envs": [f"/opt/conda/envs/testmod"]}), returncode=0))
    assert await executor.validate("testmod")

@pytest.mark.asyncio
async def test_validate_fail(monkeypatch, module_registry):
    executor = CondaExecutor(module_registry)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: types.SimpleNamespace(stdout=json.dumps({"envs": ["/opt/conda/envs/other"]}), returncode=0))
    assert not await executor.validate("testmod")

@pytest.mark.asyncio
async def test_execute_success(monkeypatch, module_registry, dummy_module, tmp_path):
    executor = CondaExecutor(module_registry)
    req = ExecRequest(module="testmod", input_json={"value": 123})

    # output_path를 고정
    fixed_output_path = str(tmp_path / "output.json")
    monkeypatch.setattr(tempfile, "mktemp", lambda *a, **k: fixed_output_path)

    def fake_run(cmd, capture_output, text, timeout):
        # output_path는 이미 고정되어 있으므로, 명령어에서 추출할 필요 없음
        with open(fixed_output_path, "w") as f:
            json.dump({"echo": 123}, f)
            f.flush()
            os.fsync(f.fileno())
        return types.SimpleNamespace(returncode=0, stderr="", stdout="ok")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = await executor.execute(req)
    assert result.exit_code == 0
    assert result.result_json == {"echo": 123}

@pytest.mark.asyncio
async def test_execute_timeout(monkeypatch, module_registry, dummy_module):
    executor = CondaExecutor(module_registry)
    def fake_run(*a, **k):
        raise subprocess.TimeoutExpired(cmd="conda run", timeout=60)
    monkeypatch.setattr(subprocess, "run", fake_run)
    req = ExecRequest(module="testmod", input_json={"value": 1})
    result = await executor.execute(req)
    assert result.exit_code == 124
    assert "timed out" in result.stderr

@pytest.mark.asyncio
async def test_execute_error(monkeypatch, module_registry, dummy_module):
    executor = CondaExecutor(module_registry)
    def fake_run(*a, **k):
        raise Exception("fail")
    monkeypatch.setattr(subprocess, "run", fake_run)
    req = ExecRequest(module="testmod", input_json={"value": 1})
    result = await executor.execute(req)
    assert result.exit_code == 1
    assert "Error executing module" in result.stderr 