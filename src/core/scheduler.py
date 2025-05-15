# core/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from core.config import DEBUG, DEBUG_SCHEDULER_INTERVAL, TIMEZONE, WORKING_HOURS
import schemas.kobo_schema as schemas
from services.db_ops import get_existing_uuids, insert_new_records
from services.kobo import fetch_kobo_data, get_int_duration, fetch_submissions
from services.logger import logger


async def scheduled_job__Get_interview_duration():
    logger.info("Scheduled job started.")

    await fetch_submissions()

    saved_uuids = await get_existing_uuids()
    if saved_uuids:
        logger.info(f"Fetched {len(saved_uuids)} existing UUIDs from the database.")

    fetched = await fetch_kobo_data(
        schema=schemas.FormSubmissionInterview,
        fields=['metadata/enumerator_Id', '_attachments']
    )
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
            record.interview_duration = (
                interview_duration if interview_duration is not None else None
            )

    await insert_new_records(submissions=schemas.convert_model_to_dict_list(fetched))


scheduler = AsyncIOScheduler()


def setup_jobs():
    if DEBUG:
        scheduler.add_job(
            func=scheduled_job__Get_interview_duration,
            trigger=IntervalTrigger(minutes=DEBUG_SCHEDULER_INTERVAL),  # Run every 5 minutes
            id="debug_job",  # Unique ID for the job
            replace_existing=False,  # Actually, this is the default behavior
        )
        logger.info(
            f"Scheduler is running in DEBUG mode. Job is set to run every {DEBUG_SCHEDULER_INTERVAL} minutes."
        )
    else:
        scheduler.add_job(
            func=scheduled_job__Get_interview_duration,
            trigger=CronTrigger(
                timezone=TIMEZONE,
                hour=f'{WORKING_HOURS["start"]}-{WORKING_HOURS["end"]}',
                minute=0,
            ),
            id="production_job",  # Unique ID for the job
            replace_existing=False,  # Actually, this is the default behavior
        )
        logger.info(
            f"Scheduler is running in PRODUCTION mode. Job is set to run every hour from {WORKING_HOURS['start']} to {WORKING_HOURS['end']}."
        )
