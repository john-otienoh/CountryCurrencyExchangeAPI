from sqlalchemy import Table, Column, Integer, String, Float, DateTime
from sqlalchemy.dialects.mysql import DATETIME
from db.database import metadata


countries = Table(
    'countries',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(200), nullable=False, unique=True, index=True),
    Column('capital', String(200), nullable=True),
    Column('region', String(100), nullable=True),
    Column('population', Integer, nullable=False),
    Column('currency_code', String(10), nullable=True),
    Column('exchange_rate', Float, nullable=True),
    Column('estimated_gdp', Float, nullable=True),
    Column('flag_url', String(500), nullable=True),
    Column('last_refreshed_at', DATETIME(timezone=True, fsp=3), nullable=True),
)
