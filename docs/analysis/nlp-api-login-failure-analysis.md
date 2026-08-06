# nlp-api.arcanaverse.ai 로그인 무한 대기 장애 — 조사·수정 종합 정리

- 작업일: 2026-08-06
- 브랜치: `dev` (커밋 `27b6912`, **아직 push 안 함 — 사용자 확인 후 결정 예정**)
- 관련 상세 리포트:
  - 조사: `docs/report/18_NLP_Login_Failure_Investigation.md`
  - 수정 적용: `docs/report/19_NLP_Login_Failure_Fix_Applied.md`
- 변경 파일: `infra/nginx/conf.d/nlp-api.arcanaverse.ai.conf` (Oracle VM `reverse-proxy` 컨테이너 전용, HF Space 쪽은 미수정)

---

## 1. 문제

브라우저에서 `https://nlp-api.arcanaverse.ai/auth/google/start?next=/` 호출 시 **무한 대기**.
- HF Space 직접 호출은 정상
- `/health`, `/docs`는 (겉보기엔) 정상

## 2. 조사 (읽기 전용, 수정 없이 진행)

`nginx -T`, docker compose, reverse-proxy 컨테이너 설정, `proxy_pass`/`proxy_ssl_server_name`/`resolver` 점검, curl로 upstream 직접 비교, `docker logs` 분석 순으로 진행. 요지:

- 실제 `nlp-api.arcanaverse.ai`를 처리하는 건 host nginx가 아니라 **Docker 컨테이너 `reverse-proxy`**(nginx:1.27-alpine, 7주째 재기동 없음).
- `location / { proxy_pass https://sungbae74-traffic-accident-legal-rag.hf.space; ... }` — **정적(literal) hostname**을 사용하는데 **`resolver` 지시어가 어디에도 없음**.
- 이 조합에서 nginx는 **설정 로드(=컨테이너 최초 기동) 시점에 딱 1회만 DNS를 조회**하고 이후 영구 캐시. 컨테이너가 7주간 재기동/reload 없이 떠 있었던 사이 HF Space측 IP 일부가 죽어(dead), 요청마다 무작위로 살아있는 IP/죽은 IP 중 하나에 걸림.
- `docker logs reverse-proxy`에서 `upstream timed out (110: Operation timed out) while connecting to upstream` 에러 **13건** (2026-06-27 ~ 2026-08-05 23:48, 장애 전날 밤 실사용자 `/auth/google/start` 요청 4건 포함) 확인. 이때 연결 시도한 IP 6종은 **지금 신선하게 조회한 DNS 결과와 하나도 겹치지 않음** → 캐시된 dead IP 사용 확정.
- 재현 테스트에서도 `/health`, `/docs`가 "정상"이라던 것은 경로별 문제가 아니라 **테스트 시점에 우연히 살아있는 캐시 IP를 뽑은 것**이었음(재시도 시 000 타임아웃 재현됨).

**결론(추정, 높은 확신도): `resolver` 부재로 인한 DNS 캐시 고착이 근본 원인.** 경로 무관, IP 뽑기 운에 좌우되는 랜덤 실패 패턴.

## 3. 수정

`infra/nginx/conf.d/nlp-api.arcanaverse.ai.conf`의 `nlp-api.arcanaverse.ai` 443 server block에 다음을 추가/변경 (스코프를 이 server block 내부로 한정, `api.arcanaverse.ai.conf`는 미변경):

| 항목 | 내용 | 목적 |
|---|---|---|
| `resolver 127.0.0.11 valid=30s;` | 컨테이너 내장 Docker DNS 사용 | 외부 의존성 없이 주기적 DNS 재조회 활성화 (실측 HF TTL 60s보다 짧게 잡아 더 빠르게 반응) |
| `resolver_timeout 5s;` | | resolver 응답 지연 방지 |
| `proxy_pass` 대상을 **변수**(`set $hf_backend ...; proxy_pass https://$hf_backend;`)로 변경 | | 리터럴 hostname은 resolver가 있어도 1회만 조회됨 — 변수를 써야 매 요청마다(TTL 기준) 재조회됨 |
| `proxy_ssl_name` 명시 | | 변수 기반으로 바뀌어도 SNI가 정확한 hostname으로 나가도록 고정 (HF Space는 SNI 기반 라우팅) |
| `proxy_http_version 1.1;` + `proxy_set_header Connection "";` | | 스트리밍/청크 응답 호환성(nginx 권장 설정) |
| `proxy_connect_timeout 5s;` | | 죽은 IP에 걸려도 기본 60초 대신 5초 만에 실패 → "무한 대기" 체감 제거 |
| `proxy_send_timeout 60s; proxy_read_timeout 60s;` | 기존 기본값과 동일하게 **명시만** | 응답이 오래 걸리는 요청(향후 LLM 생성 등)을 깨뜨리지 않기 위해 임의로 단축하지 않음 |

**검토했으나 채택하지 않은 방식**: NGINX Plus의 `upstream { server ... resolve; }` — 상용 전용 기능이라 현재 사용 중인 OSS `nginx:1.27-alpine`에서는 사용 불가. `resolver` + 변수 기반 `proxy_pass`가 OSS에서 통용되는 동등 대안.

## 4. 적용 및 검증

```
docker exec reverse-proxy nginx -t        # 문법 검사 통과 (기존부터 있던 http2 deprecated 경고만 존재)
docker exec reverse-proxy nginx -s reload # graceful reload, 기존 연결 유지
```

- `/auth/google/start?next=/` **10회 연속 302** (수정 전엔 404/타임아웃/302가 뒤섞였음), 응답 헤더에 실제 앱(uvicorn) 고유 헤더(`x-proxied-host`, `x-proxied-replica`, `x-request-id`)와 올바른 `Location: https://accounts.google.com/...redirect_uri=https%3A%2F%2Fnlp-api.arcanaverse.ai%2Fauth%2Fgoogle%2Fcallback...` 포함 확인.
- `/health`, `/docs` **각 5회 연속 200**, 응답시간 0.76~0.85초로 일정 (수정 전 관찰된 간헐적 15초 타임아웃 재현 안 됨) — **기존 기능 회귀 없음**.
- reload 이후 `upstream timed out` 재발 없음 (로그 확인).

## 5. 커밋 및 후속 조치

- 커밋: `27b6912` (`dev` 브랜치) — nginx 설정 + 조사 리포트(18) + 수정 리포트(19) 3개 파일.
- **push는 아직 하지 않았음** — 사용자 확인 후 결정.
- 커밋 직전 `docs/report/18_...md` 파일이 디스크에서 사라져 있던 것을 발견해 원 내용으로 복원 후 커밋함(원인 미상, Claude가 지운 적 없음).

## 6. 후속 권고 (이번 작업 범위 밖)

- `api.arcanaverse.ai.conf`(내부 `trpg-api` 대상)도 동일한 "정적 hostname + resolver 없음" 패턴이 잠재적으로 존재. 현재 장애 미보고 상태지만 동일 근본 원인이 잠재하므로 필요 시 같은 패턴 적용 검토 권고.
- `listen ... http2` deprecated 경고(nginx 1.25+에서 `http2 on;` 방식 권장)는 이번 수정 범위에서 제외, 별도 정리 권장.
- HF Space 쪽 재빌드/재배포 이력과 IP 로테이션 시점의 상관관계는 HF 대시보드에서 별도 확인 필요.
