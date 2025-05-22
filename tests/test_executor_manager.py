import pytest
import asyncio
from executor_manager import ExecutorManager
from module_registry import ModuleRegistry
from models import Module, ExecRequest, ExecResult
from datetime import datetime
from executors.base import Executor

class DummyExecutor(Executor):
    def __init__(self, result=None, valid=True):
        self._result = result or ExecResult(result_json={"ok": True}, exit_code=0, stderr="", stdout="", duration=0.01)
        self._valid = valid
        self.executed = False
    async def execute(self, request):
        self.executed = True
        return self._result
    async def validate(self, module_name):
        return self._valid
    async def cleanup(self):
        self.executed = False
    @property
    def executor_type(self):
        return "dummy"

def make_module(name, env="inline"):
    return Module(
        name=name,
        env=env,
        code="print('hi')",
        path=None,
        created_at=datetime.now(),
        version="1.0.0",
        tags=[]
    )

@pytest.mark.asyncio
async def test_routing_to_correct_executor():
    reg = ModuleRegistry(config_path=":memory:")
    mod = make_module("mod1", env="dummy")
    reg.register_module(mod)
    mgr = ExecutorManager(reg)
    dummy = DummyExecutor()
    mgr.register_executor("dummy", dummy)
    req = ExecRequest(module="mod1", input_json={})
    result = await mgr.execute(req)
    assert dummy.executed
    assert result.result_json["ok"] is True

@pytest.mark.asyncio
async def test_error_missing_module():
    reg = ModuleRegistry(config_path=":memory:")
    mgr = ExecutorManager(reg)
    req = ExecRequest(module="notfound", input_json={})
    result = await mgr.execute(req)
    assert result.exit_code == 1
    assert "not found" in result.stderr

@pytest.mark.asyncio
async def test_error_missing_executor():
    reg = ModuleRegistry(config_path=":memory:")
    mod = make_module("mod2", env="notexist")
    reg.register_module(mod)
    mgr = ExecutorManager(reg)
    req = ExecRequest(module="mod2", input_json={})
    result = await mgr.execute(req)
    assert result.exit_code == 1
    assert "No executor available" in result.stderr

@pytest.mark.asyncio
async def test_validation_failure():
    reg = ModuleRegistry(config_path=":memory:")
    mod = make_module("mod3", env="dummy")
    reg.register_module(mod)
    mgr = ExecutorManager(reg)
    dummy = DummyExecutor(valid=False)
    mgr.register_executor("dummy", dummy)
    req = ExecRequest(module="mod3", input_json={})
    result = await mgr.execute(req)
    assert result.exit_code == 1
    assert "cannot be executed" in result.stderr

@pytest.mark.asyncio
async def test_register_executor_and_environments():
    reg = ModuleRegistry(config_path=":memory:")
    mgr = ExecutorManager(reg)
    dummy = DummyExecutor()
    mgr.register_executor("dummy", dummy)
    envs = mgr.get_available_environments()
    assert "dummy" in envs

@pytest.mark.asyncio
async def test_cleanup_all_executors():
    reg = ModuleRegistry(config_path=":memory:")
    mgr = ExecutorManager(reg)
    dummy = DummyExecutor()
    mgr.register_executor("dummy", dummy)
    dummy.executed = True
    await mgr.cleanup()
    assert not dummy.executed 