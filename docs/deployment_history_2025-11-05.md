# 배포 이력 - 2025-11-05

## Cloudflare

- 도메인: arcanaverse.ai
- Pages: https://arcanaverse.pages.dev
- DNS: app.arcanaverse.ai / api.arcanaverse.ai 연결
- Cloudflare Tunnel 설정 및 해제 과정 포함

## Render

- Dockerfile: docker/api.Dockerfile
- Branch: prd
- 주요 이슈: COPY assets not found → 해결
- 환경 변수 설정 (JWT_SECRET, DB_PATH 등)
- Deploy URL: https://arcanaverse-api.onrender.com

## FastAPI 테스트

```bash
curl -I https://api.arcanaverse.ai/health
curl -I https://api.arcanaverse.ai/docs
```

