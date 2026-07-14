from playwright.sync_api import Page, Locator, expect
from utils.common.logger import setup_logger
import time
import re
from typing import Optional, Union, List
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
        msg = f"Not found: '{before_text}' or '{after_text}'"
        logger.error(msg)
        errors.append(msg)
        return

    if index_before < index_after:
        logger.info(f"'{after_text}' appears after '{before_text}' (positions: {index_after} > {index_before})")
    else:
        msg = f"'{after_text}' does not appear after '{before_text}' (positions: {index_after} >! {index_before})"
        logger.warning(msg)
        errors.append(msg)


def login_check(locator: Locator, error_message: str = "Login failed"):
    try:
        expect(locator).to_be_visible()
    except AssertionError:
        logger.error(error_message)
        raise AssertionError(error_message)


def fill_t_date(page):
    current_date = date.today()
    t_date = current_date - timedelta(days=(current_date.weekday()))
    t_date = t_date.strftime("%Y-%m-%d")

    group = page.locator("p-input-group").filter(
    has=page.locator("p-inputgroup-addon").filter(has_text=re.compile(r"^T$")))

    if group.count() == 0:
        return

    input_field = group.locator("input.p-inputtext")
    if not input_field.is_visible():
        return

    expect(input_field).to_be_visible()
    input_field.fill(t_date)
    group.get_by_role("button", name="Apply").click()
    logger.info(f"T-date filled with {t_date}")


def wait_for_ready_or_fail_on_interrupted(page, timeout=600):
    """
    Wait until #instanceState shows 'Ready'.
    Fails immediately when the status contains 'interrupted'.
    Polls every 5 seconds.

    :param page: Playwright page object
    :param timeout: maximum wait time in seconds
    """
    poll_interval = 5
    elapsed = 0

    while elapsed < timeout:
        status = page.locator("#instanceState").inner_text().lower()
        if "ready" in status:
            logger.info(f"Status is Ready after {elapsed}s")
            return
        elif "interrupted" in status:
            logger.error(f"Test is interrupted after {elapsed}s, stopping.")
            raise AssertionError("Test instance status is interrupted")
        else:
            # logger.info(f"Status: {status} after {elapsed}s")
            time.sleep(poll_interval)
            elapsed += poll_interval
    msg = f"Timeout after {timeout} seconds: status never became Ready (last status: {status})"
    logger.error(msg)
    raise AssertionError(msg)


# Helper function to generate test URLs.
def generate_test_urls(json_paths: Union[str, List[str]]):
    # json_path can be a string, tuple or list, so multiple sources can be loaded.
    if isinstance(json_paths, (list, tuple)):
        combinations = []
        for path in json_paths:
            with open(path, encoding="utf-8") as f:
                combinations.extend(json.load(f))
    else:
        with open(json_paths, encoding="utf-8") as f:
            combinations = json.load(f)

    urls = []
    for comb in combinations:
        params = {
            'informationStandard': comb.get('informationStandard')
        }

        branch = comb.get('branch')
        if branch and branch != "main":
            params['Branch'] = branch

        # Add optional parameters only when they are not None/null.
        optional_params = {
            'goal': comb.get('goal'),
            'category': comb.get('category'),
            'subcategory': comb.get('subcategory'),
            'role': comb.get('role'),
            'variant': comb.get('variant')
        }

        # Add only parameters that are not None.
        params.update({k: v for k, v in optional_params.items() if v is not None})

        # Build the URL.
        query_params = "&".join(
            f"{k}={urllib.parse.quote(str(v))}"
            for k, v in params.items()
        )

        url = f"https://my.interoplab.eu/uc-nictiz/tests?{query_params}"
        urls.append(url)
    return urls



