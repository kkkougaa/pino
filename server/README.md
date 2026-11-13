# 코우가 챌린지 랭킹 서버 만들기

**Cloudflare Workers**(서버 코드) + **D1**(데이터베이스)로 만들어요.

- **무료**예요. 하루 요청 10만 건, DB 5GB까지 무료라서 3일짜리 이벤트에는 충분해요.
- 서버 컴퓨터를 직접 관리할 필요가 없어요. 코드만 올리면 전 세계에서 빠르게 응답해요.
- 이 폴더(`server/`)에 필요한 코드가 다 들어 있어요. 아래 순서대로만 하면 돼요.

```
server/
├─ src/index.js    서버 본체 (토큰 발급, 점수 등록, 랭킹, 관리자)
├─ src/rules.js    점수 검사 규칙 (숫자를 여기서 조절해요)
├─ src/admin.js    관리자 페이지 (/admin)
├─ schema.sql      데이터베이스 표 구조
├─ wrangler.toml   서버 설정 (DB 연결, 이벤트 기간)
└─ test/local.mjs  내 컴퓨터에서 돌려 보는 테스트
```

---

## 0. 준비물

1. **Node.js 20 이상**: https://nodejs.org 에서 LTS 버전을 설치해요.
2. **Cloudflare 계정**: https://dash.cloudflare.com/sign-up 에서 이메일로 가입해요(무료).

터미널(맥은 "터미널", 윈도우는 "PowerShell")을 열고 이 폴더로 이동해요.

```bash
cd pino/server
```

## 1. 내 컴퓨터에서 먼저 돌려 보기 (선택)

Cloudflare에 올리기 전에 동작을 확인할 수 있어요.

```bash
node --no-warnings test/local.mjs
```

`PASS`가 23줄 나오면 정상이에요. 샘플 랭킹이 들어간 가짜 서버를 띄워 볼 수도 있어요.

```bash
node --no-warnings test/local.mjs serve demo
```

이 상태에서 `pino.html`의 `RANK_API`를 `'http://localhost:8787'`로 바꾸고 게임을 열면 랭킹 기능을 체험할 수 있어요. 관리자 페이지는 http://localhost:8787/admin 이고, 키는 `test-admin`이에요.

## 2. Cloudflare에 로그인

```bash
npx wrangler login
```

브라우저가 열리면 "Allow"를 눌러요. `wrangler`는 Cloudflare 공식 도구이고, `npx`가 알아서 내려받아요.

## 3. 데이터베이스 만들기

```bash
npx wrangler d1 create kouga-ranking
```

출력에 이런 줄이 나와요.

```
database_id = "1234abcd-...."
```

이 값을 복사해서 `wrangler.toml`의 `database_id = "PUT-YOUR-DATABASE-ID-HERE"` 자리에 붙여 넣어요.

그다음 표를 만들어요.

```bash
npx wrangler d1 execute kouga-ranking --remote --file=schema.sql
```

## 4. 이벤트 기간 정하기

`wrangler.toml`에서 시작과 끝 시각을 바꿔요. 끝에 붙은 `+09:00`은 한국·일본 시간이라는 뜻이에요.

```toml
EVENT_START = "2026-11-10T18:00:00+09:00"
EVENT_END   = "2026-11-13T18:00:00+09:00"
```

- 이 기간 **안에 시작한 판**만 랭킹에 들어가요.
- 기간 전에는 게임 화면에 "◯ 뒤 시작", 끝난 뒤에는 "종료 · 최종 순위"가 나와요.

## 5. 관리자 키 정하기

관리자 페이지에서 쓸 비밀번호예요. 길고 아무도 모르는 값으로 정해요.

```bash
npx wrangler secret put ADMIN_KEY
```

입력하라고 나오면 키를 붙여 넣어요. 화면에 안 보여도 정상이에요. 이 키는 Cloudflare에만 저장되고 코드에는 들어가지 않아요.

## 6. 서버 올리기

```bash
npx wrangler deploy
```

마지막에 이런 주소가 나와요. 이게 랭킹 서버 주소예요.

```
https://kouga-ranking.<내아이디>.workers.dev
```

브라우저에서 `그주소/api/event`를 열어 `{"start":...,"open":...}`가 보이면 성공이에요.

## 7. 게임에 연결하기

`pino.html`에서 `const RANK_API='';`를 찾아 주소를 넣어요.

```js
const RANK_API='https://kouga-ranking.<내아이디>.workers.dev';
```

- 이 값이 비어 있으면 랭킹 기능이 화면에서 통째로 숨겨져요.
- 게임을 올려 둔 주소가 정해지면, 다른 사이트에서 서버를 쓰지 못하게 `wrangler.toml`의 `ALLOWED_ORIGIN`을 그 주소로 바꾸고 다시 `npx wrangler deploy` 해요.
  예: `ALLOWED_ORIGIN = "https://kkkougaa.github.io"`

## 8. 운영하기 (관리자 페이지)

`https://kouga-ranking.<내아이디>.workers.dev/admin` 에서 5번에서 정한 키를 넣고 "불러오기"를 눌러요.

| 탭 | 뜻 | 할 일 |
|---|---|---|
| **검토 대기** | 가능은 하지만 자동 플레이보다 훨씬 높은 점수 | 확인 후 **공개** 또는 **삭제** |
| **공개 중** | 랭킹에 보이는 기록 | 이상하면 **삭제** |
| **자동 거절** | 게임에서 나올 수 없는 기록 (사유 표시) | 보통은 그대로 둬요 |
| **삭제됨** | 지운 기록 | 실수로 지웠으면 **공개** |

X 아이디는 관리자 페이지에서만 보여요. 아이디를 누르면 그 사람의 X 프로필이 열려요.

## 점수 검사 규칙 (`src/rules.js`)

**자동 거절**(게임에서 불가능한 기록)
- 게임 시간이 실제 흐른 시간보다 길다
- 시간에 비해 상자를 너무 많이 먹었다 (상자 하나 최소 1.2초)
- 먹은 알 수와 상자 수가 안 맞는다, 콤보가 먹은 알보다 길다
- 너무 이른 시점에 화남이나 폭주에 도달했다
- 모든 보너스를 최대로 받아도 나올 수 없는 점수다

**검토 대기**(가능하지만 수상한 기록)
- 실수 없이 콤보를 계속 이은 자동 플레이 기준(초당 약 1,300점 × 단계 배율)에 하트·별·순찰 보너스를 다 더하고, 그보다 30% 넘게 높은 점수

숫자는 파일 위쪽 `RULES`에서 조절할 수 있어요. 바꾼 뒤에는 `npx wrangler deploy`로 다시 올려요.

## 다음 이벤트를 열 때

1. `wrangler.toml`의 기간을 바꾸고 `npx wrangler deploy` 해요.
2. 지난 기록을 지우고 새로 시작하려면 아래 명령을 써요(되돌릴 수 없어요).

```bash
npx wrangler d1 execute kouga-ranking --remote --command "DELETE FROM scores; DELETE FROM tokens;"
```
