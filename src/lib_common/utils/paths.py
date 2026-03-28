from pathlib import Path

from ..settings import Settings


class Paths:
    def __init__(self, settings: Settings):
        self._settings = settings

        self._root_path = Path(self._settings.app.root)
        self._temp_path = self._root_path / "temp"

    @property
    def root(self) -> Path:
        return self._root_path

    @property
    def temp(self) -> Path:
        return self._temp_path
