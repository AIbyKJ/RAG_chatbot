def pytest_addoption(parser):
    parser.addoption("--log-to-file", action="store_true", help="Enable logging to file")
    parser.addoption("--log-to-prompt", action="store_true", help="Enable logging to console")