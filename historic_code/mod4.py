from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import time
from historic_code.mod2 import scrape_page

first_page = "https://handbook.curtin.edu.au"

chrome_options = Options()
chrome_options.add_argument("--headless=new")

driver = webdriver.Chrome(options = chrome_options)
driver.get(first_page)
wait = WebDriverWait(driver, 10)

#--------------------------- POP-UP ------------------------------------
try:
    pop_up = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-set-segment='dom']"))
    )
    pop_up.click()
except Exception as err:
    print("Pop-up failed.")
#------------------------------------------------------------------------
for i in range(180,181):
    next_page = "https://handbook.curtin.edu.au/?page={}&search_text=&location=1&study_level=Undergraduate&study_type=unit".format(i)

    driver.get(next_page)

    wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "div[class='search-results__card-container']")
        )
    )
    unit_container = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div[class='search-results__card-container']")
        )
    )
#--------------------------- SERVER-DOWN HANDLING ------------------------
    # Presuming the server is always down
    server_down = True
    while server_down:
        try:
            unit_container = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[class='search-results__card-container']")
                )
            )
            unit_container.find_element(By.CSS_SELECTOR, "div[role='alert']")
            # This code runs when the server is down
            print("Webpage is down. Retrying in 10s...")
            driver.refresh()
            time.sleep(10)
        except:
            print("Webpage is active. Scraping page {}...".format(i))
            # This code runs when the server is normal
            server_down = False
#------------------------------------------------------------------------
    unit_cards = unit_container.find_elements(By.CSS_SELECTOR, "div[class='search-card']")
    with open("full_1800v2.csv", "a") as f:
        scrape_page(unit_cards, driver, wait, f)