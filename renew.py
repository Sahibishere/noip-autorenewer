import os
import random
import time
from getpass import getpass
from sys import argv
from time import sleep

import pyotp
import undetected_chromedriver as uc
from deep_translator import GoogleTranslator
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

browser_options = ChromeOptions()
browser_options.add_argument("--headless")
browser_options.add_argument("--no-sandbox")
browser_options.add_argument("--disable-dev-shm-usage")
browser_options.add_argument("--disable-blink-features=AutomationControlled")
browser_options.add_argument("start-maximized")
browser_options.add_experimental_option("excludeSwitches", ["enable-automation"])
browser_options.add_experimental_option("useAutomationExtension", False)

service = ChromeService(executable_path='/usr/local/bin/chromedriver')

browser = uc.Chrome(options=browser_options, service=ChromeService(ChromeDriverManager().install()))


def get_hosts():
    """
    Return every hostname row (<tr>) in the host-panel table.
    """
    return (
        browser.find_element(By.ID, "host-panel")      # outer wrapper
        .find_element(By.TAG_NAME, "tbody")
        .find_elements(By.TAG_NAME, "tr")
    )



def translate(text):
    if str(os.getenv("TRANSLATE_ENABLED", True)).lower() == "true":
        return GoogleTranslator(source="auto", target="en").translate(text=text)
    return text
    

def exit_with_error(message):
    print(str(message))
    browser.quit()
    exit(1)

import os


def get_credentials():
    email = os.getenv("NOIP_USERNAME")
    password = os.getenv("NOIP_PASSWORD")
    if not email or not password:
        raise ValueError("NOIP_USERNAME or NOIP_PASSWORD not set in environment.")
    return email, password


def get_totp_code():
    totp_key = os.getenv("NOIP_TOTP_KEY")
    if not totp_key:
        print("No TOTP key set. Skipping TOTP.")
        return None
    try:
        totp = pyotp.TOTP(totp_key)
        return totp.now()
    except Exception as e:
        raise ValueError(f"Invalid TOTP key or generation error: {e}")



def validate_otp(code):
    valid = True

    if len(code) != 6:
        exit_with_error(
            message="Invalid email verification code. The code must have 6 digits. Exiting."
        )
        valid = False
    if otp_code.isnumeric() is False:
        exit_with_error("Email verification code must be numeric. Exiting.")
        valid = False

    return valid


def validate_2fa(code):
    if len(code) != 16 or code.isalnum() is False:
        exit_with_error(
            message="Invalid 2FA key. Key must have 16 alphanumeric characters. Exiting."
        )
        return False
    return True


