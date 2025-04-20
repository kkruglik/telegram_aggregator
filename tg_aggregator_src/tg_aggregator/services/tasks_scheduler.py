import asyncio
import logging
from typing import Callable, Dict, Any, Union, Coroutine

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger('news_aggregator')


class TasksScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs = {}

    def add_job(self,
                func: Union[Callable[..., Coroutine[Any, Any, Any]], Callable[..., Any]],
                job_id: str,
                interval_minutes: int = None,
                cron: str = None,
                **kwargs) -> str:
        """
        Add a job to the scheduler

        Args:
            func: The function to schedule (can be async or regular)
            job_id: Unique identifier for the job
            interval_minutes: Run job every X minutes (alternative to cron)
            cron: Cron-style scheduling (alternative to interval)
            **kwargs: Additional arguments to pass to the job function

        Returns:
            job_id: The ID of the scheduled job
        """
        if job_id in self.jobs:
            logger.warning(f"Job {job_id} already exists. Replacing.")

        is_coroutine = asyncio.iscoroutinefunction(func)

        # Create appropriate wrapper based on function type
        if is_coroutine:
            # Wrapper for coroutine functions
            async def run_coroutine():
                try:
                    await func(**kwargs)
                except Exception as e:
                    logger.error(f"Error in scheduled job '{job_id}': {e}")

            job_func = run_coroutine
        else:
            def run_function():
                try:
                    func(**kwargs)
                except Exception as e:
                    logger.error(f"Error in scheduled job '{job_id}': {e}")

            job_func = run_function

        if cron:
            job = self.scheduler.add_job(
                job_func,
                'cron',
                id=job_id,
                replace_existing=True,
                **self._parse_cron(cron)
            )
        elif interval_minutes:
            job = self.scheduler.add_job(
                job_func,
                'interval',
                minutes=interval_minutes,
                id=job_id,
                replace_existing=True
            )
        else:
            raise ValueError("Either interval_minutes or cron must be specified")

        self.jobs[job_id] = job
        logger.info(f"Added job '{job_id}' to scheduler" +
                    f" ({'async' if is_coroutine else 'sync'})")
        return job_id

    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the scheduler"""
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            logger.info(f"Removed job '{job_id}' from scheduler")
            return True
        return False

    def start(self) -> None:
        """Start the scheduler"""
        self.scheduler.start()
        logger.info(f"Scheduler started with {len(self.jobs)} jobs")

    def shutdown(self) -> None:
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler shut down")

    def _parse_cron(self, cron_string: str) -> Dict[str, Any]:
        """Parse a cron string into kwargs for APScheduler"""
        parts = cron_string.split()
        if len(parts) != 5:
            raise ValueError("Cron string must have 5 parts: minute hour day month day_of_week")

        return {
            'minute': parts[0],
            'hour': parts[1],
            'day': parts[2],
            'month': parts[3],
            'day_of_week': parts[4]
        }
