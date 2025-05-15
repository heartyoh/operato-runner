# Operato Runner

Operato Runner는 다양한 실행 환경(inline, venv, conda, docker)에서 Python 모듈을 안전하게 실행할 수 있는 플랫폼입니다. REST API와 gRPC 인터페이스를 통해 원격 코드 실행을 지원하며, 모듈 관리 및 실행 결과 추적 기능을 제공합니다.

## 주요 기능

- **다양한 실행 환경 지원**

  - `inline`: 현재 프로세스에서 직접 실행
  - `venv`: Python 가상환경에서 실행
  - `conda`: Conda 환경에서 실행
  - `docker`: Docker 컨테이너에서 실행

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

## 설치 방법

### 소스에서 설치

```bash
# 저장소 복제
git clone https://github.com/yourusername/operato-runner.git
cd operato-runner

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
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
│   └── docker.py           # Docker 실행기
├── proto/                  # gRPC 프로토콜 정의
│   ├── executor.proto      # 프로토콜 버퍼 정의
│   ├── executor_pb2.py     # 생성된 프로토콜 버퍼 코드
│   └── executor_pb2_grpc.py # 생성된 gRPC 코드
├── operato-runner/         # Helm 차트 (Kubernetes 배포용)
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
helm install operato-runner ./operato-runner -f values.yaml

# 환경별 배포
helm install operato-runner-dev ./operato-runner -f values-dev.yaml
```

자세한 배포 정보는 [배포 가이드](operato-runner/ci/README.md)를 참조하세요.

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 기여하기

기여는 언제나 환영합니다! [CONTRIBUTING.md](CONTRIBUTING.md) 파일을 참조하여 기여 방법을 확인하세요.
