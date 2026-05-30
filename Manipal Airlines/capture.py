from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(color_scheme="dark", viewport={'width': 1280, 'height': 800})
        
        try:
            page.goto("http://localhost:8001/", wait_until="networkidle")
            page.screenshot(path="screenshot_home.png")
            print("Saved screenshot_home.png")
        except Exception as e:
            print(f"Failed to capture home: {e}")

        try:
            page.goto("http://localhost:8001/login/", wait_until="networkidle")
            page.screenshot(path="screenshot_login.png")
            print("Saved screenshot_login.png")
        except Exception as e:
            pass

        try:
            page.goto("http://localhost:8001/register/", wait_until="networkidle")
            page.screenshot(path="screenshot_register.png")
            print("Saved screenshot_register.png")
        except Exception as e:
            pass

        browser.close()

if __name__ == "__main__":
    run()
