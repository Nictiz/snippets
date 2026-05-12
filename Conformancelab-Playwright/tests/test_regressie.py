
from config.config import CONFIG
from playwright.sync_api import expect, Page
from .helpers import login_check, wait_for_ready_or_fail_on_interrupted, fill_t_date
from utils.common.logger import setup_logger
from pathlib import Path
from datetime import date, timedelta
import urllib.parse
import json

# Configuratie
logger = setup_logger()
test_failed = False

c_datum = date.today()
t_datum = c_datum - timedelta(days=(c_datum.weekday()))

# BRANCH = "Conformancelab-test"
# INFO_STANDARD = [
#     "STU3\\eAppointment-2-0"
# ]

BRANCH = "MP9-3.0.0-rc.1"
INFO_STANDARD = ["R4\\MP9-3-0-0-beta\\MO"]

project_root = Path(__file__).resolve().parents[1]
INPUT_DIR = "Nictiz-testscripts/output"


def _find_json_record(json_path, goal, role, information_standard, category, subcategory):
    """
    Zoek het juiste record in het JSON-bestand op basis van
    goal, role, informationStandard, category, subcategory.
    Category en subcategory zijn optioneel (kunnen empty string of None zijn).
    Goal, informationStandard en role zijn verplicht voor unieke match.
    """
    try:
        with open(json_path, encoding="utf-8") as f:
            records = json.load(f)
    except Exception as e:
        logger.error(f"Kon JSON niet laden: {json_path} - {e}")
        return None

    for rec in records:
        # Match op goal, role en informationStandard (verplicht)
        if (rec.get('goal') != goal or 
            rec.get('role') != role or
            rec.get('informationStandard') != information_standard):
            continue
        
        # Match op category (optioneel: '' of None in URL means any)
        if category and category != '':
            if rec.get('category') != category:
                continue
        
        # Match op subcategory (optioneel: '' of None in URL means any)
        if subcategory and subcategory != '':
            if rec.get('subcategory') != subcategory:
                continue
        
        # Match gevonden
        return rec

    logger.warning(f"Kon geen matching record vinden voor: goal={goal}, role={role}, "
                   f"informationStandard={information_standard}, category={category}, subcategory={subcategory}")
    return None


