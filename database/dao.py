# database/dao.py

from sqlalchemy import select, func, UniqueConstraint
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any, Optional
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
from .db import async_session
from .models import (
    User,
    DirectTrades,
    ArbitrationManager,
    ArbitrationManagerContact,
    Lot,
    UserAction,
    RequestLog,
    UserViewedTrade,
    Task,
)

# Настройка логгирования
logger = logging.getLogger(__name__)


async def set_user(tg_id: int, username: str, full_name: str) -> Optional[User]:
    """
    Находит пользователя по tg_id или создаёт нового.
    """
    async with async_session() as session:
        try:
            logger.debug(f"Поиск/создание пользователя с ID {tg_id}")
            result = await session.execute(select(User).filter_by(id=tg_id))
            user = result.scalar_one_or_none()

            if not user:
                new_user = User(id=tg_id, username=username, full_name=full_name)
                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)
                logger.info(f"Зарегистрирован новый пользователь с ID {tg_id}")
                return new_user
            else:
                logger.info(f"Пользователь с ID {tg_id} уже существует")
                return user
        except SQLAlchemyError as e:
            logger.error(f"Ошибка SQLAlchemy при работе с пользователем {tg_id}: {e}", exc_info=True)
            await session.rollback()
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при работе с пользователем {tg_id}: {e}", exc_info=True)
            await session.rollback()
            return None


