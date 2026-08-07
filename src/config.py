"""설정값. README 1단계에서 확인한 내용을 여기에 채워 넣으세요."""
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
    "MENU_CLICK_PATH", "데이터센터,부가기록,기대득점,선수별 기대득점"
).split(",")

# 메뉴 클릭 사이 대기 시간(ms). SPA 전환 애니메이션/데이터 로딩 시간을 감안.
MENU_CLICK_WAIT_MS = int(os.environ.get("MENU_CLICK_WAIT_MS", "1500"))

# 사이트에는 팀별 필터가 없고 K리그2 전체 선수 표만 제공됨.
# 그 표에서 구단명(팀명) 열 값이 아래 후보 중 하나와 일치하는 행만 남긴다.
# 사이트에 표시되는 정확한 표기로 맞춰주세요.
# (예: "서울이랜드FC", "서울 이랜드", "서울이랜드" 등 사이트마다 표기가 다를 수 있음)
TEAM_NAME_CANDIDATES = ["서울이랜드FC", "서울 이랜드 FC", "서울이랜드", "서울 이랜드"]

# 전체 선수 표가 여러 페이지에 걸쳐 나오는 경우(페이지네이션) 다음 페이지 버튼을 찾기 위한 힌트.
PAGINATION_NEXT_HINTS = ["다음", "Next", "next", ">"]

# 무한 루프 방지용 최대 페이지 수
MAX_PAGES = 50

# 표 헤더에서 "선수명", "xG" 등에 해당하는 열을 찾기 위한 힌트.
# 실제 사이트 헤더 텍스트를 확인해서 추가/수정하세요.
COLUMN_HEADER_HINTS = {
    "player_name": ["선수명", "선수", "이름"],
    "team_name": ["팀명", "소속팀", "팀"],
    "position": ["포지션"],
    "xg": ["기대득점", "xG", "XG"],
    "goals": ["득점", "골"],
    "matches": ["출전", "경기수"],
}

# 구글시트 설정
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get(
    "GOOGLE_SERVICE_ACCOUNT_FILE", "service-account.json"
)
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")  # CI용(내용 자체)
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
GOOGLE_WORKSHEET_NAME = os.environ.get("GOOGLE_WORKSHEET_NAME", "서울이랜드_xG")

DATA_CSV_PATH = os.environ.get("DATA_CSV_PATH", "data/xg_players.csv")