def test_server_scenarios(page: Page, test_url: str):
    """
    Voert de scenarios uit voor elke gegenereerde test URL.
    De parameters worden uit het JSON-bestand gelezen, niet uit de URL.
    """

    logger.info(f"Testing URL: {test_url}")
    page.goto(test_url)
    login_check(page.locator(f"text=Test set-up overview"))

    # Parse querystring om identifiers op te halen
    parsed_url = urllib.parse.urlparse(test_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    
    goal = query_params.get('goal', [''])[0]
    role = query_params.get('role', [''])[0]
    information_standard = query_params.get('informationStandard', [''])[0]
    category = query_params.get('category', [''])[0]
    subcategory = query_params.get('subcategory', [''])[0]

    # Laad het volledige record uit JSON-bestand
    json_path = project_root / "utils" / "common" / "unieke_combinaties_all.json"
    combo = _find_json_record(str(json_path), goal, role, information_standard, category, subcategory)

    if not combo:
        raise AssertionError(f"Kon geen testcombinatie vinden voor: "
                             f"goal={goal}, role={role}, informationStandard={information_standard}, "
                             f"category={category}, subcategory={subcategory}")

    # Extraheer alle parameters uit het JSON-record
    branch = combo.get('branch', 'main')
    fhir_versie = combo.get('fhirVersion', '')
    information_standard = combo.get('informationStandard', '')
    use_case_raw = combo.get('usecase', '')
    variant = combo.get('variant') or 'default'
    server_alias = combo.get('serverAlias', '')

    logger.info(f"Geladen combinatie: branch={branch}, fhir_versie={fhir_versie}, "
                f"info_standard={information_standard}, role={role}")

    use_case = "medmij" if "MedMij" in use_case_raw else "nictiz"
    fhir_versie = "r4" if "R4" in fhir_versie else "stu3"
    
    # Vul TestSetup in
    expect(page.get_by_role("heading", name="Test set-up overview")).to_be_visible()
    auth_field = page.get_by_label("Your custom Authorization header")

    if branch == "main":
        if use_case == "nictiz":
            page.get_by_role("textbox", name="Your FHIR server base url").fill(
                f"https://my.interoplab.eu/uc-nictiz/{fhir_versie}/fhir"
            )
            if auth_field.count() > 0:
                page.get_by_role("textbox", name="Your custom Authorization header").fill(
                    f"Basic TmljdGl6OlBhc3N3b3Jk"
                )
                logger.info("Authorization header ingevuld")
        elif use_case == "medmij":
            page.get_by_role("textbox", name="Your FHIR server base url").fill(
                f"https://nictiz.fhir.interoplab.eu/medmij/{fhir_versie}/fhir"
            )
    else:
        page.get_by_role("textbox", name="Your FHIR server base url").fill(
                f"https://nictiz.fhir.interoplab.eu/dev/{fhir_versie}/fhir"
            )
        if auth_field.count() > 0:
                page.get_by_role("textbox", name="Your custom Authorization header").fill(
                    f"Basic TmljdGl6OlBhc3N3b3Jk"
                )
                logger.info("Authorization header ingevuld")
        
       

    fill_t_date(page)

    # Start de test instance
    page.get_by_role("button", name="Create test instance").click()
    text = page.locator("#instanceDetails").inner_text()
    try:
        expect(page.locator("#testInstanceHeader")).to_contain_text("Test Run")
        for part in [information_standard,use_case_raw,category,subcategory,role]:
            if part:  # alleen checken als parameter aanwezig is
                assert part in text, f"'{part}' ontbreekt in tekst: {text}"

        expect(page.locator("#instanceState")).to_contain_text("Waiting")
    except AssertionError as e:
        testrun = page.locator("#testInstanceHeader").inner_text()
        logger.info(f"Test instance {testrun} is fout")
        raise

    page.get_by_role("button", name="Start test instance").click()
    expect(page.locator("#instanceState")).to_contain_text("Running")


    # # Deel uitgeschakeld want duurt lang
    # # Start timer
    # start = time.perf_counter()
    # logger.info("Wacht op status: Running")
    # expect(page.locator("#instanceState")).to_contain_text("Running")

    # logger.info("Wacht op status: Ready")
    # wait_for_ready_or_fail_on_interrupted(page, timeout=700)

    # # Stop timer
    # end = time.perf_counter()
    # elapsed = end - start
    # logger.info(f"⏱️ Test status wisselde naar Ready in {elapsed:.2f} seconden")
    # logger.info("Status is nu Ready ✅")

    # # Testresultaten controleren

    # successful_block = page.locator("mat-card-content >> div", has_text="Successful")
    # expect(successful_block.locator("h3")).to_have_text("Successful")

    # percentage_text = successful_block.locator("span").nth(1).inner_text().strip() # Haal de waarde op van het tweede <span> element (het percentage)

    # # Extract het numerieke deel (zonder %)
    # try:
    #     percentage_value = int(percentage_text.replace("%", "").strip())
    # except ValueError:
    #     raise AssertionError(f"Kon percentage niet uitlezen uit '{percentage_text}'")

    # # Logging + controles
    # if percentage_value == 0:
    #     logger.error("❌ Testresultaat is 0% — test is gefaald.")
    #     assert False, "0% succesvolle testcases — test mislukt."
    # elif percentage_value < 100:
    #     logger.warning(f"⚠️ Testresultaat is {percentage_value}% — niet alle testcases succesvol.")
    # else:
    #     logger.info("✅ Alle testcases zijn succesvol uitgevoerd (100%)")