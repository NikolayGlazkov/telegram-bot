# utils/email_sender.py
import smtplib
import logging
from email.mime.text import MIMEText
from email.header import Header
from dotenv import dotenv_values

config = dotenv_values(".env")
logger = logging.getLogger(__name__)

def generate_email_text(trade_data: dict) -> str:
    manager_name = trade_data.get('arbitrator_name')
    if manager_name and '(' in manager_name:
        manager_name = manager_name.split('(')[0].strip()
    if not manager_name:
        manager_name = trade_data.get('debtor_name', 'Уважаемый(ая) коллега')

    # Исправлено: если None — подставляем "не указано"
    message_number = trade_data.get("message_number", "не указано")
    if message_number is None:
        message_number = "не указано"

    debtor_name = trade_data.get("debtor_name", "не указано")
    if debtor_name is None:
        debtor_name = "не указано"

    debtor_inn = trade_data.get("debtor_inn", "не указано")
    if debtor_inn is None:
        debtor_inn = "не указано"

    lots_text = ""
    if trade_data.get('lots'):
        for lot in trade_data['lots']:
            lot_number = lot.get('lot_number', '–')
            description = lot.get('description', 'Без описания')
            price_value = lot.get('price')

            try:
                price = f"{float(price_value):,.0f}".replace(",", " ") if price_value else "0"
            except (TypeError, ValueError):
                price = "уточняется"

            lots_text += f"{lot_number}. {description} — {price} руб.\n"
    else:
        lots_text = "Лоты не указаны."

    return f"""Здравствуйте уважаемый(ая) {manager_name},

Прошу вас предоставить мне информацию по лотам, опубликованным на сайте ЕФРСБ.
№ сообщения: {message_number}
Должник: {debtor_name}
ИНН: {debtor_inn}

А именно:

{lots_text.strip()}

- Номер контактного телефона для осмотра имущества.
- Сканы документов имущества.
- Фото имущества.
- Место нахождения имущества.

С уважением,
Глазков Николай Александрович
Телефон: 8 937 741-95-82
Дополнительная почта: vanohaker@yandex.ru
"""



async def send_request_email(trade_data: dict, user_id: int = None) -> bool:
    sender = "gn9377419582@gmail.com"
    password = config.get("EMAIL_PASSWORD")
    recipient_emails = trade_data.get("emails")

    if not recipient_emails:
        logger.warning(f"Нет email для отправки по сделке {trade_data['id']}")
        return False

    # Парсим все email
    recipients = [email.strip() for email in recipient_emails.split(",") if "@" in email]
    if not recipients:
        logger.warning(f"Некорректные email: {recipient_emails}")
        return False

    try:
        msg_text = generate_email_text(trade_data)
        msg = MIMEText(msg_text, "plain", "utf-8")
        msg["Subject"] = Header(f"Запрос по лотам должника {trade_data.get('debtor_name', 'Неизвестный')}", "utf-8")
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)  # Все email в поле To

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
            logger.info(f"📧 Письмо отправлено на: {recipients}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("❌ Ошибка аутентификации SMTP. Проверьте логин/пароль.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"❌ SMTP ошибка: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке письма: {e}", exc_info=True)
        return False