if __name__ == "__main__":
    LOGIN_URL = "https://www.noip.com/login?ref_url=console"
    HOST_URL = "https://my.noip.com/dynamic-dns"
    LOGOUT_URL = "https://my.noip.com/logout"

    email, password = get_credentials()

    # Open browser
    print(
        'Using user agent "'
        + browser.execute_script("return navigator.userAgent;")
        + '"'
    )
    print("Opening browser")

    # Go to login page
    browser.get(LOGIN_URL)

    if browser.current_url == LOGIN_URL:

        # Find and fill login form
        try:
            username_input = WebDriverWait(browser, 10).until(
                lambda browser: browser.find_element(by=By.ID, value="username")
            )
        except TimeoutException:
            exit_with_error(
                message="Username input not found within the specified timeout."
            )

        try:
            password_input = WebDriverWait(browser, 10).until(
                lambda browser: browser.find_element(by=By.ID, value="password")
            )
        except TimeoutException:
            exit_with_error(
                message="Password input not found within the specified timeout."
            )

        username_input.send_keys(email)
        password_input.send_keys(password)

        # ---- wait until the Log-In button is really clickable, then click it ----
        try:
            login_button = WebDriverWait(browser, 60).until(
                EC.element_to_be_clickable((By.ID, "clogs-captcha-button"))
            )
            # bring it into view & click via JS (avoids overlay / reCAPTCHA issues)
            browser.execute_script("arguments[0].scrollIntoView(true);", login_button)
            browser.execute_script("arguments[0].click();", login_button)
            print("Clicked Log-In button.")
        except TimeoutException:
            exit_with_error("Log-In button never became clickable.")

        # ---- Wait until we are on the dashboard OR the TOTP page ----
        try:
            WebDriverWait(browser, 20).until(
                lambda d: (
                    "my.noip.com" in d.current_url               # dashboard
                    or d.find_elements(By.ID, "totp-input")      # 6-box TOTP form
                )
            )
        except TimeoutException:
            browser.save_screenshot("after_login.png")
            exit_with_error("Login did not advance to dashboard or 2-factor page.")



        # Check if login has 2FA enabled and handle it
        if browser.current_url.find("2fa") > -1:

            # Wait for submit button to ensure page is loaded
            try:
                WebDriverWait(driver=browser, timeout=60, poll_frequency=3).until(
                    EC.element_to_be_clickable((By.NAME, "submit"))
                )
                submit_button = browser.find_elements(By.NAME, "submit")
                if len(submit_button) < 1:
                    exit_with_error(message="2FA submit button not found. Exiting.")
            except TimeoutException:
                exit_with_error(
                    message="2FA page did not load within the specified timeout. Exiting."
                )
            except NoSuchElementException:
                exit_with_error(message="2FA submit button not found. Exiting.")

            # Find if account has 2FA enabled or if is relying on email verification code
            # ---- Detect TOTP page (six boxes inside div id="totp-input") ----
            try:
                code_form = browser.find_element(By.ID, "totp-input")
                CODE_METHOD = "totp6"          # our new code path
            except NoSuchElementException:
                CODE_METHOD = None

            # Account has email verification code
            if CODE_METHOD == "email":
                otp_code = str(input("Enter OTP code: ")).replace("\n", "")
                if validate_otp(otp_code):
                    code_inputs = code_form.find_elements(by=By.TAG_NAME, value="input")
                    if len(code_inputs) == 6:
                        for i in range(len(code_inputs)):
                            code_inputs[i].send_keys(otp_code[i])
                    else:
                        exit_with_error(message="Email code input not found. Exiting.")

        # ---- Six-digit TOTP (id="totp-input") ----
        if CODE_METHOD == "totp6":
            totp_secret = os.getenv("NOIP_TOTP_KEY")
            if not totp_secret:
                exit_with_error("NOIP_TOTP_KEY secret missing – cannot fill TOTP code.")

            totp_code = pyotp.TOTP(totp_secret).now()
            print(f"TOTP code being entered: {totp_code}")

            try:
                # Optional: take a screenshot for debugging
                browser.save_screenshot("before_totp_input.png")
                print("📸 Screenshot saved: before_totp_input.png")

                # Dismiss the "Locale Mismatch" popup if it appears
                try:
                    WebDriverWait(browser, 5).until(
                        EC.visibility_of_element_located((By.XPATH, "//button[contains(text(), 'Yes')]"))
                    )
                    locale_popup_button = browser.find_element(By.XPATH, "//button[contains(text(), 'Yes')]")
                    browser.execute_script("arguments[0].click();", locale_popup_button)
                    print("🟢 Locale mismatch popup dismissed.")
                except TimeoutException:
                    print("🔵 No locale mismatch popup appeared.")

                # ✅ Find the 6 TOTP input fields freshly by CSS selector
                otp_inputs = browser.find_elements(By.CSS_SELECTOR, "#totp-input input")

                if len(otp_inputs) != 6:
                    exit_with_error("Expected 6 input boxes for TOTP, found "
                                    f"{len(otp_inputs)}. Layout may have changed.")

                # Now send the TOTP code
                for idx, digit in enumerate(totp_code):
                    otp_inputs[idx].send_keys(digit)
                    time.sleep(0.2)
                time.sleep(2)

                submit_button = WebDriverWait(browser, 10).until(
                    EC.element_to_be_clickable((By.NAME, "submit"))
                )
                browser.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                browser.execute_script("arguments[0].click();", submit_button)
                print("Clicked Verify (submit) button.")

            except Exception as e:
                exit_with_error(f"❌ TOTP autofill or verification failed: {e}")

        # ---- Wait until we are on the dashboard OR the TOTP page ----
        try:
            WebDriverWait(browser, 20).until(
                lambda d: (
                    "my.noip.com" in d.current_url               # dashboard
                    or d.find_elements(By.ID, "totp-input")      # 6-box TOTP form
                )
            )
        except TimeoutException:
            browser.save_screenshot("after_login.png")
            exit_with_error("Login did not advance to dashboard or 2-factor page.")




        # Go to hostnames page
        browser.get(HOST_URL)
        sleep(2)  # wait for possible redirect

        # Print current URL to see if we're actually on the host page
        print("📍 Current URL after host page load:", browser.current_url)
        browser.save_screenshot("host_page_check.png")

        # Check if we're back on the login page (session may have failed)
        if "login" in browser.current_url:
            exit_with_error("❌ Redirected back to login — session may have failed after 2FA.")

        # Now check for the host panel
        try:
            WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.ID, "host-panel"))
            )
            print("✅ Hosts page loaded.")
        except TimeoutException:
            browser.save_screenshot("hosts_page_error.png")
            exit_with_error("❌ Could not load NO-IP hostnames page — host panel missing.")



    # Confirm hosts
    try:
        hosts = get_hosts()
        print("Confirming hosts phase")
        confirmed_hosts = 0

        for host in hosts:
            try:
                current_host = host.find_element(by=By.TAG_NAME, value="a").text
                print(f'Checking if host "{current_host}" needs confirmation')
            except Exception:
                print("⚠️ Could not read host name — skipping.")
                continue

            try:
                button = host.find_element(by=By.TAG_NAME, value="button")
            except NoSuchElementException:
                print(f'No button found for host "{current_host}" — skipping.')
                continue

            if button.text.strip().lower() == "confirm" or translate(button.text).strip().lower() == "confirm":
                button.click()
                confirmed_hosts += 1
                print(f'✅ Host "{current_host}" confirmed')
                sleep(0.5)  # avoid rate limits

    # Summary message after loop
        if confirmed_hosts == 0:
            print("⚠️ No hosts required confirmation.")
        elif confirmed_hosts == 1:
            print("✅ 1 host confirmed.")
        else:
            print(f"✅ {confirmed_hosts} hosts confirmed.")

    except Exception as e:
        print("❌ Error during confirmation phase:", e)

    # Ensure login page is accessible
    if browser.current_url != LOGIN_URL:
        print("❌ Cannot access login page:\t" + LOGIN_URL)
        browser.quit()
        exit(1)

    try:
        pass  # Placeholder for 2FA and host confirmation logic

        print("✅ Logging off...")
        browser.get(LOGOUT_URL)
       
    except Exception as e:
        print("❌ Script failed with error:", e)
        browser.save_screenshot("fatal_error.png")

    finally:
        print("🧹 Closing browser.")
        browser.quit()
