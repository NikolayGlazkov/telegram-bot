
import os
from dotenv import load_dotenv

load_dotenv()

class Setting_:
    def __init__(self):
        self.DB_USER = os.environ.get("DB_USER")
        self.DB_PASSWORD = os.environ.get("DB_PASSWORD")
        self.DB_HOST = os.environ.get("DB_HOST")
        self.DB_PORT = int(os.environ.get("DB_PORT"))
        self.DB_NAME = os.environ.get("DB_NAME")

    def get_db_url(self):
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

# Создаем экземпляр
setting = Setting_()

# print(setting.get_db_url())