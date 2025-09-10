# Operato Runner

Operato Runner는 다양한 실행 환경(inline, venv, conda, docker)에서 Python 모듈을 안전하게 실행할 수 있는 플랫폼입니다. REST API와 gRPC 인터페이스를 통해 원격 코드 실행을 지원하며, 모듈 관리 및 실행 결과 추적 기능을 제공합니다.

## 주요 기능

- **다양한 실행 환경 지원**

  - `inline`: 현재 프로세스에서 직접 실행
  - `venv`: Python 가상환경에서 실행
  - `conda`: Conda 환경에서 실행
  - `docker`: Docker 컨테이너에서 실행
  - `uv`: uv 가상환경에서 실행 (초고속 Python 패키지/실행 환경)

- **모듈 관리**

  - YAML 기반 모듈 설정
  - 모듈 CRUD 기능
  - 태그 및 환경 기반 필터링

- **API 인터페이스**

  - REST API (FastAPI 기반)
  - gRPC 서비스
  - JWT 기반 인증

- **실행 결과 추적**
  - 실행 히스토리 관리
  - 오류 처리 및 재시도 정책

## 시스템 요구사항

- Python 3.8 이상
- 선택적 요구사항:
  - Docker (Docker 실행 환경 사용 시)
  - Conda (Conda 실행 환경 사용 시)
  - uv (uv 실행 환경 사용 시, https://github.com/astral-sh/uv)

## ⚡️ uv 기반 개발 환경(권장)

[uv](https://github.com/astral-sh/uv)는 초고속 Python 패키지/가상환경 관리 도구입니다. 기존 venv 환경과 100% 호환되며, 훨씬 빠른 설치/실행이 가능합니다.

### uv 설치

- macOS: `brew install astral-sh/uv/uv`
- 또는 [공식 문서](https://github.com/astral-sh/uv) 참고

### uv로 가상환경 생성 (선택)

```bash
uv venv  # .venv 폴더 생성 (기존 venv도 그대로 사용 가능)
```

### 패키지 설치

```bash
uv pip install -r requirements.txt
```

### 실행

```bash
uv run python main.py
uv run pytest
```

### 기존 venv 환경과의 호환성

- 기존 `.venv` 폴더가 있다면 별도 생성 없이 바로 uv 명령어 사용 가능
- 기존 venv 워크플로우와 병행 가능

## 설치 방법 (venv/uv 모두 지원)

### 소스에서 설치

```bash
# 저장소 복제
git clone https://github.com/yourusername/operato-runner.git
cd operato-runner

# 가상환경 생성 및 활성화 (venv)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 또는 uv로 가상환경 생성 (권장)
uv venv

# 의존성 설치 (uv 권장)
uv pip install -r requirements.txt
# 또는 pip install -r requirements.txt
```

### Docker를 통한 설치

```bash
docker pull operato/runner:latest
```

## 사용 방법

### 서버 실행

```bash
# 기본 설정으로 실행
python main.py

# 사용자 정의 설정으로 실행
python main.py --config=path/to/modules.yaml --rest-port=8080 --grpc-port=50052 --venv-path=./custom_venvs
```

### 명령줄 옵션

- `--config`: 모듈 설정 파일 경로 (기본값: `./modules.yaml`)
- `--rest-port`: REST API 포트 (기본값: `8000`)
- `--grpc-port`: gRPC 서버 포트 (기본값: `50051`)
- `--venv-path`: 가상환경 경로 (기본값: `./venvs`)
- `--no-rest`: REST API 비활성화
- `--no-grpc`: gRPC 서버 비활성화

### 모듈 설정 예제

```yaml
modules:
  - name: hello-world
    env: inline
    code: |
      def handler(input):
          return {"message": f"Hello, {input.get('name', 'World')}!"}
    version: "0.1.0"
    tags:
      - example
      - greeting

  - name: data-processor
    env: venv
    path: ./modules/data_processor.py
    version: "1.0.0"
    tags:
      - data
      - processing

  - name: fast-ml
    env: uv
    path: ./modules/fast_ml.py
    version: "0.1.0"
    tags:
      - ml
      - fast
```

### REST API 사용 예제

```bash
# 모듈 실행
curl -X POST "http://localhost:8000/modules/execute/hello-world" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -d '{"name": "User"}'

# 모듈 목록 조회
curl -X GET "http://localhost:8000/modules" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### gRPC 클라이언트 예제

```python
import grpc
from proto import executor_pb2, executor_pb2_grpc
import json

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = executor_pb2_grpc.ExecutorServiceStub(channel)

        # 모듈 실행
        request = executor_pb2.ExecuteRequest(
            module_name="hello-world",
            input_json=json.dumps({"name": "User"})
        )
        response = stub.Execute(request)
        print(f"Result: {response.result_json}")

if __name__ == '__main__':
    run()

## Python 패키지 요구사항

`operato-runner`에서 실행할 Python 패키지는 다음 최소 요구사항을 충족해야 합니다:

### 필수 파일

1. **`handler.py`** - 엔트리 포인트 역할
   - `operato-runner`가 실행할 메인 함수가 포함되어야 함
   - 함수는 입력 파라미터를 받아 결과를 반환하는 형태여야 함

2. **`requirements.txt`** - 의존성 설치
   - 패키지 실행에 필요한 Python 라이브러리 목록

### 패키지 업로드

각 Python 프로젝트는 **zip 파일로 업로드**할 수 있으며, 관련 템플릿은 새 모듈 업로드 화면에서 다운로드 받을 수 있습니다.

### 예제 구조

```

my-python-package/
├── handler.py # 필수: 엔트리 포인트
├── requirements.txt # 필수: 의존성 목록
└── etc...

````

### handler.py 예제

```python
def handler(input):
    """
    operato-runner에서 호출되는 메인 함수

    Args:
        input (dict): 입력 데이터 (dictionary 타입)
            - 파라미터들은 input 딕셔너리의 키-값 쌍으로 전달됨
            - 예: input.get('text', ''), input.get('limit', 10) 등

    Returns:
        dict: 실행 결과 (dictionary 타입)
            - 결과 데이터를 딕셔너리 형태로 반환해야 함
    """
    # 입력 데이터 추출
    text = input.get('text', '')
    limit = input.get('limit', 10)

    # 여기에 실제 로직 구현
    result = process_input(text, limit)

    return {
        "result": result,
        "status": "success",
        "input_received": input  # 디버깅용
    }

def process_input(text, limit):
    # 실제 처리 로직
    return f"Processed: {text[:limit]}"
````

### requirements.txt 예제

```
numpy>=1.21.0
pandas>=1.3.0
requests>=2.25.0
```

## 프로젝트 구조

```
operato-runner/
├── api/                    # API 인터페이스
│   ├── auth.py             # 인증 관련 기능
│   ├── rest.py             # REST API (FastAPI)
│   └── grpc_server.py      # gRPC 서버
├── executors/              # 실행 환경 구현
│   ├── base.py             # 기본 Executor 인터페이스
│   ├── inline.py           # 인라인 실행기
│   ├── venv.py             # 가상환경 실행기
│   ├── conda.py            # Conda 실행기
│   ├── docker.py           # Docker 실행기
│   ├── uv.py               # uv 실행기 (초고속 Python 환경)
│   └── ... (uv 실행기 구현 파일)
├── proto/                  # gRPC 프로토콜 정의
│   ├── executor.proto      # 프로토콜 버퍼 정의
│   ├── executor_pb2.py     # 생성된 프로토콜 버퍼 코드
│   └── executor_pb2_grpc.py # 생성된 gRPC 코드
├── helm-chart/            # Helm 차트 (Kubernetes 배포용)
├── models.py               # 데이터 모델 정의
├── module_registry.py      # 모듈 레지스트리
├── executor_manager.py     # 실행기 관리자
├── execution_history.py    # 실행 히스토리 관리
├── retry_policy.py         # 재시도 정책
├── main.py                 # 메인 애플리케이션
└── requirements.txt        # 의존성 목록
```

## 배포

### Docker 컨테이너 배포

```bash
# 이미지 빌드
docker build -t operato/runner:latest .

# 컨테이너 실행
docker run -p 8000:8000 -p 50051:50051 -v ./modules.yaml:/app/modules.yaml operato/runner:latest
```

### Kubernetes 배포 (Helm)

```bash
# Helm 차트 설치
helm install operato-runner ./helm-chart -f values.yaml

# 환경별 배포
helm install operato-runner-dev ./helm-chart -f values-dev.yaml
```

자세한 배포 정보는 [배포 가이드](helm-chart/ci/README.md)를 참조하세요.

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 기여하기

기여는 언제나 환영합니다! [CONTRIBUTING.md](CONTRIBUTING.md) 파일을 참조하여 기여 방법을 확인하세요.

## 데이터베이스 마이그레이션(Alembic) 사용법

이 프로젝트는 DB 스키마 관리를 위해 Alembic을 사용합니다.

### 마이그레이션 환경 준비

- Alembic 패키지 설치: `pip install alembic`
- 환경설정: `alembic.ini`, `alembic/env.py`에서 DB URL, 모델 경로 등 확인

### 마이그레이션 스크립트 생성

```bash
alembic revision --autogenerate -m "설명"
```

### 마이그레이션 적용

```bash
alembic upgrade head
```

### 마이그레이션 롤백

```bash
alembic downgrade base
```

### 참고

- DB URL 등 환경설정은 `alembic.ini`/`alembic/env.py`에서 관리
- 모델 구조 변경 시 반드시 새 마이그레이션을 생성해야 함
- 마이그레이션 버전 관리는 `alembic/versions/` 디렉토리에서 확인
