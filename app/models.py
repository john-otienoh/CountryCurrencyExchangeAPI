from sqlalchemy import Column, Integer, String, Float, BigInteger, DateTime
from sqlalchemy.sql import func
from .database import Base

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    capital = Column(String(255))
    region = Column(String(255))
    population = Column(BigInteger, nullable=False)
    currency_code = Column(String(10))
    exchange_rate = Column(Float)
    estimated_gdp = Column(Float)
    flag_url = Column(String(512))
    last_refreshed_at = Column(DateTime, nullable=False, default=func.now())
