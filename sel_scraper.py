from datetime import datetime
import os.path
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager import chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from globals import Driver
from check_rank import run_check


def scrap_all_titles(driver: webdriver.Chrome, base_url: str):
    data = []
    page = 0
    while True:
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "a[class*=newsCardTitle]")))
        except TimeoutException:
            break  # page doesn't exists
        # scrap all titles and links
        a_tags = driver.find_elements(By.CSS_SELECTOR,
                                      "a[class*=newsCardTitle]")
        for a_tag in a_tags:
            title = a_tag.text
            link = a_tag.get_attribute("href")
            data.append(
                [title, link]
            )
        button_selector = "li.ant-pagination-next>button.ant-pagination-item-link"
        button_state_disabled = driver.execute_script(
            f"return document.querySelector('{button_selector}').disabled")
        print("button state:", button_state_disabled)
        if button_state_disabled:  # break loop when button not clickable
            break
        driver.execute_script('document.querySelector('
                              f'"{button_selector}").click()')
        page += 1
        time.sleep(3.0)
    return data


def update_required(category: str):
    expected_file_path = os.path.join("data", f"scraped_{category}_Output.csv")
    if os.path.exists(expected_file_path):
        use_new = input("Use existing scraped data or scrape new articles?:"
                        " [Y]es/[n]")
        return use_new.lower() != 'y'
    return True


def main():
    if not os.path.exists("data"):
        os.mkdir("data")

    category = input("Enter search category:")
    __allowed_category = (
        'technology',
        'work-career',
        'business',
        'finance',
        'lifestyle',
        'knowledge'
    )
    if category not in __allowed_category:
        print("")
        exit(0)

    info_csv_path = os.path.join("data", f"scraped_{category}_Output.csv")
    if update_required(category):
        start_url = f"https://news.geeksforgeeks.org/{category}"

        exe = chrome.ChromeDriverManager().install()
        service = Service(exe)
        driver = webdriver.Chrome(service=service)
        Driver.driver = driver  # store the driver instance
        # load page
        driver.get(start_url)

        # crawling website for all pages
        data = scrap_all_titles(driver, start_url)

        # driver.quit()  # todo: check what is the scraping method, if selenium don't quit

        df = pd.DataFrame(data, columns=['Title', "Link"])

        df.to_csv(info_csv_path, index=False)
    else:
        pass

    out_path = os.path.join("data", f"rank_{category}.csv")
    # scrap all ranking for the links & titles fetched
    run_check.main(info_csv_path, out_path)


if __name__ == '__main__':
    main()
