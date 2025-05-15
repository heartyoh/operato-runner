<context>
# Operato Runner – Product Requirements Document (PRD)

# Overview  

Operato Runner는 다양한 실행 환경에서 Python 모듈을 안전하고 일관되게 실행할 수 있는 고유한 실행 플랫폼입니다. REST 및 gRPC 인터페이스를 통해 외부 시스템이 Python 스크립트 또는 코드 블록을 등록하고 실행할 수 있으며, 실행 결과는 구조화된 JSON 형태로 반환됩니다. 이 시스템은 AI 중심의 워크플로우, 자동화 파이프라인, 동적 분석 태스크를 위한 \*\*실행 계층(Task Layer)\*\*으로 사용되며, Operato 플랫폼의 **MCP(Model Context Protocol)** 기반 자동화 인프라의 핵심 구성 요소로 자리잡습니다.

**대상 사용자:**

* AI/ML 실험 실행기 및 LLM 기반 코드 평가 시스템
* 물류, 제조, 운영 시스템의 자동 분석 트리거
* Python 기반 기능을 온디맨드로 실행하고자 하는 SaaS/플랫폼 서비스

**해결 과제:**

* 다양한 환경별 파이썬 실행(venv, conda, docker 등)의 통일된 실행 인터페이스 부재
* Python 코드를 외부에서 안전하게 실행하는 방법에 대한 필요
* 실행 환경 충돌, 라이브러리 충돌 문제 해결

---

# Core Features  

### ✅ 모듈 실행 엔진

* 다양한 환경별 실행 지원: `inline`, `venv`, `conda`, `docker`
* 실행 단위: `handler(input: dict) -> output: dict` 형태로 표준화
* 중요성: 복잡한 의존성과 환경 구성을 서버가 추상화하여 사용자 경험 단순화

### ✅ 동적 모듈 등록

* 코드/스크립트를 REST API 또는 gRPC를 통해 실시간 등록
* 메타데이터 기반 모듈 식별 및 버전 관리 가능
* 중요성: 운영 중인 시스템에서도 유연하게 기능 업데이트 가능

### ✅ 표준화된 인터페이스

* REST API: `/run/{module}`, `/modules`
* gRPC: `Execute(ExecRequest) → ExecResponse`
* 중요성: 다양한 시스템 언어/환경에서 호출 가능

### ✅ 실행 결과 추적

* stdout, stderr, exit\_code, duration 등을 기록
* 실패 시 재시도 정책, 에러 메시지 구조화 포함

### ✅ 스케줄러/AI 연동 가능

* 외부 scheduler-service와 연동하여 정기 실행 가능
* LLM이 생성한 코드 실행 가능 (코드 → 모듈화 → 실행 → 결과 피드백)

# User Experience  

### 👤 User Personas

* **AI 엔지니어**: 분석 모델 실행 결과를 API로 관리
* **시스템 통합자**: 외부 시스템에서 특정 기능을 트리거
* **운영 관리자**: 스케줄된 자동화 기능 실행 및 실패 추적

### 🔁 Key User Flows

1. 사용자 또는 LLM이 코드 업로드 (inline 등록)
2. 등록된 모듈을 REST API 또는 gRPC로 실행
3. 실행 결과를 응답받아 처리 (또는 피드백)

### 🎨 UI/UX Considerations (선택사항)

* Operato 플랫폼의 관리 UI에서 모듈 등록/실행 기록 확인 가능
* Swagger UI 기반 OpenAPI 문서 자동 생성
</context>
<PRD>
# Technical Architecture  

### 🧱 System Components

* `ExecutorManager`: 실행 요청 라우팅 및 Executor 선택
* `Executors/`: InlineExecutor, VenvExecutor, CondaExecutor, DockerExecutor
* `ModuleRegistry`: 등록된 모듈 관리 (memory + YAML/DB)
* `api/rest.py`: FastAPI 기반 REST 라우터
* `api/grpc_server.py`: gRPC 인터페이스 처리

