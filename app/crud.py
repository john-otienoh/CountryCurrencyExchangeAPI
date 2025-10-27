# app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime
import random

from app import models

def get_country_by_name(db: Session, name: str) -> Optional[models.Country]:
    return db.query(models.Country).filter(func.lower(models.Country.name) == name.lower()).first()

def list_countries(db: Session, region: Optional[str]=None, currency: Optional[str]=None, sort: Optional[str]=None) -> List[models.Country]:
    q = db.query(models.Country)
    if region:
        q = q.filter(models.Country.region == region)
    if currency:
        q = q.filter(models.Country.currency_code == currency)
    if sort == "gdp_desc":
        q = q.order_by(models.Country.estimated_gdp.desc().nullslast())
    elif sort == "gdp_asc":
        q = q.order_by(models.Country.estimated_gdp.asc().nullslast())
    return q.all()

def delete_country(db: Session, name: str) -> bool:
    c = get_country_by_name(db, name)
    if not c:
        return False
    db.delete(c)
    db.commit()
    return True

def upsert_country(db: Session, data: dict, last_refreshed_at: datetime):
    """
    data: dictionary with keys: name, capital, region, population, currency_code, exchange_rate, estimated_gdp, flag_url
    Updates existing row or inserts.
    """
    existing = get_country_by_name(db, data["name"])
    if existing:
        # update fields
        existing.capital = data.get("capital")
        existing.region = data.get("region")
        existing.population = data.get("population")
        existing.currency_code = data.get("currency_code")
        existing.exchange_rate = data.get("exchange_rate")
        existing.estimated_gdp = data.get("estimated_gdp")
        existing.flag_url = data.get("flag_url")
        existing.last_refreshed_at = last_refreshed_at
        db.add(existing)
    else:
        new = models.Country(
            name=data["name"],
            capital=data.get("capital"),
            region=data.get("region"),
            population=data.get("population"),
            currency_code=data.get("currency_code"),
            exchange_rate=data.get("exchange_rate"),
            estimated_gdp=data.get("estimated_gdp"),
            flag_url=data.get("flag_url"),
            last_refreshed_at=last_refreshed_at
        )
        db.add(new)
    db.commit()
