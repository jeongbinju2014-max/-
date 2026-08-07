"""K리그 데이터포탈에서 K리그2 전체 선수 xG 표를 수집한 뒤,
구단명이 서울 이랜드 FC인 행만 걸러 CSV로 저장한다.

사이트에는 팀별 필터가 없고 전체 선수 표만 제공되므로, 필요하면 페이지를
넘겨가며(pagination) 모든 선수를 모은 뒤 마지막에 구단명으로 필터링한다.

data.kleague.com은 화면 일부가 (i)frame 안에 내장되어 있을 수 있어서,
메인 문서뿐 아니라 page.frames 전체를 뒤져 요소를 찾는다.

주의: 정확한 페이지 URL / 표 헤더 / 페이지네이션 UI는 사이트를 직접 열어
확인해야 한다. README.md의 "1단계: 사이트 구조 확인"을 먼저 진행할 것.
"""
import csv
import datetime
import sys

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

import config


def find_text_in_frames(page: Page, label: str):
    """모든 프레임(메인 문서 포함)을 뒤져 label 텍스트를 가진 첫 프레임/로케이터를 반환."""
    for frame in page.frames:
        try:
            locator = frame.get_by_text(label, exact=False)
            if locator.count() > 0:
                return frame, locator
        except Exception:
            continue
    return None, None


def find_css_in_frames(page: Page, css: str):
    """모든 프레임을 뒤져 css 셀렉터에 매칭되는 첫 프레임/로케이터를 반환."""
    for frame in page.frames:
        try:
            locator = frame.locator(css)
            if locator.count() > 0:
                return frame, locator
        except Exception:
            continue
    return None, None


def collect_clickable_texts(page: Page, limit: int = 100):
    """모든 프레임에서 클릭 가능해 보이는 요소들의 글자를 모아 디버깅에 쓴다."""
    texts = []
    seen = set()
    for frame in page.frames:
        for sel in ["nav a", "nav button", "header a", "header button",
                    "[role='menuitem']", "a", "button", "li"]:
            try:
                elements = frame.locator(sel).all()
            except Exception:
                continue
            for el in elements:
                try:
                    t = el.inner_text(timeout=300).strip()
                except Exception:
                    continue
                if t and 1 <= len(t) <= 20 and t not in seen:
                    seen.add(t)
                    texts.append(t)
                if len(texts) >= limit:
                    return texts
    return texts


def click_menu_path(page: Page, menu_path) -> bool:
    """SPA/프레임 메뉴를 순서대로 클릭해 목표 화면까지 이동한다. 실패하면 False."""
    for label in menu_path:
        label = label.strip()
        if not label:
            continue
        frame, locator = find_text_in_frames(page, label)
        if locator is None:
            print(f"[오류] 메뉴 '{label}'을(를) 어느 프레임에서도 찾지 못했습니다.")
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


def select_competition(page: Page, hints) -> bool:
    """'대회명' 드롭다운을 K리그2로 바꾼다. 기본값이 K리그1이라 필요함."""
    for frame in page.frames:
        try:
            selects = frame.locator("select").all()
        except Exception:
            continue
        for select_el in selects:
            try:
                options = select_el.locator("option").all_inner_texts()
            except Exception:
                continue
            for hint in hints:
                hint = hint.strip()
                matches = [o for o in options if hint and hint in o]
                if matches:
                    try:
                        select_el.select_option(label=matches[0])
                        print(f"[정보] 대회명 선택: {matches[0]}")
                        return True
                    except Exception as e:
                        print(f"[경고] 대회명 드롭다운 선택 실패: {e}")
    print("[경고] 'K리그2' 대회명 드롭다운을 찾지 못했습니다. 기본값으로 계속 진행합니다.")
    return False


