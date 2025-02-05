import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException
from selenium.common.exceptions import NoSuchElementException


class BrowserWrapper:

    def __init__(self, driver):
        self.driver = driver
        self.user_name = None

    def get_element(self, by, id, timeout=10):
        self.remove_cookies_popup()
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.visibility_of_element_located((by, id)))
            return element
        except TimeoutException:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, id)))
            return element

    def remove_cookies_popup(self):
        divs_to_remove = self.driver.find_elements(By.XPATH, "//div[@id='cmpbox' or @id='cmpbox2']")
        for div in divs_to_remove:
            self.driver.execute_script("arguments[0].remove();", div)

    def click_button(self, by, id):
        self.remove_cookies_popup()
        self.driver.implicitly_wait(2)
        try:
            element = self.get_element(by, id)
            self.driver.implicitly_wait(2)
            element.click()
        except ElementNotInteractableException:
            raise ElementNotInteractableException()

    def click_at_coordinates(self, x, y):
        self.remove_cookies_popup()
        self.driver.implicitly_wait(2)
        action = ActionChains(self.driver)
        action.move_by_offset(x, y).click().perform()

    def send_keys(self, by, id, send_str):
        self.driver.implicitly_wait(2)
        try:
            element = self.get_element(by, id)
            element.send_keys(send_str)
        except ElementNotInteractableException:
            raise ElementNotInteractableException(f"Could not enter: {send_str}")

    def navigate_to(self, url):
        self.driver.get(url)
        self.remove_cookies_popup()

    def login(self, email: str, password: str):
        self.navigate_to("https://www.wg-gesucht.de/")
        self.click_button(By.XPATH, "//*[contains(text(), 'Mein Konto')]")
        self.send_keys(By.ID, "login_email_username", email)
        self.send_keys(By.ID, "login_password", password)
        self.click_button(By.ID, "login_submit")

        # Save screenshot for verification
        import time
        time.sleep(0.5)
        self.screenshot("login_verification")
        self.remove_cookies_popup()

        try:
            # Checking for the alert element:
            # Bitte geben Sie eine gültige E-Mail-Adresse und/oder ein Passwort ein.
            error_element = self.driver.find_element(
                By.CSS_SELECTOR,
                "#credentials_error > div > div",
            )
            if error_element.is_displayed():
                return False
        except NoSuchElementException:
            pass
        self.user_name = email.split("@")[0]
        return True

    def is_logged_in(self):
        self.navigate_to("https://www.wg-gesucht.de/")
        self.click_button(By.XPATH, "//*[contains(text(), 'Mein Konto')]")
        try:
            element = self.driver.find_element(By.ID, "login_email_username")
            return False
        except NoSuchElementException:
            pass
        return True

    def hover_and_click(self, hover_element_locator, click_element_locator):
        hover_element = self.get_element(*hover_element_locator)
        ActionChains(self.driver).move_to_element(hover_element).perform()
        click_element = self.get_element(*click_element_locator)
        click_element.click()

    def get_page_source(self):
        return self.driver.page_source

    def get_title(self):
        return self.driver.title

    def screenshot(self, file_name: str):
        self.driver.save_screenshot(f"{file_name}.png")

    def quit(self):
        self.driver.quit()

    def close(self):
        self.driver.close()
