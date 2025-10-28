from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel


class CountryOut(BaseModel):
    id: int
    name: str
    capital: Optional[str]
    region: Optional[str]
    population: int
    currency_code: Optional[str]
    exchange_rate: Optional[float]
    estimated_gdp: Optional[float]
    flag_url: Optional[str]
    last_refreshed_at: Optional[datetime]

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: (
                v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v.astimezone(timezone.utc)
            ).isoformat(timespec="milliseconds").rstrip('Z').replace("+00:00", "") + "Z"
        }


class StatusOut(BaseModel):
    total_countries: int
    last_refreshed_at: Optional[datetime]

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: (
                v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v.astimezone(timezone.utc)
            ).isoformat(timespec="milliseconds").rstrip('Z').replace("+00:00", "") + "Z"
        }


class ErrorOut(BaseModel):
    error: str
    details: Optional[dict] = None
