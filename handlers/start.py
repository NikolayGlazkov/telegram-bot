# handlers/start.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from database.dao import get_new_direct_trades_for_user, mark_trade_as_viewed
from keyboards import main_reply_keyboard, item_inline_keyboard
from utils.tasks import user_tasks  # ← импортируем user_tasks сюда
import asyncio
import logging

router = Router()

logger = logging.getLogger(__name__)

def format_trade_message(trade_data: dict) -> str:
    """
    Форматирует данные сделки в красивое HTML-сообщение для Telegram.
    """
    msg_parts = ["📢 <b>НОВАЯ ПРЯМАЯ СДЕЛКА !!!!!!------!!!!!!</b>\n"]

    # Ссылка
    if trade_data.get('url'):
        msg_parts.append(f"\n🔗 Ссылка: {trade_data['url']}\n")

    # Номер сообщения
    if trade_data.get('message_number'):
        msg_parts.append(f"#⃣ Номер сообщения: {trade_data['message_number']}")

    # Дата публикации
    pub_date = trade_data.get('publication_date')
    if pub_date:
        if hasattr(pub_date, 'strftime'):
            formatted_date = pub_date.strftime('%d.%m.%Y')
        else:
            formatted_date = str(pub_date)
        msg_parts.append(f"📅 Дата публикации: {formatted_date}")

    # Должник
    if trade_data.get('debtor_name'):
        msg_parts.append(f"👤 Должник: {trade_data['debtor_name']}")
    if trade_data.get('debtor_inn'):
        msg_parts.append(f"🔢 ИНН должника: {trade_data['debtor_inn']}")

    # Вид торгов и место проведения
    if trade_data.get('auction_type'):
        msg_parts.append(f"⚖️ Вид торгов: {trade_data['auction_type']}")
    if trade_data.get('place_of_conduct'):
        msg_parts.append(f"📍 Место проведения: {trade_data['place_of_conduct']}")

    # Время подачи заявок
    start_apps = trade_data.get('start_applications')
    if start_apps:
        if hasattr(start_apps, 'strftime'):
            formatted_time = start_apps.strftime('%d.%m.%Y %H:%M')
        else:
            formatted_time = str(start_apps)
        msg_parts.append(f"⏳ Начало заявок: {formatted_time}")

    end_apps = trade_data.get('end_applications')
    if end_apps:
        if hasattr(end_apps, 'strftime'):
            formatted_time = end_apps.strftime('%d.%m.%Y %H:%M')
        else:
            formatted_time = str(end_apps)
        msg_parts.append(f"⌛ Конец заявок: {formatted_time}")

    # Арбитражный управляющий
    if trade_data.get('arbitrator_name'):
        msg_parts.append(f"🧑‍⚖️ Арбитр: {trade_data['arbitrator_name']}")
    if trade_data.get('arbitrator_inn'):
        msg_parts.append(f"🔢 ИНН арбитра: {trade_data['arbitrator_inn']}")
    if trade_data.get('emails'):
        msg_parts.append(f"📧 Email: {trade_data['emails']}")

    # Лоты
    lots = trade_data.get('lots', [])
    if lots:
        msg_parts.append("\n📦 <b>ЛОТЫ:</b>\n")
        for lot in lots:
            lot_number = lot.get('lot_number', '–')
            description = lot.get('description', 'Без описания')
            price_value = lot.get('price')

            # Обработка цены
            try:
                price_float = float(price_value) if price_value not in (None, '') else 0.0
                price_str = f"{price_float:,.0f}".replace(",", " ")
            except (ValueError, TypeError):
                price_str = "0"

            msg_parts.append(f"{lot_number}. {description} — <b>{price_str} руб.</b>")

    return "\n".join(msg_parts)



async def send_trades_to_user(bot, user_id):
    iteration_count = 0
    while True:
        iteration_count += 1
        try:
            logger.info(f"[Пользователь {user_id}] Итерация #{iteration_count}: Проверяю новые сделки...")
            
            # Получаем только те сделки, которые пользователь ещё не видел
            trades = await get_new_direct_trades_for_user(user_id, limit=5)
            logger.info(f"[Пользователь {user_id}] Получено {len(trades)} новых сделок")

            if not trades:
                logger.info(f"[Пользователь {user_id}] Новых сделок нет")
            else:
                for trade in trades:
                    try:
                        msg_text = format_trade_message(trade)
                        sent_message = await bot.send_message(
                            chat_id=user_id,
                            text=msg_text,
                            parse_mode="HTML",
                            reply_markup=item_inline_keyboard(trade['id'])
                        )
                        logger.info(f"[Пользователь {user_id}] Отправлена сделка {trade['id']} (message_id: {sent_message.message_id})")

                        # Помечаем, что пользователь увидел сделку
                        await mark_trade_as_viewed(user_id, trade['id'])

                    except Exception as send_error:
                        logger.error(f"[Пользователь {user_id}] Ошибка отправки сделки {trade['id']}: {send_error}", exc_info=True)

        except Exception as e:
            logger.error(f"[Пользователь {user_id}] Ошибка в фоновой задаче: {e}", exc_info=True)

        await asyncio.sleep(20)


@router.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    logger.info(f"Пользователь {user_id} ({username}) отправил /start")

    await message.answer(
        "Привет! Начинаю отправлять данные о прямых сделках...",
        reply_markup=main_reply_keyboard()
    )

    # Отмена предыдущей задачи
    if user_id in user_tasks:
        old_task = user_tasks[user_id]
        if not old_task.done():
            old_task.cancel()
        del user_tasks[user_id]
        logger.info(f"Предыдущая задача для {user_id} отменена")

    # Запуск новой задачи
    task = asyncio.create_task(send_trades_to_user(message.bot, user_id))
    user_tasks[user_id] = task
    logger.info(f"Запущена фоновая задача для пользователя {user_id}")