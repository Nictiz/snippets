from playwright.sync_api import Page,Locator, expect
from utils.common.logger import setup_logger
import time
import re
from typing import Optional, Union, List
import time
import subprocess
import os
from datetime import date, timedelta
import json
import urllib.parse

logger = setup_logger()

def check_text_order_soft(page: Page, before_text: str, after_text: str, errors: list):
    items = page.locator("div.provisioning-instance a.instance-name").all_inner_texts()

    try:
        index_before = next(i for i, t in enumerate(items) if before_text in t)
        index_after = next(i for i, t in enumerate(items) if after_text in t)
    except StopIteration:
        msg = f"❌ Niet gevonden: '{before_text}' of '{after_text}'"
        logger.error(msg)
        errors.append(msg)
        return

    if index_before < index_after:
        logger.info(f"✅ '{after_text}' komt ná '{before_text}' (posities: {index_after} > {index_before})")
    else:
        msg = f"⚠️ '{after_text}' komt niet ná '{before_text}' (posities: {index_after} >! {index_before})"
        logger.warning(msg)
        errors.append(msg)


def login_check(locator: Locator, foutmelding: str = "Inloggen is mislukt"):
    try:
        expect(locator).to_be_visible()
    except AssertionError:
        logger.error(foutmelding)
        raise AssertionError(foutmelding)

def fill_t_date(page):
    from datetime import date, timedelta
    c_datum = date.today()
    t_datum = c_datum - timedelta(days=(c_datum.weekday()))
    t_datum = t_datum.strftime("%Y-%m-%d")

    group = page.locator("p-input-group").filter(
    has=page.locator("p-inputgroup-addon").filter(has_text=re.compile(r"^T$")))

    if group.count() == 0:
        return  # Geen T-datum veld gevonden

    input_field = group.locator("input.p-inputtext")
    if not input_field.is_visible():
        return  # Geen zichtbaar invoerveld gevonden

    expect(input_field).to_be_visible()
    input_field.fill(t_datum)
    group.get_by_role("button", name="Apply").click()
    logger.info(f"✅ T-datum ingevuld met {t_datum}")


def wait_for_ready_or_fail_on_interrupted(page, timeout=600):
    """
    Wacht totdat #instanceState 'Ready' toont.
    Stopt direct met een AssertionError als status 'interrupted' bevat.
    Logt voortgang elke 5 seconden.

    :param page: Playwright page object
    :param timeout: maximale wachttijd in seconden
    """
    poll_interval = 5  # seconden
    elapsed = 0

    while elapsed < timeout:
        status = page.locator("#instanceState").inner_text().lower()
        if "ready" in status:
            logger.info(f"✅ Status is Ready (na {elapsed}s)")
            return
        elif "interrupted" in status:
            logger.error(f"❌ Test is interrupted na {elapsed}s, stoppen.")
            raise AssertionError("Test instance status is interrupted")
        else:
            #logger.info(f"⏳ Status: {status} (na {elapsed}s)")
            time.sleep(poll_interval)
            elapsed += poll_interval
    msg = f"⏰ Timeout na {timeout} seconden: status nooit Ready (laatste status: {status})"
    logger.error(msg)
    raise AssertionError(msg)


