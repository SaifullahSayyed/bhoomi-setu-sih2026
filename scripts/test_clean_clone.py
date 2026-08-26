import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

SCRATCH_DIR = Path("C:/Users/Sayyed Saifullah/.gemini/antigravity/scratch")
TEST_DIR = SCRATCH_DIR / "clean_clone_audit"


def remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clean_dir(d: Path):
    if d.exists():
        shutil.rmtree(d, onerror=remove_readonly)


def run_cmd(cmd, cwd=None):
    print(f"\n--- Running: {cmd} (in {cwd or '.'}) ---")
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(res.stderr.strip())
    if res.returncode != 0:
        raise RuntimeError(f"Command failed with code {res.returncode}: {cmd}")
    return res


def main():
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    clean_dir(TEST_DIR)

    try:
        print("=== 1. CLONING REPOSITORY FROM GITHUB ===")
        run_cmd("git clone https://github.com/SaifullahSayyed/bhoomi-setu-sih2026.git clean_clone_audit", cwd=SCRATCH_DIR)

        print("\n=== 2. GENERATING SYNTHETIC DATASET ===")
        run_cmd("python scripts/generate_synthetic_data.py --seed 42", cwd=TEST_DIR)

        print("\n=== 3. CONTRACTS TEST SUITE ===")
        run_cmd("npm install", cwd=TEST_DIR / "contracts")
        run_cmd("npx hardhat test", cwd=TEST_DIR / "contracts")

        print("\n=== 4. BACKEND PYTEST SUITE ===")
        run_cmd("python -m pytest ../tests/ -v", cwd=TEST_DIR / "backend")

        print("\n=== 5. FRONTEND TEST AND PRODUCTION BUILD ===")
        run_cmd("npm install", cwd=TEST_DIR / "frontend")
        run_cmd("npm test", cwd=TEST_DIR / "frontend")
        run_cmd("npm run build", cwd=TEST_DIR / "frontend")

        print("\n=== CLEAN-CLONE AUDIT RESULT: 100% SUCCESSFUL ===")
    finally:
        clean_dir(TEST_DIR)
        print("Cleaned up temporary test directory.")


if __name__ == "__main__":
    main()
