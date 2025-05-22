import os
import yaml
from typing import Dict, List, Optional, Any
from datetime import datetime
from module_models import Module

class ModuleRegistry:
    def __init__(self, config_path="./modules.yaml"):
        self.config_path = config_path
        self.modules: Dict[str, Module] = {}
        self._load_modules()

    def _load_modules(self) -> None:
        """Load modules from YAML file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    modules_data = yaml.safe_load(f) or {}
                for name, data in modules_data.items():
                    self.modules[name] = Module(
                        name=name,
                        env=data.get('env', 'inline'),
                        code=data.get('code'),
                        path=data.get('path'),
                        created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
                        version=data.get('version', '0.1.0'),
                        tags=data.get('tags', [])
                    )
            except Exception as e:
                print(f"Error loading modules: {str(e)}")

    def _save_modules(self) -> None:
        """Save modules to YAML file"""
        modules_data = {}
        for name, module in self.modules.items():
            modules_data[name] = {
                'env': module.env,
                'code': module.code,
                'path': module.path,
                'created_at': module.created_at.isoformat(),
                'version': module.version,
                'tags': module.tags
            }
        with open(self.config_path, 'w') as f:
            yaml.dump(modules_data, f)

    def get_module(self, name: str) -> Optional[Module]:
        """Get a module by name"""
        return self.modules.get(name)

    def list_modules(self) -> List[Module]:
        """List all registered modules"""
        return list(self.modules.values())

    def register_module(self, module: Module) -> None:
        """Register a new module or update existing one"""
        self.modules[module.name] = module
        self._save_modules()

    def delete_module(self, name: str) -> bool:
        """Delete a module by name"""
        if name in self.modules:
            del self.modules[name]
            self._save_modules()
            return True
        return False

    def get_modules_by_env(self, env: str) -> List[Module]:
        """Get all modules for a specific environment"""
        return [m for m in self.modules.values() if m.env == env]

    def get_modules_by_tag(self, tag: str) -> List[Module]:
        """Get all modules with a specific tag"""
        return [m for m in self.modules.values() if tag in m.tags] 