import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_cookie_token():
    options = Options()
    # options.add_argument("--headless")   # Uncomment for headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://d247.com/")

        # Wait for login button
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Login with demo ID')]"))
        )

        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login with demo ID')]")
        login_button.click()

        time.sleep(5)  # TODO: Replace with smarter wait for post-login element

        g_token = None
        for cookie in driver.get_cookies():
            if cookie["name"] == "g_token":
                g_token = f"{cookie['name']}={cookie['value']};"
                break

        return g_token
    finally:
        driver.quit()
