from typing import Type
import os
import signal
import subprocess

from celery import Celery
from celery.beat import Scheduler

from ..settings import Settings, get_settings
from ..logger.configs import loggers
from .schemas import CeleryConfigsM
from .scheduer import DatabaseScheduler

run_logger = loggers.get_logger("run")


class CeleryBase:
    tag = "base"

    def __init__(self, configs: CeleryConfigsM) -> None:
        self.configs = configs
        self._process: subprocess.Popen | None = None

    def run(self):
        run_logger.info(f"Run celery {self.tag} process.")
        self._process = self._run_process()

    def stop(self):
        run_logger.info(f"Stop celery {self.tag} process.")
        self._stop_process()

    def _run_process(self) -> subprocess.Popen:
        return None  # type: ignore

    def _stop_process(self):
        """
        停止 Celery 进程
        :param process: 进程对象
        :param process_name: 进程名称（用于日志记录）
        """
        if self._process:
            try:
                if os.name == "nt":  # Windows 系统
                    subprocess.run(["taskkill", "/PID", str(self._process.pid), "/F"])
                else:  # Linux/macOS 系统
                    os.kill(self._process.pid, signal.SIGTERM)
                run_logger.info(f"Celery {self.tag} with PID {self._process.pid} has been stopped.")
            except Exception as e:
                run_logger.error(f"Failed to stop Celery {self.tag}: {e}", exc_info=True)
        else:
            run_logger.info(f"No Celery {self.tag} process is running.")


class CeleryWork(CeleryBase):
    tag = "worker"

    def _run_process(self) -> subprocess.Popen:
        run_logger.info(f"Run celery {self.tag} process.")
        env = os.environ.copy()
        args = [
            "celery",
            "-A",
            f"{self.configs.app}",
            "worker",
            f"--loglevel={self.configs.worker.loglevel}",
            f"--logfile={self.configs.worker.logfile}",
            f"--pool={self.configs.worker.pool or 'threads'}",
            f"--concurrency={self.configs.worker.concurrency or 5}",
        ]
        process = subprocess.Popen(args, env=env)
        run_logger.info(f"Run celery worker process with PID: {process.pid}")
        return process


class CeleryBeat(CeleryBase):
    tag = "beat"

    def _run_process(self) -> subprocess.Popen:
        run_logger.info(f"Run celery {self.tag} process.")
        env = os.environ.copy()
        args = [
            "celery",
            "-A",
            f"{self.configs.app}",
            "beat",
            f"--loglevel={self.configs.beat.loglevel}",
            f"--logfile={self.configs.beat.logfile}",
        ]
        process = subprocess.Popen(args, env=env)
        run_logger.info(f"Celery beat started with PID: {process.pid}")
        return process


def get_celery(scheduler_cls: Type[Scheduler] = DatabaseScheduler) -> Celery:
    settings: Settings = get_settings()
    if not settings.tasker.broker:
        raise ValueError("Celery broker is empty.")

    if not settings.tasker.backend:
        raise ValueError("Celery backend is empty")

    _celery = Celery(f"{settings.app.name}", broker=settings.tasker.broker, backend=settings.tasker.backend)

    # 配置Celery
    _celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Shanghai",
        task_default_queue=f"{settings.app.name}_default",
        broker_connection_retry_on_startup=True,
    )

    # 设置自定义调度器
    _celery.conf.beat_scheduler = scheduler_cls  # type: ignore
    return _celery
