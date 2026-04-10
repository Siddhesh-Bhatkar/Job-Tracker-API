import asyncio
from playwright.async_api import async_playwright

NAUKRI_URL = "https://www.naukri.com/fresher-jobs"

async def scrape_naukri_freshers(location: str = "", role: str = "",
                                  max_jobs: int = 20) -> list[dict]:
    """Scrape Naukri.com for fresher/entry-level jobs using Playwright."""
    jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        # Build URL with optional filters
        url = NAUKRI_URL
        params = []
        if role:
            params.append(f"k={role.replace(' ', '%20')}-fresher-jobs")
        if location:
            params.append(f"l={location.replace(' ', '%20')}")
        if params:
            url = f"https://www.naukri.com/{'-'.join(params)}-jobs"

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Wait for job cards to load
        try:
            await page.wait_for_selector(".srp-jobtuple-wrapper", timeout=15000)
        except Exception:
            await page.wait_for_selector("article.jobTuple", timeout=10000)

        # Scroll to load more jobs
        for _ in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1.5)

        # Extract job cards (try multiple selectors for resilience)
        cards = await page.query_selector_all(".srp-jobtuple-wrapper")
        if not cards:
            cards = await page.query_selector_all("article.jobTuple")

        for card in cards[:max_jobs]:
            try:
                title_el  = await card.query_selector(".title, .jobTitle a, a.title")
                comp_el   = await card.query_selector(".comp-name, .company-name")
                loc_el    = await card.query_selector(".locWdth, .location span")
                exp_el    = await card.query_selector(".expwdth, .experience span")
                salary_el = await card.query_selector(".salary-icon, .sal span")
                link_el   = await card.query_selector("a.title, .title a")

                title    = await title_el.inner_text()  if title_el  else "N/A"
                company  = await comp_el.inner_text()   if comp_el   else "N/A"
                location = await loc_el.inner_text()    if loc_el    else "N/A"
                exp      = await exp_el.inner_text()    if exp_el    else "0-1 Yrs"
                salary   = await salary_el.inner_text() if salary_el else "Not disclosed"
                link     = await link_el.get_attribute("href") if link_el else ""

                jobs.append({
                    "title":   title.strip(),
                    "company": company.strip(),
                    "location": location.strip(),
                    "experience": exp.strip(),
                    "salary":  salary.strip(),
                    "link":    link,
                    "source":  "Naukri"
                })
            except Exception as e:
                print(f"Error parsing card: {e}")
                continue

        await browser.close()

    return jobs


# Run standalone: python scrapers/naukri_scraper.py
if __name__ == "__main__":
    results = asyncio.run(scrape_naukri_freshers(role="python developer"))
    for j in results:
        print(j)