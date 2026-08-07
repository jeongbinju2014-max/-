"""K리그 데이터포탈에서 K리그2 전체 선수 xG 표를 수집한 뒤,
구단명이 서울 이랜드 FC인 행만 걸러 CSV로 저장한다.

사이트에는 팀별 필터가 없고 전체 선수 표만 제공되므로, 필요하면 페이지를
넘겨가며(pagination) 모든 선수를 모은 뒤 마지막에 구단명으로 필터링한다.

주의: 정확한 페이지 URL / 표 헤더 / 페이지네이션 UI는 사이트를 직접 열어
확인해야 한다. README.md의 "1단계: 사이트 구조 확인"을 먼저 진행할 것.
"""
import csv
import datetime
import sys

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

import config


def click_menu_path(page: Page, menu_path) -> bool:
    """SPA 메뉴를 순서대로 클릭해 목표 화면까지 이동한다. 실패하면 False."""
    for label in menu_path:
        label = label.strip()
        if not label:
            continue
        locator = page.get_by_text(label, exact=False)
        if locator.count() == 0:
            print(f"[오류] 메뉴 '{label}'을(를) 화면에서 찾지 못했습니다.")
            return False
        try:
            locator.first.click()
        except Exception as e:
            print(f"[오류] 메뉴 '{label}' 클릭 실패: {e}")
            return False
        page.wait_for_timeout(config.MENU_CLICK_WAIT_MS)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except PlaywrightTimeoutError:
            pass
        print(f"[정보] 메뉴 클릭: {label}")
    return True


def click_next_page(page: Page) -> bool:
    """다음 페이지 버튼 클릭을 시도. 성공하면 True, 더 이상 없으면 False."""
    for hint in config.PAGINATION_NEXT_HINTS:
        locator = page.locator(f"a:has-text('{hint}'), button:has-text('{hint}')")
        if locator.count() == 0:
            continue
        candidate = locator.first
        try:
            class_attr = candidate.get_attribute("class") or ""
            aria_disabled = candidate.get_attribute("aria-disabled")
            if "disabled" in class_attr.lower() or aria_disabled == "true":
                continue
            candidate.click()
            page.wait_for_load_state("networkidle")
            return True
        except Exception:
            continue
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
    """구단명(team_name) 열 값으로 서울 이랜드 FC 소속 선수만 남긴다."""
    if not rows or "team_name" not in rows[0]:
        print("[경고] 구단명 열을 찾지 못해 팀 필터링을 건너뜁니다. "
              "config.COLUMN_HEADER_HINTS['team_name']을 확인해주세요.")
        return rows
    filtered = [
        r for r in rows
        if any(team in r.get("team_name", "") for team in config.TEAM_NAME_CANDIDATES)
    ]
    if not filtered:
        print("[경고] 서울 이랜드 FC와 일치하는 행이 없습니다. "
              "config.TEAM_NAME_CANDIDATES의 표기를 실제 사이트 값에 맞게 조정해주세요.")
    return filtered


def main():
    all_rows = []
    seen_signatures = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"[정보] 접속: {config.KLEAGUE_BASE_URL}")
        try:
            page.goto(config.KLEAGUE_BASE_URL, wait_until="networkidle", timeout=30000)
        except PlaywrightTimeoutError:
            print("[경고] networkidle 대기 타임아웃, 계속 진행합니다.")

        if not click_menu_path(page, config.MENU_CLICK_PATH):
            page.screenshot(path="data/debug_screenshot.png", full_page=True)
            print(
                "[오류] 메뉴 이동에 실패했습니다. data/debug_screenshot.png를 확인하거나 "
                "config.MENU_CLICK_PATH를 실제 메뉴 텍스트에 맞게 수정해주세요."
            )
            browser.close()
            sys.exit(1)

        for page_num in range(1, config.MAX_PAGES + 1):
            table, header_texts = find_stats_table(page)
            if table is None:
                page.screenshot(path="data/debug_screenshot.png", full_page=True)
                print(
                    "[오류] 표를 찾지 못했습니다. data/debug_screenshot.png를 확인하거나 "
                    "페이지 구조를 다시 확인해주세요."
                )
                browser.close()
                sys.exit(1)

            header_mapping = map_headers(header_texts)
            rows = extract_rows(table, header_mapping, header_texts)
            signature = tuple(tuple(sorted(r.items())) for r in rows)

            if not rows or signature in seen_signatures:
                print(f"[정보] {page_num}페이지에서 새 데이터가 없어 수집을 종료합니다.")
                break

            seen_signatures.add(signature)
            all_rows.extend(rows)
            print(f"[정보] {page_num}페이지에서 {len(rows)}행 수집 (누적 {len(all_rows)}행)")

            if not click_next_page(page):
                break

        browser.close()

    rows = filter_team(all_rows)

    if not rows:
        print("[오류] 서울 이랜드 FC 선수 데이터를 찾지 못했습니다.")
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
