from typing import List, Optional
from models.module import Module
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
import os, shutil

class ModuleRegistry:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_module(self, name: str) -> Optional[Module]:
        result = await self.db.execute(select(Module).where(Module.name == name))
        return result.scalars().first()

    async def list_modules(self) -> List[Module]:
        result = await self.db.execute(select(Module))
        return result.scalars().all()

    async def register_module(self, module: Module) -> None:
        # upsert: name이 있으면 update, 없으면 insert
        existing = await self.get_module(module.name)
        if existing:
            for attr in ["description", "code", "path", "version", "tags", "owner_id"]:
                setattr(existing, attr, getattr(module, attr))
            await self.db.commit()
        else:
            self.db.add(module)
            await self.db.commit()

    async def delete_module(self, name: str) -> bool:
        result = await self.db.execute(select(Module).where(Module.name == name))
        module = result.scalars().first()
        if module:
            # venv 타입이면 환경/모듈 폴더 삭제
            if module.env == "venv":
                venv_dir = os.path.abspath(os.path.join("module_envs", name, "venv"))
                module_env_dir = os.path.abspath(os.path.join("module_envs", name))
                modules_dir = os.path.abspath(os.path.join("modules", name))
                # 1. venv 프로세스 종료 (ExecutorManager가 있으면 활용)
                if hasattr(self, "executor_manager") and self.executor_manager:
                    await self.executor_manager.cleanup_module_venv(name)
                # 2. venv 폴더 삭제
                if os.path.exists(module_env_dir):
                    try:
                        shutil.rmtree(module_env_dir)
                    except Exception:
                        pass
                # 3. modules/{name} 폴더 삭제
                if os.path.exists(modules_dir):
                    try:
                        shutil.rmtree(modules_dir)
                    except Exception:
                        pass
            await self.db.delete(module)
            await self.db.flush()  # 자식 레코드 삭제 보장
            await self.db.commit()
            return True
        return False

    async def get_modules_by_env(self, env: str) -> List[Module]:
        result = await self.db.execute(select(Module).where(Module.env == env))
        return result.scalars().all()

    async def get_modules_by_tag(self, tag: str) -> List[Module]:
        result = await self.db.execute(select(Module))
        return [m for m in result.scalars().all() if m.tags and tag in m.tags]

    async def get_versions(self, name: str):
        module = await self.get_module(name)
        if not module:
            return []
        return module.versions

    # 롤백/활성화/비활성화/이력 관련 메서드는 FastAPI에서 직접 처리하므로, 필요시 여기에 추가 구현 가능 