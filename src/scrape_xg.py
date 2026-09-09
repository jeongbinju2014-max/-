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


def select_dropdown_option(page: Page, hints, label: str) -> bool:
    """모든 프레임의 <select> 중 hints와 일치하는 옵션이 있는 것을 찾아 선택한다."""
    seen_options = []
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
            seen_options.append([o.strip() for o in options if o.strip()])
            for hint in hints:
                hint = hint.strip()
                matches = [o for o in options if hint and hint in o]
                if matches:
                    try:
                        select_el.select_option(label=matches[0])
                        print(f"[정보] {label} 선택: {matches[0]}")
                        return True
                    except Exception as e:
                        print(f"[경고] {label} 드롭다운 선택 실패: {e}")
    print(f"[경고] {label} 드롭다운을 찾지 못했습니다({', '.join(hints)}). 기본값으로 계속 진행합니다.")
    if seen_options:
        print(f"[정보] 현재 화면의 <select> 옵션들(참고용, {label} 진단):")
        for opts in seen_options:
            print(f"  - {opts}")
    return False


def select_competition(page: Page, hints) -> bool:
    """'대회명' 드롭다운을 K리그2로 바꾼다. 기본값이 K리그1이라 필요함."""
    return select_dropdown_option(page, hints, "대회명")


def select_year(page: Page, year: str) -> bool:
    """'대회년도' 드롭다운을 지정한 연도로 맞춘다.

    이전에는 이 값을 사이트 기본값에 그대로 맡겨서, 어떤 시즌 데이터를
    보고 있는지 로그만으로는 알 수 없었다. 매번 실행 시점의 연도로
    명시적으로 맞추고, 실제로 어떤 값이 선택됐는지 로그에 남긴다.
    """
    return select_dropdown_option(page, [year], "대회년도")


def dump_filter_state(page: Page):
    """현재 화면의 모든 <select> 드롭다운에서 선택된 값을 로그로 남긴다.

    "대회년도가 2026이 맞는지" 같은 질문에 다음 실행 로그만 보고도 바로
    답할 수 있도록 하기 위한 진단 기능.

    주의: HTML의 정적 `selected` 속성(option[selected])은 자바스크립트로
    값을 바꿔도 갱신되지 않는다. 실시간 선택 상태를 보려면 DOM의
    selectedIndex/options를 직접 읽어야 한다(el => el.options[el.selectedIndex]).
    """
    print("[정보] 현재 필터 드롭다운 상태:")
    seen = set()
    for frame in page.frames:
        try:
            selects = frame.locator("select").all()
        except Exception:
            continue
        for select_el in selects:
            try:
                s = select_el.evaluate(
                    "el => (el.options[el.selectedIndex] && el.options[el.selectedIndex].text) || ''"
                )
            except Exception:
                continue
            s = (s or "").strip()
            if s and s not in seen:
                seen.add(s)
                print(f"  - {s}")


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


