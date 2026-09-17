#!/usr/bin/env python3
"""
Run this once before the first real run, and it's safe to re-run anytime.

Checks/installs what it safely can (Python packages, Playwright's browser
binary). Warns — but does not hard-fail — on things that need a human
(secrets in .env, git remote configured), since those can't be auto-solved
and this shouldn't block someone from at least seeing what's missing.

Usage:
    python setup_check.py
"""
import sys
import subprocess
import importlib.util


def check_python_version():
    ok = sys.version_info >= (3, 9)
    print(f"{'[OK]' if ok else '[FAIL]'} Python {sys.version.split()[0]} "
          f"({'>= 3.9 required' if not ok else 'OK'})")
    return ok


def check_and_install_packages():
    required = ["playwright", "requests", "dotenv", "openai"]
    missing = [pkg for pkg in required if importlib.util.find_spec(pkg) is None]
    if not missing:
        print("[OK] All required Python packages already installed.")
        return True

    print(f"[INFO] Missing packages: {missing} — installing from requirements.txt...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("[OK] Packages installed.")
        return True
    print(f"[FAIL] pip install failed:\n{result.stderr}")
    return False


def check_and_install_playwright_browser():
    result = subprocess.run(
        ["playwright", "install", "chromium"], capture_output=True, text=True
    )
    if result.returncode == 0:
        print("[OK] Playwright's Chromium browser is installed.")
        return True
    print(f"[FAIL] 'playwright install chromium' failed:\n{result.stderr}")
    print("       Try running it manually — it needs to download a browser binary.")
    return False


def check_git():
    result = subprocess.run(["git", "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[OK] {result.stdout.strip()}")
        remote = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
        if not remote.stdout.strip():
            print("[WARN] No git remote configured — commits will succeed locally "
                  "but won't push anywhere. Fine for local testing.")
        return True
    print("[WARN] git not found — versioning (git_ops.py) will skip silently.")
    return False


def check_secrets():
    import config  # imported late so python-dotenv is guaranteed installed first
    missing = config.missing_secrets()
    if not missing:
        print("[OK] All required secrets are set in .env.")
    else:
        print(f"[WARN] Missing from .env: {', '.join(missing)}")
        print("       The pipeline will run, but the step needing each one will fail "
              "until it's set. Copy .env.example to .env and fill these in.")
    return not missing


def main():
    print("--- Environment check ---")
    results = [
        check_python_version(),
        check_and_install_packages(),
    ]
    results.append(check_and_install_playwright_browser())
    results.append(check_git())
    results.append(check_secrets())

    print("\n--- Summary ---")
    if all(results):
        print("Everything is ready.")
    else:
        print("Some items need attention above (warnings won't block a test run; "
              "[FAIL] items will).")


if __name__ == "__main__":
    main()
