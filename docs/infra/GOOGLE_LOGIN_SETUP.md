# 구글 로그인 설정 가이드

## 1. Google Cloud Console 설정

### 1.1 프로젝트 생성 및 OAuth 2.0 클라이언트 ID 발급

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 프로젝트 생성 또는 기존 프로젝트 선택
3. **API 및 서비스** > **사용자 인증 정보**로 이동
4. **+ 사용자 인증 정보 만들기** > **OAuth 클라이언트 ID** 선택
5. **애플리케이션 유형**: 웹 애플리케이션
6. **승인된 JavaScript 원본**:
   - `http://localhost:8080` (개발 환경)
   - `https://yourdomain.com` (프로덕션 환경)
7. **승인된 리디렉션 URI**: 비워두거나 필요시 추가
8. **만들기** 클릭하여 클라이언트 ID 발급

### 1.2 클라이언트 ID 확인

발급된 클라이언트 ID를 복사합니다. (예: `123456789-abcdefghijklmnop.apps.googleusercontent.com`)

## 2. 프론트엔드 설정

### 2.1 `my.html` 파일 수정

`apps/web-html/my.html` 파일에서 다음 부분을 찾아 클라이언트 ID를 입력:

```javascript
google.accounts.id.initialize({
  client_id: 'YOUR_GOOGLE_CLIENT_ID', // ← 여기에 발급받은 클라이언트 ID 입력
  callback: handleGoogleLogin,
  // ...
});
```

**예시:**
```javascript
client_id: '123456789-abcdefghijklmnop.apps.googleusercontent.com',
```

## 3. 백엔드 설정 (선택사항)

### 3.1 JWT 시크릿 키 설정

프로덕션 환경에서는 환경 변수로 JWT 시크릿 키를 설정하세요:

```bash
# .env 파일 또는 환경 변수
JWT_SECRET=your-very-secure-random-secret-key-here
```

**주의**: 개발 환경에서는 기본값을 사용하지만, 프로덕션에서는 반드시 안전한 시크릿 키를 사용하세요.

## 4. 테스트

### 4.1 서비스 재시작

```bash
cd infra
docker-compose restart api web
```

### 4.2 로그인 테스트

1. 브라우저에서 `http://localhost:8080/home.html` 접속
2. 상단 네비게이션 바에서 **My** 클릭
3. 구글 로그인 버튼 클릭
4. Google 계정으로 로그인
5. 로그인 성공 시 프로필 정보가 표시되는지 확인

## 5. 기능 확인

### 5.1 로그인 후 기능

- ✅ My 메뉴에서 프로필 정보 확인
- ✅ 채팅 시 로그인 토큰이 자동으로 전송
- ✅ 다른 메뉴(Search, Create, My List) 접근 시 로그인 체크 통과

### 5.2 비로그인 시 기능

- ✅ 다른 메뉴 클릭 시 "로그인이 필요합니다." 팝업 표시
- ✅ My 메뉴는 접근 가능 (로그인 페이지로 사용)

## 6. 문제 해결

### 6.1 "Invalid Client" 오류

- 클라이언트 ID가 올바르게 입력되었는지 확인
- Google Cloud Console에서 승인된 JavaScript 원본에 현재 도메인이 포함되어 있는지 확인

### 6.2 "Token verification failed" 오류

- 네트워크 연결 확인
- Google API 접근 가능 여부 확인

### 6.3 로그인은 되지만 채팅에서 토큰이 전송되지 않음

- 브라우저 개발자 도구(F12) > Network 탭에서 `/v1/chat/` 요청 헤더 확인
- `Authorization: Bearer ...` 헤더가 포함되어 있는지 확인

## 7. API 엔드포인트

- `POST /v1/auth/google` - 구글 로그인
- `GET /v1/auth/me` - 현재 사용자 정보 조회 (Authorization 헤더 필요)
- `POST /v1/auth/logout` - 로그아웃

## 8. 보안 고려사항

1. **JWT 시크릿 키**: 프로덕션 환경에서는 환경 변수로 관리
2. **HTTPS**: 프로덕션 환경에서는 반드시 HTTPS 사용
3. **토큰 만료 시간**: 현재 7일로 설정되어 있음 (필요시 조정)
4. **CORS 설정**: `CORS_ALLOW_ORIGINS` 환경 변수로 허용 도메인 제한

