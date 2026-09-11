"""
Every run that changes state (roster snapshot, ledger, pending/processed
files) commits that change. Non-fatal if git isn't set up (e.g. a local
throwaway test run with no remote) — this warns instead of crashing the
pipeline, since versioning is valuable but shouldn't be a hard blocker on
a test machine.
"""
import subprocess


def commit_and_push(message: str, paths: list[str] | None = None) -> bool:
    try:
        add_cmd = ["git", "add"] + (paths if paths else ["-A"])
        subprocess.run(add_cmd, check=True, capture_output=True)

        result = subprocess.run(
            ["git", "commit", "-m", message], capture_output=True, text=True
        )
        if result.returncode != 0:
            if "nothing to commit" in (result.stdout + result.stderr):
                return True  # not an error — just no state actually changed
            print(f"[git_ops] commit failed: {result.stderr.strip()}")
            return False

        push = subprocess.run(["git", "push"], capture_output=True, text=True)
        if push.returncode != 0:
            print(f"[git_ops] push failed (commit still saved locally): {push.stderr.strip()}")
            return False

        return True
    except FileNotFoundError:
        print("[git_ops] git not found on this machine — skipping versioning")
        return False
    except subprocess.CalledProcessError as e:
        print(f"[git_ops] git command failed: {e}")
        return False
