# app/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CountryBase(BaseModel):
    name: str = Field(..., min_length=1)
    capital: Optional[str]
    region: Optional[str]
    population: int = Field(..., ge=0)

class CountryCreate(CountryBase):
    currency_code: Optional[str]

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
        orm_mode = True

class StatusOut(BaseModel):
    total_countries: int
    last_refreshed_at: Optional[datetime]
