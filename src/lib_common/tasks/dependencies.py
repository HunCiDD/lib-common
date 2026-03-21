from .services import JobConfigService


async def job_config_service() -> JobConfigService:
    return JobConfigService()