def click_search_button(page: Page, hints) -> bool:
    """조건을 채운 뒤 '조회' 버튼을 눌러 결과 표를 로드한다."""
    for hint in hints:
        hint = hint.strip()
        if not hint:
            continue
        frame, locator = find_css_in_frames(page, f"button:has-text('{hint}'), a:has-text('{hint}')")
        if locator is None:
            continue
        try:
            locator.first.click()
            page.wait_for_timeout(1000)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeoutError:
                pass
            print(f"[정보] '{hint}' 버튼 클릭")
            return True
        except Exception as e:
            print(f"[경고] '{hint}' 버튼 클릭 실패: {e}")
    print("[경고] 조회/검색 버튼을 찾지 못했습니다.")
    return False


def click_next_page(page: Page) -> bool:
    """다음 페이지 버튼 클릭을 시도. 성공하면 True, 더 이상 없으면 False."""
    for hint in config.PAGINATION_NEXT_HINTS:
        frame, locator = find_css_in_frames(page, f"a:has-text('{hint}'), button:has-text('{hint}')")
        if locator is None:
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
    """모든 프레임에서 헤더에 xG 관련 힌트가 포함된 표를 찾는다."""
    xg_hints = config.COLUMN_HEADER_HINTS["xg"]
    fallback = None
    fallback_headers = None
    for frame in page.frames:
        try:
            tables = frame.locator("table").all()
        except Exception:
            continue
        for table in tables:
            header_texts = table.locator("th").all_inner_texts()
            if any(any(hint in h for hint in xg_hints) for h in header_texts):
                return table, header_texts
            if header_texts and (fallback is None or len(header_texts) > len(fallback_headers)):
                fallback = table
                fallback_headers = header_texts
    if fallback is not None:
        return fallback, fallback_headers
    return None, []


def map_headers(header_texts):
    """실제 헤더 텍스트 -> 표준 필드명 매핑.

    "xG", "득점/xG", "90분당 xG"처럼 한 열의 텍스트가 다른 열 힌트의 부분
    문자열이 되는 경우가 있어(예: "90분당 xG"에도 "xG"가 들어 있음), 정확히
    일치하는 열을 먼저 배정하고 남은 열에만 부분 일치를 적용한다.
    """
    stripped = [t.strip() for t in header_texts]
    mapping = {}
    assigned_fields = set()

    for idx, text in enumerate(stripped):
        for field, hints in config.COLUMN_HEADER_HINTS.items():
            if field in assigned_fields:
                continue
            if text in hints:
                mapping[idx] = field
                assigned_fields.add(field)
                break

    for idx, text in enumerate(stripped):
        if idx in mapping:
            continue
        for field, hints in config.COLUMN_HEADER_HINTS.items():
            if field in assigned_fields:
                continue
            if any(hint in text for hint in hints):
                mapping[idx] = field
                assigned_fields.add(field)
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


def dump_debug(page: Page, reason: str):
    page.screenshot(path="data/debug_screenshot.png", full_page=True)
    texts = collect_clickable_texts(page)
    with open("data/debug_menu_texts.txt", "w", encoding="utf-8") as f:
        f.write(f"URL: {page.url}\nTitle: {page.title()}\n")
        f.write(f"프레임 수: {len(page.frames)}\n\n")
        f.write("\n".join(texts))
    print(f"[오류] {reason}")
    print(f"[정보] 페이지 제목: {page.title()} / 현재 URL: {page.url} / 프레임 수: {len(page.frames)}")
    print("[정보] 현재 화면(모든 프레임)에서 인식된 클릭 가능한 글자들(이 목록을 그대로 복사해서 알려주세요):")
    for t in texts:
        print(f"  - {t}")


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
        page.wait_for_timeout(2000)

        if not click_menu_path(page, config.MENU_CLICK_PATH):
            dump_debug(page, "메뉴 이동에 실패했습니다. config.MENU_CLICK_PATH를 실제 메뉴 텍스트에 맞게 수정해주세요.")
            browser.close()
            sys.exit(1)

        select_competition(page, config.COMPETITION_NAME_CANDIDATES)
        click_search_button(page, config.SEARCH_BUTTON_HINTS)

        for page_num in range(1, config.MAX_PAGES + 1):
            table, header_texts = find_stats_table(page)
            if table is None:
                dump_debug(page, "표를 찾지 못했습니다. 페이지 구조를 다시 확인해주세요.")
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
