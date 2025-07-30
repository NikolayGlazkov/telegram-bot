# database/test_db.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import engine, Base
from database.config import setting

if __name__ == "__main__":
    print("Database URL:", setting.get_db_url())
    print("Engine created:", engine)
    print("Base created:", Base)