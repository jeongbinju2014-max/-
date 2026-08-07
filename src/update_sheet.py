"""수집한 CSV 데이터를 구글시트에 반영한다."""
import csv
import json
import os
import sys

import gspread
from google.oauth2.service_account import Credentials

import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


def get_client() -> gspread.Client:
    if config.GOOGLE_SERVICE_ACCOUNT_JSON:
        info = json.loads(config.GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    elif os.path.exists(config.GOOGLE_SERVICE_ACCOUNT_FILE):
        creds = Credentials.from_service_account_file(
            config.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
    else:
        print(
            "[오류] 구글 서비스 계정 인증 정보를 찾을 수 없습니다. "
            "GOOGLE_SERVICE_ACCOUNT_FILE 또는 GOOGLE_SERVICE_ACCOUNT_JSON을 확인하세요."
        )
        sys.exit(1)
    return gspread.authorize(creds)


def load_rows(csv_path: str):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames


def main():
    if not config.GOOGLE_SHEET_ID:
        print("[오류] GOOGLE_SHEET_ID가 설정되어 있지 않습니다.")
        sys.exit(1)

    rows, fieldnames = load_rows(config.DATA_CSV_PATH)
    if not rows:
        print("[오류] 업데이트할 데이터가 없습니다. 먼저 scrape_xg.py를 실행하세요.")
        sys.exit(1)

    client = get_client()
    spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID)

    try:
        worksheet = spreadsheet.worksheet(config.GOOGLE_WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=config.GOOGLE_WORKSHEET_NAME, rows=len(rows) + 10, cols=len(fieldnames) + 2
        )

    worksheet.clear()
    values = [fieldnames] + [[row.get(col, "") for col in fieldnames] for row in rows]
    worksheet.update(values, value_input_option="USER_ENTERED")

    print(
        f"[완료] '{config.GOOGLE_WORKSHEET_NAME}' 시트에 {len(rows)}행을 업데이트했습니다."
    )


if __name__ == "__main__":
    main()
