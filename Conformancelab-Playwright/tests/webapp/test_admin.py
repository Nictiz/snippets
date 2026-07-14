from playwright.sync_api import expect
from tests.helpers import login_check
from utils.common.logger import setup_logger
import pytest
import time

pytestmark = pytest.mark.webapp

logger = setup_logger()


def test_login(page):
    page.goto("https://my.interoplab.eu/uc-nictiz/")
    try:
        assert page.locator("text=Welcome").is_visible()
        assert page.locator("text=Your personal Nictiz dashboard").is_visible()
    except AssertionError:
        raise AssertionError("Login failed")


def test_provisioning(page):
    page.goto("https://my.interoplab.eu/uc-nictiz/tests/manage")
    login_check(page.locator("text=Manage Conformancelab"))

    # Click provisioning for the main branch.
    branch_card = page.locator(".default-branch").filter(has=page.get_by_text("main"))
    branch_card.locator(".open-branch-provisioning button").click()

    # Check whether all instances passed.
    # Find the text line that contains the ratio.
    locator_last_provisioning = page.locator("span.text-sm:has-text('passed instances')").first

    expect(locator_last_provisioning).to_be_visible()
    text = locator_last_provisioning.inner_text()
    passed, total = map(int, text.split(" ")[0].split("/"))
    if passed != total:
        logger.warning(f"Not all instances passed: {passed}/{total}")
    else:
        logger.info(f"All instances passed: {passed}/{total}")


def test_main_sync(page):
    page.goto("https://my.interoplab.eu/uc-nictiz/tests/manage")
    login_check(page.locator("text=Manage Conformancelab"))
    branch_card = page.locator(".default-branch").filter(has=page.get_by_text("main"))
    sync_button = branch_card.locator(".sync-branch button")
    expect(sync_button).to_be_disabled()


def test_main_published(page):
    page.goto("https://my.interoplab.eu/uc-nictiz/tests/manage")
    login_check(page.locator("text=Manage Conformancelab"))
    branch_card = page.locator(".default-branch").filter(has=page.get_by_text("main"))
    publish_button = branch_card.locator("#default-branch-publishing").get_by_role("button")
    expect(publish_button).to_be_disabled()


def test_setup_link(page):
    page.goto("https://my.interoplab.eu/uc-nictiz/tests?informationStandard=BgZ%203.x&role=PHR-Client")
    expect(page.get_by_role("heading", name="Test setup")).to_be_visible()
    expect(page.get_by_role("heading", name="BgZ 3.x-Cert-MedMij-PHR-Client")).to_be_visible()


def test_report_page(page):
    page.goto("https://my.interoplab.eu/uc-nictiz")
    page.get_by_text("Conformancelab - Instance list").click()
    expect(page.get_by_role("heading", name="Conformancelab - Instance list")).to_be_visible()
    expect(page.locator('.p-datatable-mask')).to_be_visible()
    start = time.perf_counter()
    expect(page.locator('.p-datatable-mask')).not_to_be_visible(timeout=60000)
    elapsed = time.perf_counter() - start
    logger.info(f"Loader disappeared after {elapsed:.2f} seconds")