def run_client_test(page: Page,
                    environment: str,
                    information_standard: str,
                    role: str,
                    # test_count: int,
                    category: Optional[str] = None,
                    subcategory: Optional[str] = None,
                    variant: Optional[str] = "default"):
    page.goto(f"https://my.interoplab.eu/uc-nictiz/tests/kickstart/{environment}")
    login_check(page.locator(f"text=Kickstart your test ({environment})"))

    # Select test set.
    page.get_by_text(information_standard).click()
    # Optionally select category and subcategory.
    if category:
        logger.info(f"Select category: {category}")
        page.get_by_text(category, exact=True).click()

    if subcategory:
        logger.info(f"Select subcategory: {subcategory}")
        page.get_by_text(subcategory, exact=True).click()

    # Select specific client test role.
    logger.info(f"Select test role: {role}")
    card = page.locator(
    "mat-card",
    has=page.locator("mat-card-title", has_text=f"{role}")
        ).filter(
            has=page.locator("span", has_text=f"variant: {variant}")
        )
    card.click()

    # Check that we are on the correct page.
    expect(page.get_by_role("heading", name="Test set-up overview")).to_be_visible()

    # Check the simulator URL.
    locator_sim_url = page.locator("#destinationInfo span", has_text="https://nictiz.proxy.interoplab.eu")
    assert locator_sim_url.inner_text().find("/q/") != -1, f"No production environment in URL: {locator_sim_url.inner_text()}"
    assert locator_sim_url.inner_text().find("/64e4b4df21773f655267edfe"), f"Unexpected organization ID in URL: {locator_sim_url.inner_text()}"

    # Start test instance.
    page.get_by_role("checkbox", name="Automated").check()
    page.get_by_role("button", name="Create test instance").click()

    expect(page.locator("#testInstanceHeader")).to_contain_text("Test Run")
    expect(page.locator("#testInstanceHeader")).to_contain_text(f"{role} - {environment} - {information_standard}")
    expect(page.locator("#instanceState")).to_contain_text("Waiting")

    page.get_by_role("button", name="Start test instance").click()

    # Start timer.
    start = time.perf_counter()
    logger.info("Waiting for status: Running")
    expect(page.locator("#instanceState")).to_contain_text("Running")
    # expect(page.locator("app-test-instance")).to_have_text(re.compile(fr"Running test \d+/{test_count}"))

    # Wait until the test is ready.
    logger.info("Waiting for status: Ready")
    wait_for_ready_or_fail_on_interrupted(page, timeout=120)

    # Stop timer.
    elapsed = time.perf_counter() - start
    logger.info(f"Test status changed to Ready in {elapsed:.2f} seconds")
    logger.info("Status is now Ready")

    # Validate successful execution.
    successful_block = page.locator("mat-card-content >> div", has_text="Successful")
    expect(successful_block.locator("h3")).to_have_text("Successful")
    # expect(successful_block.locator("span").nth(0)).to_have_text(str(test_count))
    expect(successful_block.locator("span").nth(1)).to_have_text("100%")
    logger.info("All test cases completed successfully")



def run_server_test(page: Page,
                    environment: str,
                    information_standard: str,
                    role: str,
                    use_case: str,
                    fhir_version: str,
                    # test_count: int,
                    category: Optional[str] = None,
                    subcategory: Optional[str] = None,
                    variant: Optional[str] = "default"):
    page.goto(f"https://my.interoplab.eu/uc-nictiz/tests/kickstart/{environment}")
    login_check(page.locator(f"text=Kickstart your test ({environment})"))

    # Select test set.
    page.get_by_text(information_standard).click()
    # Optionally select category and subcategory.
    if category:
        logger.info(f"Select category: {category}")
        page.locator("mat-card", has_text=f"{category}").first.click()

    if subcategory:
        logger.info(f"Select subcategory: {subcategory}")
        page.locator("mat-card", has_text=f"{subcategory}").first.click()

    # Select specific test role.
    logger.info(f"Select test role: {role}")
    card = page.locator(
    "mat-card",
    has=page.locator("mat-card-title", has_text=f"{role}")
        ).filter(
            has=page.locator("span", has_text=f"variant: {variant}")
        )
    card.click()

    # Test setup page.
    expect(page.get_by_role("heading", name="Test set-up overview")).to_be_visible()

    if use_case == "nictiz":
        page.get_by_role("textbox", name="Your FHIR server base url").fill(f"https://my.interoplab.eu/uc-nictiz/{fhir_version}/fhir")
    elif use_case == "medmij":
        page.get_by_role("textbox", name="Your FHIR server base url").fill(f"https://nictiz.fhir.interoplab.eu/medmij/{fhir_version}/fhir")
    elif use_case == "nictizmedmij":
        page.get_by_role("textbox", name="Your FHIR server base url").fill(f"https://nictiz.fhir.interoplab.eu/medmij/{fhir_version}/fhir")

    fill_t_date(page)

    page.get_by_role("button", name="Create test instance").click()

    # Test run page.
    text = page.locator("#instanceDetails").inner_text()
    try:
        expect(page.locator("#testInstanceHeader")).to_contain_text("Test Run")
        for part in [information_standard,environment,category,subcategory,role]:
            if part:
                assert part in text, f"'{part}' is missing from text: {text}"

        expect(page.locator("#instanceState")).to_contain_text("Waiting")
    except AssertionError as e:
        test_run = page.locator("#testInstanceHeader").inner_text()
        logger.info(f"Test instance {test_run} failed")
        raise

    page.get_by_role("button", name="Start test instance").click()
    # Start timer.
    start = time.perf_counter()
    logger.info("Waiting for status: Running")
    expect(page.locator("#instanceState")).to_contain_text("Running")
    # expect(page.locator("app-test-instance")).to_have_text(re.compile(fr"Running test \d+/{test_count}"))


    logger.info("Waiting for status: Ready")
    wait_for_ready_or_fail_on_interrupted(page, timeout=600)

    # Stop timer.
    end = time.perf_counter()
    elapsed = end - start
    logger.info(f"Test status changed to Ready in {elapsed:.2f} seconds")
    logger.info("Status is now Ready")

    successful_block = page.locator("mat-card-content >> div", has_text="Successful")
    expect(successful_block.locator("h3")).to_have_text("Successful")
    # expect(successful_block.locator("span").nth(0)).to_have_text(str(test_count))
    expect(successful_block.locator("span").nth(1)).to_have_text("100%")
    logger.info("All test cases completed successfully")
