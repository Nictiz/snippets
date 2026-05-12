# Conformancelab Tests

This repository uses [Playwright for Python](https://playwright.dev/python/) to test the Nictiz setup in Conformancelab. The tests can also be used to automate Conformancelab workflows.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Access to the Interoplab platform
- A local checkout of `Nictiz-testscripts` with generated output

The bulk tests use this folder structure by default:

```text
Nictiz/
  Conformancelab-tests/
  Nictiz-testscripts/
    output/
```

If `Nictiz-testscripts` is located somewhere else, pass the path to its `output` folder with `--input_dir`.

## Installation

Run this from the root of this repository:

```powershell
cd C:\path\to\Conformancelab-tests
uv sync
uv run playwright install chromium
```

## Login Credentials

Copy `.env.example` to `.env` and fill in your Interoplab credentials:

```powershell
Copy-Item .env.example .env
```

The `.env` file contains:

```env
CL_USERNAME=your.CL.username
CL_PASSWORD=your.CL.password
CL_TOTP_SECRET=your.CL.TOTP.secret
```

`CL_TOTP_SECRET` can be found in the password manager or when setting up the 2MFA for your Interoplab account. The `.env` file is ignored by Git.

During a test run, `utils/auth/login_once.py` automatically creates `utils/auth/state.json`. This file is also ignored by Git.

## Bulk Tests

The bulk test is located at:

```text
tests/bulk/test_regression.py
```

Bulk test sets are configured with profiles in:

```text
config/bulk-testsets.toml
```

Run a shared profile:

```powershell
uv run pytest .\tests\bulk\test_regression.py `
  -m bulk `
  --bulk-profile ggz
```

The repository includes profiles such as `all` and single information standard tests. The default profile is configured in `[defaults]`.

For a personal test set, copy the example file and add your own profiles:

```powershell
Copy-Item .\config\bulk.local.example.toml .\config\bulk.local.toml
```

`config/bulk.local.toml` is ignored by Git, so every user can keep their own test sets locally:

```toml
[profiles.my-set]
branch = "main"
info_standards = [
  'STU3\BgZ-3-0',
  'R4\Immunization-2-0',
]
```

Run that local profile:

```powershell
uv run pytest .\tests\bulk\test_regression.py `
  -m bulk `
  --bulk-profile my-set
```

You can still override profile values from the command line for one-off runs:

```powershell
uv run pytest .\tests\bulk\test_regression.py `
  -m bulk `
  --branch main `
  --info-standard "STU3\BgZ-MSZ-2-0"
```

For an output folder in a different location:

```powershell
uv run pytest .\tests\bulk\test_regression.py `
  -m bulk `
  --bulk-profile all `
  --input_dir "C:\path\to\Nictiz-testscripts\output"
```

Important: first check out the correct branch of `Nictiz-testscripts`. The extractor reads the local files from the configured `input_dir`.

## Checking The Bulk Flow

The generated combinations file is:

```text
utils/common/unique_combinations_all.json
```

This file is ignored by Git and is automatically recreated for the selected bulk profile.

Extract only the test sets:

```powershell
uv run python .\utils\common\extract_testset.py `
  --root ..\Nictiz-testscripts\output `
  --branch main `
  --folders "STU3\BgZ-MSZ-2-0"
```

Print only the generated URLs:

```powershell
uv run python -c "from tests.helpers import generate_test_urls; [print(u) for u in generate_test_urls(['utils/common/unique_combinations_all.json'])]"
```

Check which bulk tests are collected, without starting a browser:

```powershell
uv run pytest --collect-only -q -m bulk --bulk-profile pdfa
```

Run the bulk tests:

```powershell
uv run pytest -m bulk --bulk-profile all
```

## Other Tests

Run all tests:

```powershell
uv run pytest
```

Run only webapp tests:

```powershell
uv run pytest -m webapp
```

Run only bulk tests:

```powershell
uv run pytest -m bulk --bulk-profile all
```
