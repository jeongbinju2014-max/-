# 초보자용 설치 · 실행 가이드

컴퓨터를 잘 몰라도 위에서부터 순서대로 그대로 따라 하면 됩니다.
막히는 단계가 있으면 **그 단계 번호와 화면에 뜬 메시지를 그대로 복사**해서 알려주세요.

이 작업은 여러분의 컴퓨터에서 직접 실행해야 합니다 (인터넷 연결, 브라우저, 구글 로그인이
필요하기 때문). 아래 내용은 Mac과 Windows 둘 다 설명하니, **본인 컴퓨터에 해당하는 부분만**
따라 하면 됩니다.

---

## 0단계. "터미널"이 뭔가요

터미널(Mac) / PowerShell(Windows)은 마우스 대신 글자로 명령을 내리는 검은/흰 화면입니다.
아래 모든 단계는 이 화면에 **명령어를 정확히 복사해서 붙여넣고 Enter**를 누르는 방식으로
진행합니다.

- **Mac**: `Cmd + Space` → "터미널" 입력 → Enter
- **Windows**: 시작 버튼 클릭 → "PowerShell" 입력 → "Windows PowerShell" 클릭

터미널 창이 하나 열리면 준비 끝입니다. 이 창을 이 작업이 끝날 때까지 계속 사용합니다.

---

## 1단계. Python 설치 확인

터미널에 아래 명령어를 입력하고 Enter.

- **Mac**: `python3 --version`
- **Windows**: `python --version`

### 결과가 `Python 3.10` 이상 숫자로 나오면
설치돼 있는 것이니 2단계로 넘어가세요.

### "command not found" 또는 오류가 나오면 (설치 필요)
1. https://www.python.org/downloads/ 접속
2. 노란색/파란색 "Download Python 3.x.x" 큰 버튼 클릭 → 다운로드된 설치 파일 실행
3. **(Windows만 해당, 매우 중요)** 설치 화면 맨 아래 **"Add python.exe to PATH"** 체크박스를
   반드시 체크한 다음 "Install Now" 클릭
4. 설치가 끝나면 **터미널 창을 완전히 닫고 다시 연 뒤**, 1단계 명령어를 다시 실행해서
   버전이 나오는지 확인

---

## 2단계. Git 설치 확인

터미널에 입력:

```
git --version
```

- 버전이 나오면 통과.
- **Mac**: 오류가 나면 "명령어 도구를 설치하시겠습니까?" 같은 팝업이 뜹니다 → "설치" 클릭 →
  끝날 때까지 기다렸다가 다시 `git --version` 실행.
- **Windows**: 오류가 나면 https://git-scm.com/download/win 접속 → 다운로드된 설치 파일 실행 →
  화면마다 그냥 "Next"만 눌러서 설치 완료 → 터미널 다시 열기.

---

## 3단계. 프로젝트 다운로드

터미널에 아래 명령어를 **한 줄씩** 입력 (줄마다 Enter):

```
git clone https://github.com/jeongbinju2014-max/- kleague-xg
cd kleague-xg
git checkout claude/seoul-eland-xg-extraction-04vpnp
```

이제 터미널 프롬프트(왼쪽 글자)에 `kleague-xg` 라는 폴더 이름이 보이면 성공입니다.
**이후 모든 명령어는 이 폴더 안에서 실행**한다고 생각하면 됩니다 (터미널을 새로 열면
`cd kleague-xg`를 다시 입력해서 이 폴더로 들어와야 함).

---

## 4단계. 파이썬 가상환경 만들기

"가상환경"은 이 프로젝트 전용 파이썬 상자를 하나 만드는 것입니다 (다른 프로그램과 안 섞이게).
아래 명령어를 순서대로, 한 줄씩 입력하세요.

### Mac
```
python3 -m venv .venv
source .venv/bin/activate
```

### Windows (PowerShell)
```
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> **Windows에서 "실행할 수 없습니다" / "스크립트 실행이 비활성화되어 있습니다" 오류가 나면:**
> PowerShell에 아래 명령어를 입력해 Enter → `Y` 입력 후 Enter → 그다음 위 `Activate.ps1`
> 명령어를 다시 실행하세요.
> ```
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

