from typing import Any, List, Dict

from pydantic import BaseModel, Field

from ..types import PathType, UpperType, LowerType


class CeleryWorkerConfigsM(BaseModel):
    logfile: PathType | None = None
    loglevel: UpperType = "DEBUG"
    pool: LowerType = "threads"
    concurrency: int = 4


class CeleryBeatConfigsM(BaseModel):
    logfile: PathType | None = None
    loglevel: UpperType = "DEBUG"


class CeleryConfigsM(BaseModel):
    run: bool | None = False
    broker: str
    backend: str
    worker: CeleryWorkerConfigsM | None = None
    beat: CeleryBeatConfigsM | None = None


class TaskCronJobBase(BaseModel):
    name: str = Field(..., max_length=255, title="定时任务名称")
    expression: str = Field("", title="cron表达式")
    t_name: str
    t_args: List[Any] = []
    t_kwargs: Dict[str, Any] = {}
    enabled: bool = True
    one_off: bool = False


class TaskCronJobAdd(BaseModel):
    name: str = Field(..., max_length=255, title="定时任务名称")
    expression: str = Field("", title="cron表达式")
    t_name: str = Field(..., max_length=255, title="映射任务名")


class TaskCronJobGet(BaseModel):
    id: str = Field(..., max_length=64)
    name: str


class TaskCronJobSet(BaseModel): ...


class TaskCronJobList(BaseModel): ...
