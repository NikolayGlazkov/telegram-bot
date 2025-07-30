# /Users/nikolai/Documents/telegram-bot/database/db.py
import aiomysql
from database.config import setting
from sqlalchemy import func
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession

 

engine = create_async_engine(url=setting.get_db_url(), echo=True) #echo=True
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())



# async def get_db_connection():
#     return await aiomysql.connect(
#         host=setting.DB_HOST,
#         port=setting.DB_PORT,
#         user=setting.DB_USER,
#         password=setting.DB_PASSWORD,
#         db=setting.DB_NAME,
#         autocommit=True
#     )
