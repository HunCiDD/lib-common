from typing import Callable, List
from pathlib import Path
import os

import pytest
from dotenv import load_dotenv


def pytest_configure():
    print("----pytest_configure---")
    os.environ["environment"] = "dev"
    os.environ["root"] = r"/Users/huncidd/Develop/Code/Self/Libs/lib-common"
