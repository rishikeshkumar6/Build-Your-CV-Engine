from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker, declarative_base
from config import Database_Url
from sqlalchemy.exc import SQLAlchemyError

# Replace with your actual credentials

engine = create_engine(Database_Url)
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Connected to database successfully")
except SQLAlchemyError as e:
    print("❌ Failed to connect to the database")
    print(e)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()
