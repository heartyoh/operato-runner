#!/usr/bin/env python3
"""
마이그레이션 파일의 now() 함수를 SQLite 호환 방식으로 변경하는 스크립트
"""

import re

def fix_migration_file():
    file_path = 'alembic/versions/264e6234169e_init.py'
    
    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # now() 함수를 SQLite 호환 방식으로 변경
    # PostgreSQL: now() -> SQLite: (datetime('now'))
    content = re.sub(
        r"server_default=sa\.text\('now\(\)'\)",
        "server_default=sa.text(\"(datetime('now'))\")",
        content
    )
    
    # 파일에 다시 쓰기
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {file_path} 파일이 수정되었습니다.")
    print("now() 함수가 (datetime('now'))로 변경되었습니다.")

if __name__ == "__main__":
    fix_migration_file()
