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
    arg_list = []
    line_list = [line.strip().lower().split("| ") for line in f]

    for line in line_list:
        line[1] = " ".join(line[1].split(", "))
        line[1] = " ".join(line[1].split(": ")).split(" ")

    for line in line_list:
        arg_list.append("unit-ug-{}--{}".format("-".join(line[1]), line[0]))
    
    for arg in arg_list:
        flag = True
        ver = 1
        while flag:
            url = "https://handbook.curtin.edu.au/units/{}v{}".format(arg, ver)
            driver.get(url)
            try:
                # how to maximise this wait time?
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
                    raise Exception("invalid page")
#------------------------------------------------------------------------
                info_container = driver.find_element(By.CSS_SELECTOR, "div[class='card__content']")
                info_cards = info_container.find_elements(By.CSS_SELECTOR, "div[class='mobile_card__block']")
                text_list = []
                for card in info_cards:
                    text = card.find_element(By.CSS_SELECTOR, "ul li").get_attribute("innerHTML")
                    text_list.append(text)
                with open("sample.txt", "a") as f:
                    f.write("{}|{}|{}|{}|{}\n".format(text_list[0], text_list[1], text_list[2], text_list[3], text_list[4]))
#------------------------------------------------------------------------
                flag = False
            except Exception as err:
                if err == "invalid page":
                    print("invalid url: {}".format(url))
                else:
                    print("error: ", err)
                if ver == 5:
                    print("skipping unit...")
                    with open("sample.txt", "w") as f:
                        f.write("skipped\n")
                    flag = False
                ver += 1


        