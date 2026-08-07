"""이 저장소의 xG 수집/업데이트 파이프라인을 MCP 도구로 노출하는 서버.

scrape_xg.py / update_sheet.py는 내부에서 sys.exit()을 호출하므로,
같은 프로세스에서 직접 import해 실행하면 MCP 서버까지 함께 종료된다.
그래서 run_all.py와 동일하게 서브프로세스로 실행하고 stdout/stderr와
종료 코드만 결과로 돌려준다.
"""
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

REPO_ROOT = Path(__file__).resolve().parent.parent

mcp = FastMCP("kleague-xg-updater")


def _run_script(script_name: str) -> str:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "src" / script_name)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    status = "성공" if result.returncode == 0 else f"실패 (exit code {result.returncode})"
    output = (result.stdout + result.stderr).strip()
    return f"[{status}] {script_name}\n{output}"


@mcp.tool()
def scrape_xg() -> str:
    """K리그 데이터포탈에서 서울 이랜드 FC 선수 xG 데이터를 수집해 data/xg_players.csv로 저장한다."""
    return _run_script("scrape_xg.py")


@mcp.tool()
def update_sheet() -> str:
    """가장 최근에 수집된 data/xg_players.csv 내용을 구글시트에 반영한다."""
    return _run_script("update_sheet.py")


@mcp.tool()
def run_pipeline() -> str:
    """scrape_xg 실행 후 성공하면 이어서 update_sheet를 실행한다."""
    scrape_result = _run_script("scrape_xg.py")
    if not scrape_result.startswith("[성공]"):
        return scrape_result
    update_result = _run_script("update_sheet.py")
    return f"{scrape_result}\n\n{update_result}"


@mcp.tool()
def read_latest_csv(max_rows: int = 20) -> str:
    """가장 최근 수집 결과(data/xg_players.csv)를 텍스트로 반환한다. max_rows로 미리보기 행 수를 제한한다."""
    csv_path = REPO_ROOT / "data" / "xg_players.csv"
    if not csv_path.exists():
        return "data/xg_players.csv가 없습니다. 먼저 scrape_xg 도구를 실행하세요."
    lines = csv_path.read_text(encoding="utf-8-sig").splitlines()
    return "\n".join(lines[: max_rows + 1])


if __name__ == "__main__":
    mcp.run()
