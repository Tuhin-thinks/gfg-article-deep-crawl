from selenium import webdriver
import typing

METHOD = "selenium"

class Driver:
    driver: typing.Union[None, webdriver.Chrome] = None
