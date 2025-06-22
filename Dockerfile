# Python 3.10 베이스 이미지 사용
FROM python:3.10-slim

# 버전 정보 설정
ARG VERSION=1.0.0
ARG BUILD_DATE
ARG VCS_REF

# 이미지 메타데이터
LABEL maintainer="hatiolab"
LABEL description="Operato Runner Backend Service"
LABEL version="${VERSION}"
LABEL build-date="${BUILD_DATE}"
LABEL vcs-ref="${VCS_REF}"
LABEL org.opencontainers.image.title="Operato Runner Service"
LABEL org.opencontainers.image.description="Backend service for Operato Runner"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.vendor="hatiolab"

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치 (Redis 없이)
COPY requirements-minimal.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 버전 정보를 환경변수로 설정
ENV APP_VERSION=${VERSION}
ENV BUILD_DATE=${BUILD_DATE}

# 필요한 디렉토리 생성
RUN mkdir -p /app/modules /app/module_envs /app/templates

# 포트 노출
EXPOSE 8000 50051

# 환경 변수 설정 (Redis 비활성화)
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV REDIS_ENABLED=false

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/db || exit 1

# 애플리케이션 실행 (Redis 없이)
CMD ["python", "main.py", "--rest-port", "8000", "--grpc-port", "50051", "--no-redis"] 