from pydantic import BaseModel

from ..types import PathType, UpperType, LowerType


class WorkerConfigsM(BaseModel):
    logfile: PathType | None = None
    loglevel: UpperType = "DEBUG"
    pool: LowerType = "threads"
    concurrency: int = 4


class BeatConfigsM(BaseModel):
    logfile: PathType | None = None
    loglevel: UpperType = "DEBUG"


class CeleryConfigsM(BaseModel):
    broker: str
    backend: str
    worker: WorkerConfigsM | None = None
    beat: BeatConfigsM | None = None
