import os
import tempfile
import yaml
import pytest
import pytest_asyncio
from datetime import datetime
from module_registry import ModuleRegistry
from src.models import Module, ModuleSchema
from conftest import TestingSessionLocal

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

@pytest.mark.asyncio
async def test_register_and_get_module():
    async with TestingSessionLocal() as session:
        reg = ModuleRegistry(db=session)
        
        # ModuleSchema를 Module ORM 객체로 변환
        module_data = make_module("mod1", env="venv", tags=["t1"])
        module = Module(
            name=module_data.name,
            code=module_data.code,
            env=module_data.env,
            version=module_data.version,
            tags=",".join(module_data.tags)  # tags를 문자열로 저장
        )
        
        await reg.register_module(module)
        loaded = await reg.get_module("mod1")
        assert loaded is not None
        assert loaded.name == "mod1"
        assert loaded.env == "venv"

@pytest.mark.asyncio
async def test_list_modules():
    async with TestingSessionLocal() as session:
        reg = ModuleRegistry(db=session)
        
        # 두 개의 모듈 등록
        for name in ["mod1", "mod2"]:
            module_data = make_module(name)
            module = Module(
                name=module_data.name,
                code=module_data.code,
                env=module_data.env,
                version=module_data.version
            )
            await reg.register_module(module)
        
        mods = await reg.list_modules()
        assert len(mods) == 2

@pytest.mark.asyncio
async def test_delete_module():
    async with TestingSessionLocal() as session:
        reg = ModuleRegistry(db=session)
        
        # 모듈 등록
        module_data = make_module("mod1")
        module = Module(
            name=module_data.name,
            code=module_data.code,
            env=module_data.env,
            version=module_data.version
        )
        await reg.register_module(module)
        
        # 삭제 테스트
        assert await reg.delete_module("mod1")
        assert await reg.get_module("mod1") is None
        assert not await reg.delete_module("notfound")

@pytest.mark.asyncio
async def test_get_modules_by_env_and_tag():
    async with TestingSessionLocal() as session:
        reg = ModuleRegistry(db=session)
        
        # 두 개의 다른 환경/태그 모듈 등록
        mod1_data = make_module("mod1", env="venv", tags=["a"])
        mod1 = Module(
            name=mod1_data.name,
            code=mod1_data.code,
            env=mod1_data.env,
            version=mod1_data.version,
            tags=",".join(mod1_data.tags)
        )
        await reg.register_module(mod1)
        
        mod2_data = make_module("mod2", env="inline", tags=["b"])
        mod2 = Module(
            name=mod2_data.name,
            code=mod2_data.code,
            env=mod2_data.env,
            version=mod2_data.version,
            tags=",".join(mod2_data.tags)
        )
        await reg.register_module(mod2)
        
        # 환경별/태그별 조회 테스트
        venv_mods = await reg.get_modules_by_env("venv")
        assert len(venv_mods) == 1 and venv_mods[0].name == "mod1"
        tag_mods = await reg.get_modules_by_tag("b")
        assert len(tag_mods) == 1 and tag_mods[0].name == "mod2"

@pytest.mark.asyncio
async def test_db_persistence():
    # 데이터베이스 지속성 테스트
    async with TestingSessionLocal() as session:
        reg = ModuleRegistry(db=session)
        
        module_data = make_module("mod1", env="venv", tags=["t1"])
        module = Module(
            name=module_data.name,
            code=module_data.code,
            env=module_data.env,
            version=module_data.version,
            tags=",".join(module_data.tags)
        )
        await reg.register_module(module)
        
        # 같은 세션에서 조회
        loaded = await reg.get_module("mod1")
        assert loaded is not None
        assert loaded.env == "venv"

@pytest.mark.asyncio
async def test_empty_registry():
    # 빈 레지스트리 테스트 (새 세션 사용으로 격리)
    async with TestingSessionLocal() as session:
        reg = ModuleRegistry(db=session)
        
        # 먼저 기존 모든 모듈 삭제로 깨끗한 상태 만들기
        existing_modules = await reg.list_modules()
        for module in existing_modules:
            await reg.delete_module(module.name)
        
        # 이제 빈 상태 확인
        modules = await reg.list_modules()
        assert len(modules) == 0 