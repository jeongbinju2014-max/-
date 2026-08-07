"""scrape_xg.py 실행 후 update_sheet.py를 순서대로 실행한다."""
import subprocess
import sys

STEPS = [
    [sys.executable, "src/scrape_xg.py"],
    [sys.executable, "src/update_sheet.py"],
]


def main():
    for step in STEPS:
        print(f"[실행] {' '.join(step)}")
        result = subprocess.run(step)
        if result.returncode != 0:
            print(f"[중단] {' '.join(step)} 실패 (exit code {result.returncode})")
            sys.exit(result.returncode)
    print("[완료] 전체 파이프라인이 성공적으로 끝났습니다.")


if __name__ == "__main__":
    main()
