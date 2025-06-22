# Operato Runner Docker 배포 가이드

## 🐳 Docker 관리 스크립트

모든 Docker 관련 작업을 하나의 스크립트로 관리합니다.

### 📋 사용법

```bash
# 도움말 보기
./docker.sh

# 이미지 빌드
./docker.sh build

# 빌드 후 자동 푸시
./docker.sh push

# 빌드 후 푸시 여부 확인
./docker.sh release

# 서비스 시작
./docker.sh start

# 서비스 중지
./docker.sh stop

# 서비스 재시작
./docker.sh restart

# 상태 확인
./docker.sh status

# 로그 확인
./docker.sh logs

# 정리
./docker.sh cleanup

# 전체 빌드 및 시작
./docker.sh full
```

## 🚀 빠른 시작

### 1. 로컬 개발 환경

```bash
# 이미지 빌드 및 서비스 시작
./docker.sh full
```

### 2. Docker Hub 배포

```bash
# 빌드 후 푸시 여부 확인
./docker.sh release

# 또는 자동 푸시
./docker.sh push
```

## 📦 Docker 이미지

### Backend Service

- **이미지**: `hatiolab/operato-runner-service`
- **태그**: `latest`, `1.0.0`
- **포트**: 8000 (REST API), 50051 (gRPC)

### Frontend

- **이미지**: `hatiolab/operato-runner`
- **태그**: `latest`, `1.0.0`
- **포트**: 80 (Nginx)

## 🌐 접속 정보

- **웹 UI**: http://localhost:3000
- **REST API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **gRPC**: localhost:50051

## 🔗 Docker Hub

- **Backend**: https://hub.docker.com/r/hatiolab/operato-runner-service
- **Frontend**: https://hub.docker.com/r/hatiolab/operato-runner

## ⚙️ 환경 설정

### Redis 설정

- **기본**: Redis 없이 실행 (캐싱 기능 비활성화)
- **선택사항**: Redis 추가 시 성능 향상

### 데이터베이스

- **개발**: SQLite (app.db)
- **프로덕션**: PostgreSQL 권장

## 🛠️ 문제 해결

### Docker 로그인

```bash
docker login
```

### 이미지 정보 확인

```bash
docker inspect hatiolab/operato-runner-service:latest
docker inspect hatiolab/operato-runner:latest
```

### 컨테이너 로그

```bash
# 전체 로그
./docker.sh logs

# 특정 서비스 로그
docker-compose -f docker-compose-minimal.yml logs backend
docker-compose -f docker-compose-minimal.yml logs frontend
```

### 정리

```bash
# 컨테이너 및 볼륨 정리
./docker.sh cleanup
```
