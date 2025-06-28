# 간단한 환경변수 테스트 코드

import os

# 'A' 환경변수 값을 읽어서 출력
a_value = os.environ.get('A', 'NOT_SET')
print(f"A={a_value}") 