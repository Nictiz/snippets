from playwright.sync_api import sync_playwright
import pyotp
import sys
import os
import json
from dotenv import load_dotenv
import argparse
from pathlib import Path

# Add the project root to the path (2 folders up from auth/).
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from config.config import CONFIG # type: ignore

# Load environment variables.
load_dotenv()

def login_and_save_storage(storage_state_path: str):
    output_path = Path(storage_state_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        tutorial_data = [{
            "id": 65356,
            "state": "closed",
            "name": "(MAIN) Conformancelab flow",
            "currentStep": 2,
            "updatedAt": "2025-03-04T12:35:08.497Z"
        }]
        page.add_init_script(f"window.localStorage.setItem('tours', '{json.dumps(tutorial_data)}');")

        # Navigate to the login page.
        page.goto("https://my.interoplab.eu/")

        # Get credentials from environment variables.
        username = os.getenv("CL_USERNAME")
        password = os.getenv("CL_PASSWORD")
        totp_secret = os.getenv("CL_TOTP_SECRET")

        # Check whether all required variables are present.
        if not all([username, password, totp_secret]):
            raise ValueError("Missing required environment variables. Please check your .env file.")

        # Narrow types for static type checkers (assert they are str)
        assert isinstance(username, str)
        assert isinstance(password, str)
        assert isinstance(totp_secret, str)

        # Fill username and password.
        page.fill("#username", username)
        page.fill("#password", password)
        page.click("text=Sign in")

        # Wait for the 2FA page and fill in the code.
        # Use TOTP secret from environment variables.
        totp = pyotp.TOTP(totp_secret)
        code = totp.now()
        page.get_by_role("textbox", name="Token:*").fill(code)
        page.click("text=Login")

        # Wait until login is complete.
        page.get_by_role("link", name="Dashboard").wait_for(state="visible")
        assert page.url == "https://my.interoplab.eu/"


        # Save the session.
        context.storage_state(path=str(output_path))
        print(f"[INFO] Session saved in: {output_path}")
        browser.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=CONFIG["storage_state_path"],
        help="Path for the generated Playwright storage state",
    )
    args = parser.parse_args()

    login_and_save_storage(args.output)


if __name__ == "__main__":
    main()
