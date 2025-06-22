# 빌드 스테이지
FROM node:18-alpine as build

# 이미지 메타데이터
LABEL maintainer="hatiolab"
LABEL description="Operato Runner Frontend"
LABEL version="1.0.0"

# 작업 디렉토리 설정
WORKDIR /app

# package.json과 package-lock.json 복사
COPY package*.json ./

# 의존성 설치
RUN npm ci --only=production

# 소스 코드 복사
COPY . .

# 프로덕션 빌드
RUN npm run build

# 프로덕션 스테이지
FROM nginx:alpine

# 이미지 메타데이터
LABEL maintainer="hatiolab"
LABEL description="Operato Runner Frontend"
LABEL version="1.0.0"

# nginx 설정 파일 복사
COPY nginx.conf /etc/nginx/nginx.conf

# 빌드된 파일을 nginx로 복사
COPY --from=build /app/build /usr/share/nginx/html

# 포트 노출
EXPOSE 80

# nginx 시작
CMD ["nginx", "-g", "daemon off;"] 