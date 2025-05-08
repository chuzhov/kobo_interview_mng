# core/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from services.kobo import fetch_int_list, get_int_duration
from services.db_ops import insert_new_records
from services.logger import logger

async def scheduled_job():
    logger.info("Scheduled job started.")
    fetched = await fetch_int_list()
    enriched = [await get_int_duration(r) for r in fetched]
    await insert_new_records(enriched)

scheduler = AsyncIOScheduler(timezone="local")
scheduler.add_job(scheduled_job, CronTrigger(hour="7-22", minute=0))