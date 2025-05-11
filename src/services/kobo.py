# services/external.py
import csv
import os
from io import StringIO
from typing import List
from dotenv import load_dotenv

import httpx

import schemas.kobo_schema as schemas
from services.logger import logger


load_dotenv()

KOBO_SERVER = os.getenv("KOBO_SERVER")
API_TOKEN = os.getenv("API_TOKEN")
FORM_UID = os.getenv("FORM_UID")

FORM_SUBMISSIONS_API = f"{KOBO_SERVER}/api/v2/assets/{FORM_UID}/data/?fields=%5B%22metadata/enumerator_Id%22%2C%20%22_attachments%22%5D&format=json"
AUDIT_API = "https://api.example.com/audit/"
AUDIT_URL = "https://kobocat.unhcr.org/media/original?media_file="

API_HEADERS = {"Authorization": f"Token {API_TOKEN}", "Accept": "application/json"}


async def fetch_int_list(
    headers: dict = API_HEADERS,
) -> List[schemas.FormSubmissionInterview]:
    """Fetch form submissions from external API."""
    try:
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(FORM_SUBMISSIONS_API)
            response.raise_for_status()
            # Mock response parsing (adjust based on actual API response)
            results = response.json().get("results", [])
            logger.info(f"Fetched {len(results)} form submissions")
            return [schemas.FormSubmissionInterview(**item) for item in results]
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch form submissions: {e}")
        return []


async def get_int_duration(
    audit_url: str,
    headers: dict = API_HEADERS,
    node_start: str = "/aDYFXRVSK37D2AKJAS4AB9/group_introduction/a_1_first_interaction_note",
    node_end: str = "/aDYFXRVSK37D2AKJAS4AB9/group_main/group_interview_quality/interview_quality_note",
    precision: int = 1,
) -> float | None:
    """Fetch audit file and calculate interview duration."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url=AUDIT_URL + audit_url, headers=headers)
            response.raise_for_status()
            csv_file = StringIO(response.text)

        start_ts = None
        end_ts = None

        reader = csv.DictReader(csv_file)
        for row in reader:
            if row["node"] == node_start and start_ts is None:
                start_ts = int(row["start"])
            elif row["node"] == node_end:
                end_ts = int(row["end"])
                break
        if start_ts is not None and end_ts is not None:
            return round((end_ts - start_ts) / (1000 * 60), precision)
        else:
            return None
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error(f"Audit file not found at {audit_url}")
            return None
        else:
            logger.error(
                f"HTTP error occurred while fetching audit data for {audit_url}: {e}"
            )
            return None
    except (httpx.HTTPError, ValueError) as e:
        logger.error(f"Failed to fetch or process audit data for {audit_url}: {e}")
        return None
