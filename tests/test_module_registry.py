import os
import tempfile
import yaml
import pytest
from datetime import datetime
from module_registry import ModuleRegistry
from models import ModuleSchema

def make_module(name, env="inline", tags=None):
    return ModuleSchema(
        name=name,
        env=env,
        code="print('hi')",
        path=None,
        created_at=datetime.now(),
        version="1.0.0",
        tags=tags or []
    )

def test_register_and_get_module():
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tf:
        reg = ModuleRegistry(config_path=tf.name)
        m = make_module("mod1", env="venv", tags=["t1"])
        reg.register_module(m)
        loaded = reg.get_module("mod1")
        assert loaded is not None
        assert loaded.name == "mod1"
        assert loaded.env == "venv"
        assert "t1" in loaded.tags
        os.unlink(tf.name)

def test_list_modules():
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tf:
        reg = ModuleRegistry(config_path=tf.name)
        reg.register_module(make_module("mod1"))
        reg.register_module(make_module("mod2"))
        mods = reg.list_modules()
        assert len(mods) == 2
        os.unlink(tf.name)

def test_delete_module():
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tf:
        reg = ModuleRegistry(config_path=tf.name)
        reg.register_module(make_module("mod1"))
        assert reg.delete_module("mod1")
        assert reg.get_module("mod1") is None
        assert not reg.delete_module("notfound")
        os.unlink(tf.name)

def test_get_modules_by_env_and_tag():
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tf:
        reg = ModuleRegistry(config_path=tf.name)
        reg.register_module(make_module("mod1", env="venv", tags=["a"]))
        reg.register_module(make_module("mod2", env="inline", tags=["b"]))
        venv_mods = reg.get_modules_by_env("venv")
        assert len(venv_mods) == 1 and venv_mods[0].name == "mod1"
        tag_mods = reg.get_modules_by_tag("b")
        assert len(tag_mods) == 1 and tag_mods[0].name == "mod2"
        os.unlink(tf.name)

def test_yaml_persistence():
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tf:
        reg = ModuleRegistry(config_path=tf.name)
        m = make_module("mod1", env="venv", tags=["t1"])
        reg.register_module(m)
        # 새 인스턴스에서 불러오기
        reg2 = ModuleRegistry(config_path=tf.name)
        loaded = reg2.get_module("mod1")
        assert loaded is not None
        assert loaded.env == "venv"
        os.unlink(tf.name)

def test_invalid_yaml():
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False, mode='w') as tf:
        tf.write("not: [valid: yaml: - here]")
    reg = ModuleRegistry(config_path=tf.name)
    # 에러 발생해도 예외로 죽지 않고, modules는 비어 있어야 함
    assert reg.list_modules() == []
    os.unlink(tf.name) 