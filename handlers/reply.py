# handlers/reply.py
from aiogram import Router, F
from aiogram.types import Message
from utils.tasks import user_tasks
from keyboards import stopped_keyboard, main_reply_keyboard  # ✅ Исправлено
import logging
import asyncio

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "Избранное")
async def favorites(message: Message):
    await message.answer("Ваши избранные записи...")


@router.message(F.text == "Остановить")
async def stop_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    logger.info(f"Пользователь {user_id} (@{username}) нажал 'Остановить'")

    if user_id in user_tasks:
        task = user_tasks[user_id]
        if not task.done():
            task.cancel()
            logger.info(f"Фоновая задача для пользователя {user_id} отменена")
        del user_tasks[user_id]
    else:
        logger.info(f"Пользователь {user_id} нажал 'Остановить', но задача не найдена")

    await message.answer(
        "🛑 Рассылка остановлена.\n\nЧтобы возобновить — нажмите 'Старт'.",
        reply_markup=stopped_keyboard()
    )


@router.message(F.text == "Старт")
async def start_again(message: Message):
    """
    Обработка кнопки 'Старт' после остановки
    Повторно запускает фоновую задачу
    """
    user_id = message.from_user.id
    username = message.from_user.username
    logger.info(f"Пользователь {user_id} (@{username}) нажал 'Старт' после остановки")

    # Отменяем старую задачу, если есть
    if user_id in user_tasks:
        old_task = user_tasks[user_id]
        if not old_task.done():
            old_task.cancel()
        del user_tasks[user_id]
        logger.info(f"Старая задача для {user_id} отменена")

    # Запускаем новую фоновую задачу
    from handlers.start import send_trades_to_user  # ✅ Ленивый импорт, чтобы избежать цикла
    task = asyncio.create_task(send_trades_to_user(message.bot, user_id))
    user_tasks[user_id] = task
    logger.info(f"Запущена фоновая задача для пользователя {user_id}")

    await message.answer(
        "✅ Рассылка возобновлена!\n\nТеперь вы будете получать новые сделки.",
        reply_markup=main_reply_keyboard()
    )