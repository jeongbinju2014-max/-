# 서울 이랜드 FC xG 데이터 → 구글시트 자동 업데이트

한국프로축구연맹 K리그 데이터포탈(`data.kleague.com`, 경로: 데이터센터 → 부가기록 →
기대득점 → 선수별 기대득점)에서 서울 이랜드 FC 소속 선수들의 xG(기대득점, Expected Goals)
기록을 가져와 구글시트에 자동으로 업데이트하는 도구입니다.

> 컴퓨터 사용이 익숙하지 않다면, 이 README 대신 **[SETUP_GUIDE.md](SETUP_GUIDE.md)**를
> 처음부터 끝까지 그대로 따라 하세요. 터미널 여는 법부터 클릭 한 번 한 번까지 설명되어
> 있습니다.

## ⚠️ 먼저 읽어주세요 (중요)

이 코드는 초안입니다. `data.kleague.com`은 봇 차단(WAF)이 걸려 있어 이 코드를 만든
환경에서는 어떤 방법으로도(직접 접속, 웹 조회 도구 모두 403) 실제 페이지에 접근하지
못했습니다. 확인된 사실은 다음과 같습니다.

- 사이트는 **SPA**라서 "데이터센터 → 부가기록 → 기대득점 → 선수별 기대득점" 메뉴를
  눌러도 주소창 URL은 바뀌지 않는다 (사용자 확인).
- 그래서 스크립트는 기본 URL(`https://data.kleague.com/`)로 접속한 뒤,
  이 메뉴 경로를 **순서대로 자동 클릭**해서 화면에 도달하도록 만들어져 있다
  (`src/config.py`의 `MENU_CLICK_PATH`).
- 팀별 필터는 없고 K리그2 전체 선수 표만 나오므로, 전체 표를 다 모은 뒤
  구단명(팀명) 열 값으로 서울 이랜드 FC만 걸러낸다.

메뉴 텍스트나 표 헤더가 실제 사이트와 다르면 동작하지 않을 수 있으니,
아래 "1단계: 사이트 구조 확인"을 먼저 진행해 `src/config.py`를 실제 값에 맞게
조정해주세요.

## 전체 흐름

```
data.kleague.com 접속 (Playwright)
        │  메뉴 자동 클릭: 데이터센터 → 부가기록 → 기대득점 → 선수별 기대득점
        ▼
K리그2 전체 선수 xG 표를 페이지네이션 따라가며 전부 수집
        │
        ▼
구단명(팀명) 열이 "서울 이랜드 FC"인 행만 필터링 → data/xg_players.csv
        │
        ▼
gspread(Google Sheets API)로 구글시트에 업로드/갱신
        │
        ▼
(선택) GitHub Actions로 매일 자동 실행
```

## 1단계: 사이트 구조 확인 (사용자가 브라우저에서 직접, 1회)

1. 크롬에서 `https://data.kleague.com/` 접속 → **데이터센터 → 부가기록 → 기대득점 →
   선수별 기대득점** 메뉴를 순서대로 클릭합니다.
2. 각 메뉴의 정확한 글자(공백 포함)가 스크립트의 `MENU_CLICK_PATH`와 같은지 확인합니다.
   기본값은 `데이터센터,부가기록,기대득점,선수별 기대득점` 입니다. 다르면
   `.env`의 `MENU_CLICK_PATH`를 쉼표로 구분해 실제 텍스트로 바꿔주세요.
3. **더 안정적인 방법을 원하면(선택, 권장):** F12 개발자도구 → Network 탭 → 상단
   필터를 **"Fetch/XHR"로 선택**한 뒤(전체가 아니라 XHR만 봐야 이미지/CSS가 안 섞입니다)
   "선수별 기대득점" 메뉴를 클릭합니다. 목록에 새로 뜨는 요청 중 `.gif`/`.png`/`.css`/`.js`가
   아닌 것(이름에 `player`, `expected`, `record`, `stat` 등이 들어간 것)을 찾아 클릭 →
   오른쪽 "Response" 또는 "Preview" 탭에 선수 이름/xG 숫자가 담긴 JSON이 보이면, 그
   요청 URL을 알려주세요. 있으면 지금의 "화면을 읽는" 방식보다 훨씬 간단하고 안정적인
   API 직접 호출 방식으로 바꿔드릴 수 있습니다.
4. 표가 여러 페이지로 나뉘어 있다면(페이지 하단에 1, 2, 3 ... 또는 "다음" 버튼) 스크립트가
   자동으로 다음 페이지를 눌러가며 전체 데이터를 모읍니다. 그 버튼의 텍스트가 "다음"이
   아니면 `config.PAGINATION_NEXT_HINTS`에 추가해주세요.
