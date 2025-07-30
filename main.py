# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from handlers.start import router as start_router
from handlers.inline import router as inline_router
from handlers.reply import router as reply_router
from dotenv import load_dotenv
import os

from utils.tasks import user_tasks  # ← импортируем отдельно

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logging.critical("Токен бота не найден!")
    exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    logger.info("Запуск бота...")
    dp.include_routers(start_router, inline_router, reply_router)
    logger.info("Роутеры подключены.")

    try:
        logger.info("Бот начал опрос (polling)...")
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем.")
    finally:
        for task in user_tasks.values():
            if not task.done():
                task.cancel()
        logger.info("Фоновые задачи отменены.")
        await bot.session.close()

if __name__ == "__main__":
    logger.info("Приложение запущено.")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено (Ctrl+C).")