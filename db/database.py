from sqlalchemy import MetaData, create_engine
from databases import Database
from sqlalchemy import engine as sqla_engine
from config import DATABASE_URL


metadata = MetaData()

engine = create_engine(DATABASE_URL)

database = Database(DATABASE_URL)
