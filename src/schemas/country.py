from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class CountryBase(BaseModel):
    name: str = Field(..., min_length=1, description="Country name")
    capital: Optional[str] = None
    region: Optional[str] = None
    population: int = Field(
        ..., ge=0, description="Population must be greater than or equal to 0"
    )
    currency_code: Optional[str] = None
    exchange_rate: Optional[float] = None
    estimated_gdp: Optional[float] = None
    flag_url: Optional[str] = None


class CountryCreate(CountryBase):
    """Schema for creating a country"""

    pass


class CountryResponse(CountryBase):
    """Schema for country responses"""

    id: int
    last_refreshed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CountryUpdate(BaseModel):
    """Schema for updating a country"""

    name: Optional[str] = None
    capital: Optional[str] = None
    region: Optional[str] = None
    population: Optional[int] = Field(None, gt=0)
    currency_code: Optional[str] = None
    exchange_rate: Optional[float] = None
    estimated_gdp: Optional[float] = None
    flag_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
