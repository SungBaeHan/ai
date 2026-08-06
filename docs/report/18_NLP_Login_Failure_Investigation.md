# NLP 로그인 장애 조사 보고서 (nlp-api.arcanaverse.ai)

- 조사일: 2026-08-06
- 조사 대상: Oracle VM 상의 nginx reverse-proxy → Hugging Face Space(`sungbae74-traffic-accident-legal-rag`) 연동 구간
- 조사 방식: **읽기 전용 조사만 수행. 설정/코드 수정 없음.**
- 트리거 증상: 브라우저에서 `https://nlp-api.arcanaverse.ai/auth/google/start?next=/` 호출 시 무한 대기

## 사전 확인된 사실 (사용자 제공)

- HF Space 직접 호출 정상
- `/health` 정상
- `/docs` 정상
- Oracle VM nginx가 HF Space reverse proxy 역할 수행

---

## 1. `nginx -T`

호스트 시스템에 `nginx` 패키지가 설치되어 있으나 `systemctl` 기준 **`inactive (dead)`** 상태다. 실제로 80/443 포트를 리슨하는 것은 **`reverse-proxy`라는 Docker 컨테이너(`nginx:1.27-alpine`)** 다 (`ss -tlnp`, `docker ps` 확인, 7주째 가동 중). 따라서 이후 조사는 컨테이너 내부 `nginx -T` 기준으로 진행했다.

호스트 nginx(`/etc/nginx/sites-enabled/api`)는 `api.arcanaverse.ai` → `127.0.0.1:8000` 프록시만 정의되어 있고, `nlp-api.arcanaverse.ai`와는 무관하다. `/etc/nginx/conf.d/`는 비어 있다.

컨테이너 내부 `nginx -T` 기준으로 **`resolver` 지시어가 `http{}` 블록, `nginx.conf`, `conf.d/*.conf` 어디에도 존재하지 않는다.**

## 2. docker compose

- `infra/docker-compose.yml`: `qdrant`, `api`(트래픽/캐릭터 API, container_name `trpg-api`, `127.0.0.1:8000`)
- `infra/docker-compose.reverse-proxy.yml`: `reverse-proxy`(nginx:1.27-alpine, 80/443 노출, `./nginx/conf.d`를 컨테이너의 `/etc/nginx/conf.d`에 read-only 마운트)

두 compose 파일은 `app-net` 네트워크를 공유하지만, `nlp-api.arcanaverse.ai`는 `trpg-api`가 아니라 **Hugging Face Space를 직접 proxy_pass** 한다.

`docker ps` 결과:

| 컨테이너 | 이미지 | 상태 |
|---|---|---|
| `reverse-proxy` | nginx:1.27-alpine | Up 7 weeks |
| `trpg-api` | infra-api | Up 9 days (healthy) |
| `qdrant` | qdrant/qdrant | Up 9 days |

## 3. reverse-proxy 설정

`infra/nginx/conf.d/nlp-api.arcanaverse.ai.conf`(저장소상 `git status`에 `??`(untracked)로 표시됨)는 이미 컨테이너에 마운트되어 **현재도 로드되어 있음을 확인**했다 (컨테이너 내부 `nginx -T` 출력과 호스트 파일 내용이 100% 동일). `/health`, `/docs`가 평소 되는 이유는 이 라우팅 자체는 살아 있기 때문이다.

## 4. `nlp-api.arcanaverse.ai` server block

```nginx
server {
    listen 80;
    server_name nlp-api.arcanaverse.ai;
    return 301 https://$host$request_uri;
}

server {
  listen 443 ssl http2;
  server_name nlp-api.arcanaverse.ai;

  ssl_certificate     /etc/nginx/certs/origin.pem;
  ssl_certificate_key /etc/nginx/certs/origin.key;

  location / {
      proxy_pass https://sungbae74-traffic-accident-legal-rag.hf.space;
      proxy_set_header Host sungbae74-traffic-accident-legal-rag.hf.space;
      proxy_set_header X-Forwarded-Proto https;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_ssl_server_name on;
      proxy_redirect off;
  }
}
```

`proxy_connect_timeout` / `proxy_read_timeout` 등 **타임아웃 관련 지시어가 전혀 없다** → nginx 기본값(각 60초)이 적용된다.

## 5. proxy_pass 대상

`https://sungbae74-traffic-accident-legal-rag.hf.space` — **변수가 아닌 정적 문자열(literal hostname)** 로 지정되어 있다. `upstream{}` 블록도 사용하지 않는다.

## 6. `proxy_ssl_server_name`

`on`으로 설정되어 있어 SNI는 정상적으로 `sungbae74-traffic-accident-legal-rag.hf.space`로 전송된다 (curl 테스트에서 TLS handshake 자체는 문제없이 완료됨을 확인).

## 7. `resolver`

