# Operato Runner Docker 배포 가이드

이 문서는 Operato Runner 애플리케이션을 Docker를 사용하여 배포하는 방법을 설명합니다.

## 📋 사전 요구사항

- Docker (20.10 이상)
- Docker Compose (2.0 이상)
- 최소 4GB RAM
- 최소 10GB 디스크 공간

## 🚀 빠른 시작

### 1. 전체 빌드 및 실행

```bash
# 전체 빌드 및 시작
./docker-build.sh full
```

### 2. 단계별 실행

```bash
# 1. 이미지 빌드
./docker-build.sh build

# 2. 서비스 시작
./docker-build.sh start

# 3. 상태 확인
./docker-build.sh status
```

## 📁 생성된 파일들

```
operato-runner/
├── Dockerfile                    # 백엔드 Docker 이미지
├── docker-compose.yml           # 전체 서비스 구성
├── .dockerignore                # Docker 빌드 제외 파일
├── docker-build.sh              # 빌드 및 실행 스크립트
├── admin-ui/
│   ├── Dockerfile               # 프론트엔드 Docker 이미지
│   ├── nginx.conf               # nginx 설정
│   └── .dockerignore            # 프론트엔드 빌드 제외 파일
└── DOCKER.md                    # 이 파일
```

## 🌐 접속 정보

서비스가 시작되면 다음 주소로 접속할 수 있습니다:

- **웹 UI**: http://localhost:3000
- **REST API**: http://localhost:8000
- **gRPC**: localhost:50051
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🔧 서비스 관리

### 스크립트 사용법

```bash
# 서비스 시작
./docker-build.sh start

# 서비스 중지
./docker-build.sh stop

# 서비스 재시작
./docker-build.sh restart

# 로그 확인
./docker-build.sh logs

# 상태 확인
./docker-build.sh status

# 전체 정리 (볼륨 포함)
./docker-build.sh cleanup
```

### Docker Compose 직접 사용

```bash
# 서비스 시작
docker-compose up -d

# 서비스 중지
docker-compose down

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 📊 서비스 구성

### 백엔드 (operato-backend)

- **포트**: 8000 (REST API), 50051 (gRPC)
- **이미지**: Python 3.10-slim 기반
- **볼륨**:
  - `./modules` → `/app/modules`
  - `./module_envs` → `/app/module_envs`
  - `./app.db` → `/app/app.db`

### 프론트엔드 (operato-frontend)

- **포트**: 3000 (웹 UI)
- **이미지**: Node.js 18 + nginx 기반
- **기능**: React 앱 서빙 + API 프록시

### PostgreSQL (operato-postgres)

- **포트**: 5432
- **데이터베이스**: operato
- **사용자**: operato / operato123

### Redis (operato-redis)

- **포트**: 6379
- **용도**: 캐싱 및 세션 저장

## 🔒 보안 설정

### 환경 변수 설정

프로덕션 환경에서는 환경 변수를 설정하세요:

```bash
# .env 파일 생성
cat > .env << EOF
POSTGRES_PASSWORD=your_secure_password
JWT_SECRET_KEY=your_jwt_secret
DATABASE_URL=postgresql://operato:your_secure_password@postgres:5432/operato
CORS_ORIGINS=https://your-domain.com,https://admin.your-domain.com
EOF
```

### CORS 설정

외부 도메인에서 API 접근을 허용하려면 CORS를 설정하세요:

#### 1. 완전 개방 (개발 환경)

```bash
# 환경변수 없이 실행하면 모든 도메인 허용
docker-compose up
```

#### 2. 특정 도메인만 허용 (권장)

```bash
# 환경변수로 특정 도메인 지정
export CORS_ORIGINS="http://localhost:3000,https://admin.example.com"
docker-compose up
```

또는 docker-compose.yml에서:

```yaml
services:
  backend:
    environment:
      - CORS_ORIGINS=http://localhost:3000,https://your-admin-domain.com
```

#### 3. 완전 차단 (보안 환경)

```bash
export CORS_ORIGINS=""
```

**백엔드 CORS 정책:**
- ✅ **Origin 제어**: `CORS_ORIGINS` 환경변수로 허용 도메인 지정
- ✅ **모든 HTTP 메소드**: GET, POST, PUT, DELETE, OPTIONS, PATCH
- ✅ **모든 헤더 허용**: Authorization, Content-Type 등
- ✅ **자격증명 허용**: 쿠키 및 인증 헤더 포함 요청 지원

**nginx CORS 정책:**
- ✅ **모든 Origin 허용**: `Access-Control-Allow-Origin: *`
- ✅ **Preflight 요청 처리**: OPTIONS 메소드 자동 응답
- ✅ **캐시 최적화**: `Access-Control-Max-Age: 1728000` (20일)
- ✅ **프록시 적용**: `/api/`, `/auth/` 경로 모두 포함

> **참고**: nginx와 FastAPI 양쪽에서 CORS를 설정해도 충돌하지 않습니다. nginx가 먼저 처리하고 백엔드로 전달합니다.

### SSL/TLS 설정

프로덕션에서는 nginx 설정에 SSL 인증서를 추가하세요:

```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    # ... 기타 설정
}
```

## 🐛 문제 해결

### 일반적인 문제들

1. **포트 충돌**

   ```bash
   # 사용 중인 포트 확인
   lsof -i :3000
   lsof -i :8000

   # docker-compose.yml에서 포트 변경
   ports:
     - "3001:80"  # 3000 → 3001
   ```

2. **권한 문제**

   ```bash
   # 볼륨 권한 수정
   sudo chown -R $USER:$USER ./modules ./module_envs
   ```

3. **메모리 부족**

   ```bash
   # Docker 메모리 제한 확인
   docker stats

   # 시스템 메모리 확인
   free -h
   ```

### 로그 확인

```bash
# 전체 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs backend
docker-compose logs frontend

# 실시간 로그
docker-compose logs -f
```

### 컨테이너 내부 접속

```bash
# 백엔드 컨테이너 접속
docker exec -it operato-backend bash

# 프론트엔드 컨테이너 접속
docker exec -it operato-frontend sh

# PostgreSQL 접속
docker exec -it operato-postgres psql -U operato -d operato
```

## 📈 모니터링

### 헬스체크

백엔드 서비스는 자동 헬스체크를 수행합니다:

```bash
# 헬스체크 상태 확인
docker-compose ps

# 수동 헬스체크
curl http://localhost:8000/api/health/db
```

### 리소스 모니터링

```bash
# 컨테이너 리소스 사용량
docker stats

# 디스크 사용량
docker system df
```

## 🔄 업데이트

### 코드 업데이트

```bash
# 1. 코드 변경 후 이미지 재빌드
./docker-build.sh build

# 2. 서비스 재시작
./docker-build.sh restart
```

### 데이터베이스 마이그레이션

```bash
# 백엔드 컨테이너 접속
docker exec -it operato-backend bash

# 마이그레이션 실행
alembic upgrade head
```

## 🗑️ 정리

### 전체 정리

```bash
# 모든 컨테이너, 이미지, 볼륨 삭제
./docker-build.sh cleanup
```

### 선택적 정리

```bash
# 컨테이너만 중지
docker-compose down

# 볼륨 포함 중지
docker-compose down -v

# 이미지 삭제
docker rmi operato-backend operato-frontend

# 사용하지 않는 리소스 정리
docker system prune -f
```

## 📚 추가 정보

- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 공식 문서](https://docs.docker.com/compose/)
- [Nginx 설정 가이드](https://nginx.org/en/docs/)
- [PostgreSQL Docker 가이드](https://hub.docker.com/_/postgres)
