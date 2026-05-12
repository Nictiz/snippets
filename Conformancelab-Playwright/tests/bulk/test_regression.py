from playwright.sync_api import expect, Page
from tests.helpers import login_check, fill_t_date
from utils.common.logger import setup_logger
from pathlib import Path
import urllib.parse
import json
import re
import pytest

pytestmark = pytest.mark.bulk

# Configuration
logger = setup_logger()

project_root = Path(__file__).resolve().parents[2]


def _find_json_record(json_path, goal, role, information_standard, category, subcategory, variant):
    """
    Find the matching record in the JSON file based on
    goal, role, informationStandard, category, subcategory and variant.
    Category, subcategory and variant are optional (empty string or None).
    """
    try:
        with open(json_path, encoding="utf-8") as f:
            records = json.load(f)
    except Exception as e:
        logger.error(f"Could not load JSON: {json_path} - {e}")
        return None

    for rec in records:
        # Match on required identifiers.
        if (rec.get('goal') != goal or 
            rec.get('role') != role or
            rec.get('informationStandard') != information_standard):
            continue
        
        # Match category when present in the URL.
        if category and category != '':
            if rec.get('category') != category:
                continue
        
        # Match subcategory when present in the URL.
        if subcategory and subcategory != '':
            if rec.get('subcategory') != subcategory:
                continue

        # Match variant when present in the URL.
        if variant and variant != '':
            if rec.get('variant') != variant:
                continue
        
        return rec

    logger.warning(f"Could not find a matching record for: goal={goal}, role={role}, "
                   f"informationStandard={information_standard}, category={category}, "
                   f"subcategory={subcategory}, variant={variant}")
    return None


def test_server_scenarios(page: Page, test_url: str):
    """
    Runs the scenarios for each generated test URL.
    Parameters are read from the JSON file, not from the URL.
    """

    logger.info(f"Testing URL: {test_url}")
    page.goto(test_url)
    login_check(page.locator(f"text=Test setup"))

    # Parse query string to retrieve identifiers.
    parsed_url = urllib.parse.urlparse(test_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    
    goal = query_params.get('goal', [''])[0]
    role = query_params.get('role', [''])[0]
    information_standard = query_params.get('informationStandard', [''])[0]
    category = query_params.get('category', [''])[0]
    subcategory = query_params.get('subcategory', [''])[0]
    variant = query_params.get('variant', [''])[0]

    # Load the full record from the JSON file.
    json_path = project_root / "utils" / "common" / "unique_combinations_all.json"
    combo = _find_json_record(str(json_path), goal, role, information_standard, category, subcategory, variant)

    if not combo:
        raise AssertionError(f"Could not find a test combination for: "
                             f"goal={goal}, role={role}, informationStandard={information_standard}, "
                             f"category={category}, subcategory={subcategory}, variant={variant}")

    # Extract all parameters from the JSON record.
    branch = combo.get('branch', 'main')
    fhir_version = combo.get('fhirVersion', '')
    information_standard = combo.get('informationStandard', '')
    use_case_raw = combo.get('usecase', '')

    logger.info(f"Loaded combination: branch={branch}, fhir_version={fhir_version}, "
                f"info_standard={information_standard}, role={role}")

    use_case = "medmij" if "MedMij" in use_case_raw else "nictiz"
    fhir_version = "r4" if "R4" in fhir_version else "stu3"
    
    # Fill in the test setup.
    expect(page.get_by_role("heading", name="Test setup")).to_be_visible()
    server_field = page.get_by_role("textbox", name="Your server base URL")
    auth_field = page.get_by_role("textbox", name="Your custom Authorization header")

    if branch == "main":
        if use_case == "nictiz":
            server_field.fill(
                f"https://my.interoplab.eu/uc-nictiz/{fhir_version}/fhir"
            )
            if auth_field.count() > 0:
                auth_field.fill(
                    f"Basic TmljdGl6OlBhc3N3b3Jk"
                )
                logger.info("Server base URL filled")
        elif use_case == "medmij":
            server_field.fill(
                f"https://nictiz.fhir.interoplab.eu/medmij/{fhir_version}/fhir"
            )
    else:
        server_field.fill(
                f"https://nictiz.fhir.interoplab.eu/dev/{fhir_version}/fhir"
            )
        if auth_field.count() > 0:
                auth_field.fill(
                    f"Basic TmljdGl6OlBhc3N3b3Jk"
                )
                logger.info("Server base URL filled")
        
       

    fill_t_date(page)

    # Start the test run.
    page.get_by_role("button", name="Create test run").click()
    text = page.locator("#instanceDetails").inner_text()
    try:
        expect(page.locator("#testInstanceHeader")).to_contain_text("Test run")
        for part in [information_standard, category, subcategory, variant, role]:
            if part:
                assert part in text, f"'{part}' is missing from text: {text}"

        expect(page.locator("#instanceState")).to_contain_text("Waiting")
    except AssertionError:
        test_run = page.locator("#testInstanceHeader").inner_text()
        logger.info(f"Test run {test_run} failed")
        raise

    page.get_by_role("button", name="Start test run").click()
    expect(page.locator("#instanceState")).to_contain_text(re.compile(r"\b(Running|Ready)\b"))