5. 표(테이블)의 헤더 행에 있는 정확한 열 이름(예: "선수명", "구단명", "기대득점(xG)")을
   확인하고, 실제 표기가 다르면 `config.COLUMN_HEADER_HINTS`와
   `config.TEAM_NAME_CANDIDATES`(서울 이랜드가 사이트에 표기되는 정확한 이름)를 맞춰주세요.

확인한 내용을 `src/config.py`와 `.env`에 채워 넣으세요.

## 2단계: 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## 3단계: 구글시트 연동 준비

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. "Google Sheets API"와 "Google Drive API" 활성화
3. 서비스 계정(Service Account) 생성 → JSON 키 다운로드
4. 업데이트할 구글시트를 열어서, 서비스 계정 이메일(`xxx@xxx.iam.gserviceaccount.com`)을
   **편집자**로 공유
5. 구글시트 URL에서 스프레드시트 ID 확인
   (`https://docs.google.com/spreadsheets/d/여기부분/edit`)
6. 환경변수 설정 (`.env` 파일 생성, `.env.example` 참고)

```
GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json
GOOGLE_SHEET_ID=여기에_스프레드시트_ID
GOOGLE_WORKSHEET_NAME=서울이랜드_xG
KLEAGUE_BASE_URL=https://data.kleague.com/
MENU_CLICK_PATH=데이터센터,부가기록,기대득점,선수별 기대득점
```

## 4단계: 실행

```bash
python src/scrape_xg.py      # 데이터 수집 → data/xg_players.csv 생성
python src/update_sheet.py   # csv를 구글시트에 반영
```

또는 한 번에:

```bash
python src/run_all.py
```

메뉴 클릭이나 표 찾기에 실패하면 `data/debug_screenshot.png`가 자동 저장되니
그 화면을 보고 `config.py`를 조정하거나 스크린샷을 공유해주세요.

## 5단계 (선택): 매일 자동 업데이트 — GitHub Actions

`.github/workflows/update-xg-sheet.yml`이 이미 포함되어 있습니다.
저장소 Settings → Secrets and variables → Actions 에서 아래 값을 등록하면
매일 정해진 시간(기본 KST 09:00)에 자동으로 실행됩니다.

**Secrets:**
- `GOOGLE_SERVICE_ACCOUNT_JSON` : 서비스 계정 JSON 파일 내용 전체(문자열)
- `GOOGLE_SHEET_ID` : 스프레드시트 ID

**Variables (Settings → Secrets and variables → Actions → Variables):**
- `KLEAGUE_BASE_URL` : `https://data.kleague.com/` (기본값 그대로 써도 됨)
- `MENU_CLICK_PATH` : `데이터센터,부가기록,기대득점,선수별 기대득점`
- `GOOGLE_WORKSHEET_NAME` : 예) `서울이랜드_xG`

실패하면 Actions 실행 결과의 "debug-screenshot" 아티팩트에서 그 시점 화면을
확인할 수 있습니다.

## 폴더 구조

```
src/
  config.py       # 설정값 (URL, 메뉴 경로, 팀명, 열 이름 매핑)
  scrape_xg.py    # Playwright로 K리그 포탈에서 xG 표 추출
  update_sheet.py # gspread로 구글시트 업데이트
  run_all.py      # scrape → update 순차 실행
data/
  xg_players.csv  # 최근 수집 결과 (실행 후 생성됨)
  debug_screenshot.png  # 실패 시 자동 저장되는 디버깅용 스크린샷
.github/workflows/update-xg-sheet.yml
```

## 문제가 생기면

- 메뉴 클릭이 실패하면(`메뉴 'X'을(를) 화면에서 찾지 못했습니다`): 실제 메뉴 글자를
  확인해 `MENU_CLICK_PATH`를 맞춰주세요. `data/debug_screenshot.png`도 확인해보세요.
- `scrape_xg.py`가 표를 못 찾으면: `COLUMN_HEADER_HINTS`(config.py)에 실제 사이트의
  헤더 텍스트를 추가해 보세요.
- 로그인/세션이 필요한 페이지라면: `scrape_xg.py`에 로그인 단계를 추가해야 합니다.
- Network 탭에서 JSON API 요청을 찾았다면, 그 URL(과 요청 시 필요한 파라미터)을
  알려주시면 훨씬 안정적인 API 직접 호출 방식으로 바꿔드릴 수 있습니다.
