from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .database import Base

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    capital = Column(String(100))
    region = Column(String(100))
    population = Column(Integer, nullable=False)
    currency_code = Column(String(10))
    exchange_rate = Column(Float)
    estimated_gdp = Column(Float)
    flag_url = Column(String(255))
    last_refreshed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

