from typing import Dict, List, Any, Optional
from executors.base import Executor
from executors.inline import InlineExecutor
from executors.venv import VenvExecutor
from module_registry import ModuleRegistry
from models import ExecRequest, ExecResult

class ExecutorManager:
    def __init__(self, module_registry: ModuleRegistry):
        self.module_registry = module_registry
        self.executors: Dict[str, Executor] = {}

    async def execute(self, request: ExecRequest) -> ExecResult:
        module_name = request.module
        module = await self.module_registry.get_module(module_name)
        if not module:
            return ExecResult(
                result_json={},
                exit_code=1,
                stderr=f"Module '{module_name}' not found",
                stdout="",
                duration=0
            )
        executor = self.executors.get(module.env)
        if not executor:
            return ExecResult(
                result_json={},
                exit_code=1,
                stderr=f"No executor available for environment '{module.env}'",
                stdout="",
                duration=0
            )
        if not await executor.validate(module_name):
            return ExecResult(
                result_json={},
                exit_code=1,
                stderr=f"Module '{module_name}' cannot be executed in environment '{module.env}'",
                stdout="",
                duration=0
            )
        return await executor.execute(request)

    def register_executor(self, env: str, executor: Executor) -> None:
        self.executors[env] = executor

    def get_available_environments(self) -> List[str]:
        return list(self.executors.keys())

    async def cleanup(self) -> None:
        for executor in self.executors.values():
            await executor.cleanup()

    async def cleanup_module_uv(self, name: str) -> None:
        """uv 환경의 가상환경 폴더(module_envs/{name}/uv)를 안전하게 삭제"""
        import shutil, os, logging
        uv_dir = os.path.abspath(os.path.join("module_envs", name, "uv"))
        if os.path.exists(uv_dir):
            try:
                shutil.rmtree(uv_dir)
                logging.info(f"[cleanup_module_uv] {uv_dir} 삭제 완료")
            except Exception as e:
                logging.warning(f"[cleanup_module_uv] {uv_dir} 삭제 실패: {str(e)}")

    async def cleanup_module_venv(self, name: str) -> None:
        """venv 환경의 가상환경 폴더(module_envs/{name}/venv)를 안전하게 삭제"""
        import shutil, os, logging, psutil, glob
        venv_dir = os.path.abspath(os.path.join("module_envs", name, "venv"))
        # 1. 실행 중인 프로세스 종료
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if venv_dir in ' '.join(proc.info.get('cmdline', [])):
                    proc.kill()
                    logging.info(f"[cleanup_module_venv] 프로세스 종료: {proc.info}")
            except Exception as e:
                logging.warning(f"[cleanup_module_venv] 프로세스 종료 실패: {str(e)}")
        # 2. 임시/캐시 파일 정리
        temp_patterns = ['*.lock', '*.tmp', '__pycache__', '.cache', '.mypy_cache']
        for pattern in temp_patterns:
            for path in glob.glob(os.path.join(venv_dir, '**', pattern), recursive=True):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    logging.info(f"[cleanup_module_venv] 임시파일 삭제: {path}")
                except Exception as e:
                    logging.warning(f"[cleanup_module_venv] 임시파일 삭제 실패: {path}, {str(e)}")
        # 3. venv 폴더 삭제
        if os.path.exists(venv_dir):
            try:
                shutil.rmtree(venv_dir)
                logging.info(f"[cleanup_module_venv] {venv_dir} 삭제 완료")
            except Exception as e:
                logging.warning(f"[cleanup_module_venv] {venv_dir} 삭제 실패: {str(e)}")

    async def cleanup_module_conda(self, name: str) -> None:
        """conda 환경의 가상환경 폴더(module_envs/{name}/conda_env)를 안전하게 삭제"""
        import shutil, os, logging, psutil, glob, subprocess
        conda_env_dir = os.path.abspath(os.path.join("module_envs", name, "conda_env"))
        # 1. 실행 중인 프로세스 종료
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if conda_env_dir in ' '.join(proc.info.get('cmdline', [])):
                    proc.kill()
                    logging.info(f"[cleanup_module_conda] 프로세스 종료: {proc.info}")
            except Exception as e:
                logging.warning(f"[cleanup_module_conda] 프로세스 종료 실패: {str(e)}")
        # 2. 임시/캐시 파일 정리
        temp_patterns = ['*.lock', '*.tmp', '__pycache__', '.cache', '.mypy_cache']
        for pattern in temp_patterns:
            for path in glob.glob(os.path.join(conda_env_dir, '**', pattern), recursive=True):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    logging.info(f"[cleanup_module_conda] 임시파일 삭제: {path}")
                except Exception as e:
                    logging.warning(f"[cleanup_module_conda] 임시파일 삭제 실패: {path}, {str(e)}")
        # 3. conda 환경 삭제 (conda 명령어)
        try:
            subprocess.run(["conda", "remove", "-y", "-p", conda_env_dir, "--all"], check=False)
            logging.info(f"[cleanup_module_conda] conda remove 명령 실행: {conda_env_dir}")
        except Exception as e:
            logging.warning(f"[cleanup_module_conda] conda remove 명령 실패: {str(e)}")
        # 4. 폴더 삭제
        if os.path.exists(conda_env_dir):
            try:
                shutil.rmtree(conda_env_dir)
                logging.info(f"[cleanup_module_conda] {conda_env_dir} 삭제 완료")
            except Exception as e:
                logging.warning(f"[cleanup_module_conda] {conda_env_dir} 삭제 실패: {str(e)}") 