# 환경변수 주입 테스트용 inline 코드 예제

import os
import json

def main(input_data):
    """
    환경변수 주입 테스트용 함수
    
    입력 예시:
    {
        "test_key": "test_value"
    }
    
    출력 예시:
    {
        "all_env_vars": {"API_KEY": "secret123", "DATABASE_URL": "postgresql://..."},
        "specific_vars": {"API_KEY": "secret123"},
        "input_data": {"test_key": "test_value"},
        "message": "환경변수 주입 테스트 완료"
    }
    """
    
    # 모든 환경변수 수집 (보안상 실제 운영에서는 민감한 정보 제외)
    all_env_vars = dict(os.environ)
    
    # 테스트용 환경변수들만 필터링 (실제 운영에서는 더 엄격하게)
    test_env_vars = {}
    for key, value in all_env_vars.items():
        if key in ['API_KEY', 'DATABASE_URL', 'REDIS_URL', 'SECRET_KEY', 'TEST_VAR']:
            test_env_vars[key] = value
    
    # 입력 데이터와 함께 결과 반환
    result = {
        "all_env_vars": all_env_vars,
        "specific_vars": test_env_vars,
        "input_data": input_data,
        "message": "환경변수 주입 테스트 완료",
        "python_path": os.environ.get('PYTHONPATH', 'Not set'),
        "current_working_dir": os.getcwd(),
        "env_file_exists": os.path.exists('.env')
    }
    
    return result

# 테스트용 코드 (실행 시 확인용)
if __name__ == "__main__":
    test_input = {"test_key": "test_value"}
    result = main(test_input)
    print(json.dumps(result, indent=2, ensure_ascii=False)) 