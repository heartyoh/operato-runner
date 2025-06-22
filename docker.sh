#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 에러 처리 함수
error_exit() {
    echo -e "${RED}❌ 오류: $1${NC}" >&2
    exit 1
}

# 성공 메시지 함수
success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 정보 메시지 함수
info_msg() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 경고 메시지 함수
warning_msg() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 버전 정보 설정
VERSION=$(cat VERSION 2>/dev/null || echo "1.0.0")
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Docker 이미지 빌드 함수
build_images() {
    info_msg "Docker 이미지 빌드 시작..."
    echo "📋 버전 정보:"
    echo "   - Version: $VERSION"
    echo "   - Build Date: $BUILD_DATE"
    echo "   - Git Commit: $VCS_REF"
    echo ""

    # Docker 상태 확인
    if ! docker info >/dev/null 2>&1; then
        error_exit "Docker가 실행되지 않았습니다. Docker Desktop을 시작해주세요."
    fi

    # Backend 이미지 빌드
    info_msg "Backend 이미지 빌드 중..."
    docker build \
        --build-arg VERSION=$VERSION \
        --build-arg BUILD_DATE=$BUILD_DATE \
        --build-arg VCS_REF=$VCS_REF \
        -t hatiolab/operato-runner-service:$VERSION \
        -t hatiolab/operato-runner-service:latest \
        . || error_exit "Backend 이미지 빌드 실패"
    success_msg "Backend 이미지 빌드 완료"

    echo ""

    # Frontend 이미지 빌드
    info_msg "Frontend 이미지 빌드 중..."
    docker build \
        --build-arg VERSION=$VERSION \
        --build-arg BUILD_DATE=$BUILD_DATE \
        --build-arg VCS_REF=$VCS_REF \
        -t hatiolab/operato-runner:$VERSION \
        -t hatiolab/operato-runner:latest \
        ./admin-ui || error_exit "Frontend 이미지 빌드 실패"
    success_msg "Frontend 이미지 빌드 완료"

    echo ""
    success_msg "모든 이미지 빌드 완료!"
}

# Docker Hub 푸시 함수
push_images() {
    info_msg "Docker Hub에 푸시 시작..."
    
    # Backend 이미지 푸시
    info_msg "Backend 이미지 푸시 중..."
    docker push hatiolab/operato-runner-service:$VERSION || error_exit "Backend 이미지 푸시 실패"
    docker push hatiolab/operato-runner-service:latest || error_exit "Backend latest 태그 푸시 실패"
    success_msg "Backend 이미지 푸시 완료"
    
    echo ""
    
    # Frontend 이미지 푸시
    info_msg "Frontend 이미지 푸시 중..."
    docker push hatiolab/operato-runner:$VERSION || error_exit "Frontend 이미지 푸시 실패"
    docker push hatiolab/operato-runner:latest || error_exit "Frontend latest 태그 푸시 실패"
    success_msg "Frontend 이미지 푸시 완료"
    
    echo ""
    success_msg "🎉 모든 이미지 푸시 완료!"
}

# 서비스 관리 함수들
start_services() {
    info_msg "서비스 시작 중..."
    docker-compose -f docker-compose-minimal.yml up -d || error_exit "서비스 시작 실패"
    success_msg "서비스 시작 완료"
}

stop_services() {
    info_msg "서비스 중지 중..."
    docker-compose -f docker-compose-minimal.yml down || error_exit "서비스 중지 실패"
    success_msg "서비스 중지 완료"
}

restart_services() {
    stop_services
    start_services
}

show_status() {
    info_msg "서비스 상태 확인 중..."
    docker-compose -f docker-compose-minimal.yml ps
}

show_logs() {
    info_msg "로그 확인 중..."
    docker-compose -f docker-compose-minimal.yml logs -f
}

cleanup() {
    info_msg "정리 중..."
    docker-compose -f docker-compose-minimal.yml down -v
    docker system prune -f
    success_msg "정리 완료"
}

# 메인 로직
case "$1" in
    "build")
        build_images
        ;;
    "push")
        build_images
        push_images
        ;;
    "release")
        build_images
        echo ""
        read -p "🚀 Docker Hub에 푸시하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            push_images
        else
            warning_msg "푸시를 건너뜁니다."
        fi
        ;;
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "cleanup")
        cleanup
        ;;
    "full")
        build_images
        start_services
        ;;
    *)
        echo -e "${GREEN}🏗️  Operato Runner Docker 관리 스크립트${NC}"
        echo ""
        echo -e "${GREEN}사용법:${NC}"
        echo -e "  ${YELLOW}./docker.sh build${NC}     - 이미지 빌드"
        echo -e "  ${YELLOW}./docker.sh push${NC}      - 빌드 후 자동 푸시"
        echo -e "  ${YELLOW}./docker.sh release${NC}   - 빌드 후 푸시 여부 확인"
        echo -e "  ${YELLOW}./docker.sh start${NC}     - 서비스 시작"
        echo -e "  ${YELLOW}./docker.sh stop${NC}      - 서비스 중지"
        echo -e "  ${YELLOW}./docker.sh restart${NC}   - 서비스 재시작"
        echo -e "  ${YELLOW}./docker.sh status${NC}    - 상태 확인"
        echo -e "  ${YELLOW}./docker.sh logs${NC}      - 로그 확인"
        echo -e "  ${YELLOW}./docker.sh cleanup${NC}   - 정리"
        echo -e "  ${YELLOW}./docker.sh full${NC}      - 전체 빌드 및 시작"
        echo ""
        echo -e "${GREEN}접속 정보:${NC}"
        echo -e "  ${YELLOW}웹 UI:${NC} http://localhost:3000"
        echo -e "  ${YELLOW}REST API:${NC} http://localhost:8000"
        echo -e "  ${YELLOW}API 문서:${NC} http://localhost:8000/docs"
        echo -e "  ${YELLOW}gRPC:${NC} localhost:50051"
        echo ""
        echo -e "${GREEN}Docker Hub:${NC}"
        echo -e "  ${YELLOW}Backend:${NC} https://hub.docker.com/r/hatiolab/operato-runner-service"
        echo -e "  ${YELLOW}Frontend:${NC} https://hub.docker.com/r/hatiolab/operato-runner"
        ;;
esac 