import os


def pytest_configure():
    print("----pytest_configure---")
    os.environ["environment"] = "dev"
    os.environ["root"] = r"/Users/huncidd/Develop/Code/Self/Libs/lib-common"
