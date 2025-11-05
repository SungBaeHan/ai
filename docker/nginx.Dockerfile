FROM nginx:alpine

# nginx 설정 파일 복사
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# 기본 NGINX 정적 호스팅
# html 디렉토리에 home.html/chat.html이 마운트되고,
# /assets 경로도 compose에서 볼륨으로 연결됨.
