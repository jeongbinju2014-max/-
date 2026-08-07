"""K리그 데이터포탈에서 서울 이랜드 FC 선수들의 xG 기록을 수집해 CSV로 저장한다.

주의: 정확한 페이지 URL / 팀 필터 UI / 표 헤더는 사이트를 직접 열어 확인해야 한다.
README.md의 "1단계: 사이트 구조 확인"을 먼저 진행할 것.
"""
import csv
import datetime
import sys

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

import config


def select_team(page: Page) -> bool:
    """팀 필터에서 서울 이랜드 FC를 선택 시도. 성공하면 True."""
    for team_name in config.TEAM_NAME_CANDIDATES:
        # 1) <select> 드롭다운에 팀명이 옵션으로 있는 경우
        for select_el in page.locator("select").all():
            try:
                options = select_el.locator("option").all_inner_texts()
            except Exception:
                continue
            if any(team_name in opt for opt in options):
                select_el.select_option(label=[o for o in options if team_name in o][0])
                page.wait_for_load_state("networkidle")
                return True

        # 2) 버튼/링크 형태로 팀명이 노출된 경우
        locator = page.get_by_text(team_name, exact=False)
        if locator.count() > 0:
            try:
                locator.first.click()
                page.wait_for_load_state("networkidle")
                return True
            except Exception:
                continue

    print("[경고] 팀 필터를 자동으로 찾지 못했습니다. 전체 선수 표에서 팀명으로 필터링합니다.")
    return False


def find_stats_table(page: Page):
    """헤더에 xG 관련 힌트가 포함된 표를 찾는다."""
    tables = page.locator("table").all()
    xg_hints = config.COLUMN_HEADER_HINTS["xg"]
    for table in tables:
        header_texts = table.locator("th").all_inner_texts()
        if any(any(hint in h for hint in xg_hints) for h in header_texts):
            return table, header_texts
    if tables:
        # xG 열을 못 찾으면 가장 열이 많은 표를 fallback으로 사용
        best = max(tables, key=lambda t: len(t.locator("th").all_inner_texts()))
        return best, best.locator("th").all_inner_texts()
    return None, []


def map_headers(header_texts):
    """실제 헤더 텍스트 -> 표준 필드명 매핑."""
    mapping = {}
    for idx, text in enumerate(header_texts):
        text = text.strip()
        for field, hints in config.COLUMN_HEADER_HINTS.items():
            if any(hint in text for hint in hints):
                mapping[idx] = field
                break
    return mapping


def extract_rows(table, header_mapping, header_texts):
    rows = []
    for tr in table.locator("tbody tr").all():
        cells = tr.locator("td").all_inner_texts()
        if not cells:
            continue
        row = {}
        for idx, cell in enumerate(cells):
            field = header_mapping.get(idx)
            key = field if field else (header_texts[idx].strip() if idx < len(header_texts) else f"col_{idx}")
            row[key] = cell.strip()
        rows.append(row)
    return rows


def filter_team(rows):
    if not rows or "team_name" not in rows[0]:
        return rows
    filtered = [
        r for r in rows
        if any(team in r.get("team_name", "") for team in config.TEAM_NAME_CANDIDATES)
    ]
    return filtered if filtered else rows


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"[정보] 접속: {config.KLEAGUE_STATS_URL}")
        try:
            page.goto(config.KLEAGUE_STATS_URL, wait_until="networkidle", timeout=30000)
        except PlaywrightTimeoutError:
            print("[경고] networkidle 대기 타임아웃, 계속 진행합니다.")

        team_selected = select_team(page)

        table, header_texts = find_stats_table(page)
        if table is None:
            print("[오류] 표를 찾지 못했습니다. URL/페이지 구조를 다시 확인해주세요.")
            browser.close()
            sys.exit(1)

        header_mapping = map_headers(header_texts)
        rows = extract_rows(table, header_mapping, header_texts)

        if not team_selected:
            rows = filter_team(rows)

        browser.close()

    if not rows:
        print("[오류] 추출된 선수 데이터가 없습니다.")
        sys.exit(1)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    for row in rows:
        row["업데이트일시"] = timestamp

    fieldnames = list(rows[0].keys())
    with open(config.DATA_CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[완료] {len(rows)}명의 선수 데이터를 {config.DATA_CSV_PATH} 에 저장했습니다.")


if __name__ == "__main__":
    main()
