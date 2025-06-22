# 빌드 스테이지
FROM node:18-alpine as build

# 버전 정보 설정
ARG VERSION=1.0.0
ARG BUILD_DATE
ARG VCS_REF

# 이미지 메타데이터
LABEL maintainer="hatiolab"
LABEL description="Operato Runner Frontend"
LABEL version="${VERSION}"
LABEL build-date="${BUILD_DATE}"
LABEL vcs-ref="${VCS_REF}"
LABEL org.opencontainers.image.title="Operato Runner Frontend"
LABEL org.opencontainers.image.description="Frontend for Operato Runner"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.vendor="hatiolab"

# 작업 디렉토리 설정
WORKDIR /app

# package.json만 복사 (package-lock.json은 제외)
COPY package.json ./

# 의존성 설치 (package-lock.json 없이)
RUN npm install --omit=dev

# 소스 코드 복사
COPY . .

# 버전 정보를 환경변수로 설정
ENV REACT_APP_VERSION=${VERSION}
ENV REACT_APP_BUILD_DATE=${BUILD_DATE}

# 프로덕션 빌드
RUN npm run build

# 프로덕션 스테이지
FROM nginx:alpine

# 버전 정보 설정
ARG VERSION=1.0.0
ARG BUILD_DATE
ARG VCS_REF

# 이미지 메타데이터
LABEL maintainer="hatiolab"
LABEL description="Operato Runner Frontend"
LABEL version="${VERSION}"
LABEL build-date="${BUILD_DATE}"
LABEL vcs-ref="${VCS_REF}"
LABEL org.opencontainers.image.title="Operato Runner Frontend"
LABEL org.opencontainers.image.description="Frontend for Operato Runner"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.vendor="hatiolab"

# nginx 설정 파일 복사
COPY nginx.conf /etc/nginx/nginx.conf

# 빌드된 파일을 nginx로 복사
COPY --from=build /app/build /usr/share/nginx/html

# 버전 정보를 환경변수로 설정
ENV APP_VERSION=${VERSION}
ENV BUILD_DATE=${BUILD_DATE}

# 포트 노출
EXPOSE 80

# nginx 시작
CMD ["nginx", "-g", "daemon off;"] 