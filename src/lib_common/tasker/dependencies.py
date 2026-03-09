from .services import TaskCronJobService


async def task_cron_job_service() -> TaskCronJobService:
    return TaskCronJobService()
