from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]

def main():
    out=ROOT/"artifacts";out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={"width":1440,"height":1000})
        page.goto("http://127.0.0.1:8000/demo",wait_until="networkidle")
        page.click("[data-s='outage']");page.click("#run");page.wait_for_timeout(300)
        page.screenshot(path=str(out/"gateway_dashboard.png"),full_page=True)
        arch=browser.new_page(viewport={"width":1440,"height":900})
        arch.goto("http://127.0.0.1:8000/architecture",wait_until="networkidle")
        arch.screenshot(path=str(out/"architecture_process.png"),full_page=True)
        browser.close()

if __name__=="__main__":main()
