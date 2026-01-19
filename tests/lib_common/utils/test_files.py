import os
from os import mkdir
from pathlib import Path

import pytest
from app_base.utils.files import Dir, File, IniFile, JsonFile, YamlFile

CUR_DIR = Path(__file__).parent


TEST_TMP_DIR = CUR_DIR / "test_tmp"
if not os.path.exists(TEST_TMP_DIR):
    mkdir(TEST_TMP_DIR)


@pytest.fixture
def test_file():
    return TEST_TMP_DIR / "test_file.txt"


@pytest.fixture
def test_dir():
    _dir = TEST_TMP_DIR / "test_dir"
    if not os.path.exists(_dir):
        mkdir(_dir)
    return TEST_TMP_DIR / "test_dir"


class TestFile:
    def test_file_base(self, test_file):
        content = "test content"
        with open(test_file, "w+", encoding="utf-8") as fp:
            fp.write(content)

        f = File(test_file)
        assert f.exist is True
        assert f.size == len(content)
        assert f.read() == content
        assert f.suffix == ".txt"
        assert f.name == "test_file.txt"

        f.write("new content")
        assert f.read() == "new content"
        f.remove()
        assert f.exist is False


class TestDir:
    def test_dir_iters(self, test_dir):
        _dir = Dir(test_dir)
        items = _dir.iters()
        assert len(items) == 0


class TestJsonFile:
    def test_base(self):
        file_path = TEST_TMP_DIR / "test.json"

        jf = JsonFile(file_path)
        if jf.exist:
            jf.remove()

        data = {"key": "value"}
        jf.dump(data)
        assert jf.exist is True
        assert jf.suffix == ".json"

        loaded_data = jf.load()
        assert loaded_data == data

        jf.remove()


class TestIniFile:
    def test_base(self):
        file_path = TEST_TMP_DIR / "test.ini"
        with open(file_path, "w", encoding="utf-8") as fp:
            fp.write("""[test]
            a=1
            """)

        ini_file = IniFile(file_path)
        loaded_data = ini_file.load()
        assert loaded_data["test"]["a"] == "1"
        ini_file.remove()


class TestYamlFile:
    def test_base(self):
        file_path = TEST_TMP_DIR / "test.yaml"
        with open(file_path, "w", encoding="utf-8") as fp:
            fp.write("""'test':  1
            """)
        yaml_file = YamlFile(file_path)

        loaded_data = yaml_file.load()
        assert loaded_data["test"] == 1
        yaml_file.remove()


if __name__ == "__main__":
    pytest.main()