def load_all_rows(page: Page, table, max_rounds: int = 80,
                   stable_rounds_needed: int = 5, wait_ms: int = 800) -> int:
    """가상 스크롤/무한 스크롤 표에 대응: 마지막 행을 계속 보이게 스크롤해서
    더 이상 행이 늘어나지 않을 때까지(=전부 로드될 때까지) 반복한다.

    실제로 GitHub Actions에서 조회는 성공했지만 272~289행만 잡히고(정상은
    384~392행) 서울 이랜드 선수가 하나도 안 걸린 사례가 반복됐음. 스크롤 후
    대기 시간이 짧아서(0.4초, 안정 판정 3회) 네트워크가 느린 날엔 아직
    로딩 중인데 다 됐다고 오판했던 것으로 추정 — 대기 시간과 안정 판정
    횟수를 늘리고, 안정된 것처럼 보여도 한 번 더 길게 기다렸다가 재확인하는
    단계를 추가했다.
    """
    stable_rounds = 0
    last_count = -1
    for _ in range(max_rounds):
        rows = table.locator("tbody tr")
        count = rows.count()
        if count == 0:
            break
        try:
            rows.last.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            pass
        page.wait_for_timeout(wait_ms)
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except PlaywrightTimeoutError:
            pass
        new_count = table.locator("tbody tr").count()
        if new_count <= count:
            stable_rounds += 1
            last_count = new_count
            if stable_rounds >= stable_rounds_needed:
                # 안정된 것처럼 보여도 한 번 더 길게 대기 후 재확인한다.
                # (짧은 대기만으로는 배치 로딩 사이의 "잠깐 멈춤"을 완료로
                # 오판할 수 있어, 마지막에 한 번 더 크게 여유를 준다.)
                page.wait_for_timeout(2500)
                confirm_count = table.locator("tbody tr").count()
                if confirm_count <= new_count:
                    last_count = confirm_count
                    break
                stable_rounds = 0
                last_count = confirm_count
        else:
            stable_rounds = 0
            last_count = new_count
    return last_count


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
    """구단명(team_name) 열 값으로 서울 이랜드 FC 소속 선수만 남긴다.

    구단 열을 못 찾거나, 일치하는 팀이 없거나, 다른 리그 구단으로 보이는
    이름이 섞여 있으면 None을 반환한다. 예전에는 구단 열을 못 찾아도
    필터링 없이 전체 선수 데이터를 그대로 반환해서, K리그2 전체 명단이
    그대로 구글시트에 덮어써진 사고가 있었음. 이제는 이런 경우 전부
    실패로 취급해 아무것도 쓰지 않는다.
    """
    if not rows:
        print("[오류] 표에서 추출된 선수 데이터가 없습니다.")
        return None
    if "team_name" not in rows[0]:
        print("[오류] '구단' 열을 찾지 못했습니다. 지금 실제로 인식된 열 이름:")
        for key in rows[0].keys():
            print(f"  - {key}")
        print("config.COLUMN_HEADER_HINTS['team_name']을 위 목록에 맞게 수정해주세요.")
        return None

    all_teams = sorted({r.get("team_name", "").strip() for r in rows})

    flagged = [t for t in all_teams if any(marker in t for marker in config.UNEXPECTED_TEAM_MARKERS)]
    if flagged:
        print(f"[오류] K리그2가 아닌 다른 리그 구단으로 보이는 이름이 섞여 있습니다: {', '.join(flagged)}")
        print("대회명(K리그2)/대회년도 선택이 실패했을 가능성이 있습니다. 실제로 수집된 구단명 전체:")
        for t in all_teams:
            print(f"  - {t}")
        return None

    if abs(len(all_teams) - config.EXPECTED_TEAM_COUNT) > 2:
        print(f"[경고] 수집된 구단 수({len(all_teams)}개)가 예상 K리그2 구단 수"
              f"({config.EXPECTED_TEAM_COUNT}개)와 차이가 큽니다. 실제로 수집된 구단명:")
        for t in all_teams:
            print(f"  - {t}")

    # 포함(in) 대신 시작 일치(startswith)를 쓴다 — "서울"만으로 포함 매칭하면
    # "FC서울"(K리그1)까지 걸릴 수 있는데, "FC서울"은 "서울"로 시작하지
    # 않으므로 시작 일치는 안전하다.
    filtered = [
        r for r in rows
        if any(r.get("team_name", "").strip().startswith(team) for team in config.TEAM_NAME_CANDIDATES)
    ]
    if not filtered:
        print("[오류] 서울 이랜드 FC와 일치하는 행이 없습니다. 실제로 수집된 구단명 전체:")
        for t in all_teams:
            print(f"  - {t}")
        print("config.TEAM_NAME_CANDIDATES의 표기를 위 목록에 맞게 조정해주세요.")
        return None
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

        select_year(page, config.SEASON_YEAR)
        # 연도를 바꾸면 '대회명' 드롭다운의 옵션 목록이 AJAX로 다시 로딩되는
        # 짧은 지연이 있는 것으로 보여, 곧바로 다음 선택을 시도하면 옵션이
        # 아직 갱신 중이라 못 찾을 수 있다. 안정될 때까지 잠깐 기다린다.
        page.wait_for_timeout(1200)
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except PlaywrightTimeoutError:
            pass
        select_competition(page, config.COMPETITION_NAME_CANDIDATES)
        dump_filter_state(page)
        click_search_button(page, config.SEARCH_BUTTON_HINTS)

        for page_num in range(1, config.MAX_PAGES + 1):
            table, header_texts = find_stats_table(page)
            if table is None:
                dump_debug(page, "표를 찾지 못했습니다. 페이지 구조를 다시 확인해주세요.")
                browser.close()
                sys.exit(1)

            loaded_count = load_all_rows(page, table)
            print(f"[정보] 스크롤 로딩 완료 (표에 실제로 로드된 행 수: {loaded_count})")

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
        print("[오류] 서울 이랜드 FC 선수 데이터를 확보하지 못해 CSV/시트를 갱신하지 않고 종료합니다.")
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
