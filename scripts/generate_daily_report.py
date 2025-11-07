"""
매일의 배포 진행 로그를 Markdown 문서로 자동 정리합니다.
"""
import datetime
from pathlib import Path

date = datetime.datetime.now().strftime("%Y-%m-%d")
output = Path(f"docs/deployment_history_{date}.md")

sections = {
    "Cloudflare": """
- 도메인: arcanaverse.ai
- Pages: https://arcanaverse.pages.dev
- DNS: app.arcanaverse.ai / api.arcanaverse.ai 연결
- Cloudflare Tunnel 설정 및 해제 과정 포함
""",
    "Render": """
- Dockerfile: docker/api.Dockerfile
- Branch: prd
- 주요 이슈: COPY assets not found → 해결
- 환경 변수 설정 (JWT_SECRET, DB_PATH 등)
- Deploy URL: https://arcanaverse-api.onrender.com
""",
    "FastAPI 테스트": """
```bash
curl -I https://api.arcanaverse.ai/health
curl -I https://api.arcanaverse.ai/docs
```
""",
}

# Markdown 문서 생성
content = f"""# 배포 이력 - {date}

"""
for title, body in sections.items():
    content += f"## {title}\n{body}\n"

output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(content, encoding="utf-8")

print(f"[OK] 배포 이력이 생성되었습니다: {output}")
