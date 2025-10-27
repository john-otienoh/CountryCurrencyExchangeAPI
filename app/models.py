# app/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.dialects.mysql import VARCHAR
from app.database import Base

class Country(Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(VARCHAR(255), unique=True, nullable=False)
    capital = Column(VARCHAR(255), nullable=True)
    region = Column(VARCHAR(100), nullable=True)
    population = Column(Integer, nullable=False)
    currency_code = Column(VARCHAR(10), nullable=True)
    exchange_rate = Column(Float, nullable=True)
    estimated_gdp = Column(Float, nullable=True)
    flag_url = Column(VARCHAR(512), nullable=True)
    last_refreshed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
