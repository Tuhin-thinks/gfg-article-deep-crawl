import re
from globals import Driver
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager import chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def init_driver():
    driver = Driver.driver
    if not driver:
        service = Service(chrome.ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        Driver.driver = driver
    return driver


def get_search_links_selenium(search_url):
    """
    find all search results and their links in a Google search
    :param search_url:
    :return: list of titles and links
    """
    driver = init_driver()
    driver.get(search_url)
    try:
        # wait a minute for user to solve captcha (if captcha appeared)
        WebDriverWait(driver, 60).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div>a>h3")))
    except TimeoutException:
        print("Timed out while waiting to find <a> tags. "
              "Might be due to page protected by captcha.")
        return [], []
    a_tags = driver.execute_script(
        "return document.querySelectorAll('div>a');")

    titles = []
    links = []
    for a in a_tags:
        try:
            h3 = a.find_element(By.CSS_SELECTOR, "h3").text
        except NoSuchElementException:
            h3 = None
        if h3 and h3.strip() and a.get_attribute('href').startswith(
                'https://'):
            print(h3, a.get_attribute('href'))
            titles.append(h3)
            links.append(a.get_attribute('href'))
    return titles, links


def check_has_more_contents():
    driver = init_driver()
    try:
        p_tag = driver.find_element(By.CSS_SELECTOR, 'div.card-section>p')
        p_text = p_tag.text
    except NoSuchElementException:
        p_text = None
    if p_text:
        match = re.search('your search.*did not match any documents.*', p_text,
                          re.I)
        if match:
            return False
    else:
        return True
