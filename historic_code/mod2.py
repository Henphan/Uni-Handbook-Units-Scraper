from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

def scrape_page(pList, pDriver, pWait, pPath):
    for i in range(len(pList)):
        unit_container = pWait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[class='search-results__card-container']")
            )
        )

        pList = unit_container.find_elements(By.CSS_SELECTOR, "div[class='search-card']")

        unit_link = pList[i].find_element(By.CSS_SELECTOR, "h2 a")
        pPath.write("{}\n".format(unit_link.text))


