from datetime import datetime

from ..data.generator import UuidGenerator
from ..logger.configs import loggers
from ..connect.configs import databases
from .factory import TaskFuncFactory
from .schemas import JobConfigGet
from .models import JobRecord, JobStatus

task_logger = loggers.get_logger("task")
local_db = databases.get_database("local")


@TaskFuncFactory.register("default.task")
def task_func(*args, **kwargs):
    task_logger.info(f"xxxx, task_func, {args}, {kwargs}")


class TaskExecutor:

    def __init__(self, configs: JobConfigGet):
        self.configs = configs

    def run(self, *args, **kwargs):
        func = TaskFuncFactory.get(self.configs.t_name, None)
        if func is None:
            raise ValueError(f"Task '{self.configs.t_name}' not registered")

        with local_db.connection() as conn:
            try:
                record_id = str(UuidGenerator.by_time())
                record = JobRecord(
                    id=record_id,
                    config_id=self.configs.id,
                    status=JobStatus.pending,
                    args=self.configs.t_args,
                    kwargs=self.configs.t_kwargs
                )
                conn.add(record)
                conn.flush()
                task_logger.info(f"Add pending JobRecord {self.configs.t_name}...")
            except Exception as e:
                task_logger.exception(f"Add pending JobRecord {self.configs.t_name}, failed: {e}")
                return

            # 开始运行
            record.status = JobStatus.running
            record.start_at = datetime.now()
            conn.commit()

            try:
                # 执行对应函数
                rst = func(*self.configs.t_args, **self.configs.t_kwargs)
                record.status = JobStatus.completed
                record.result = rst
            except Exception as e:
                task_logger.exception(f"Run task func, failed: {e}")
                record.status = JobStatus.failed
                record.error = f"{e}"
            record.end_at = datetime.now()
            conn.commit()
        return
