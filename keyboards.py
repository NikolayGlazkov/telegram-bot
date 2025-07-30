# keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def item_inline_keyboard(item_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Составить заявку", callback_data=f"request_{item_id}")],
        [InlineKeyboardButton(text="Отправить запрос", callback_data=f"send_request_{item_id}")],
        [InlineKeyboardButton(text="Добавить в избранное", callback_data=f"favorite_{item_id}")]
    ])

def main_reply_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Избранное"), KeyboardButton(text="Остановить")],
        [KeyboardButton(text="Старт")]
    ], resize_keyboard=True)

def stopped_keyboard():
    """Клавиатура после остановки"""
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Избранное")],
        [KeyboardButton(text="Старт")]
    ], resize_keyboard=True)