import os
import tempfile
import pytest
import json
from execution_history import ExecutionHistory
from models import ExecResult

@pytest.fixture
def temp_db_path(tmp_path):
    return str(tmp_path / "test_exec_history.db")

@pytest.fixture
def exec_history(temp_db_path):
    return ExecutionHistory(db_path=temp_db_path)

@pytest.fixture
def sample_result():
    return ExecResult(
        result_json={"out": 1},
        exit_code=0,
        stderr="",
        stdout="ok",
        duration=0.5
    )

def test_db_init(exec_history):
    # DB 파일이 생성되고 테이블이 존재해야 함
    assert os.path.exists(exec_history.db_path)
    # 테이블 존재 확인
    import sqlite3
    conn = sqlite3.connect(exec_history.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='executions'")
    assert cursor.fetchone() is not None
    conn.close()

def test_record_and_get(exec_history, sample_result):
    eid = exec_history.record_execution("mod1", {"x": 1}, sample_result)
    row = exec_history.get_execution(eid)
    assert row["module_name"] == "mod1"
    assert row["input_json"] == {"x": 1}
    assert row["result_json"] == {"out": 1}
    assert row["exit_code"] == 0
    assert row["stdout"] == "ok"
    assert row["stderr"] == ""

def test_list_executions(exec_history, sample_result):
    for i in range(5):
        exec_history.record_execution("modA", {"i": i}, sample_result)
    for i in range(3):
        exec_history.record_execution("modB", {"i": i}, sample_result)
    all_rows = exec_history.list_executions()
    assert len(all_rows) == 8
    modA_rows = exec_history.list_executions(module_name="modA")
    assert len(modA_rows) == 5
    modB_rows = exec_history.list_executions(module_name="modB")
    assert len(modB_rows) == 3
    # pagination
    paged = exec_history.list_executions(limit=2, offset=1)
    assert len(paged) == 2

def test_get_module_stats(exec_history, sample_result):
    # 성공 3, 실패 2
    for i in range(3):
        exec_history.record_execution("modC", {"i": i}, sample_result)
    fail_result = ExecResult(result_json={}, exit_code=1, stderr="fail", stdout="", duration=1.0)
    for i in range(2):
        exec_history.record_execution("modC", {"i": i}, fail_result)
    stats = exec_history.get_module_stats("modC")
    assert stats["total_executions"] == 5
    assert stats["successful_executions"] == 3
    assert stats["failed_executions"] == 2
    assert stats["success_rate"] == 60.0
    assert stats["min_duration"] == 0.5
    assert stats["max_duration"] == 1.0
    assert stats["avg_duration"] > 0.5 and stats["avg_duration"] < 1.0 