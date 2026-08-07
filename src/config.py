"""설정값. README 1단계에서 확인한 내용을 여기에 채워 넣으세요."""
import os

from dotenv import load_dotenv

load_dotenv()

# README 1단계에서 브라우저로 확인한, "선수 기록 / 기대득점(xG)" 표가 있는 페이지 URL.
KLEAGUE_STATS_URL = os.environ.get(
    "KLEAGUE_STATS_URL", "https://portal.kleague.com/CHANGE_ME"
)

# 필터링할 팀명. 사이트에 표시되는 정확한 표기로 맞춰주세요.
# (예: "서울이랜드FC", "서울 이랜드", "서울이랜드" 등 사이트마다 표기가 다를 수 있음)
TEAM_NAME_CANDIDATES = ["서울이랜드FC", "서울 이랜드 FC", "서울이랜드", "서울 이랜드"]

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