# Hulp functie om test URLs te genereren
def generate_test_urls(json_paths: Union[str, List[str]]):
    # json_path kan een string of een tuple/list van twee paden zijn
    # gedaan om zowel medmij als mo combinaties in te laden
    if isinstance(json_paths, (list, tuple)):
        combinaties = []
        for path in json_paths:
            with open(path, encoding="utf-8") as f:
                combinaties.extend(json.load(f))
    else:
        with open(json_paths, encoding="utf-8") as f:
            combinaties = json.load(f)

    urls = []
    for comb in combinaties:
        # Start met de basis URL en verplichte parameters
        params = {
            'branch': comb.get('branch'),
            'informationStandard': comb.get('informationStandard')
        }

        # Voeg optionele parameters alleen toe als ze niet None/null zijn
        optional_params = {
            'goal': comb.get('goal'),
            'category': comb.get('category'),
            'subcategory': comb.get('subcategory'),
            'role': comb.get('role'),
            'variant': comb.get('variant')
        }

        # Voeg alleen parameters toe die niet None zijn
        params.update({k: v for k, v in optional_params.items() if v is not None})

        # Bouw de URL op
        query_params = "&".join(
            f"{k}={urllib.parse.quote(str(v))}"
            for k, v in params.items()
        )

        url = f"https://my.interoplab.eu/uc-nictiz/tests?{query_params}"
        urls.append(url)
    return urls



def run_client_test(page: Page,
                    omgeving: str,
                    informationStandard: str,
                    role: str,
                    #test_count: int,
                    category: Optional[str] = None,
                    subcategory: Optional[str] = None,
                    variant: Optional[str] = "default"):
    page.goto(f"https://my.interoplab.eu/uc-nictiz/tests/kickstart/{omgeving}")
    login_check(page.locator(f"text=Kickstart your test ({omgeving})"))

    # Selecteer test set
    page.get_by_text(informationStandard).click()
    # Optioneel: kies category en subcategory
    if category:
        logger.info(f"Selecteer categorie: {category}")
        page.get_by_text(category, exact=True).click()

    if subcategory:
        logger.info(f"Selecteer subcategorie: {subcategory}")
        page.get_by_text(subcategory, exact=True).click()

    # Kies specifieke client testrol
    logger.info(f"Kies testrol: {role}")
    card = page.locator(
    "mat-card",
    has=page.locator("mat-card-title", has_text=f"{role}")
        ).filter(
            has=page.locator("span", has_text=f"variant: {variant}")
        )
    card.click()

    # Controleer of we op de juiste pagina zijn
    expect(page.get_by_role("heading", name="Test set-up overview")).to_be_visible()

    # Controleer juiste simulator URL
    locator_sim_url = page.locator("#destinationInfo span", has_text="https://nictiz.proxy.interoplab.eu")
    assert locator_sim_url.inner_text().find("/q/") != -1, f"Geen productieomgeving in URL: {locator_sim_url.inner_text()}"
    assert locator_sim_url.inner_text().find("/64e4b4df21773f655267edfe"), f"Niet de juiste organisatie-ID in URL: {locator_sim_url.inner_text()}"

    # Start test instance
    page.get_by_role("checkbox", name="Automated").check()
    page.get_by_role("button", name="Create test instance").click()

    expect(page.locator("#testInstanceHeader")).to_contain_text("Test Run")
    expect(page.locator("#testInstanceHeader")).to_contain_text(f"{role} - {omgeving} - {informationStandard}")
    expect(page.locator("#instanceState")).to_contain_text("Waiting")

    page.get_by_role("button", name="Start test instance").click()

    # Timer starten
    start = time.perf_counter()
    logger.info("Wacht op status: Running")
    expect(page.locator("#instanceState")).to_contain_text("Running")
    #expect(page.locator("app-test-instance")).to_have_text(re.compile(fr"Running test \d+/{test_count}"))

    # Wachten tot test gereed is
    logger.info("Wacht op status: Ready")
    wait_for_ready_or_fail_on_interrupted(page, timeout=120)

    # Timer stoppen
    elapsed = time.perf_counter() - start
    logger.info(f"⏱️ Test status wisselde naar Ready in {elapsed:.2f} seconden")
    logger.info("Status is nu Ready ✅")

    # Valideer succesvolle uitvoering
    successful_block = page.locator("mat-card-content >> div", has_text="Successful")
    expect(successful_block.locator("h3")).to_have_text("Successful")
    #expect(successful_block.locator("span").nth(0)).to_have_text(str(test_count)) #maakt de test minder flexibel
    expect(successful_block.locator("span").nth(1)).to_have_text("100%")
    logger.info(f"Alle test cases zijn succesvol uitgevoerd ✅")



