from typing import List
from pydantic import BaseModel, Field


class TasksConfigsM(BaseModel):
    sources: List[str] = []


class JobConfig(BaseModel):
    name: str
    description: str | None
    category: str = "date"
    expression: str
    t_name: str
    t_args: list = []
    t_kwargs: dict = {}
    is_active: bool = False


class JobConfigGet(JobConfig):
    id: str


class JobConfigAdd(JobConfig): ...


class JobConfigSet(JobConfig):
    id: str
    name: str | None = None
    category: str | None = None
    expression: str | None = None
    t_name: str | None = None
    t_args: list | None = None
    t_kwargs: dict | None = None
    is_active: bool | None = None


class JobConfigFilter(JobConfigSet):
    id: str | None = Field(None, max_length=64)