**전역/서버/로케이션 어디에도 없다.** 정적 hostname을 쓰는 `proxy_pass`에서 `resolver`가 없으면, nginx는 **설정 로드(=컨테이너 최초 기동/최근 reload) 시점에 딱 한 번 DNS를 조회**하고 그 결과(IP 목록)를 **재조회 없이 계속 재사용**한다. 이 컨테이너는 **2026-06-16 최초 기동 이후 7주째 재기동/reload 이력이 확인되지 않는다.**

```
container Created: 2026-06-14T12:31:23Z
container StartedAt: 2026-06-16T13:00:08Z
```

## 8. curl로 upstream 테스트

| 대상 | 결과 |
|---|---|
| HF Space 직접, `/health` | 200 OK, 0.77s |
| HF Space 직접, `/docs` | 200 OK, 0.78s |
| HF Space 직접, `/auth/google/start?next=/` | **302, 0.91s**, `Location: https://accounts.google.com/...&redirect_uri=https://nlp-api.arcanaverse.ai/auth/google/callback` (정상. `server: uvicorn`, `x-proxied-replica` 등 실제 앱 응답 헤더 포함) |
| 도메인 경유, `/health` | 1회차 000(15s 타임아웃) → 재시도 200 OK (0.79s) — **불안정** |
| 도메인 경유, `/docs` | 1회차 200 → 재시도 **000 (15s 타임아웃)** — **불안정** |
| 도메인 경유, `/auth/google/start?next=/` | **404 `page not found`** (실제 앱 응답이 아닌, HF 엣지 라우터 추정 응답. `server: nginx/1.27.5`만 있고 앱 고유 헤더는 없음) |

→ **같은 엔드포인트가 도메인 경유로는 요청마다 결과가 달라짐**(성공/느림/타임아웃/엉뚱한 404가 랜덤하게 섞임). 경로 자체 문제가 아니라 **어느 IP로 연결되느냐**에 좌우되는 패턴이다.

## 9. docker logs (reverse-proxy)

결정적 증거를 발견했다 — `upstream timed out (110: Operation timed out) while connecting to upstream` 에러가 **13건** (2026-06-27 최초 ~ 2026-08-05 23:48 최후, 조사 전날 밤) 반복 기록되어 있고, 실제 연결 시도한 업스트림 IP는:

```
100.56.55.64, 3.223.177.194, 34.198.138.197, 44.193.152.212, 44.207.216.101, 54.243.37.31
```

**지금 시점에 신선하게 DNS 조회한 IP**(`107.23.203.43`, `54.235.73.222`, `100.58.89.109` — 조회할 때마다도 바뀜, 즉 HF Space는 다중 A레코드 라운드로빈)와 **단 하나도 겹치지 않는다.**

가장 결정적인 로그 — 사용자가 겪은 증상과 시점/내용이 정확히 일치:

```
2026/08/05 23:20:20 ... GET /auth/google/start?next=%2Fwargames ... upstream: "https://34.198.138.197:443/..."  → timeout
2026/08/05 23:40:33 ... GET /auth/google/start?next=%2Fwargames ... upstream: "https://3.223.177.194:443/..."   → timeout
2026/08/05 23:47:17 ... GET /auth/google/start?next=%2Fwargames ... upstream: "https://34.198.138.197:443/..." → timeout
2026/08/05 23:48:17 ... GET /auth/google/start?next=%2Fwargames ... upstream: "https://54.243.37.31:443/..."   → timeout
```

(4건 모두 실제 유저의 `/auth/google/start` 요청이며, referrer가 `nlp.arcanaverse.ai`인 것으로 보아 실사용자 로그인 시도로 보인다.)

타임아웃은 `/`, `/auth/google/start`, 잡다한 스캐너 요청 경로에서도 랜덤하게 발생 — **경로 무관, 랜덤한 dead IP 선택에 의한 실패**임을 뒷받침한다.

또한 참고로, 동일 로그에서 다수의 봇 스캐닝 트래픽(`/authorized_keys`, `/.env`, `/wp-includes/...` 등)과 SSL handshake 실패(`SSL_do_handshake() failed`, TLS record 오류) 항목도 관찰되었으나, 이는 인터넷에 노출된 서버에서 흔한 잡음(스캐너/봇)으로 보이며 이번 장애와 직접 관련성은 낮다.

## 10. 가장 가능성이 높은 원인 (추정)

**`resolver` 지시어 부재 + 정적 hostname `proxy_pass` → 7주 전(최초 기동) 캐시된 HF Space IP 세트 중 일부가 이후(AWS 인프라 IP 로테이션 등으로 추정) 죽었고, 매 요청마다 살아있는 IP/죽은 IP 중 하나에 무작위로 연결을 시도 → 죽은 IP에 걸리면 nginx 기본 60초 connect timeout까지 응답 없이 대기 → 브라우저에서는 "무한 대기"로 체감된다.**

---

## 최종 정리

