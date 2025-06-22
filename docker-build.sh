#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Operato Runner Docker 빌드 및 실행 스크립트${NC}"

# 함수 정의
build_images() {
    echo -e "${YELLOW}📦 Docker 이미지 빌드 중...${NC}"
    
    # 백엔드 이미지 빌드
    echo -e "${YELLOW}🔧 백엔드 이미지 빌드 중...${NC}"
    docker build -t operato-backend .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 백엔드 이미지 빌드 완료${NC}"
    else
        echo -e "${RED}❌ 백엔드 이미지 빌드 실패${NC}"
        exit 1
    fi
    
    # 프론트엔드 이미지 빌드
    echo -e "${YELLOW}🎨 프론트엔드 이미지 빌드 중...${NC}"
    docker build -t operato-frontend ./admin-ui
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 프론트엔드 이미지 빌드 완료${NC}"
    else
        echo -e "${RED}❌ 프론트엔드 이미지 빌드 실패${NC}"
        exit 1
    fi
}

start_services() {
    echo -e "${YELLOW}🚀 서비스 시작 중...${NC}"
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 서비스 시작 완료${NC}"
    else
        echo -e "${RED}❌ 서비스 시작 실패${NC}"
        exit 1
    fi
}

stop_services() {
    echo -e "${YELLOW}🛑 서비스 중지 중...${NC}"
    docker-compose down
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 서비스 중지 완료${NC}"
    else
        echo -e "${RED}❌ 서비스 중지 실패${NC}"
    fi
}

show_status() {
    echo -e "${YELLOW}📊 서비스 상태 확인 중...${NC}"
    docker-compose ps
}

show_logs() {
    echo -e "${YELLOW}📋 로그 확인 중...${NC}"
    docker-compose logs -f
}

cleanup() {
    echo -e "${YELLOW}🧹 정리 중...${NC}"
    docker-compose down -v
    docker system prune -f
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 정리 완료${NC}"
    else
        echo -e "${RED}❌ 정리 실패${NC}"
    fi
}

# 메인 로직
case "$1" in
    "build")
        build_images
        ;;
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        start_services
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
        echo -e "${GREEN}사용법:${NC}"
        echo -e "  ${YELLOW}./docker-build.sh build${NC}     - 이미지 빌드"
        echo -e "  ${YELLOW}./docker-build.sh start${NC}     - 서비스 시작"
        echo -e "  ${YELLOW}./docker-build.sh stop${NC}      - 서비스 중지"
        echo -e "  ${YELLOW}./docker-build.sh restart${NC}   - 서비스 재시작"
        echo -e "  ${YELLOW}./docker-build.sh status${NC}    - 상태 확인"
        echo -e "  ${YELLOW}./docker-build.sh logs${NC}      - 로그 확인"
        echo -e "  ${YELLOW}./docker-build.sh cleanup${NC}   - 정리"
        echo -e "  ${YELLOW}./docker-build.sh full${NC}      - 전체 빌드 및 시작"
        echo ""
        echo -e "${GREEN}접속 정보:${NC}"
        echo -e "  ${YELLOW}웹 UI:${NC} http://localhost:3000"
        echo -e "  ${YELLOW}REST API:${NC} http://localhost:8000"
        echo -e "  ${YELLOW}gRPC:${NC} localhost:50051"
        echo -e "  ${YELLOW}PostgreSQL:${NC} localhost:5432"
        echo -e "  ${YELLOW}Redis:${NC} localhost:6379"
        ;;
esac 