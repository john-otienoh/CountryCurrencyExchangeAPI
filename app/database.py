# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Get DATABASE_URL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in environment")

# ✅ Ensure correct SQLAlchemy scheme for MySQL
# Railway usually gives: mysql://user:pass@host:3306/db
# SQLAlchemy requires: mysql+pymysql://user:pass@host:3306/db
if SQLALCHEMY_DATABASE_URL.startswith("mysql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

# ✅ Create engine with pool pre-ping
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# ✅ Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Base model
Base = declarative_base()

# ✅ FastAPI dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Optional: Print connection source for clarity
print(
    f"✅ Connected to: {'Railway MySQL' if 'railway.internal' in SQLALCHEMY_DATABASE_URL else 'Local MySQL'}"
)
