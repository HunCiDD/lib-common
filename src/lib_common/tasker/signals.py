from datetime import datetime, UTC
from celery import signals

from ..logger.configs import loggers
from ..connect.configs import databases
from .models import TaskExecution

run_logger = loggers.get_logger("run")
local_db = databases.get_database("local")


@signals.task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    """任务开始前，创建或更新执行记录，标记为 STARTED"""
    _args = args[0] if args else []
    _kwargs = kwargs if kwargs else {}
    with local_db.connection() as conn:
        try:
            execution: TaskExecution = conn.query(TaskExecution).filter(TaskExecution.id == task_id).first()
            if not execution:
                execution = TaskExecution(id=task_id, status="STARTED", args=_args, kwargs=_kwargs)
                conn.add(execution)
            else:
                execution.status = "STARTED"
                execution.args = _args
                execution.kwargs = _kwargs
            execution.start_at = datetime.now(UTC)
            conn.commit()
        except Exception as e:
            run_logger.exception(f"Failed to update task execution on prerun: {e}")


@signals.task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """任务成功完成"""
    task_id = sender.request.id
    try:
        with local_db.connection() as conn:
            execution: TaskExecution = conn.query(TaskExecution).filter(TaskExecution.id == task_id).first()
            if execution:
                execution.status = "SUCCESS"
                execution.result = result
                execution.end_at = datetime.now(UTC)
                conn.commit()
    except Exception as e:
        run_logger.exception(f"Failed to update task execution on success: {e}")


@signals.task_failure.connect
def task_failure_handler(sender=None, exception=None, traceback=None, **kwargs):
    """任务失败"""
    task_id = sender.request.id
    try:
        with local_db.connection() as conn:
            execution: TaskExecution = conn.query(TaskExecution).filter(TaskExecution.id == task_id).first()
            if execution:
                execution.status = "FAILURE"
                execution.error = str(exception) + "\n" + str(traceback)
                execution.end_at = datetime.now(UTC)
                conn.commit()
    except Exception as e:
        run_logger.exception(f"Failed to update task execution on failure: {e}")


@signals.task_retry.connect
def task_retry_handler(sender=None, reason=None, **kwargs):
    """任务重试"""
    task_id = sender.request.id
    try:
        with local_db.connection() as conn:
            execution: TaskExecution = conn.query(TaskExecution).filter(TaskExecution.id == task_id).first()
            if execution:
                execution.status = "RETRY"
                execution.error = reason
                execution.retry_count += 1
                conn.commit()
    except Exception as e:
        run_logger.exception(f"Failed to update task execution on failure: {e}")
