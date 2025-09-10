from typing import Dict, List, Any, Optional
import asyncio
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor
from executors.base import Executor
from executors.inline import InlineExecutor
from executors.venv import VenvExecutor
from module_registry import ModuleRegistry
from models import ExecRequest, ExecResult
import logging

logger = logging.getLogger(__name__)

class ExecutorManager:
    def __init__(self, module_registry: ModuleRegistry, max_workers: int = 4):
        self.module_registry = module_registry
        self.executors: Dict[str, Executor] = {}
        # ProcessPoolExecutor 초기화
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers)
        self.max_workers = max_workers
        logger.info(f"ExecutorManager initialized with {max_workers} worker processes")

    @staticmethod
    def _execute_sync(request_dict: dict, module_registry_config: dict) -> dict:
        """동기 실행 함수 - 별도 프로세스에서 실행될 함수 (static method)"""
        import asyncio
        
        # 새 이벤트 루프 생성 (프로세스 내에서)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(
                ExecutorManager._execute_in_process_static(request_dict, module_registry_config)
            )
        finally:
            loop.close()
    
    @staticmethod
    async def _execute_in_process_static(request_dict: dict, module_registry_config: dict) -> dict:
        """프로세스 내에서 실행되는 비동기 함수 (static method)"""
        from core.db import get_sessionmaker, init_engine
        from module_registry import ModuleRegistry
        from executors.inline import InlineExecutor
        from executors.venv import VenvExecutor  
        from executors.conda import CondaExecutor
        from executors.uv import UvExecutor
        from models import ExecRequest
        
        # 프로세스에서 DB 엔진 초기화
        init_engine()
        
        # DB 세션 및 모듈 레지스트리 재구성
        SessionLocal = get_sessionmaker()
        async with SessionLocal() as db:
            module_registry = ModuleRegistry(db)
            
            # executors 재구성 (필요한 것만)
            executors = {
                "inline": InlineExecutor(module_registry),
                "venv": VenvExecutor(venv_path=module_registry_config.get("venv_path", "./module_envs"), module_registry=module_registry),
                "conda": CondaExecutor(module_registry),
                "uv": UvExecutor(uv_path=module_registry_config.get("venv_path", "./module_envs"), module_registry=module_registry)
            }
            
            # Docker는 선택적으로
            try:
                from executors.docker import DockerExecutor
                executors["docker"] = DockerExecutor(module_registry)
            except Exception:
                pass
            
            # ExecRequest 재구성
            request = ExecRequest(
                module=request_dict["module"],
                input_json=request_dict["input_json"]
            )
            
            # 실행
            module_name = request.module
            module = await module_registry.get_module(module_name)
            
            if not module:
                return {
                    "result_json": {},
                    "exit_code": 1,
                    "stderr": f"Module '{module_name}' not found",
                    "stdout": "",
                    "duration": 0,
                    "work_directory": None
                }
            
            executor = executors.get(module.env)
            if not executor:
                return {
                    "result_json": {},
                    "exit_code": 1,
                    "stderr": f"No executor available for environment '{module.env}'",
                    "stdout": "",
                    "duration": 0,
                    "work_directory": None
                }
                
            if not await executor.validate(module_name):
                return {
                    "result_json": {},
                    "exit_code": 1,
                    "stderr": f"Module '{module_name}' cannot be executed in environment '{module.env}'",
                    "stdout": "",
                    "duration": 0,
                    "work_directory": None
                }
            
            # 실제 실행
            result = await executor.execute(request)
            
            # ExecResult를 dict로 변환
            return {
                "result_json": result.result_json,
                "exit_code": result.exit_code,
                "stderr": result.stderr,
                "stdout": result.stdout,
                "duration": result.duration,
                "work_directory": result.work_directory
            }

    async def execute(self, request: ExecRequest) -> ExecResult:
        """비동기 실행 - ProcessPoolExecutor 사용"""
        try:
            # inline executor는 빠르므로 메인 프로세스에서 직접 실행
            module = await self.module_registry.get_module(request.module)
            if module and module.env == "inline":
                return await self._execute_inline(request)
            
            # 다른 executor들은 별도 프로세스에서 실행
            logger.info(f"Executing module {request.module} in worker process")
            
            # 요청을 dict로 직렬화
            request_dict = {
                "module": request.module,
                "input_json": request.input_json
            }
            
            # 설정 정보 전달
            module_registry_config = {
                "venv_path": getattr(self, 'venv_path', "./module_envs")
            }
            
            # ProcessPoolExecutor로 실행
            loop = asyncio.get_event_loop()
            result_dict = await loop.run_in_executor(
                self.process_pool,
                ExecutorManager._execute_sync,
                request_dict,
                module_registry_config
            )
            
            # dict를 ExecResult로 변환
            return ExecResult(
                result_json=result_dict["result_json"],
                exit_code=result_dict["exit_code"],
                stderr=result_dict["stderr"],
                stdout=result_dict["stdout"],
                duration=result_dict["duration"],
                work_directory=result_dict["work_directory"]
            )
            
        except Exception as e:
            logger.error(f"Process execution failed for {request.module}: {str(e)}")
            return ExecResult(
                result_json={},
                exit_code=1,
                stderr=f"Process execution error: {str(e)}",
                stdout="",
                duration=0,
                work_directory=None
            )
    
    async def _execute_inline(self, request: ExecRequest) -> ExecResult:
        """inline executor는 메인 프로세스에서 실행"""
        executor = self.executors.get("inline")
        if not executor:
            return ExecResult(
                result_json={},
                exit_code=1,
                stderr="Inline executor not available",
                stdout="",
                duration=0
            )
        
        if not await executor.validate(request.module):
            return ExecResult(
                result_json={},
                exit_code=1,
                stderr=f"Module '{request.module}' cannot be executed in inline environment",
                stdout="",
                duration=0
            )
        
        return await executor.execute(request)

    def register_executor(self, env: str, executor: Executor) -> None:
        self.executors[env] = executor

    def get_available_environments(self) -> List[str]:
        return list(self.executors.keys())

    async def cleanup(self) -> None:
        # 인라인 executor들 정리
        for executor in self.executors.values():
            await executor.cleanup()
        
        # ProcessPoolExecutor 종료
        if hasattr(self, 'process_pool'):
            self.process_pool.shutdown(wait=True)
            logger.info("ProcessPoolExecutor shutdown completed")

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