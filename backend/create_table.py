
import sys
import os
from sqlalchemy import create_engine
from app.models.custom_quiz import CustomQuizRecord
from app.core.config import settings
from app.core.database import Base

def create_table():
    print(f"Connecting to database: {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    
    print("Creating tables...")
    CustomQuizRecord.__table__.create(engine)
    print("Table custom_quiz_records created successfully.")

if __name__ == "__main__":
    # Add parent directory to path to allow importing app modules
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    create_table()
