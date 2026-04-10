import asyncio
import re
from playwright.async_api import async_playwright

# Target handles — these are PUBLIC accounts
TARGET_HANDLES = [
    "googlecareers",
    "lifeatmicrosoft",
    "instagram",      # Example only — replace with real career pages
    "indianstartupjobs",
]

JOB_KEYWORDS = [
    "hiring", "we're hiring", "apply now", "open roles", "join us",
    "internship", "fresher", "entry level", "careers", "job opening",
    "we are looking", "recruitment"
]


def is_job_post(caption: str) -> bool:
    """Detect if a post caption is job-related."""
    caption_lower = caption.lower()
    return any(kw in caption_lower for kw in JOB_KEYWORDS)


async def scrape_instagram_jobs(
    handles: list[str] = None,
    posts_per_handle: int = 6
) -> list[dict]:
    """
    Scrape public Instagram profiles for hiring posts.
    Uses Playwright headless browser — requires you to be logged in or
    set IG_SESSION_COOKIE in .env for persistent access.

    IMPORTANT: Instagram blocks headless browsers aggressively.
    This works best with a real session cookie from your own IG account.
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()

    handles = handles or TARGET_HANDLES
    session_cookie = os.getenv("IG_SESSION_COOKIE", "")
    job_posts = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
                "Mobile/15E148 Safari/604.1"
            ),
            viewport={"width": 390, "height": 844},
        )

        # Inject session cookie if available (get from browser DevTools)
        if session_cookie:
            await context.add_cookies([{
                "name": "sessionid",
                "value": session_cookie,
                "domain": ".instagram.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
            }])

        page = await context.new_page()

        for handle in handles:
            try:
                url = f"https://www.instagram.com/{handle}/"
                await page.goto(url, wait_until="networkidle", timeout=25000)
                await asyncio.sleep(2)

                # Try to get post captions from meta tags / JSON-LD
                # Instagram loads data in a script tag
                content = await page.content()

                # Extract captions from JSON embedded in page
                # Pattern: looks for "edge_media_to_caption" in script tags
                captions = re.findall(
                    r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', content
                )

                for caption in captions[:posts_per_handle]:
                    caption_clean = caption.replace("\\n", " ").replace('\\"', '"')
                    if is_job_post(caption_clean) and len(caption_clean) > 20:
                        # Try to extract role/link from caption
                        link_match = re.search(
                            r'(https?://[^\s"]+)', caption_clean
                        )
                        job_posts.append({
                            "title":   extract_role_from_caption(caption_clean),
                            "company": handle,
                            "source":  "Instagram",
                            "caption": caption_clean[:400],
                            "link":    link_match.group(1) if link_match else url,
                            "location": "See post",
                            "salary":  "See post",
                        })

            except Exception as e:
                print(f"Error scraping @{handle}: {e}")
                continue

        await browser.close()

    return job_posts


def extract_role_from_caption(caption: str) -> str:
    """Heuristically extract a job title from an IG post caption."""
    patterns = [
        r'hiring\s+(?:a\s+)?([A-Z][A-Za-z\s]+(?:Engineer|Developer|Analyst|Manager|Designer|Intern))',
        r'looking for\s+(?:a\s+)?([A-Z][A-Za-z\s]+(?:Engineer|Developer|Analyst))',
        r'([A-Z][A-Za-z\s]+(?:Engineer|Developer|Analyst|Manager|Designer|Intern))\s+(?:role|position|opening)',
    ]
    for pattern in patterns:
        match = re.search(pattern, caption)
        if match:
            return match.group(1).strip()
    return "Job Opportunity"