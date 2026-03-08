import os


def pytest_configure():
    print("----pytest_configure---")
    os.environ["APP__ENVIRONMENT"] = "dev"
    os.environ["APP__ROOT"] = r"F:\Code\A-Self\Libs\lib-common"