async def get_new_direct_trades_for_user(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Возвращает новые прямые сделки, которые пользователь ещё не видел.
    """
    async with async_session() as session:
        try:
            # Получаем ID сделок, которые пользователь уже видел
            viewed_stmt = select(UserViewedTrade.trade_id).where(UserViewedTrade.user_id == user_id)
            result = await session.execute(viewed_stmt)
            viewed_ids = set(result.scalars().all())  # Работает даже с пустым результатом

            # Получаем сделки, исключая уже просмотренные
            stmt = (
                select(DirectTrades)
                .options(
                    selectinload(DirectTrades.arbitrator).selectinload(ArbitrationManager.contacts),
                    selectinload(DirectTrades.lots)
                )
                .where(
                    DirectTrades.type_ == True,
                    DirectTrades.id.not_in(viewed_ids)  # Теперь всегда работает, даже если viewed_ids пуст
                )
                .order_by(DirectTrades.publication_date.desc())  # Самые свежие — вперед
                .limit(limit)
            )
            result = await session.execute(stmt)
            trades = result.scalars().all()

            # Преобразуем сделки в словари
            trades_data = []
            for trade in trades:
                # Собираем email'ы
                emails = []
                if trade.arbitrator and trade.arbitrator.contacts:
                    emails = [c.email for c in trade.arbitrator.contacts if c.email]

                # Собираем лоты
                lots_data = []
                if trade.lots:
                    for lot in trade.lots:
                        lots_data.append({
                            'lot_number': lot.lot_number,
                            'description': lot.description or '',
                            'price': float(lot.price) if lot.price else 0.0
                        })

                # Формируем данные сделки
                trade_data = {
                    'id': trade.id,
                    'message_number': trade.message_number,
                    'publication_date': trade.publication_date,
                    'url': trade.url,
                    'debtor_name': trade.debtor_name,
                    'debtor_inn': trade.debtor_inn,
                    'auction_type': trade.auction_type,
                    'place_of_conduct': trade.place_of_conduct,
                    'start_applications': trade.start_applications,
                    'end_applications': trade.end_applications,
                    'arbitrator_name': trade.arbitrator.full_name if trade.arbitrator else None,
                    'arbitrator_inn': trade.arbitrator.inn if trade.arbitrator else None,
                    'emails': ', '.join(emails) if emails else None,
                    'lots': lots_data
                }
                trades_data.append(trade_data)

            logger.info(f"Найдено {len(trades_data)} новых сделок для пользователя {user_id}")
            return trades_data

        except Exception as e:
            logger.error(f"Ошибка при получении новых сделок для пользователя {user_id}: {e}", exc_info=True)
            return []


async def mark_trade_as_viewed(user_id: int, trade_id: int):
    """
    Помечает сделку как просмотренную пользователем.
    """
    async with async_session() as session:
        try:
            # Проверяем, не помечал ли пользователь уже эту сделку
            stmt = select(UserViewedTrade).where(
                UserViewedTrade.user_id == user_id,
                UserViewedTrade.trade_id == trade_id
            )
            result = await session.execute(stmt)
            exists = result.scalar_one_or_none()

            if exists:
                logger.debug(f"Пользователь {user_id} уже видел сделку {trade_id}")
                return

            # Добавляем запись
            viewed = UserViewedTrade(user_id=user_id, trade_id=trade_id)
            session.add(viewed)
            await session.commit()
            logger.info(f"Пользователь {user_id} успешно пометил сделку {trade_id} как просмотренную")
        except Exception as e:
            logger.error(f"Ошибка при пометке сделки {trade_id} как просмотренной: {e}", exc_info=True)
            await session.rollback()


async def get_trade_by_id(trade_id: int) -> Optional[Dict[str, Any]]:
    """
    Получает данные одной сделки по ID (включая арбитра и лоты)
    """
    async with async_session() as session:
        try:
            stmt = (
                select(DirectTrades)
                .options(
                    selectinload(DirectTrades.arbitrator).selectinload(ArbitrationManager.contacts),
                    selectinload(DirectTrades.lots)
                )
                .where(DirectTrades.id == trade_id)
            )
            result = await session.execute(stmt)
            trade = result.scalar_one_or_none()

            if not trade:
                return None

            # Собираем email'ы
            emails = []
            if trade.arbitrator and trade.arbitrator.contacts:
                emails = [c.email for c in trade.arbitrator.contacts if c.email]

            # Собираем лоты
            lots_data = []
            if trade.lots:
                for lot in trade.lots:
                    lots_data.append({
                        'lot_number': lot.lot_number,
                        'description': lot.description or '',
                        'price': float(lot.price) if lot.price else 0.0
                    })

            return {
                'id': trade.id,
                'message_number': trade.message_number,
                'publication_date': trade.publication_date,
                'url': trade.url,
                'debtor_name': trade.debtor_name,
                'debtor_inn': trade.debtor_inn,
                'auction_type': trade.auction_type,
                'place_of_conduct': trade.place_of_conduct,
                'start_applications': trade.start_applications,
                'end_applications': trade.end_applications,
                'arbitrator_name': trade.arbitrator.full_name if trade.arbitrator else None,
                'arbitrator_inn': trade.arbitrator.inn if trade.arbitrator else None,
                'emails': ', '.join(emails) if emails else None,
                'lots': lots_data
            }
        except Exception as e:
            logger.error(f"Ошибка при получении сделки {trade_id}: {e}", exc_info=True)
            return None


async def log_request_sent(trade_id: int, user_id: int) -> bool:
    """
    Логирует факт отправки запроса по сделке
    """
    async with async_session() as session:
        try:
            log = RequestLog(trade_id=trade_id, user_id=user_id)
            session.add(log)
            await session.commit()
            logger.info(f"Запрос по сделке {trade_id} от пользователя {user_id} записан в лог")
            return True
        except Exception as e:
            logger.error(f"Ошибка при записи лога запроса: {e}", exc_info=True)
            await session.rollback()
            return False


async def get_request_logs(trade_id: int) -> List[Dict[str, Any]]:
    """
    Возвращает историю запросов по сделке
    """
    async with async_session() as session:
        try:
            stmt = (
                select(RequestLog)
                .where(RequestLog.trade_id == trade_id)
                .order_by(RequestLog.sent_at.desc())
            )
            result = await session.execute(stmt)
            logs = result.scalars().all()

            return [
                {
                    'user_id': log.user_id,
                    'sent_at': log.sent_at
                }
                for log in logs
            ]
        except Exception as e:
            logger.error(f"Ошибка при получении логов запросов для сделки {trade_id}: {e}", exc_info=True)
            return []
        
# database/dao.py

async def add_to_favorites(user_id: int, trade_id: int) -> bool:
    """Добавляет сделку в избранное"""
    async with async_session() as session:
        try:
            # Проверим, нет ли уже
            stmt = select(UserAction).where(
                UserAction.user_id == user_id,
                UserAction.trade_id == trade_id,
                UserAction.action_type == 'favorite'
            )
            result = await session.execute(stmt)
            exists = result.scalar_one_or_none()

            if exists:
                return True  # Уже в избранном

            action = UserAction(
                user_id=user_id,
                trade_id=trade_id,
                action_type='favorite'
            )
            session.add(action)
            await session.commit()
            logger.info(f"Пользователь {user_id} добавил сделку {trade_id} в избранное")
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении в избранное: {e}", exc_info=True)
            await session.rollback()
            return False


async def create_task(user_id: int, trade_id: int, name: str, description: str, deadline: datetime) -> bool:
    """Создаёт задачу с напоминанием"""
    async with async_session() as session:
        try:
            task = Task(
                user_id=user_id,
                trade_id=trade_id,
                name=name,
                description=description,
                deadline=deadline
            )
            session.add(task)
            await session.commit()
            logger.info(f"Пользователь {user_id} создал задачу '{name}' на {deadline} для сделки {trade_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании задачи: {e}", exc_info=True)
            await session.rollback()
            return False


async def get_user_tasks(user_id: int) -> List[Dict[str, Any]]:
    """Получает все задачи пользователя"""
    async with async_session() as session:
        try:
            stmt = (
                select(Task)
                .options(selectinload(Task.trade))
                .where(Task.user_id == user_id, Task.is_completed == False)
                .order_by(Task.deadline)
            )
            result = await session.execute(stmt)
            tasks = result.scalars().all()

            return [
                {
                    'id': t.id,
                    'name': t.name,
                    'description': t.description,
                    'deadline': t.deadline,
                    'trade_id': t.trade_id,
                    'debtor_name': t.trade.debtor_name if t.trade else 'Неизвестно'
                }
                for t in tasks
            ]
        except Exception as e:
            logger.error(f"Ошибка при получении задач: {e}", exc_info=True)
            return []