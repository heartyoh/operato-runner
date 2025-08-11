#!/usr/bin/env python3
"""
func.now()가 SQLite에서 어떻게 동작하는지 테스트
"""

import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from sqlalchemy import create_engine, Column, DateTime, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

Base = declarative_base()

class TestTable(Base):
    __tablename__ = 'test_table'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    # 방법 1: func.now() 사용
    created_at_func = Column(DateTime, server_default=func.now())
    # 방법 2: text() 사용  
    created_at_text = Column(DateTime, server_default=text("(datetime('now'))"))
    # 방법 3: Python default 사용
    created_at_python = Column(DateTime)

def test_func_now():
    # SQLite 데이터베이스 생성
    engine = create_engine('sqlite:///test_func_now.db', echo=True)
    
    try:
        # 테이블 생성
        Base.metadata.create_all(engine)
        print("✅ 테이블 생성 성공")
        
        # 세션 생성
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 데이터 삽입
        test_row = TestTable(
            name="test",
            created_at_python=func.now()  # Python 레벨에서 func.now() 사용
        )
        
        session.add(test_row)
        session.commit()
        print("✅ 데이터 삽입 성공")
        
        # 데이터 조회
        result = session.query(TestTable).first()
        print(f"ID: {result.id}")
        print(f"Name: {result.name}")
        print(f"Created at (func): {result.created_at_func}")
        print(f"Created at (text): {result.created_at_text}")
        print(f"Created at (python): {result.created_at_python}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print(f"오류 타입: {type(e).__name__}")
    finally:
        session.close()
        engine.dispose()
        # 테스트 DB 파일 정리
        if os.path.exists('test_func_now.db'):
            os.remove('test_func_now.db')

if __name__ == "__main__":
    test_func_now()
