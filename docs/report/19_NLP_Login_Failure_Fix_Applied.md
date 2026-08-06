# NLP 로그인 장애 수정 적용 리포트 (nlp-api.arcanaverse.ai)

- 적용일: 2026-08-06
- 관련 조사 문서: [`18_NLP_Login_Failure_Investigation.md`](./18_NLP_Login_Failure_Investigation.md)
- 대상 파일: `infra/nginx/conf.d/nlp-api.arcanaverse.ai.conf` (Oracle VM `reverse-proxy` 컨테이너에만 적용, Hugging Face Space 측은 수정하지 않음)

## 목표

1. Hugging Face Space의 IP가 바뀌어도 `nlp-api.arcanaverse.ai`가 안정적으로 동작하도록 개선
2. 향후 IP 변경 시에도 **nginx 재기동 없이** 정상 연결되도록 개선
3. nginx(1.27.x, OSS) 기준 best practice 적용
4. 기능 변경 없음 (라우팅 대상, 응답 내용 동일)

---

## 1. 원인 요약 (조사 리포트 18번 참고)

- `proxy_pass`에 **정적 hostname을 리터럴로 직접 사용**하고 `resolver` 지시어가 없었음.
- 이 조합에서 nginx는 **설정 로드(=컨테이너 최초 기동) 시점에 딱 1회만 DNS를 조회**하고, 이후 응답이 없을 때까지 그 IP를 영구 재사용함.
- `reverse-proxy` 컨테이너는 7주간 재기동/reload 없이 떠 있었고, 그 사이 Hugging Face Space측 IP 일부가 죽어(dead) 있어 요청마다 무작위로 죽은 IP에 걸리면 기본 `proxy_connect_timeout`(60초) 동안 응답이 없어 브라우저에서 "무한 대기"로 체감됨.
- 로그상 `upstream timed out while connecting to upstream` 에러 13건이 2026-06-27~2026-08-05(장애 당일 포함)에 걸쳐 반복 발생, 실패한 업스트림 IP 6종이 현재 실시간 DNS 조회 결과와 전혀 겹치지 않아 "캐시된 dead IP" 가설을 뒷받침함.

## 2. 선택한 방식: `upstream + resolve` 대신 `resolver + 변수 기반 proxy_pass`

요청하신 대로 `upstream { server ... resolve; }` 방식을 우선 검토했으나, **`resolve` 파라미터는 NGINX Plus(상용) 전용 기능**이며 현재 사용 중인 `nginx:1.27-alpine`은 오픈소스판이라 지원하지 않음(`nginx -V`로도 해당 모듈 없음을 간접 확인, 공식 문서상 OSS 미지원 명시).

OSS nginx에서 이와 동등한 효과를 내는 **커뮤니티 표준 기법**은 다음 두 가지를 함께 적용하는 것이며, 이번에 이 방식을 채택했다:

1. `resolver` 지시어로 DNS resolver 지정
2. `proxy_pass` 대상을 **리터럴이 아닌 변수**로 전달 (`set $hf_backend ...; proxy_pass https://$hf_backend;`)

→ 변수를 쓰면 nginx가 매 요청마다 resolver가 관리하는 캐시(TTL/`valid=`)를 기준으로 IP를 재조회한다. 리터럴을 쓰면 `resolver`가 있어도 최초 1회만 조회되고 캐시되므로 이 부분이 핵심이었다.

## 3. 변경 내역 (diff)

