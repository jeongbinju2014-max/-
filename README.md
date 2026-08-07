# 서울 이랜드 FC xG 데이터 → 구글시트 자동 업데이트

한국프로축구연맹 K리그 데이터포탈(`portal.kleague.com`)에서 서울 이랜드 FC 소속 선수들의
xG(기대득점, Expected Goals) 기록을 가져와 구글시트에 자동으로 업데이트하는 도구입니다.

## ⚠️ 먼저 읽어주세요 (중요)

이 코드는 초안입니다. K리그 데이터포탈은 로그인/세션(JSP, frame) 기반의 동적 사이트라
정확한 페이지 URL과 표(테이블) 구조를 **직접 브라우저로 한 번 확인**해야 합니다.
(이 코드를 만든 환경에서는 보안 정책상 `portal.kleague.com`에 직접 접속할 수 없어
실제 HTML 구조를 확인하지 못했습니다.)

아래 "1단계: 사이트 구조 확인"을 먼저 진행한 뒤, `src/config.py`의 값 몇 개만 채우면
나머지는 그대로 동작하도록 만들었습니다.

## 전체 흐름

```
K리그 데이터포탈 (Playwright로 브라우저 자동조작)
        │  K리그2 전체 선수 xG 표를 페이지네이션 따라가며 전부 수집
        ▼
구단명(팀명) 열이 "서울 이랜드 FC"인 행만 필터링 → data/xg_players.csv
        │
        ▼
gspread(Google Sheets API)로 구글시트에 업로드/갱신
        │
        ▼
(선택) GitHub Actions로 매일 자동 실행
```

## 1단계: 사이트 구조 확인 (사용자가 브라우저에서 직접)

1. 크롬에서 `https://portal.kleague.com` 접속
2. 좌측/상단 메뉴에서 "기록실" 또는 "선수 기록" → "기대득점(xG)" 관련 메뉴를 찾습니다.
   (K리그2 전체 선수 xG 표가 나오는 페이지이며, **팀별 필터는 없습니다** —
   서울 이랜드 FC 소속 선수만 보려면 전체 표에서 "구단명" 열 값으로 직접 찾아야 합니다.)
3. 그 페이지의 URL을 그대로 `KLEAGUE_STATS_URL`로 사용합니다.
4. 표가 여러 페이지로 나뉘어 있다면(페이지 하단에 1, 2, 3 ... 또는 "다음" 버튼) 몇 페이지까지
   있는지 확인합니다. 스크립트는 "다음" 버튼을 자동으로 눌러가며 전체 페이지를 모두 수집한
   뒤, 마지막에 구단명으로 서울 이랜드 FC만 걸러냅니다.
5. F12 개발자도구 → Network 탭에서 페이지 이동 시 XHR/Fetch로 JSON 응답이 오는지 확인합니다.
   JSON API가 보이면 표를 직접 파싱하는 것보다 훨씬 안정적이니, 확인되면 알려주시면
   API 방식으로 바꿔드릴 수 있습니다.
6. 표(테이블)의 헤더 행에 있는 정확한 열 이름(예: "선수명", "구단명", "기대득점(xG)")을
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
KLEAGUE_STATS_URL=여기에_1단계에서_확인한_URL
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

## 5단계 (선택): 매일 자동 업데이트 — GitHub Actions

`.github/workflows/update-xg-sheet.yml`이 이미 포함되어 있습니다.
저장소 Settings → Secrets and variables → Actions 에서 아래 시크릿을 등록하면
매일 정해진 시간(기본 KST 09:00)에 자동으로 실행됩니다.

- `GOOGLE_SERVICE_ACCOUNT_JSON` : 서비스 계정 JSON 파일 내용 전체(문자열)
- `GOOGLE_SHEET_ID` : 스프레드시트 ID
- `KLEAGUE_STATS_URL` : 1단계에서 확인한 선수 기록 페이지 URL

## 폴더 구조

```
src/
  config.py       # 설정값 (URL, 팀명, 열 이름 매핑)
  scrape_xg.py    # Playwright로 K리그 포탈에서 xG 표 추출
  update_sheet.py # gspread로 구글시트 업데이트
  run_all.py      # scrape → update 순차 실행
data/
  xg_players.csv  # 최근 수집 결과 (실행 후 생성됨)
.github/workflows/update-xg-sheet.yml
```

## 문제가 생기면

- `scrape_xg.py`가 표를 못 찾으면: `COLUMN_HEADER_HINTS`(config.py)에 실제 사이트의
  헤더 텍스트를 추가해 보세요.
- 팀 필터가 자동으로 안 눌리면: `select_team()` 함수의 셀렉터를 브라우저 개발자도구에서
  확인한 실제 값으로 바꿔주세요 (예: `select` 태그의 `name` 속성, 또는 버튼의 텍스트).
- 로그인/세션이 필요한 페이지라면: `scrape_xg.py`에 로그인 단계를 추가해야 합니다.
