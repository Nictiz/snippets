def pytest_addoption(parser):
    """Add project CLI options early, so pytest always recognizes them."""
    parser.addoption(
        "--branch",
        action="store",
        default=None,
        help="Override the branch for bulk tests",
    )
    parser.addoption(
        "--bulk-profile",
        action="store",
        default=None,
        help="Bulk profile from config/bulk-testsets.toml or config/bulk.local.toml",
    )
    parser.addoption(
        "--info-standard",
        action="append",
        default=None,
        help="Override the profile with one or more information standards for bulk tests",
    )
    parser.addoption(
        "--input_dir",
        action="store",
        default=None,
        help="Override the input directory for bulk tests",
    )