성공하면 터미널 맨 왼쪽에 `(.venv)`라는 글자가 새로 붙습니다. **앞으로 이 터미널 창에서
작업할 때는 항상 `(.venv)`가 보이는 상태여야 합니다.** (터미널을 닫았다 새로 열면 3단계의
`cd kleague-xg`와 이 4단계의 activate 명령어를 다시 실행해야 `(.venv)`가 다시 붙습니다.)

---

## 5단계. 필요한 패키지 설치

`(.venv)`가 보이는 상태에서 아래 명령어를 순서대로 입력 (각각 몇 초~몇 분 걸릴 수 있음,
글자가 주르륵 나오다가 멈추면 완료된 것):

```
pip install -r requirements.txt
playwright install chromium
```

두 번째 명령어는 화면을 읽기 위한 미니 브라우저(용량 큼, 다운로드에 시간이 좀 걸릴 수
있음)를 설치하는 것입니다. 끝날 때까지 기다려주세요.

---

## 6단계. 구글 서비스 계정 만들기 (구글시트에 자동으로 쓰기 위한 열쇠)

이건 터미널이 아니라 **웹 브라우저**에서 진행합니다.

1. https://console.cloud.google.com/ 접속 → 구글 계정(jeongbinju2014@gmail.com)으로 로그인
2. 화면 위쪽 "프로젝트 선택" 클릭 → "새 프로젝트" 클릭 → 이름은 아무거나(예: `kleague-xg`)
   입력 → "만들기" 클릭. 몇 초 기다린 뒤 방금 만든 프로젝트를 다시 선택.
3. 왼쪽 상단 ☰(메뉴) → "API 및 서비스" → "라이브러리" 클릭
4. 검색창에 `Google Sheets API` 입력 → 검색 결과 클릭 → 파란 "사용" 버튼 클릭
5. 같은 방법으로 `Google Drive API`도 검색해서 "사용" 클릭
6. 왼쪽 메뉴 "API 및 서비스" → "사용자 인증 정보" 클릭
7. 위쪽 "+ 사용자 인증 정보 만들기" → "서비스 계정" 클릭
8. 서비스 계정 이름 아무거나 입력(예: `xg-sheet-bot`) → "만들기 및 계속하기" → 다음 화면들은
   그냥 "계속" → "완료" 클릭
9. 방금 만든 서비스 계정 이름을 목록에서 클릭 → 위쪽 탭 중 "키" 클릭 → "키 추가" →
   "새 키 만들기" → 키 유형 "JSON" 선택 → "만들기" 클릭
   → `xxxxx.json` 파일이 자동으로 다운로드됩니다 (보통 "다운로드" 폴더에 저장됨).
10. **이 파일이 비밀번호 역할을 합니다. 남에게 공유하거나 인터넷에 올리면 안 됩니다.**
11. 방금 다운로드된 파일을 **`kleague-xg` 프로젝트 폴더 안으로 옮기고**,
    파일 이름을 정확히 `service-account.json`으로 바꿔주세요.
    - Mac: Finder에서 다운로드 폴더 → 파일을 kleague-xg 폴더로 드래그 → 이름 바꾸기(Enter)
    - Windows: 탐색기에서 다운로드 폴더 → 파일을 kleague-xg 폴더로 드래그 → 이름 바꾸기(F2)
12. 그 JSON 파일을 텍스트 편집기(메모장 등)로 열어서 `"client_email"` 항목의 값을
    복사해두세요. 형태가 `xg-sheet-bot@프로젝트이름.iam.gserviceaccount.com` 같이
    생겼습니다. 다음 단계에서 씁니다.

---

## 7단계. 데이터를 받을 구글시트 준비

1. https://sheets.google.com 접속 → "빈 스프레드시트"로 새 시트 생성 (이름은 자유롭게,
   예: "서울이랜드 xG")
