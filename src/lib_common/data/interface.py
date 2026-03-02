from abc import ABC, abstractmethod

import pandas as pd


class ICollector(ABC):
    @abstractmethod
    def collect(self, **kwargs) -> pd.DataFrame: ...


class ICleaner(ABC):
    @abstractmethod
    def clean(self, df_collect_rst: pd.DataFrame, **kwargs) -> pd.DataFrame: ...


class IStorager(ABC):
    @abstractmethod
    def store(self, df_clean_rst: pd.DataFrame, **kwargs) -> None: ...