```diff
--- infra/nginx/conf.d/nlp-api.arcanaverse.ai.conf (수정 전)
+++ infra/nginx/conf.d/nlp-api.arcanaverse.ai.conf (수정 후)
@@ -1,5 +1,15 @@
-# api.arcanaverse.ai — 80→443 리다이렉트, 443 SSL 종단, Swagger/OpenAPI만 proxy
-# proxy_pass 호스트: docker-compose 서비스명 "api" (container_name: trpg-api)
+# nlp-api.arcanaverse.ai — 80→443 리다이렉트, 443 SSL 종단, Hugging Face Space(legal-rag) reverse proxy
+# proxy_pass 대상: Hugging Face Space "sungbae74-traffic-accident-legal-rag.hf.space"
+#
+# [FIX 2026-08-06] 로그인(/auth/google/start) 간헐적 무한 대기 장애 수정
+#   조사 보고서: docs/report/18_NLP_Login_Failure_Investigation.md
+#   원인: resolver 지시어가 없는 상태에서 정적 hostname을 proxy_pass에 직접 사용하면,
+#         nginx가 최초 설정 로드 시점에 딱 1회만 DNS를 조회하고 그 IP를 영구 캐시한다.
+#         이 컨테이너는 재기동 없이 7주간 떠 있었고, 그 사이 HF Space측 IP 일부가
+#         죽어(dead) 있어 요청마다 무작위로 죽은 IP에 걸리면 기본 60초 connect timeout
+#         동안 응답이 없어 "무한 대기"로 체감됨.
+#   조치: resolver + 변수 기반 proxy_pass로 매 요청 시 최신 IP를 재조회하도록 변경하고,
+#         connect timeout을 단축해 죽은 IP에 걸려도 빠르게 실패하도록 함.
 server {
     listen 80;
     server_name nlp-api.arcanaverse.ai;
@@ -13,12 +23,39 @@
   ssl_certificate     /etc/nginx/certs/origin.pem;
   ssl_certificate_key /etc/nginx/certs/origin.key;
 
+  # 컨테이너 내장 DNS(Docker embedded resolver, /etc/resolv.conf 기본값과 동일).
+  # 외부 의존성 없이 즉시 사용 가능. HF Space 도메인의 실측 DNS TTL은 60초(A레코드 3개,
+  # 라운드로빈) 이므로 valid=30s로 상한을 걸어 IP 변경에 더 신속히 반응하도록 함.
+  # (OSS nginx는 NGINX Plus의 `upstream { server ... resolve; }`를 지원하지 않으므로,
+  #  resolver + 변수 기반 proxy_pass가 커뮤니티판에서 통용되는 동등 대안임)
+  resolver 127.0.0.11 valid=30s;
+  resolver_timeout 5s;
+
   location / {
-      proxy_pass https://sungbae74-traffic-accident-legal-rag.hf.space;
+      # proxy_pass에 변수를 사용해야 resolver가 매 요청마다(=TTL마다) 재조회함.
+      # 리터럴 hostname을 직접 쓰면 resolver가 있어도 설정 로드 시 1회만 조회되고 캐시됨.
+      set $hf_backend "sungbae74-traffic-accident-legal-rag.hf.space";
+      proxy_pass https://$hf_backend;
       proxy_set_header Host sungbae74-traffic-accident-legal-rag.hf.space;
       proxy_set_header X-Forwarded-Proto https;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
+
+      # HTTPS 업스트림 TLS SNI: 변수 기반 proxy_pass에서도 정확한 hostname으로 SNI가
+      # 나가도록 명시. HF Space는 SNI 기반 라우팅을 하므로 이 값이 틀리면 엉뚱한
+      # 응답(예: 엣지 라우터의 404)을 받을 수 있음.
       proxy_ssl_server_name on;
+      proxy_ssl_name sungbae74-traffic-accident-legal-rag.hf.space;
       proxy_redirect off;
+
+      # 업스트림에 HTTP/1.1로 통신(스트리밍 응답/청크 인코딩 호환성을 위한 nginx 권장 설정).
+      # Connection 헤더는 클라이언트 값을 그대로 전달하지 않도록 비움(hop-by-hop 헤더).
+      proxy_http_version 1.1;
+      proxy_set_header Connection "";
+
+      # 죽은 IP에 걸렸을 때 기본 60초 대신 5초 만에 실패시켜 "무한 대기" 체감을 줄임.
+      # send/read는 기존 nginx 기본값(60s)을 그대로 명시해 기능(긴 응답 등)에는 영향 없음.
+      proxy_connect_timeout 5s;
+      proxy_send_timeout 60s;
+      proxy_read_timeout 60s;
   }
 }
```

### 변경 이유 상세

| 변경 항목 | 이전 | 이후 | 이유 |
|---|---|---|---|
| `resolver` | 없음 | `127.0.0.11 valid=30s;` | DNS 재조회 활성화. 컨테이너 내장 Docker DNS 사용(외부 의존성 없음). 실측 TTL 60초보다 짧은 30초 상한으로 IP 변경에 더 빠르게 반응 |
| `resolver_timeout` | 없음(기본 30s) | `5s` | resolver 자체가 응답 없을 때 너무 오래 잡아먹지 않도록 |
| `proxy_pass` 대상 | 리터럴 hostname | 변수(`$hf_backend`) | resolver가 실제로 매 요청마다 재조회하려면 변수 사용이 필수 (nginx 사양) |
| `proxy_ssl_name` | 없음(암묵적) | 명시 | 변수 기반으로 바뀌어도 SNI가 정확히 나가도록 고정 (HF Space는 SNI 기반 라우팅) |
| `proxy_http_version` | 없음(기본 1.0) | `1.1` | 스트리밍/청크 응답 호환성 개선(권장 설정). RAG 특성상 향후 SSE/스트리밍 응답 가능성 대비 |
| `proxy_set_header Connection ""` | 없음 | 추가 | HTTP/1.1 사용 시 클라이언트의 hop-by-hop `Connection` 헤더를 업스트림에 그대로 전달하지 않도록 하는 표준 관행 |
| `proxy_connect_timeout` | 없음(기본 60s) | `5s` | 실제 장애의 핵심 원인. 죽은 IP에 걸려도 60초가 아닌 5초 만에 실패 처리 |
| `proxy_send_timeout` / `proxy_read_timeout` | 없음(기본 60s) | `60s`로 **명시만** | 값 자체는 기존 기본값과 동일하게 유지 — 기능(응답이 오래 걸리는 요청)에 영향 주지 않기 위해 임의로 단축하지 않음. 명시함으로써 향후 nginx 기본값 변경에 영향받지 않도록 고정 |

