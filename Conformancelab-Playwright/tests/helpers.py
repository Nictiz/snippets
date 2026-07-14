from playwright.sync_api import Page, Locator, expect
from utils.common.logger import setup_logger
import time
import re
from typing import Optional, Union, List
from datetime import date, timedelta
import json
import urllib.parse

logger = setup_logger()

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
