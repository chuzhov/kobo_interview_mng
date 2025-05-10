from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from services.logger import logger


# Data models
class FormSubmissionInterview(BaseModel):
    uuid: str = Field(..., alias="_uuid")
    enumerator_Id: str = Field(
        ..., alias="metadata/enumerator_Id"
    )  # Map API key directly to enumerator_Id
    audit_URL: Optional[str] = Field(
        None, alias="_attachments"
    )  # Single filename or None
    interview_duration: Optional[float] = Field(
        None
    )  # Duration in minutes, could be empty

    @field_validator("audit_URL", mode="before")
    @classmethod
    def extract_filename(cls, value):
        """Extract filename from the first attachment dictionary, or return None."""
        if not isinstance(value, list) or not value:
            return None
        first_item = value[0]
        if isinstance(first_item, dict) and "filename" in first_item:
            return first_item["filename"]
        logger.warning(f"Invalid attachment format: {first_item}")
        return None

    class Config:
        # Optional: Allows population by field name (e.g., enumerator_Id) in addition to alias
        validate_by_name = True


def convert_model_to_dict_list(instances: List[BaseModel]) -> List[dict]:
    if not isinstance(instances, list):
        raise ValueError("Expected a list of BaseModel instances.")

    return [instance.model_dump() for instance in instances]
