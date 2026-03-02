from ..logger.configs import loggers
from .interface import ICollector, ICleaner, IStorager

run_logger = loggers.get_logger("run")


class Pipeline:
    def __init__(self, collector: ICollector, cleaner: ICleaner = None, storager: IStorager = None):
        self.collector = collector
        self.cleaner = cleaner
        self.storager = storager

    def run(self, **kwargs):
        run_logger.info("run")
        df_collect_rst = self.collector.collect(**kwargs)
        df_clean_rst = self.cleaner.clean(df_collect_rst, **kwargs)
        self.storager.store(df_clean_rst, **kwargs)
