# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from handlers.start import router as start_router
from handlers.inline import router as inline_router
from handlers.reply import router as reply_router
from datetime import datetime
from dotenv import load_dotenv
import os

# Импортируем из utils
from utils.tasks import user_tasks

# Импортируем из database
from database.db import async_session
from database.models import Task

# Импортируем из sqlalchemy
from sqlalchemy import select

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logging.critical("Токен бота не найден!")
    exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def check_tasks(bot: Bot):
    """Фоновая задача: проверяет и отправляет напоминания по задачам"""
    while True:
        try:
            now = datetime.now()
            async with async_session() as session:
                # Получаем просроченные задачи
                stmt = select(Task).where(Task.deadline <= now, Task.is_completed == False)
                result = await session.execute(stmt)
                tasks = result.scalars().all()

                for task in tasks:
                    try:
                        # Формируем сообщение
                        debtor_name = task.trade.debtor_name if task.trade else "Неизвестно"
                        text = (
                            f"⏰ <b>Напоминание!</b>\n\n"
                            f"Задача: {task.name}\n"
                            f"Сделка: {debtor_name}\n\n"
                            f"{task.description or 'Без описания'}"
                        )
                        await bot.send_message(task.user_id, text, parse_mode="HTML")
                        
                        # Помечаем как выполненную
                        task.is_completed = True
                        await session.commit()
                        logger.info(f"Напоминание отправлено пользователю {task.user_id} для задачи {task.id}")
                    except Exception as e:
                        logger.error(f"Ошибка отправки напоминания для задачи {task.id}: {e}", exc_info=True)
                        await session.rollback()
        except Exception as e:
            logger.error(f"Ошибка в фоновой проверке задач: {e}", exc_info=True)

        await asyncio.sleep(60)  # Проверяем каждую минуту


async def main():
    logger.info("Запуск бота...")
    dp.include_routers(start_router, inline_router, reply_router)
    logger.info("Роутеры подключены.")

    # Запускаем фоновую проверку задач
    task_checker = asyncio.create_task(check_tasks(bot))
    logger.info("Фоновая проверка задач запущена")

    try:
        logger.info("Бот начал опрос (polling)...")
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем.")
    finally:
        # Отменяем все фоновые задачи
        for task in user_tasks.values():
            if not task.done():
                task.cancel()
        if not task_checker.done():
            task_checker.cancel()
        logger.info("Фоновые задачи отменены.")

        # Закрываем сессию бота
        await bot.session.close()
        logger.info("Сессия бота закрыта.")


if __name__ == "__main__":
    logger.info("Приложение запущено.")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено (Ctrl+C).")