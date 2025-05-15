# services/external.py
import csv
import os
import json
from io import StringIO
from typing import List, Dict, Optional, TypeVar, Type, Any
from pydantic import BaseModel
from dotenv import load_dotenv

import httpx

import schemas.kobo_schema as schemas
from services.logger import logger


load_dotenv()

KOBO_SERVER = os.getenv("KOBO_SERVER", default="")
API_TOKEN = os.getenv("API_TOKEN", default="")
FORM_UID = os.getenv("FORM_UID", default="")

if not KOBO_SERVER or not API_TOKEN or not FORM_UID:
    logger.critical(
        "KOBO_SERVER, API_TOKEN, and FORM_UID must be set in the environment variables.")

#FORM_SUBMISSIONS_API = f"{KOBO_SERVER}/api/v2/assets/{FORM_UID}/data/?fields=%5B%22metadata/enumerator_Id%22%2C%20%22_attachments%22%5D&format=json"

AUDIT_URL = "https://kobocat.unhcr.org/media/original?media_file="

API_HEADERS = {"Authorization": f"Token {API_TOKEN}", "Accept": "application/json"}


async def fetch_submissions(
    kobo_server_url: str = KOBO_SERVER,
    form_id: str = FORM_UID,
    headers: dict = API_HEADERS,
    
    params: Optional[Dict[str, str]] = None,
) -> list[Dict[str, Any]]:
    """Fetch all form submissions from external API and parse them into the given schema.

    """
    try:    
        url = f"{kobo_server_url}/api/v2/assets/{form_id}/data/"
        
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            count, _, __, results = response.json().values()
            logger.info(f"Fetched {count} form submissions")
            # Parse the results into the given schema
            return results
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch form submissions: {e}")
        return []

# Define a generic type bound to BaseModel
T = TypeVar("T", bound=BaseModel)

async def fetch_kobo_data(
    schema: Type[T],
    fields: List[str],
    kobo_server_url: str = KOBO_SERVER,
    form_id: str = FORM_UID,
    headers: dict = API_HEADERS,
    
    params: Optional[Dict[str, str]] = None,
) -> List[T]:
    """Fetch form submissions from external API and parse them into the given schema.

    Args:
        schema: The Pydantic model to parse the API response into.
        fields: list of fields to include in the response.
        kobo_server_url: The base URL of the Kobo server.
        form_id: The ID of the form to fetch data for.
        headers: HTTP headers for the request.  
        params: Additional query parameters for the request.

    Returns:
        A list of instances of the given schema.
    """
    try:    
        url = f"{kobo_server_url}/api/v2/assets/{form_id}/data/"
        if not params:
            params = {"format": "json"}
        
        if isinstance(fields, list):
            if params is None: # the linter to not complain about the params being None
                params = {}
            params["fields"] = json.dumps(fields) 

        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            results = response.json().get("results", [])
            logger.info(f"Fetched {len(results)} form submissions")
            # Parse the results into the given schema
            return [schema(**item) for item in results]
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch form submissions: {e}")
        return []


async def fetch_audit_file(audit_url: str, headers: dict) -> Optional[List[Dict[str, str]]]:
    """Fetch the audit file from the given URL and return parsed CSV data.

    Args:
        audit_url: The URL of the audit file.
        headers: HTTP headers for the request.

    Returns:
        A list of dictionaries representing the rows in the CSV file, or None if an error occurs.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url=audit_url, headers=headers)
            response.raise_for_status()
            csv_file = StringIO(response.text)
            return list(csv.DictReader(csv_file))
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error(f"Audit file not found at {audit_url}")
        else:
            logger.error(
                f"HTTP error occurred while fetching audit data for {audit_url}: {e}"
            )
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch audit file from {audit_url}: {e}")
    return None

def calculate_duration(
    csv_data: List[Dict[str, str]],
    node_start: str,
    node_end: str,
    precision: int = 1,
) -> Optional[float]:
    """Calculate the interview duration from the parsed CSV data.

    Args:
        csv_data: A list of dictionaries representing the rows in the CSV file.
        node_start: The node indicating the start of the interview.
        node_end: The node indicating the end of the interview.
        precision: The number of decimal places for the result.

    Returns:
        The calculated duration in minutes, or None if the calculation cannot be performed.
    """
    start_ts = None
    end_ts = None

    for row in csv_data:
        if row["node"] == node_start and start_ts is None:
            start_ts = int(row["start"])
        elif row["node"] == node_end:
            end_ts = int(row["end"])
            break

    if start_ts is not None and end_ts is not None:
        return round((end_ts - start_ts) / (1000 * 60), precision)
    else:
        logger.warning("Start or end timestamp not found in the CSV data.")
        return None


async def get_int_duration(
    audit_url: str,
    headers: dict = API_HEADERS,
    node_start: str = "/aDYFXRVSK37D2AKJAS4AB9/group_introduction/a_1_first_interaction_note",
    node_end: str = "/aDYFXRVSK37D2AKJAS4AB9/group_main/group_interview_quality/interview_quality_note",
    precision: int = 1,
) -> Optional[float]:
    """Fetch audit file and calculate interview duration.

    Args:
        audit_url: The URL of the audit file.
        headers: HTTP headers for the request.
        node_start: The node indicating the start of the interview.
        node_end: The node indicating the end of the interview.
        precision: The number of decimal places for the result.

    Returns:
        The calculated duration in minutes, or None if an error occurs.
    """
    csv_data = await fetch_audit_file(AUDIT_URL + audit_url, headers)
    if csv_data is not None:
        return calculate_duration(csv_data, node_start, node_end, precision)
    return None