2. 오른쪽 위 "공유" 버튼 클릭 → 6단계 11번에서 복사해둔 `client_email` 주소를 붙여넣기 →
   권한을 **"편집자"**로 설정 → "보내기"(또는 "공유") 클릭
   (경고 팝업이 뜨면 "알림 없이 공유"를 선택해도 됩니다)
3. 주소창의 URL을 보면 다음과 같은 형태입니다:
   `https://docs.google.com/spreadsheets/d/`**`1AbCdEfGhIjKlMnOpQrStUvWxYz`**`/edit`
   굵게 표시한 긴 글자(영문+숫자 조합)가 "스프레드시트 ID"입니다. 복사해두세요.

---

## 8단계. 환경설정 파일(.env) 만들기

1. `kleague-xg` 폴더를 파일 탐색기(Finder/탐색기)로 열어서, `.env.example` 파일을 복사해
   같은 폴더에 붙여넣고 이름을 `.env`로 바꿔주세요.
   (터미널로 하려면: `cp .env.example .env`)
2. `.env` 파일을 메모장/텍스트편집기로 열어서 아래처럼 채워주세요:

```
GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json
GOOGLE_SHEET_ID=7단계에서_복사한_스프레드시트_ID
GOOGLE_WORKSHEET_NAME=서울이랜드_xG
KLEAGUE_BASE_URL=https://data.kleague.com/
MENU_CLICK_PATH=데이터 센터,부가기록,기대득점,선수별 기대득점
```

`GOOGLE_SHEET_ID=` 뒤에 7단계에서 복사한 긴 ID를 붙여넣고 저장하세요.

---

## 9단계. 실행!

터미널로 돌아와서 (여전히 `kleague-xg` 폴더 안, `(.venv)`가 보이는 상태인지 확인) 아래
명령어를 입력합니다.

- **Mac**: `python3 src/scrape_xg.py`
- **Windows**: `python src/scrape_xg.py`

화면에 `[정보] 접속: https://data.kleague.com/` 같은 로그가 주르륵 나오다가,

- `[완료] N명의 선수 데이터를 data/xg_players.csv 에 저장했습니다.` 가 나오면 **성공**입니다.
- `[오류] ...` 로 시작하는 줄이 나오면 실패한 것이니, **그 오류 문장 전체를 그대로
  복사해서** 알려주세요. `data/debug_screenshot.png` 파일도 함께 생성되니, 그 이미지를
  보내주시면 원인을 훨씬 빨리 찾을 수 있습니다.

성공했다면 이어서:

```
python src/update_sheet.py     (Windows는 python, Mac은 python3)
```

를 실행해서 방금 모은 데이터를 구글시트에 반영합니다. 실행 후 7단계에서 만든 구글시트를
새로고침 해보면 데이터가 들어가 있어야 합니다.

---

## 자주 나오는 오류 해결법

| 오류 메시지 | 원인 / 해결 |
|---|---|
| `command not found: python3` | 1단계 다시 진행, 설치 후 터미널 재시작 |
| `No module named playwright` 등 | 4단계에서 `(.venv)`가 안 보이는 상태에서 5단계를 건너뛴 경우. 4단계 activate 명령어부터 다시 |
| `메뉴 'X'을(를) 화면에서 찾지 못했습니다` | 사이트 메뉴 글자가 바뀐 것. `data/debug_screenshot.png` 확인 후 공유 |
| `[오류] 표를 찾지 못했습니다` | 페이지 구조가 예상과 다름. 마찬가지로 스크린샷 공유 |
| `GOOGLE_SHEET_ID가 설정되어 있지 않습니다` | 8단계에서 `.env` 저장을 안 했거나 오타 |
| `구글 서비스 계정 인증 정보를 찾을 수 없습니다` | `service-account.json` 파일이 `kleague-xg` 폴더 최상위에 정확한 이름으로 있는지 확인 |
| 구글시트에 반영은 됐는데 "권한 없음" 오류 | 7단계 2번에서 서비스 계정 이메일을 "편집자"로 공유했는지 다시 확인 |

막히면 언제든 그 단계 번호 + 화면 메시지를 그대로 보내주세요.
