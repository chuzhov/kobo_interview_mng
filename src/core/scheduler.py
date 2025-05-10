# core/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from core.config import DEBUG, TIMEZONE, WORKING_HOURS, DEBUG_SCHEDULER_INTERVAL

from schemas.kobo_schema import convert_model_to_dict_list
from services.kobo import fetch_int_list, get_int_duration
from services.db_ops import insert_new_records, get_existing_uuids
from services.logger import logger

async def scheduled_job():
    logger.info("Scheduled job started.")

    saved_uuids = await get_existing_uuids()
    if saved_uuids:
        logger.info(f"Fetched {len(saved_uuids)} existing UUIDs from the database.")

    fetched = await fetch_int_list()
    if not fetched:
        logger.critical("No records to process.")
        return
#    else:
#        logger.info(f"Fetched {len(fetched)} records from the external API.")
    
    if len(saved_uuids) > 0 and len(fetched) > 0:
        fetched = [r for r in fetched if r.uuid not in saved_uuids]
    if len(fetched) == 0:
        logger.info("No new records to process.")
        return

    for record in fetched:
        if record.audit_URL:
            interview_duration = await get_int_duration(record.audit_URL)
            record.interview_duration = interview_duration if interview_duration is not None else None
        
    await insert_new_records(
        submissions = convert_model_to_dict_list( fetched )
    )

scheduler = AsyncIOScheduler(timezone = TIMEZONE)
def setup_jobs():
    if DEBUG:
        scheduler.add_job(
            scheduled_job, 
            IntervalTrigger(
                minutes=DEBUG_SCHEDULER_INTERVAL
            ),  # Run every 5 minutes
            id="debug_job",  # Unique ID for the job
            replace_existing = False  # Actually, this is the default behavior
        )
        logger.info(f"Scheduler is running in DEBUG mode. Job is set to run every {DEBUG_SCHEDULER_INTERVAL} minutes.")
    else:
        scheduler.add_job(
            scheduled_job,
            CronTrigger(
                hour = f'{WORKING_HOURS["start"]}-{WORKING_HOURS["end"]}', 
                minute = 0,
            )  
        )
        logger.info(f"Scheduler is running in PRODUCTION mode. Job is set to run every hour from {WORKING_HOURS['start']} to {WORKING_HOURS['end']}.")
    