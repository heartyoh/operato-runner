import pytest
import asyncio
import time
from retry_policy import RetryPolicy, RetryableExecutorManager
from models import ExecRequest, ExecResult

@pytest.mark.asyncio
async def test_success_no_retry():
    calls = []
    async def func(x):
        calls.append(x)
        return x * 2
    policy = RetryPolicy(max_retries=2, delay=0.01)
    result = await policy.execute_with_retry(func, 3)
    assert result == 6
    assert calls == [3]

@pytest.mark.asyncio
async def test_retry_then_success():
    calls = []
    async def func(x):
        if len(calls) < 2:
            calls.append('fail')
            raise ValueError("fail")
        calls.append(x)
        return x * 2
    policy = RetryPolicy(max_retries=3, delay=0.01)
    result = await policy.execute_with_retry(func, 5)
    assert result == 10
    assert calls == ['fail', 'fail', 5]

@pytest.mark.asyncio
async def test_give_up_after_max_retries():
    calls = []
    async def func(x):
        calls.append('fail')
        raise RuntimeError("always fail")
    policy = RetryPolicy(max_retries=2, delay=0.01)
    with pytest.raises(RuntimeError):
        await policy.execute_with_retry(func, 1)
    assert calls == ['fail', 'fail', 'fail']

@pytest.mark.asyncio
async def test_backoff_delay(monkeypatch):
    delays = []
    orig_sleep = asyncio.sleep
    async def fake_sleep(secs):
        delays.append(secs)
        await orig_sleep(0)  # 실제로는 바로 통과
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    calls = []
    async def func():
        if len(calls) < 3:
            calls.append('fail')
            raise Exception("fail")
        return 42
    policy = RetryPolicy(max_retries=3, delay=0.1, backoff_factor=2)
    result = await policy.execute_with_retry(func)
    assert result == 42
    assert delays == [0.1, 0.2, 0.4]

@pytest.mark.asyncio
async def test_retryable_executor_manager_success():
    class DummyExecutorManager:
        def __init__(self):
            self.calls = []
        async def execute(self, req):
            self.calls.append(req.input_json["v"])
            if len(self.calls) < 2:
                raise Exception("fail")
            return ExecResult(result_json={"ok": True}, exit_code=0, stderr="", stdout="", duration=0.1)
        def register_executor(self, env, executor): pass
        def get_available_environments(self): return ["inline"]
        async def cleanup(self): pass
    mgr = DummyExecutorManager()
    retry_mgr = RetryableExecutorManager(mgr, RetryPolicy(max_retries=2, delay=0.01))
    req = ExecRequest(module="mod", input_json={"v": 1})
    result = await retry_mgr.execute(req)
    assert result.exit_code == 0
    assert result.result_json["ok"] is True
    assert mgr.calls == [1, 1]

@pytest.mark.asyncio
async def test_retryable_executor_manager_fail():
    class DummyExecutorManager:
        async def execute(self, req):
            raise Exception("fail")
        def register_executor(self, env, executor): pass
        def get_available_environments(self): return ["inline"]
        async def cleanup(self): pass
    mgr = DummyExecutorManager()
    retry_mgr = RetryableExecutorManager(mgr, RetryPolicy(max_retries=1, delay=0.01))
    req = ExecRequest(module="mod", input_json={})
    result = await retry_mgr.execute(req)
    assert result.exit_code == 1
    assert "Failed after 1 retries" in result.stderr 