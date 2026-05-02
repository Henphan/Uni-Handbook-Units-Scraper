from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

import time
from historic_code.mod2 import scrape_page

first_page = "https://handbook.curtin.edu.au"

chrome_options = Options()
chrome_options.add_argument("--headless=new")

driver = webdriver.Chrome(options = chrome_options)
driver.get(first_page)
wait = WebDriverWait(driver, 5)
#--------------------------- EXCEPTIONS ------------------------------------
class Invalid_URL(Exception):
    pass
#--------------------------- POP-UP ------------------------------------
try:
    pop_up = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-set-segment='dom']"))
    )
    pop_up.click()
except Exception as err:
    print("Pop-up failed.")
#-------------------------- PROCESSING CSV ---------------------------------------
with open("updated_1800.csv", "r") as f:
    unit_list = [line.strip().split("|") for line in f]
#-------------------------- URL REQUEST ---------------------------------------
open("sample.csv", "w")
# for unit in unit_list:
for i in range(len(unit_list)):
    unit = unit_list[i]
    repeat = True
    ver = 1
    while repeat:
        name_arg = "-".join(unit[1].replace(",", "").replace(":", "").lower().split(" "))
        code_arg = unit[0].lower()
        url = "https://handbook.curtin.edu.au/units/unit-ug-{}--{}v{}".format(name_arg, code_arg, ver)
        driver.get(url)
        try:
#-------------------------- PAGE STATUS CHECK ---------------------------------------
            wait.until(
                EC.any_of(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "meta[name='robots']")
                    ),
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div[class='ReactModalPortal']")
                    )
                )
            )
            if driver.current_url == "https://handbook.curtin.edu.au/":
                raise Invalid_URL
#-------------------------- SCRAPING UNIT PAGE ---------------------------------------
            info_container = driver.find_element(By.CSS_SELECTOR, "div[class='card__content']")
            info_cards = info_container.find_elements(By.CSS_SELECTOR, "div[class='mobile_card__block']")
            with open("sample.csv", "a") as f:
                f.write("{}|{}".format(unit[0], unit[1]))                
                for card in info_cards:
                    text = card.find_element(By.CSS_SELECTOR, "ul li").get_attribute("innerHTML").strip()
                    f.write("|{}".format(text))
                f.write("\n")
            repeat = False
#-------------------------- INVALID URL ---------------------------------------
        except Invalid_URL:
            print("Invalid URL: {}".format(url))
            ver += 1
            if ver == 6:
                print("Skipping...")
                with open("sample.csv", "a") as f:
                    f.write("{}|{}| SKIPPED \n".format(unit[0], unit[1]))
                repeat = False
        except TimeoutException:
            print("Server is down. Retrying in 20s...")
            time.sleep(10)