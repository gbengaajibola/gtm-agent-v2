"""
Stage 2 — visit each selected project's own site.

Plain Playwright handles the common case (a normal page that just loads).
Splash screens / click-to-start canvases need Browser-Use, which is left
as a documented stub below — see the note on why, and what happens
without it in the meantime.
"""
import re
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright
import config

MIN_USABLE_TEXT_CHARS = 40  # below this, treat the capture as "blank"


def _capture_with_playwright(demo_url: str, project_id: str) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        try:
            page.goto(demo_url, wait_until="load", timeout=20000)
            page.wait_for_timeout(1500)
            text = page.inner_text("body") or ""
            screenshot_path = config.OUTPUT_DIR / f"{project_id}.png"
            page.screenshot(path=str(screenshot_path), full_page=False)
        except Exception as e:
            return {"usable": False, "text": "", "screenshot_path": None, "error": str(e)}
        finally:
            browser.close()

    usable = len(text.strip()) >= MIN_USABLE_TEXT_CHARS
    return {
        "usable": usable,
        "text": text.strip()[:2000],
        "screenshot_path": str(screenshot_path) if usable else None,
    }


def _escalate_with_browser_use(demo_url: str, project_id: str) -> dict:
    """
    STUB — not implemented in this package.

    Browser-Use needs its own LLM wired up (any provider works, same
    agnostic principle as Stage 4) to dismiss splash screens / click an
    obvious "Start" button and retry the capture. That's a real piece of
    work with its own provider choice, and it's only needed for whichever
    subset of projects plain Playwright can't handle — building it before
    knowing how often it's actually needed would be premature.

    For this runnable v2, a project whose Playwright capture comes back
    blank is NOT blocked — it just proceeds with usable=False, and Stage 4
    is told to write around it using the project's own text description
    instead of a captured detail. Wire this in once you've seen, from a
    few real runs, how often escalation would actually fire.
    """
    raise NotImplementedError(
        "Browser-Use escalation is a stub in this package — see the "
        "docstring above. Capture proceeds without it for now."
    )


def _readme_from_github(code_url: str) -> str | None:
    """Pull a repo's README text via GitHub's public API — no scraping,
    no auth needed for public repos."""
    m = re.search(r"github\.com/([^/]+)/([^/.]+)", code_url or "")
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/readme",
            headers={"Accept": "application/vnd.github.raw+json"},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.text[:2000]
    except requests.RequestException:
        pass
    return None


def capture_project(project: dict) -> dict:
    """Returns a dict merged into the project's feature-set entry:
    {"usable": bool, "text": str, "screenshot_path": str|None, "source": str}
    """
    demo_url = project.get("demo_url")
    code_url = project.get("code_url")

    if not demo_url:
        if code_url:
            readme = _readme_from_github(code_url)
            return {
                "usable": readme is not None,
                "text": readme or "",
                "screenshot_path": None,
                "source": "github_readme",
            }
        return {"usable": False, "text": "", "screenshot_path": None, "source": "none"}

    result = _capture_with_playwright(demo_url, project["project_id"])
    result["source"] = "playwright"

    if not result["usable"]:
        try:
            escalated = _escalate_with_browser_use(demo_url, project["project_id"])
            escalated["source"] = "browser_use"
            return escalated
        except NotImplementedError:
            # Graceful degradation — see the stub's docstring. Stage 4 still
            # gets the project's own description even without a capture.
            pass

    return result
