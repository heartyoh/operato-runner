#!/usr/bin/env python3
"""
Import path fixer for Operato Runner
Fixes relative imports to work with the new src/ structure
"""

import os
import re
import glob


def fix_file_imports(file_path):
    """Fix imports in a single file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix patterns for different import types
    patterns = [
        # from ..models import -> from models import
        (r'from \.\.models import', 'from models import'),
        (r'from \.\.models\.', 'from models.'),
        
        # from ..core import -> from core import  
        (r'from \.\.core import', 'from core import'),
        (r'from \.\.core\.', 'from core.'),
        
        # from ..utils import -> from utils import
        (r'from \.\.utils import', 'from utils import'),
        (r'from \.\.utils\.', 'from utils.'),
        
        # from ..api import -> from api import
        (r'from \.\.api import', 'from api import'),
        (r'from \.\.api\.', 'from api.'),
        
        # from ..schemas import -> from schemas import
        (r'from \.\.schemas import', 'from schemas import'),
        (r'from \.\.schemas\.', 'from schemas.'),
        
        # from .models import -> from models import (within src/)
        (r'from \.models import', 'from models import'),
        (r'from \.models\.', 'from models.'),
        
        # from .core import -> from core import
        (r'from \.core import', 'from core import'),
        (r'from \.core\.', 'from core.'),
        
        # from .utils import -> from utils import
        (r'from \.utils import', 'from utils import'),
        (r'from \.utils\.', 'from utils.'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed: {file_path}")
        return True
    return False


def main():
    """Fix all Python files in src/"""
    src_dir = "src"
    if not os.path.exists(src_dir):
        print(f"Directory {src_dir} not found!")
        return
    
    python_files = glob.glob(f"{src_dir}/**/*.py", recursive=True)
    fixed_count = 0
    
    for file_path in python_files:
        if fix_file_imports(file_path):
            fixed_count += 1
    
    print(f"Fixed {fixed_count} files")


if __name__ == "__main__":
    main()