### 🧩 Data Models

* Module: name, env, path/code, created\_at, version, tags
* ExecRequest: module, input\_json
* ExecResult: result\_json, exit\_code, stderr, duration

### 🌐 APIs and Integrations

* REST (FastAPI), gRPC (grpcio, protobuf)
* Docker SDK, subprocess, conda CLI 사용
* 향후 Kafka, Redis pub/sub 연동 고려

### ☁️ Infrastructure Requirements

* Python 3.10+, Linux 기반 서버 또는 컨테이너 환경
* Docker daemon 접근 필요 (docker executor 사용 시)
* PostgreSQL or SQLite (선택)
* Redis/Kafka (선택)

---

# Development Roadmap  

### 🔹 Phase 1: MVP

* inline, venv executor 구현
* FastAPI 기반 REST `/run/{module}` 구현
* gRPC 기본 인터페이스 구현
* `modules.yaml` 기반 정적 모듈 로딩
* 로그 출력 및 stdout/stderr 반환 처리

### 🔹 Phase 2: 동적 등록 + 확장 실행기

* REST API 기반 동적 모듈 등록/조회/삭제
* docker, conda executor 추가 구현
* ModuleRegistry에 in-memory + reload 기능 구현

### 🔹 Phase 3: 안정화 및 통합

* 모듈 실행 이력 저장 (파일/DB)
* 실패 시 재시도 정책 + 상태 관리
* WASM/WASI executor 설계 착수
* 인증 헤더(JWT 또는 API Key) 도입

### 🔹 Phase 4: 연동 및 배포

* scheduler-service 연동 테스트
* Helm chart 작성 + Kubernetes 배포 구조화
* log server 또는 Grafana/Prometheus 연동

---

# Logical Dependency Chain

1. Executor 인터페이스 정의 + 기본 executor 구현 (inline, venv)
2. `ModuleRegistry` → module 관리 구조 확립
3. REST `/run`, gRPC `Execute` → 기본 실행 흐름 확인
4. modules.yaml 또는 DB 기반 초기 모듈 관리 기능 구현
5. 동적 등록 API (`/modules`) → CRUD 완성
6. 확장 실행기 (docker, conda)
7. 스케일 아웃 고려: queue 연동, 컨테이너 풀
8. 인증 및 보안 처리 → 실서비스 대응

---

# Risks and Mitigations  

| 위험요소       | 설명                             | 대응전략                                 |
| ---------- | ------------------------------ | ------------------------------------ |
| 환경 충돌      | venv, conda, docker 간 실행 경로 충돌 | executor 별 resource 제한 및 sandbox 적용  |
| inline 보안  | 사용자가 직접 코드를 등록하는 구조            | `ast` 검사, `RestrictedPython` 적용 고려   |
| 재시작시 상태 손실 | 등록된 모듈 정보 손실                   | `modules.yaml` 백업, DB 또는 Redis 캐싱 적용 |
| 실행 지연      | docker executor는 cold start 느림 | 컨테이너 풀 또는 사전 warming 구조 고려           |
| 자원 고갈      | 다중 실행 요청 시 CPU/MEM 고갈          | rate limit, 실행큐 도입, scaling 정책 적용    |

---

# Appendix  

### 참고 자료

* FastAPI: [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
* grpcio: [https://grpc.io/docs/languages/python/](https://grpc.io/docs/languages/python/)
* PyExec 패턴 사례: OpenAI Codex-Sandbox, Replit, BentoML

### Protobuf 예시

```proto
syntax = "proto3";
service Executor {
  rpc Execute(ExecRequest) returns (ExecResponse);
}
message ExecRequest {
  string module = 1;
  string json_input = 2;
}
message ExecResponse {
  string result = 1;
  int32 exit_code = 2;
  string stderr = 3;
}
```
</PRD>