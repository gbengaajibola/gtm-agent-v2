"""
Stage 1 — Roster extraction.

Selectors here are CONFIRMED against a real captured page (see
validate_selectors.py and rendered_projects.html from the architecture
delivery) — not guessed. Read-only: this only loads and reads the public
page, exactly like a visitor's browser would. No API key, no login.
"""
from playwright.sync_api import sync_playwright
import config

KNOWN_STATUSES = {"Shipped", "In Progress", "Prototype"}


def _extract_from_page(page) -> list[dict]:
    page.goto(config.PROJECTS_URL, wait_until="networkidle", timeout=30000)

    # Default sort is "Trending" (vote-based), not chronological — the site
    # has no visible submission-date field, so this is required, not just
    # a nicety.
    page.get_by_role("button", name="Newest", exact=True).click()
    page.wait_for_timeout(1500)

    cards = page.query_selector_all("article.surface-card")
    projects = []

    for card in cards:
        builder_link = card.query_selector('a[href^="/builders/"]')
        builder_name = builder_link.inner_text().strip() if builder_link else None

        title_link = card.query_selector('a[href^="/projects/"]')
        title = title_link.inner_text().strip() if title_link else None
        internal_url = title_link.get_attribute("href") if title_link else None
        project_id = internal_url.rsplit("/", 1)[-1] if internal_url else None

        builder_handle = None
        if builder_link:
            handle_el = builder_link.evaluate_handle(
                "el => el.parentElement.querySelector('div')"
            )
            if handle_el:
                text = handle_el.evaluate("el => el ? el.innerText : null")
                builder_handle = text.strip() if text else None

        description = None
        if title_link:
            desc_el = title_link.evaluate_handle(
                "el => el.parentElement.querySelector('p')"
            )
            if desc_el:
                text = desc_el.evaluate("el => el ? el.innerText : null")
                description = text.strip() if text else None

        pills = card.query_selector_all("span.glass-pill-dark")
        category, status, tech_tags = None, None, []
        for i, pill in enumerate(pills):
            text = pill.inner_text().strip()
            if i == 0:
                category = text
            elif text in KNOWN_STATUSES:
                status = text
            else:
                tech_tags.append(text)

        demo_url = None
        demo_svg = card.query_selector("a svg.lucide-external-link")
        if demo_svg:
            demo_el = demo_svg.evaluate_handle("el => el.closest('a')")
            href = demo_el.evaluate("el => el ? el.getAttribute('href') : null")
            demo_url = href

        code_url = None
        code_svg = card.query_selector("a svg.lucide-github")
        if code_svg:
            code_el = code_svg.evaluate_handle("el => el.closest('a')")
            href = code_el.evaluate("el => el ? el.getAttribute('href') : null")
            code_url = href

        comment_count = None
        comment_svg = card.query_selector("svg.lucide-message-square")
        if comment_svg:
            span_el = comment_svg.evaluate_handle("el => el.closest('span')")
            txt = span_el.evaluate("el => el ? el.innerText : ''")
            txt = (txt or "").strip()
            comment_count = int(txt) if txt.isdigit() else txt

        vote_count = None
        upvote_btn = card.query_selector('button[aria-label^="Upvote "]')
        if upvote_btn:
            txt = upvote_btn.inner_text().strip()
            vote_count = int(txt) if txt.isdigit() else txt

        projects.append({
            "project_id": project_id,
            "title": title,
            "builder_name": builder_name,
            "builder_handle": builder_handle,
            "description": description,
            "category": category,
            "status": status,
            "tech_tags": tech_tags,
            "demo_url": demo_url,
            "code_url": code_url,
            "internal_url": internal_url,
            "comment_count": comment_count,
            "vote_count": vote_count,
        })

    return projects


def extract_roster() -> list[dict]:
    """Launches a fresh headless browser, reads the real rendered page,
    and returns a list of Project records. This is the only function
    other modules should call."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            projects = _extract_from_page(page)
        finally:
            browser.close()
    return projects
