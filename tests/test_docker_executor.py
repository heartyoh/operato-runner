import os
import sys
import tempfile
import json
import pytest
import types
from unittest import mock
from models import ExecRequest, ExecResult, Module
from module_registry import ModuleRegistry
from executors.docker import DockerExecutor
import asyncio

@pytest.fixture
def dummy_module(tmp_path):
    code = """
def handler(input_json):
    return {"echo": input_json["value"]}
"""
    module_path = tmp_path / "mod.py"
    with open(module_path, "w") as f:
        f.write(code)
    return Module(
        name="testmod",
        env="docker",
        code=code,
        path=str(module_path),
        version="0.1.0",
        tags=[]
    )

@pytest.fixture
def module_registry(dummy_module, tmp_path):
    config_path = tmp_path / "modules.yaml"
    reg = ModuleRegistry(config_path=str(config_path))
    reg.modules[dummy_module.name] = dummy_module
    return reg

@pytest.mark.asyncio
async def test_validate_success(monkeypatch, module_registry):
    class DummyContainers:
        def run(self, *a, **k): pass
    class DummyClient:
        def __init__(self):
            self.containers = DummyContainers()
        def ping(self): return True
    executor = DockerExecutor(module_registry)
    executor.client = DummyClient()
    assert await executor.validate("testmod")

@pytest.mark.asyncio
async def test_validate_fail(monkeypatch, module_registry):
    class DummyContainers:
        def run(self, *a, **k): pass
    class DummyClient:
        def __init__(self):
            self.containers = DummyContainers()
        def ping(self): raise Exception("fail")
    executor = DockerExecutor(module_registry)
    executor.client = DummyClient()
    assert not await executor.validate("testmod")

@pytest.mark.asyncio
async def test_execute_success(monkeypatch, module_registry, dummy_module, tmp_path):
    class DummyContainer:
        def wait(self, timeout): return {"StatusCode": 0}
        def logs(self, stdout, stderr): return b"ok"
        def remove(self, force): pass
    class DummyContainers:
        def run(self, *a, **k): return DummyContainer()
    class DummyClient:
        def __init__(self):
            self.containers = DummyContainers()
    executor = DockerExecutor(module_registry)
    executor.client = DummyClient()
    req = ExecRequest(module="testmod", input_json={"value": 123})
    with mock.patch("docker.from_env", return_value=DummyClient()):
        result = await executor.execute(req)
    assert result.exit_code == 0
    assert result.stderr == ""
    assert result.result_json == {} or isinstance(result.result_json, dict)

@pytest.mark.asyncio
async def test_execute_error(monkeypatch, module_registry, dummy_module):
    class DummyContainer:
        def wait(self, timeout): raise Exception("fail")
        def remove(self, force): pass
    class DummyContainers:
        def run(self, *a, **k): return DummyContainer()
    class DummyClient:
        def __init__(self):
            self.containers = DummyContainers()
    executor = DockerExecutor(module_registry)
    executor.client = DummyClient()
    req = ExecRequest(module="testmod", input_json={"value": 1})
    with mock.patch("docker.from_env", return_value=DummyClient()):
        result = await executor.execute(req)
    assert result.exit_code == 1
    assert "Error executing module" in result.stderr

@pytest.mark.asyncio
async def test_cleanup(monkeypatch):
    class DummyContainer:
        def remove(self, force): pass
    class DummyContainers:
        def list(self, all, filters): return [DummyContainer()]
    class DummyClient:
        def __init__(self):
            self.containers = DummyContainers()
    executor = DockerExecutor()
    executor.client = DummyClient()
    await executor.cleanup() 