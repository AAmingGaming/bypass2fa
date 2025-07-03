from time import time
from math import ceil
import os
import asyncio

from dotenv import load_dotenv
from pyotp import TOTP
from playwright.async_api import async_playwright, Page, Error

# Set to False for Chromium based brower, True for Firefox browser
USE_FIREFOX = True

# The url where auto-login occurs, ** means wildcard
LOGIN_URL = "https://login.microsoftonline.com/**"
USER_PLACEHOLDER = "username@OX.AC.UK"
PASS_PLACEHOLDER = "Password"
CODE_PLACEHOLDER = "Code"

# How long to wait (ms) for an expected element to appear before giving up
# - (looks for Code input by default, if it cant find it in this time, paths to it)
ELEMENT_TIMEOUTS = 1000
# Delay (ms) for allowing the alternate login options to populate before continuing
OPTIONS_DELAY = 500


def display_otp(totp: TOTP) -> str:
    current_otp = totp.now()
    next_otp = totp.generate_otp(int(time())//30+1)
    next_otp_time = 30.0 - time() % 30.0
    info = f"{ceil(next_otp_time):2.0f}| Current: {current_otp} -> Next: {next_otp}"
    return info

async def terminal_otp(totp: TOTP) -> None:
    while True:
        info = display_otp(totp)
        print(info, end="\t\r")
        await asyncio.sleep(1)
        
        
async def page_watcher(page: Page, username: str, password: str, totp: TOTP):
        while True:
            if page.is_closed():
                return
            
            try:
                # wait for loaded login page
                await page.wait_for_url(LOGIN_URL, wait_until="load", timeout=0)
            except Error as e:
                if "Target page, context or browser has been closed" not in str(e):
                    # raise e
                    return
                else:
                    # simply closed browser, can ignore
                    return
            
            try:
                # input email/username
                await page.fill(f'input[placeholder="{USER_PLACEHOLDER}"]', username)
                await page.click("input[type='submit']")  # might need changing for other login pages
            except Error:
                # Presume error arrises from auto-signin
                return
            
            # input password
            await page.fill(f'input[placeholder="{PASS_PLACEHOLDER}"]', password)
            await page.click("input[type='submit']")  # might need changing for other login pages
            
            
            try:
                # Tries with finding the Code input directly
                code_input = page.locator(f'input[placeholder="{CODE_PLACEHOLDER}"]')
                await code_input.wait_for(timeout=ELEMENT_TIMEOUTS)
                print("Found!")
                await code_input.fill(totp.now())
                await page.click("input[type='submit']")  # might need changing for other login pages
            except:
                # Couldnt find Code input in time so it mustn't be default
                
                # Wait for alt-2fa to exist in the page
                other_2fa = page.locator("a#signInAnotherWay")
                await other_2fa.wait_for(timeout=ELEMENT_TIMEOUTS)
                await other_2fa.click()
                
                await asyncio.sleep(OPTIONS_DELAY/1000) # Need everything to finish loading
                    
                # Wait for correct auth method to show
                phone_otp = page.locator('div[data-value="PhoneAppOTP"]')
                await phone_otp.wait_for(timeout=ELEMENT_TIMEOUTS)
                await phone_otp.click()
                    
                # Wait for code-input to apear
                code_input = page.locator(f'input[placeholder="{CODE_PLACEHOLDER}"]')
                await code_input.wait_for(timeout=ELEMENT_TIMEOUTS)
                await code_input.fill(totp.now())
                await page.click("input[type='submit']")  # might need changing for other login pages
            
        
async def no_2fa_browser(username: str, password: str, totp: TOTP, firefox = False) -> None:
    async with async_playwright() as p:
        if firefox:
            device = p.devices["Desktop Chrome"]
            browser = await p.firefox.launch(headless=False)
        else:
            device = p.devices["Desktop Firefox"]
            browser = await p.chromium.launch(headless=False)
        
        def new_watcher(new_page):
            asyncio.create_task(page_watcher(new_page, username, password, totp))
        
        context = await browser.new_context(**device)
        context.on("page", new_watcher)
        page = await context.new_page()
        #page_watcher(page, username, password, totp)
        await asyncio.sleep(10000)
        await browser.close()


async def main():
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
    info_coroutine = terminal_otp(totp)
    
    # run browser session
    browser_coroutine = no_2fa_browser(user_value, pass_value, totp, firefox=USE_FIREFOX)
    
    await asyncio.gather(browser_coroutine, info_coroutine)
            
    
if __name__ == "__main__":
    asyncio.run(main())
