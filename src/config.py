"""설정값. README 1단계에서 확인한 내용을 여기에 채워 넣으세요."""
import datetime
import os

from dotenv import load_dotenv

load_dotenv()

# data.kleague.com은 SPA라 메뉴를 눌러도 주소창 URL이 바뀌지 않는다.
# 그래서 기본 URL로 접속한 뒤, 아래 메뉴 경로를 순서대로 자동 클릭해서
# "선수별 기대득점" 화면으로 들어간다.
KLEAGUE_BASE_URL = os.environ.get("KLEAGUE_BASE_URL", "https://data.kleague.com/")

# 데이터센터 → 부가기록 → 기대득점 → 선수별 기대득점
# (실제 사이트 상단 메뉴 표기는 "데이터센터", 띄어쓰기 없음 - 사용자 스크린샷으로 확인됨)
# 실제 메뉴 텍스트가 다르면(예: "선수별 기대 득점" 등) 여기를 맞춰주세요.
MENU_CLICK_PATH = os.environ.get(
    "MENU_CLICK_PATH", "데이터센터,부가기록,기대득점,선수별 기대득점(xG)"
).split(",")

# 메뉴 클릭 사이 대기 시간(ms). SPA 전환 애니메이션/데이터 로딩 시간을 감안.
MENU_CLICK_WAIT_MS = int(os.environ.get("MENU_CLICK_WAIT_MS", "1500"))

# "선수별 기대득점(xG)" 화면의 "대회명" 드롭다운 기본값이 K리그1이라,
# 서울 이랜드 FC(K리그2 소속)를 보려면 K리그2로 바꿔줘야 한다.
COMPETITION_NAME_CANDIDATES = os.environ.get(
    "COMPETITION_NAME_CANDIDATES", "K리그2,K리그 2,하나은행 K리그2"
).split(",")

# "대회년도" 드롭다운. 명시적으로 안 맞춰주면 사이트 기본값에 의존하게 되어
# 어떤 시즌 데이터를 보고 있는지 불확실해질 수 있어, 실행 시점의 연도로
# 매번 강제 지정한다. 필요하면 SEASON_YEAR 환경변수로 덮어쓸 수 있다.
SEASON_YEAR = os.environ.get("SEASON_YEAR", str(datetime.datetime.now().year))

# 조건을 채운 뒤 눌러야 하는 검색 버튼 텍스트 후보.
SEARCH_BUTTON_HINTS = os.environ.get("SEARCH_BUTTON_HINTS", "조회,검색").split(",")

# 사이트에는 팀별 필터가 없고 K리그2 전체 선수 표만 제공됨.
# 그 표에서 "구단" 열 값이 아래 후보 중 하나로 "시작하면" 남긴다(포함이 아니라
# 시작 일치 — "서울"만으로 매칭하면 "FC서울"(K리그1)까지 걸릴 수 있는데,
# "FC서울"은 "서울"로 시작하지 않으므로 시작 일치는 안전함).
# 9월 2일 이후 사이트가 구단명 표기를 "서울 이랜드"에서 "서울"로 축약
# 표시하도록 바뀐 적이 있어(실행 로그로 확인, 2026-09-08) 두 표기 모두 둔다.
TEAM_NAME_CANDIDATES = ["서울 이랜드", "서울이랜드FC", "서울 이랜드 FC", "서울이랜드", "서울"]

# 대회명 선택이 실패해 K리그1 데이터가 섞여 들어왔을 때를 잡아내기 위한
# 안전장치. 이 이름으로 시작하는 구단이 보이면 K리그2가 아니라고 보고
# 필터링 없이 진행하지 않고 즉시 중단한다.
UNEXPECTED_TEAM_MARKERS = ["FC서울"]

# K리그2 참가 구단 수(참고용 안전장치). 실제 수집된 구단 수가 이 값과
# 크게 다르면 시즌/대회 선택이 잘못됐을 가능성이 있다는 경고만 출력한다
# (구단 수는 시즌마다 바뀔 수 있어 경고만 하고 중단하지는 않음).
EXPECTED_TEAM_COUNT = int(os.environ.get("EXPECTED_TEAM_COUNT", "13"))

# 전체 선수 표가 여러 페이지에 걸쳐 나오는 경우(페이지네이션) 다음 페이지 버튼을 찾기 위한 힌트.
PAGINATION_NEXT_HINTS = ["다음", "Next", "next", ">"]

# 무한 루프 방지용 최대 페이지 수
MAX_PAGES = 50

# 표 헤더에서 "선수명", "xG" 등에 해당하는 열을 찾기 위한 힌트.
# "선수별 기대득점(xG)" 화면의 실제 열: 순위, 선수, 구단, 출장수, 출장시간(분),
# 슈팅, 득점, xG, 득점/xG, 90분당 xG (사용자 스크린샷으로 확인).
# "xG", "득점/xG", "90분당 xG"처럼 서로의 부분 문자열인 열이 있으니, 정확한
# 열 이름을 리스트 맨 앞에 두면 map_headers()가 우선적으로 정확히 매칭한다.
COLUMN_HEADER_HINTS = {
    "rank": ["순위"],
    "player_name": ["선수", "선수명", "이름"],
    "team_name": ["구단", "팀명", "소속팀", "팀"],
    "position": ["포지션"],
    "matches": ["출장수", "출전", "경기수"],
    "minutes": ["출장시간(분)", "출장시간"],
    "shots": ["슈팅"],
    "goals": ["득점"],
    "xg": ["xG", "기대득점"],
    "goals_per_xg": ["득점/xG"],
    "xg_per90": ["90분당 xG"],
}

# 구글시트 설정
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get(
    "GOOGLE_SERVICE_ACCOUNT_FILE", "service-account.json"
)
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")  # CI용(내용 자체)
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
GOOGLE_WORKSHEET_NAME = os.environ.get("GOOGLE_WORKSHEET_NAME", "서울이랜드_xG")

DATA_CSV_PATH = os.environ.get("DATA_CSV_PATH", "data/xg_players.csv")
