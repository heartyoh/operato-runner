# Operato Runner API 갭 분석

## 1. 경로 일관성 문제

### 식별자 불일치

| 표준 API                       | 실제 구현                      | 문제점                                |
| ------------------------------ | ------------------------------ | ------------------------------------- |
| `/api/modules/{name}`          | `/api/modules/{name}`          | (일치)                                |
| `/api/modules/{name}/versions` | `/api/modules/{name}/versions` | (일치)                                |
| `/api/run/{name}`              | `/run/{module}`                | 접두사 불일치 및 파라미터 명칭 불일치 |

### 접두사 불일치

| 표준 API            | 실제 구현       | 문제점             |
| ------------------- | --------------- | ------------------ |
| `/api/environments` | `/environments` | `/api` 접두사 누락 |
| `/api/health/db`    | `/health/db`    | `/api` 접두사 누락 |

## 2. 누락된 엔드포인트

다음 표준 API 엔드포인트들이 실제로 구현되지 않았습니다:

| 엔드포인트          | HTTP 메소드 | 설명                   |
| ------------------- | ----------- | ---------------------- |
| `/api/environments` | GET         | 환경 목록 조회         |
| `/api/health/db`    | GET         | 데이터베이스 상태 확인 |
| `/api/audit/logs`   | GET         | 감사 로그 조회         |

## 3. 추가 구현된 엔드포인트

실제 구현에는 있으나 표준 API 문서에 정의되지 않은 엔드포인트들:

| 엔드포인트                   | HTTP 메소드 | 권장 사항            |
| ---------------------------- | ----------- | -------------------- |
| `/api/modules/{name}/deploy` | POST        | 표준 API에 추가 필요 |
| `/api/modules/{name}/deploy` | DELETE      | 표준 API에 추가 필요 |

## 4. 응답 형식 불일치

### 표준 API 응답 형식

```json
{
  "success": true/false,
  "data": {
    // 실제 응답 데이터
  },
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지"
  }
}
```

### 실제 구현 응답 형식

- 일관된 응답 형식이 없음
- 직접 데이터 반환
- 에러 처리 불일치

## 5. 인증/권한 처리 불일치

### 표준

- 모든 엔드포인트에 인증 필요
- 명확한 권한 체계 정의

### 실제 구현

- 일부 엔드포인트만 `@Depends(get_current_user)` 적용
- 권한 체계 불명확

## 6. 개선 권장사항

1. 파라미터 표준화

   - 모든 엔드포인트에서 `name` 사용 (고유 문자열)
   - name의 유일성 보장, 필요시 인코딩 처리

2. 경로 표준화

   - 모든 엔드포인트에 `/api` 접두사 적용
   - RESTful 리소스 명명 규칙 준수

3. 응답 형식 표준화

   - 모든 엔드포인트가 동일한 응답 구조 사용
   - 에러 처리 일관성 확보

4. 인증/권한 표준화

   - 모든 보호된 엔드포인트에 인증 미들웨어 적용
   - 명확한 권한 체계 구현

5. 문서화
   - 추가 구현된 엔드포인트들을 표준 API 문서에 포함
   - OpenAPI (Swagger) 스펙 업데이트

## 7. 중복 구현(레드던던시) 현황

### 1) 모듈 관련 중복 엔드포인트

| 엔드포인트                               | 설명                      | UI 사용 여부 |
| ---------------------------------------- | ------------------------- | ------------ | ---- |
| `/api/modules/{name}` (GET)              | 모듈 상세 조회            | **O**        | Done |
| `/modules/{id}/status` (GET)             | 모듈 상태 조회            | X            |
| `/api/modules/{name}/history` (GET)      | 모듈 히스토리 조회        | **O**        | Done |
| `/modules/{id}/history` (GET)            | 모듈 히스토리 조회 (중복) | X            |
| `/api/modules/{name}/activate` (POST)    | 모듈 활성화               | **O**        | Done |
| `/modules/{module_id}/activate` (POST)   | 모듈 활성화 (중복)        | X            |
| `/api/modules/{name}/deactivate` (POST)  | 모듈 비활성화             | **O**        | Done |
| `/modules/{module_id}/deactivate` (POST) | 모듈 비활성화 (중복)      | X            |
| `/api/modules/upload` (POST)             | 모듈 업로드               | X            |

### 2) 실행/환경 관련 중복 엔드포인트

| 엔드포인트                | 설명                  | UI 사용 여부 |
| ------------------------- | --------------------- | ------------ | ---- |
| `/api/run/{name}` (POST)  | 모듈 실행             | X            | Done |
| `/api/environments` (GET) | 환경 목록 조회        | X            | Done |
| `/environments` (GET)     | 환경 목록 조회 (중복) | X            |

### 3) 기타 중복 엔드포인트

| 엔드포인트              | 설명                  | UI 사용 여부 |
| ----------------------- | --------------------- | ------------ | ---- |
| `/api/health/db` (GET)  | DB 상태 확인          | X            | Done |
| `/health/db` (GET)      | DB 상태 확인 (중복)   | X            |
| `/api/audit/logs` (GET) | 감사 로그 조회        | X            | Done |
| `/audit/logs` (GET)     | 감사 로그 조회 (중복) | X            |

#### 요약

- 실제 구현과 표준 API 모두 name 기반으로 일치시킴
- id 기반 엔드포인트는 deprecated 또는 제거 권장
- 중복 엔드포인트는 통합 및 일관성 확보 필요
