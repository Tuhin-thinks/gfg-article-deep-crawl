import json
import typing
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


def parse_config(config_path: str):
    with open(config_path, 'r') as reader:
        conf_data = json.load(reader)
    return conf_data


def get_config_path(out_path: str):
    base_name = os.path.basename(out_path)
    file_name, ext = os.path.splitext(base_name)
    config_file = f"{file_name}-config.json"
    config_path = os.path.join(os.path.dirname(out_path), config_file)
    return config_path


def modify_existing(out_path: str) -> typing.Tuple[bool, int]:
    if os.path.exists(out_path):

        config_path = get_config_path(out_path)

        if os.path.exists(config_path):
            # get last scraped row config
            conf_data = parse_config(config_path)
            if conf_data.get('last_scraped_row'):
                last_scraped_row = conf_data.get("last_scraped_row")
                print(f"Last scraped up-to row: {last_scraped_row}")

                print(f"{out_path} exists, "
                      f"do you want to use the existing file "
                      f"for appending results?")
                choice = input("y/n: ")
                if choice.lower() == "y":
                    return True, last_scraped_row
                return False, 0
            else:
                # remove config file, if invalid
                print(">> Removing config file, as it is invalid.")
                os.remove(config_path)
    return False, 0


def update_config(out_path, config_dict):
    with open(get_config_path(out_path), 'w') as writer:
        json.dump(config_dict, writer, indent=4)
        print(f">> Config JSON updated. [{config_dict}]")


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
    out_path = os.path.join("data", f"rank_{category}.csv")
    update_existing = False
    start_from = 0
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

        df = pd.DataFrame(data, columns=['Title', "Link"])

        df.to_csv(info_csv_path, index=False)
    else:
        update_existing, start_from = modify_existing(out_path)
    # scrap all ranking for the links & titles fetched
    last_scraped_row = run_check.main(info_csv_path, out_path,
                                      modify_existing=update_existing,
                                      start_from=start_from)
    # update config file with last scraped row data
    update_config(out_path, {"last_scraped_row": last_scraped_row or 0})
    if Driver.driver:
        try:
            Driver.driver.quit()
        except AttributeError:
            pass


if __name__ == '__main__':
    main()
