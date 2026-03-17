import importlib
import pkgutil
from types import ModuleType
from typing import List
from pytz import utc

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger

from ..data.converter import StringConverter
from ..settings import Settings
from ..logger.configs import loggers
from ..connect.configs import databases

from .models import JobConfig
from .schemas import JobConfigGet
from .executor import TaskExecutor

tasker_logger = loggers.get_logger("tasker")
local_db = databases.get_database("local")


class TaskScheduler:
    def __init__(self, settings: Settings):
        tasker_logger.info(f"Init...")

        self.settings = settings
        self._job_stores = {"default": SQLAlchemyJobStore(url=local_db.url)}
        self._job_defaults = {"coalesce": False, "max_instances": 3}
        self._executors = {"default": ThreadPoolExecutor(20), "processpool": ProcessPoolExecutor(5)}

        self._scheduler = BackgroundScheduler(
            jobstores=self._job_stores, executors=self._executors, job_defaults=self._job_defaults, timezone=utc
        )
        # 自动导入
        tasker_logger.info(f"Auto import tasks package.")
        for task_package in self.settings.tasker.tasks:
            self._auto_import_tasks(task_package)

    def _auto_import_tasks(self, package_name: str):
        """
        导入指定包及其所有子包中名为 'tasks' 的模块（tasks.py 文件）。
        对于包内的每个子包，递归查找并导入其中的 tasks 模块。
        """
        tasker_logger.info(f"Auto import task package: {package_name}")
        try:
            package = importlib.import_module(package_name)
        except ModuleNotFoundError as e:
            tasker_logger.exception(f"警告：无法导入包 {package_name} - {e}")
            return

        # 如果不是包（没有 __path__ 属性），则无法递归
        if not hasattr(package, "__path__"):
            tasker_logger.exception(f"警告：{package_name} 不是包，无法递归查找 tasks")
            return

        self._find_and_import_tasks(package_name, package)

    def _find_and_import_tasks(self, package_name: str, package: ModuleType) -> None:
        """
        递归遍历包及其子包，导入所有名为 'tasks' 的模块（即 tasks.py 文件）。
        """
        for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
            full_name = f"{package_name}.{module_name}"
            # 如果当前模块名为 'tasks' 且不是包（即 tasks.py 文件），则导入
            if module_name == "tasks" and not is_pkg:
                try:
                    importlib.import_module(full_name)
                    tasker_logger.info(f"已导入模块: {full_name}")
                except Exception as e:
                    tasker_logger.exception(f"警告无法导入: {full_name} - {e}")

            # 如果是子包，则递归进入
            if is_pkg:
                try:
                    sub_package = importlib.import_module(full_name)
                    self._find_and_import_tasks(full_name, sub_package)
                except Exception as e:
                    tasker_logger.exception(f"警告无法导入子包: {full_name}，跳过其内部 tasks - {e}")

    @property
    def scheduler(self) -> BackgroundScheduler:
        return self._scheduler

    def start(self):
        tasker_logger.info("Start...")
        self._load_jobs()
        self._scheduler.start()

    def shutdown(self):
        tasker_logger.info("Shutdown...")
        self._scheduler.shutdown()

    def _load_jobs(self):
        """
        从数据库加载配置，生成jobs
        """
        tasker_logger.info("Load jobs...")
        try:
            with local_db.connection() as conn:
                job_configs: List[JobConfig] = conn.query(JobConfig).filter(JobConfig.is_active)
                for job_config in job_configs:
                    if job_config.category == "cron":
                        trigger = CronTrigger.from_crontab(job_config.expression)
                    elif job_config.category == "interval":
                        seconds = StringConverter.to_int(job_config.expression)
                        trigger = IntervalTrigger(seconds=seconds)
                    elif job_config.category == "date":
                        date = StringConverter.to_datetime(job_config.expression)
                        trigger = DateTrigger(date)
                    else:
                        raise ValueError("非法category")

                    _schemas = job_config.to_schema(JobConfigGet)
                    task_executor = TaskExecutor(configs=_schemas)
                    tasker_logger.info(f"Add job {_schemas}")
                    self._scheduler.add_job(task_executor.run, trigger, id=_schemas.id, replace_existing=True)

        except Exception as e:
            tasker_logger.exception(f"{e}")
