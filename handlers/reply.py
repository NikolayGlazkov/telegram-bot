# handlers/reply.py
from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "Избранное")
async def favorites(message: Message):
    await message.answer("Ваши избранные записи...")

@router.message(F.text == "Остановить")
async def stop(message: Message):
    await message.answer("Остановлено.")

@router.message(F.text == "Старт")
async def start_again(message: Message):
    await message.answer("Продолжаем отправку данных...")