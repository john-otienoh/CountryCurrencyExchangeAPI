from sqlalchemy import Column, Integer, String, BigInteger, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    capital = Column(String(255), nullable=True)
    region = Column(String(100), nullable=True)
    population = Column(BigInteger, nullable=False)
    currency_code = Column(String(10), nullable=True, index=True)
    exchange_rate = Column(Float, nullable=True)
    estimated_gdp = Column(Float, nullable=True)
    flag_url = Column(String(500), nullable=True)
    last_refreshed_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<Country(name={self.name}, region={self.region}, currency={self.currency_code})>"
