import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_cookie_token():
    # Configure Chrome options
    options = Options()
    options.binary_location = "/usr/bin/chromium-browser"
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )

    # Initialize Chrome
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://d247.com/")

        # Debug: save page source and screenshot before waiting
        with open("/code/page_source_before.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.save_screenshot("/code/screenshot_before.png")

        try:
            # Wait until the login button appears
            login_button = WebDriverWait(driver, 40).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Login with demo ID')]"))
            )
            login_button.click()
        except Exception as e:
            # Debug if button not found
            with open("/code/page_source_failed.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            driver.save_screenshot("/code/screenshot_failed.png")
            raise e

        # Wait after login
        time.sleep(5)

        # Extract g_token cookie
        g_token = None
        for cookie in driver.get_cookies():
            if cookie["name"] == "g_token":
                g_token = f"{cookie['name']}={cookie['value']};"
                break

        return g_token

    finally:
        driver.quit()