def run_server_test(page: Page,
                    omgeving: str,
                    informationStandard: str,
                    role: str,
                    use_case:str,
                    fhir_versie: str,
                    #test_count: int,
                    category: Optional[str] = None,
                    subcategory: Optional[str] = None,
                    variant: Optional[str] = "default"):
    page.goto(f"https://my.interoplab.eu/uc-nictiz/tests/kickstart/{omgeving}")
    login_check(page.locator(f"text=Kickstart your test ({omgeving})"))

    # Selecteer test set
    page.get_by_text(informationStandard).click()
    # Optioneel: kies category en subcategory
    if category:
        logger.info(f"Selecteer categorie: {category}")
        page.locator("mat-card", has_text=f"{category}").first.click()

    if subcategory:
        logger.info(f"Selecteer subcategorie: {subcategory}")
        page.locator("mat-card", has_text=f"{subcategory}").first.click()

    # Kies specifieke testrol
    logger.info(f"Kies testrol: {role}")
    card = page.locator(
    "mat-card",
    has=page.locator("mat-card-title", has_text=f"{role}")
        ).filter(
            has=page.locator("span", has_text=f"variant: {variant}")
        )
    card.click()

    #Test setup pagina
    expect(page.get_by_role("heading", name="Test set-up overview")).to_be_visible()

    if use_case == "nictiz":
        page.get_by_role("textbox", name="Your FHIR server base url").fill(f"https://my.interoplab.eu/uc-nictiz/{fhir_versie}/fhir")
    elif use_case == "medmij":
        page.get_by_role("textbox", name="Your FHIR server base url").fill(f"https://nictiz.fhir.interoplab.eu/medmij/{fhir_versie}/fhir")
    elif use_case == "nictizmedmij":
        page.get_by_role("textbox", name="Your FHIR server base url").fill(f"https://nictiz.fhir.interoplab.eu/medmij/{fhir_versie}/fhir")

    fill_t_date(page)

    page.get_by_role("button", name="Create test instance").click()

    #Testrun pagina
    text = page.locator("#instanceDetails").inner_text()
    try:
        expect(page.locator("#testInstanceHeader")).to_contain_text("Test Run")
        for part in [informationStandard,omgeving,category,subcategory,role]:
            if part:  # alleen checken als parameter aanwezig is
                assert part in text, f"'{part}' ontbreekt in tekst: {text}"

        expect(page.locator("#instanceState")).to_contain_text("Waiting")
    except AssertionError as e:
        testrun = page.locator("#testInstanceHeader").inner_text()
        logger.info(f"Test instance {testrun} is fout")
        raise

    page.get_by_role("button", name="Start test instance").click()
    # Start timer
    start = time.perf_counter()
    logger.info("Wacht op status: Running")
    expect(page.locator("#instanceState")).to_contain_text("Running")
    #expect(page.locator("app-test-instance")).to_have_text(re.compile(fr"Running test \d+/{test_count}"))


    logger.info("Wacht op status: Ready")
    wait_for_ready_or_fail_on_interrupted(page, timeout=600)

    # Stop timer
    end = time.perf_counter()
    elapsed = end - start
    logger.info(f"⏱️ Test status wisselde naar Ready in {elapsed:.2f} seconden")
    logger.info("Status is nu Ready ✅")

    successful_block = page.locator("mat-card-content >> div", has_text="Successful")
    expect(successful_block.locator("h3")).to_have_text("Successful")
    #expect(successful_block.locator("span").nth(0)).to_have_text(str(test_count)) #maakt de test minder flexibel
    expect(successful_block.locator("span").nth(1)).to_have_text("100%")
    logger.info(f"Alle test cases zijn succesvol uitgevoerd ✅")