"""
keepalive.py — keeps Streamlit Community Cloud apps awake.

A plain HTTP ping does NOT work: hitting the app URL returns a static shell
without touching the app container, so the 12-hour inactivity timer never resets.
This opens each app in a real headless browser (which resets the timer) and, if
the "This app has gone to sleep" screen is showing, clicks the wake button.

Run locally:  pip install playwright && python -m playwright install chromium && python keepalive.py
On CI:        see .github/workflows/keepalive.yml
"""



import sys
from playwright.sync_api import sync_playwright

# ---- edit this list to match your apps ----
APPS = [
    "https://credit-risk-intelligence.streamlit.app/",
    "https://btp2-youtube-predictor-iitkgp.streamlit.app/",
    "https://ecommerce-analytics-vaidik.streamlit.app/",
]

WAKE_TEXT = "get this app back up"   # substring of the sleep-screen button


def visit(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(6_000)     # let the page render

    btn = page.get_by_text(WAKE_TEXT, exact=False)
    if btn.count() > 0:
        btn.first.click()
        print(f"  [WOKE]  {url} was asleep - clicked wake button, waiting for boot")
        # wait until the wake button is gone (app booted) or timeout
        try:
            page.wait_for_selector(f"text={WAKE_TEXT}", state="detached", timeout=120_000)
        except Exception:
            pass
        page.wait_for_timeout(15_000)
    else:
        print(f"  [AWAKE] {url}")

    page.wait_for_timeout(12_000)    # linger so it registers as real traffic


def main():
    failed = False
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"))
        for url in APPS:
            print(f"Visiting {url}")
            page = ctx.new_page()
            try:
                visit(page, url)
            except Exception as e:
                failed = True
                print(f"  [ERROR] {url}: {e}")
            finally:
                page.close()
        browser.close()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