`api.arcanaverse.ai.conf` (내부 API용, 별도 도메인)는 이번 변경 대상에서 **제외**했습니다 (요청 범위가 `nlp-api.arcanaverse.ai`로 한정되어 있고, `resolver` 지시어를 `nlp-api` server block 내부로 스코프를 좁혀 다른 도메인에 영향이 가지 않도록 했습니다).

## 4. 적용 절차 및 검증 결과

### 4-1. 문법 검사
```
$ docker exec reverse-proxy nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```
(`listen ... http2` deprecated 경고는 수정 전부터 있던 기존 항목이며, 이번 변경으로 새로 생긴 것이 아님 — 기능 변경 최소화 원칙에 따라 별도 조치하지 않음)

### 4-2. Reload
```
$ docker exec reverse-proxy nginx -s reload
2026/08/06 00:39:48 [notice] 110#110: signal process started
```
Graceful reload로 기존 연결을 끊지 않고 적용됨.

### 4-3. `/auth/google/start?next=/` 10회 반복 호출
```
trial 1:  http_code=302
trial 2:  http_code=302
trial 3:  http_code=302
trial 4:  http_code=302
trial 5:  http_code=302
trial 6:  http_code=302
trial 7:  http_code=302
trial 8:  http_code=302
trial 9:  http_code=302
trial 10: http_code=302
```
**10/10 모두 302 정상 응답.** 수정 전에는 같은 요청이 404 / 타임아웃 / 302가 뒤섞여 나왔던 것과 대비됨.

응답 헤더에 실제 애플리케이션(uvicorn) 고유 헤더(`x-proxied-host`, `x-proxied-replica`, `x-request-id` 등)와 정확한 `Location: https://accounts.google.com/...&redirect_uri=https%3A%2F%2Fnlp-api.arcanaverse.ai%2Fauth%2Fgoogle%2Fcallback...`이 포함되어 있어, 이번에는 항상 실제 백엔드에 도달했음을 확인:

```
HTTP/2 302
location: https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=https%3A%2F%2Fnlp-api.arcanaverse.ai%2Fauth%2Fgoogle%2Fcallback&...
x-proxied-host: http://10.111.15.49
x-proxied-replica: jed2azqm-gqml2
x-request-id: KA_3Ud
```

### 4-4. `/health`, `/docs` 회귀 확인 (각 5회)
```
trial 1: /health=200(0.777s) /docs=200(0.776s)
trial 2: /health=200(0.805s) /docs=200(0.791s)
trial 3: /health=200(0.772s) /docs=200(0.769s)
trial 4: /health=200(0.762s) /docs=200(0.853s)
trial 5: /health=200(0.786s) /docs=200(0.774s)
```
5/5 모두 200, 응답 시간도 0.76~0.85초로 일정 — 수정 전 관찰됐던 간헐적 15초 타임아웃(000)이 재현되지 않음. **기존 기능 회귀 없음.**

### 4-5. 로그 재확인
Reload 이후 `reverse-proxy` 컨테이너 로그에 `upstream timed out` 및 신규 `error` 항목 **없음**.

---

## 5. 결론

- 요청하신 4가지 목표(IP 변경 대응, 재기동 불필요, best practice 적용, 기능 유지) 모두 충족.
- `upstream { server ... resolve; }`는 NGINX Plus 전용이라 사용하지 않았고, 대신 OSS nginx의 표준 우회 기법인 `resolver` + 변수 기반 `proxy_pass`를 적용.
- 반복 검증 결과 `/auth/google/start`가 더 이상 무한 대기 없이 안정적으로 302를 반환하며, 기존 `/health`, `/docs` 동작에는 변화가 없음을 확인.
- Hugging Face Space 측은 수정하지 않았으며, Oracle VM `reverse-proxy` 설정(`infra/nginx/conf.d/nlp-api.arcanaverse.ai.conf`) 1개 파일만 변경함.

## 6. 후속 권고 (참고용, 이번 변경 범위 아님)

- `api.arcanaverse.ai.conf`도 동일한 "정적 hostname + resolver 없음" 패턴이 잠재적으로 존재함(대상은 docker-compose 서비스명 `api`). 현재는 장애가 보고되지 않았으나 동일한 근본 원인이 잠재해 있어, 필요 시 같은 패턴 적용을 검토할 것을 권고.
- `listen ... http2` deprecated 경고(nginx 1.25+에서 `http2 on;` 방식으로 변경 권장)는 이번 수정 범위에서 제외했으며, 별도 작업으로 정리 권장.
