from sqlalchemy.orm import Session
from . import models
import random

def upsert_country(db: Session, data: dict):
    existing = db.query(models.Country).filter(models.Country.name.ilike(data["name"])).first()
    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
    else:
        new_country = models.Country(**data)
        db.add(new_country)
    db.commit()

def get_countries(db: Session, region=None, currency=None, sort=None):
    query = db.query(models.Country)
    if region:
        query = query.filter(models.Country.region.ilike(region))
    if currency:
        query = query.filter(models.Country.currency_code == currency)
    if sort == "gdp_desc":
        query = query.order_by(models.Country.estimated_gdp.desc())
    return query.all()

