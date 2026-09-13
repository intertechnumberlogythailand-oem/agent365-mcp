"""
normalizer.py
Data normalization for AI model records from Dataverse
Converts raw Dataverse records to normalized Pydantic models
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AIModelNormalized(BaseModel):
    """Normalized AI Model data structure"""
    
    model_id: Optional[str] = Field(None, alias="cr_aimodelid")
    name: Optional[str] = Field(None, alias="cr_name")
    description: Optional[str] = Field(None, alias="cr_description")
    model_type: Optional[str] = Field(None, alias="cr_modeltype")
    version: Optional[str] = Field(None, alias="cr_version")
    status: Optional[str] = Field(None, alias="cr_status")
    provider: Optional[str] = Field(None, alias="cr_provider")
    endpoint: Optional[str] = Field(None, alias="cr_endpoint")
    api_key_required: Optional[bool] = Field(None, alias="cr_apikeyequired")
    max_tokens: Optional[int] = Field(None, alias="cr_maxtokens")
    temperature: Optional[float] = Field(None, alias="cr_temperature")
    created_on: Optional[datetime] = Field(None, alias="createdon")
    modified_on: Optional[datetime] = Field(None, alias="modifiedon")
    created_by: Optional[str] = Field(None, alias="createdbyname")
    modified_by: Optional[str] = Field(None, alias="modifiedbyname")
    owner: Optional[str] = Field(None, alias="ownerid")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


def normalize_ai_model(record: Dict[str, Any]) -> AIModelNormalized:
    """
    Normalize a Dataverse AI model record to standard format.
    
    Args:
        record: Raw Dataverse record dictionary
        
    Returns:
        Normalized AIModelNormalized Pydantic model
    """
    # Clean up OData metadata
    cleaned = {k: v for k, v in record.items() if not k.startswith("@")}
    
    # Handle datetime fields
    for date_field in ["createdon", "modifiedon"]:
        if date_field in cleaned and isinstance(cleaned[date_field], str):
            try:
                cleaned[date_field] = datetime.fromisoformat(cleaned[date_field].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                cleaned[date_field] = None
    
    # Handle lookup fields (extract name if nested)
    for field in ["createdbyname", "modifiedbyname", "ownerid"]:
        if field in cleaned and isinstance(cleaned[field], dict):
            cleaned[field] = cleaned[field].get("name") or cleaned[field].get("Value")
    
    # Parse numeric fields
    if "cr_maxtokens" in cleaned:
        try:
            cleaned["cr_maxtokens"] = int(cleaned["cr_maxtokens"])
        except (ValueError, TypeError):
            cleaned["cr_maxtokens"] = None
    
    if "cr_temperature" in cleaned:
        try:
            cleaned["cr_temperature"] = float(cleaned["cr_temperature"])
        except (ValueError, TypeError):
            cleaned["cr_temperature"] = None
    
    # Parse boolean fields
    if "cr_apikeyequired" in cleaned:
        cleaned["cr_apikeyequired"] = cleaned["cr_apikeyequired"] in [True, 1, "true", "1", "yes"]
    
    return AIModelNormalized(**cleaned)


def normalize_batch(records: list) -> list:
    """
    Normalize a batch of Dataverse AI model records.
    
    Args:
        records: List of raw Dataverse records
        
    Returns:
        List of normalized AIModelNormalized models
    """
    return [normalize_ai_model(record) for record in records]


def denormalize_ai_model(model: AIModelNormalized) -> Dict[str, Any]:
    """
    Convert normalized model back to Dataverse format.
    Useful for create/update operations.
    
    Args:
        model: Normalized AIModelNormalized model
        
    Returns:
        Dictionary in Dataverse format
    """
    data = model.model_dump(by_alias=True, exclude_none=True)
    
    # Convert datetime to ISO format for Dataverse
    for date_field in ["createdon", "modifiedon"]:
        if date_field in data and isinstance(data[date_field], datetime):
            data[date_field] = data[date_field].isoformat()
    
    # Convert boolean to int for Dataverse
    if "cr_apikeyequired" in data and isinstance(data["cr_apikeyequired"], bool):
        data["cr_apikeyequired"] = 1 if data["cr_apikeyequired"] else 0
    
    return data
