
from .base import IDataStrategy


class BaseCleanStrategy:
    def __init__(self):
        self.df_collect_rst = pd.DataFrame()
        self.df_clean_rst = pd.DataFrame()

    def execute(self, context: Dict[str, Any]) -> None:
        self.df_collect_rst = context.get("df_collect_rst", None)
        self.df_clean_rst = self.clean(context)

    def before(self, context: Dict[str, Any]) -> None:
        if self.df_collect_rst is None:
            raise RuntimeError("df_collect_rst must exist")

        if self.df_collect_rst.empty:
            raise RuntimeError("df_collect_rst must not empty")

    def clean(self, context: Dict[str, Any]) -> pd.DataFrame | None: ...

    def end(self, context: Dict[str, Any]) -> None:
        if self.df_clean_rst is None or self.df_clean_rst.empty:
            run_logger.error("未清洗到股票数据")
            raise ValueError("未清洗到股票数据")

        run_logger.info(f"成功获取{len(self.df_clean_rst)}条记录...")
        context["df_clean_rst"] = self.df_collect_rst