### ✅ 확인된 사실
1. 실제 `nlp-api.arcanaverse.ai`를 처리하는 것은 호스트 nginx가 아니라 Docker 컨테이너 `reverse-proxy`(7주째 재기동 없음).
2. `infra/nginx/conf.d/nlp-api.arcanaverse.ai.conf`가 컨테이너에 이미 로드되어 있음(호스트 파일과 100% 동일). git상 untracked일 뿐 배포는 이미 되어 있다.
3. 이 파일의 `proxy_pass`는 정적 hostname `https://sungbae74-traffic-accident-legal-rag.hf.space`이고, `resolver` 지시어가 전체 nginx 설정 어디에도 없다.
4. `proxy_ssl_server_name on`은 설정되어 있어 SNI/TLS 자체는 정상 동작(handshake 성공 확인).
5. HF Space를 직접 호출하면 `/health`, `/docs`, `/auth/google/start`(302 정상 리다이렉트) 모두 정상.
6. 도메인 경유 호출은 같은 경로라도 요청마다 결과가 다름(200/302 vs 404 vs 15초 타임아웃)이 재현됨.
7. reverse-proxy 로그에 `upstream timed out while connecting to upstream` 에러가 2026-06-27부터 2026-08-05 23:48(조사 전날 밤, 실제 `/auth/google/start` 요청)까지 총 13건 기록됨.
8. 타임아웃 시 로그에 찍힌 업스트림 IP 6종은 현재 실시간 DNS 조회 결과(계속 바뀌는 3개 IP)와 전혀 겹치지 않음 — 캐시된 dead IP로 연결 시도 중임을 입증.
9. `proxy_connect_timeout` / `proxy_read_timeout` 등 타임아웃 설정이 없어 기본값 60초가 적용됨.
10. `nlp-api.arcanaverse.ai`의 DNS는 Cloudflare를 경유하지 않고 Oracle VM IP(`158.180.91.4`)로 직접 연결됨(Cloudflare Origin 인증서만 재사용 중, "회색 구름"/DNS-only 상태로 보임).

### 🔎 추정
- **근본 원인**: `resolver` 부재로 인해 nginx가 최초 기동(또는 마지막 reload) 시점에 캐시한 HF Space의 IP 세트 중 일부가 이후 AWS 측 IP 로테이션 등으로 죽었고, 요청마다 죽은 IP/산 IP에 무작위로 걸리면서 간헐적 커넥션 타임아웃(최대 60초)이 발생 → 브라우저에서 "무한 대기"로 체감됨.
- `/health`, `/docs`가 "정상"이라고 보고된 것은 경로별 문제가 아니라, 테스트 시점에 우연히 살아있는 캐시 IP를 뽑았을 가능성이 높음(실제 재현 테스트에서도 `/docs`가 한 번은 성공, 한 번은 타임아웃).
- 조사 전날 밤(08/05 23:20~23:48) 실사용자로 보이는 요청이 4번 연속 `/auth/google/start`에서 타임아웃난 로그는 사용자가 보고한 장애와 시점·증상이 정확히 일치함.

### ❓ 추가 확인이 필요한 사항
- 이 `reverse-proxy` 컨테이너가 정말 **마지막으로 언제 reload/재기동**되었는지(로그 보존 기간이 6주 남짓이라 최초 기동 이후 reload 여부를 100% 특정하지 못함) — 재기동 이력 자체를 알 수 있는 별도 기록(배포 스크립트/CI 로그 등)이 있는지 확인 필요.
- HF Space(`sungbae74-traffic-accident-legal-rag`) 쪽에서 최근 재빌드/재배포가 있었는지(레플리카 IP 세트가 바뀌는 시점과 상관관계가 있는지) — HF 대시보드 확인 필요.
- 현재 살아있는 IP(`107.23.203.43`, `54.235.73.222`, `100.58.89.109` 등)로 반복 조회 시 몇 개나 죽어있는지, TTL이 얼마나 짧은지(라운드로빈 갱신 주기) 확인 필요.
- 프론트엔드(`nlp.arcanaverse.ai` 등)가 이 로그인 흐름을 어떤 순서로 호출하는지(로그의 referrer가 `nlp.arcanaverse.ai`로, 조사 대상인 `nlp-api.arcanaverse.ai`와 다른 서브도메인이었음) — 프론트/백엔드 도메인 관계 재확인 필요.
- Cloudflare가 이 도메인에 대해 proxy(주황 구름)로 붙어있는지 DNS-only(회색 구름)인지 Cloudflare 대시보드에서 최종 확인 필요(현재는 VM IP로 직접 연결되는 것으로 보아 DNS-only로 추정됨).

---

*본 문서는 조사 전용이며, 어떠한 설정 변경도 수행하지 않았다. 후속 조치(예: `resolver` 추가, 주기적 reload, 헬스체크 기반 재기동 등)는 별도 승인 후 진행 필요.*
