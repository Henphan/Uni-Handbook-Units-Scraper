from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def scrape_page(pList, pDriver, pWait, pPath):
    # this function scrapes the page of search-card objects within a card-container
    for i in range(len(pList)):
        unit_container = pWait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[class='search-results__card-container']")
            )
        )

        pList = unit_container.find_elements(By.CSS_SELECTOR, "div[class='search-card']")

        unit_link = pList[i].find_element(By.CSS_SELECTOR, "h2 a")
        pPath.write("{}\n".format(unit_link.text))

def click_popup(pWait):
    try:
        pop_up = pWait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-set-segment='dom']"))
        )
        pop_up.click()
    except Exception as err:
        print("Pop-up failed.")

def get_next_page(i, pDriver, pWait):
    # url with the configurations for: Undergraduate, Curtin Perth, and Units
    next_page = "https://handbook.curtin.edu.au/?page={}&search_text=&location=1&study_level=Undergraduate&study_type=unit".format(i)

    pDriver.get(next_page)

    # waiting until the class 'search-results__card-container' appears
    # this class contains the unit cards that the program interacts with
    pWait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "div[class='search-results__card-container']")
        )
    )
    # set the variable unit_container to the class for processing in the future
    unit_container = pWait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div[class='search-results__card-container']")
        )
    )
    pass

def check_server_down(pDriver, pWait):
    server_down = True
    while server_down:
        try:
            # attempt to get a 'search-results__card-container' class
            # this class will contain the error message if there is one
            unit_container = pWait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[class='search-results__card-container']")
                )
            )
            # checks if the error messsage is in the container
            unit_container.find_element(By.CSS_SELECTOR, "div[role='alert']")
            # this code runs when the server is down
            # if the server is up then an exception is thrown
            print("Webpage is down. Retrying in 10s...")
            pDriver.refresh()
            time.sleep(10)
        except:
            # handle the thrown exception when the error message could not be found
            # this code runs when the server is normal
            print("Webpage is active.")
            server_down = False
    return unit_container

def UnitScraper(output_path:str):
    first_page = "https://handbook.curtin.edu.au"

    driver = webdriver.Chrome()
    driver.get(first_page)
    wait = WebDriverWait(driver, 10) # initialising the wait time to 10 seconds

    #--------------------------- POP-UP ------------------------------------
    # clicking the pop-up prompting for domestic or international student
    click_popup(wait)
    #------------------------------------------------------------------------
    # iterates over all 181 pages of units, hard-coded for now
    for i in range(1,181):
        get_next_page(i, driver, wait)
    #--------------------------- SERVER-DOWN HANDLING ------------------------
        # this section handles the situation where Curtin's website is down
        # stay in a while loop while the server is down
        # return the card-container if the server is up
        unit_container = check_server_down(driver, wait)
    #------------------------------------------------------------------------
        # if the server is active and running, proceed to this section
        # unit_cards contain the search-card objectes within the card-container object
        unit_cards = unit_container.find_elements(By.CSS_SELECTOR, "div[class='search-card']")
        # process the page with scrape_page() and write to a file
        with open(output_path, "a") as f:
            scrape_page(unit_cards, driver, wait, f)
    
if __name__ == "__main__":
    UnitScraper("output1.csv")