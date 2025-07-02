import os
from time import time, sleep
from threading import Thread

from dotenv import load_dotenv
from pyotp import TOTP
from playwright.sync_api import sync_playwright, Page, Error


# the url where auto-login occurs, ** means wildcard
LOGIN_URL = "https://login.microsoftonline.com/**"
USER_PLACEHOLDER = "username@OX.AC.UK"
PASS_PLACEHOLDER = "Password"
CODE_PLACEHOLDER = "Code"


def display_otp(totp: TOTP) -> str:
    current_otp = totp.now()
    next_otp = totp.generate_otp(int(time())//30+1)
    next_otp_time = 30.0 - time() % 30.0
    info = f"{next_otp_time:2.0f}| Current: {current_otp} -> Next: {next_otp}"
    return info

def terminal_otp(totp: TOTP) -> None:
    while True:
        info = display_otp(totp)
        print(info, end="\t\r")
        sleep(1)
        
        
def page_watcher(page: Page, username: str, password: str, totp: TOTP):
        while True:
            if page.is_closed():
                return
            
            try:
                # wait for loaded login page
                page.wait_for_url(LOGIN_URL, wait_until="load", timeout=0)
            except Error as e:
                if "Target page, context or browser has been closed" not in str(e):
                    # raise e
                    return
                else:
                    # simply closed browser, can ignore
                    return
            
            try:
                # input email/username
                page.fill(f'input[placeholder="{USER_PLACEHOLDER}"]', username)
                page.click("input[type='submit']")  # might need changing for other login pages
            except Error:
                # Presume error arrises from auto-signin
                return
            
            # input password
            page.fill(f'input[placeholder="{PASS_PLACEHOLDER}"]', password)
            page.click("input[type='submit']")  # might need changing for other login pages
            
            #TODO what if phone otp is default
            
            # Wait for alt-2fa to exist in the page
            other_2fa = page.locator("a#signInAnotherWay")
            other_2fa.wait_for(timeout=5000)
            other_2fa.click()
                
            # Wait for correct auth method to show
            phone_otp = page.locator('div[data-value="PhoneAppOTP"]')
            phone_otp.wait_for(timeout=5000)
            phone_otp.click()
                
            # Wait for code-input to apear
            code_input = page.locator(f'input[placeholder="{CODE_PLACEHOLDER}"]')
            code_input.wait_for(timeout=5000)
            code_input.fill(totp.now())
            page.click("input[type='submit']")  # might need changing for other login pages
        
def no_2fa_browser(username: str, password: str, totp: TOTP, firefox = False) -> None:
    with sync_playwright() as p:
        if firefox:
            browser = p.firefox.launch(headless=False)
        else:
            browser = p.chromium.launch(headless=False)
        
        def new_watcher(new_page):
            print("New page!")
            watcher = Thread(target=page_watcher, args=(new_page, username, password, totp))
            watcher.start()
        
        context = browser.new_context()
        context.on("page", new_watcher)
        #context.new_page()
        
        input("Press enter to Close!")


def main():
    # Loads the .env file and ensures expected values exist
    load_dotenv()
    try:
        user_value = os.getenv("LOGIN_USER").strip()
        pass_value = os.getenv("LOGIN_PASS").strip()
        secret_value = os.getenv("2FA_SECRET").strip()
    except AttributeError:
        raise EnvironmentError(".env file not setup correctly. Please see README.md for setup details.")
        
    # use the secet_value to make an authentication client
    totp = TOTP(secret_value)
    
    # start an updating thread in the terminal for displaying currnet otp
    termimal_info = Thread(target=terminal_otp, args=(totp,))
    #termimal_info.start()
    
    # run browser session
    no_2fa_browser(user_value, pass_value, totp, firefox=True)
            
    
if __name__ == "__main__":
    main()
