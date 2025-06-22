#!/bin/bash

echo "🐳 Operato Runner Docker 실행 예제"
echo "=================================="

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되지 않았습니다."
    echo "https://docs.docker.com/get-docker/ 에서 Docker를 설치하세요."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되지 않았습니다."
    echo "https://docs.docker.com/compose/install/ 에서 Docker Compose를 설치하세요."
    exit 1
fi

echo "✅ Docker 및 Docker Compose 확인 완료"

# 필요한 디렉토리 생성
echo "📁 필요한 디렉토리 생성 중..."
mkdir -p modules module_envs templates

# Docker 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ 이미지 빌드 실패"
    exit 1
fi

echo "✅ 이미지 빌드 완료"

# 서비스 시작
echo "🚀 서비스 시작 중..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ 서비스 시작 실패"
    exit 1
fi

echo "✅ 서비스 시작 완료"

# 서비스 상태 확인
echo "📊 서비스 상태 확인 중..."
sleep 10
docker-compose ps

echo ""
echo "🎉 Operato Runner가 성공적으로 시작되었습니다!"
echo ""
echo "🌐 접속 정보:"
echo "   웹 UI: http://localhost:3000"
echo "   REST API: http://localhost:8000"
echo "   gRPC: localhost:50051"
echo ""
echo "📋 유용한 명령어:"
echo "   로그 확인: docker-compose logs -f"
echo "   서비스 중지: docker-compose down"
echo "   상태 확인: docker-compose ps"
echo ""
echo "🔧 문제가 있다면:"
echo "   docker-compose logs backend"
echo "   docker-compose logs frontend" 