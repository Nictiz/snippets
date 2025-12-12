from playwright.sync_api import sync_playwright
import pyotp
import sys
import os
import json
from dotenv import load_dotenv

# Voeg de project-root toe aan het pad (2 mappen omhoog vanaf auth/)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from config.config import CONFIG # type: ignore

# Laad environment variables
load_dotenv()

def login_and_save_storage():
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

        # Navigeer naar loginpagina
        page.goto("https://my.interoplab.eu/")

        # Haal credentials op uit environment variables
        username = os.getenv("CL_USERNAME")
        password = os.getenv("CL_PASSWORD")
        totp_secret = os.getenv("CL_TOTP_SECRET")

        # Controleer of alle benodigde variabelen aanwezig zijn
        if not all([username, password, totp_secret]):
            raise ValueError("Missing required environment variables. Please check your .env file.")

        # Narrow types for static type checkers (assert they are str)
        assert isinstance(username, str)
        assert isinstance(password, str)
        assert isinstance(totp_secret, str)

        # Vul gebruikersnaam en wachtwoord in
        page.fill("#username", username)
        page.fill("#password", password)
        page.click("text=Sign in")

        # Wacht op 2FA-pagina en vul de code in
        # Gebruik TOTP secret uit environment variables
        totp = pyotp.TOTP(totp_secret)
        code = totp.now()
        page.get_by_role("textbox", name="Token:*").fill(code)
        page.click("text=Login")

        # Wacht tot je bent ingelogd (bv. dashboard zichtbaar is)
        page.get_by_role("link", name="Dashboard").wait_for(state="visible")
        assert page.url == "https://my.interoplab.eu/"


        # Sla de sessie op
        context.storage_state(path=f"{CONFIG['storage_state_path']}")
        print(f"[INFO] Sessie opgeslagen in: {CONFIG['storage_state_path']}")
        browser.close()

login_and_save_storage()
