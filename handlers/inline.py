# handlers/inline.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.dao import get_trade_by_id
from utils.email_sender import send_request_email
import logging

router = Router()
logger = logging.getLogger(__name__)  # ✅ Убедись, что используешь logger


@router.callback_query(F.data.startswith("request_"))
async def handle_request(callback: CallbackQuery):
    item_id = callback.data.split("_")[1]
    await callback.answer(f"Заявка для {item_id} составлена!", show_alert=True)


@router.callback_query(F.data.startswith("send_request_"))
async def handle_send_request(callback: CallbackQuery):
    try:
        trade_id = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id
        username = callback.from_user.username
        logger.info(f"Пользователь {user_id} (@{username}) запросил отправку письма для сделки {trade_id}")

        # Отправляем "часики"
        await callback.answer("📩 Формируем запрос...", show_alert=False)

        # Получаем данные сделки
        trade_data = await get_trade_by_id(trade_id)
        
        # ✅ Логируем корректно
        if trade_data:
            logger.info(f"Данные сделки {trade_id}: {list(trade_data.keys())}")
        else:
            logger.warning(f"Сделка {trade_id} не найдена в БД")
            await callback.message.answer("❌ Ошибка: сделка не найдена.")
            return

        # Отправляем письмо
        success = await send_request_email(trade_data)

        # Кнопки остаются
        remaining_buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Составить заявку", callback_data=f"request_{trade_id}")],
            [InlineKeyboardButton(text="⭐ Добавить в избранное", callback_data=f"favorite_{trade_id}")]
        ])

        if success:
            await callback.message.edit_text(
                f"{callback.message.html_text}\n\n"
                "✅ <b>Запрос отправлен!</b>\n"
                "Арбитражному управляющему направлено письмо.",
                parse_mode="HTML",
                reply_markup=remaining_buttons
            )
            logger.info(f"Запрос по сделке {trade_id} успешно отправлен")
        else:
            await callback.message.edit_text(
                f"{callback.message.html_text}\n\n"
                "❌ <b>Не удалось отправить запрос.</b>\n"
                "Попробуйте позже.",
                parse_mode="HTML",
                reply_markup=remaining_buttons
            )
            logger.warning(f"Не удалось отправить запрос по сделке {trade_id}")

    except Exception as e:
        logger.error(f"Ошибка при отправке запроса для сделки {trade_id}: {e}", exc_info=True)
        try:
            await callback.message.answer("❌ Произошла ошибка при отправке запроса.")
        except:
            pass


@router.callback_query(F.data.startswith("favorite_"))
async def handle_favorite(callback: CallbackQuery):
    item_id = callback.data.split("_")[1]
    await callback.answer(f"Добавлено в избранное: {item_id}", show_alert=True)