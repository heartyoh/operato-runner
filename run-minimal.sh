#!/bin/bash

echo "🚀 Operato Runner (Redis 없이) 시작 중..."

# 환경 확인
if [ ! -f "docker-compose-minimal.yml" ]; then
    echo "❌ docker-compose-minimal.yml 파일을 찾을 수 없습니다."
    exit 1
fi

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리 중..."
docker-compose -f docker-compose-minimal.yml down

# 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker-compose -f docker-compose-minimal.yml build

# 서비스 시작
echo "▶️  서비스 시작 중..."
docker-compose -f docker-compose-minimal.yml up -d

# 상태 확인
echo "📊 서비스 상태 확인 중..."
sleep 10
docker-compose -f docker-compose-minimal.yml ps

echo ""
echo "✅ Operato Runner가 성공적으로 시작되었습니다!"
echo ""
echo "🌐 접속 정보:"
echo "   - 웹 UI: http://localhost:3000"
echo "   - API: http://localhost:8000"
echo "   - API 문서: http://localhost:8000/docs"
echo ""
echo "📝 로그 확인:"
echo "   docker-compose -f docker-compose-minimal.yml logs -f"
echo ""
echo "🛑 중지:"
echo "   docker-compose -f docker-compose-minimal.yml down" 