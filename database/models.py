from sqlalchemy import (
    Column, String, BigInteger, ForeignKey, Text, Numeric,
    DateTime, Date, Boolean, Enum, Integer, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database.base import Base


class ArbitrationManager(Base):
    __tablename__ = 'arbitration_managers'

    id = Column(BigInteger, primary_key=True)
    full_name = Column(String(255), nullable=True)
    inn = Column(String(12), unique=True, nullable=True)
    snils = Column(String(14), nullable=True)
    sro_id = Column(BigInteger, ForeignKey('sros.id'), nullable=True)

    contacts = relationship(
        "ArbitrationManagerContact",
        back_populates="manager",
        cascade="all, delete-orphan"
    )

    sro = relationship("SRO", back_populates="managers")
    trades = relationship("DirectTrades", back_populates="arbitrator")

    def __repr__(self):
        return f"<ArbitrationManager ID={self.id}, ФИО='{self.full_name}'>"


class ArbitrationManagerContact(Base):
    __tablename__ = 'arbitration_manager_contacts'

    id = Column(BigInteger, primary_key=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)

    manager_id = Column(BigInteger, ForeignKey('arbitration_managers.id'), nullable=False)
    manager = relationship("ArbitrationManager", back_populates="contacts")

    def __repr__(self):
        return f"<Contact ID={self.id}, Email='{self.email}'>"


class SRO(Base):
    __tablename__ = 'sros'

    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False)
    inn = Column(String(12), unique=True, nullable=True)
    ogrn = Column(String(15), unique=True, nullable=True)
    address = Column(String(255), nullable=True)

    managers = relationship("ArbitrationManager", back_populates="sro")

    def __repr__(self):
        return f"<SRO ID={self.id}, Name='{self.name}'>"


class DirectTrades(Base):
    __tablename__ = 'direct_trades'

    id = Column(BigInteger, primary_key=True)
    publication_date = Column(Date)
    message_id = Column(String(255), index=True)
    url = Column(String(255))
    type_ = Column(Boolean)
    # is_sent = Column(Boolean)
    debtor_name = Column(String(255), nullable=True)
    debtor_inn = Column(String(50), nullable=True)
    message_number = Column(String(10), nullable=True)
    case_no = Column(String(150), nullable=True)
    debtor_phone = Column(String(20), nullable=True)
    auction_type = Column(String(255))
    place_of_conduct = Column(String(255))
    start_applications = Column(DateTime, nullable=True)
    end_applications = Column(DateTime, nullable=True)

    arbitrator_id = Column(BigInteger, ForeignKey('arbitration_managers.id'), nullable=True)
    arbitrator = relationship(
        "ArbitrationManager",
        back_populates="trades",
        lazy="joined"
    )

    lots = relationship("Lot", back_populates="trade")

    def __repr__(self):
        return (
            f"<Trade ID={self.id}, URL='{self.url}', "
            f"Должник: {self.debtor_name}, Отправлено: {self.is_sent}, "
            f"АУ: {self.arbitrator.full_name if self.arbitrator else 'нет'}>"
        )


class Lot(Base):
    __tablename__ = 'lots'
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True)
    trade_id = Column(BigInteger, ForeignKey('direct_trades.id'), nullable=False)
    description = Column(Text)
    lot_number = Column(Integer)
    price = Column(Numeric(10, 2))

    trade = relationship("DirectTrades", back_populates="lots")

    def __repr__(self):
        return f"<Lot ID={self.id}, Trade ID={self.trade_id}, Price={self.price}>"


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True)  # Telegram ID
    username = Column(String(50), nullable=True)
    is_subscribed = Column(Boolean, default=True)
    subscribed_at = Column(DateTime, default=datetime.utcnow)

    actions = relationship("UserAction", back_populates="user")

    def __repr__(self):
        return f"<User ID={self.id}, Username='{self.username}'>"


class UserAction(Base):
    __tablename__ = 'user_actions'
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    trade_id = Column(BigInteger, ForeignKey('direct_trades.id'), nullable=False)
    action_type = Column(Enum('favorite', 'task', name='action_types'))
    is_done = Column(Boolean, default=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="actions")
    trade = relationship("DirectTrades")

    def __repr__(self):
        return f"<UserAction ID={self.id}, Type={self.action_type}, Done={self.is_done}>"


# class Task(Base):
#     __tablename__ = 'tasks'
#     __table_args__ = {'extend_existing': True}

#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer)
#     trade_id = Column(BigInteger, ForeignKey('direct_trades.id'))
#     name = Column(String(255))
#     deadline = Column(Date)
#     is_completed = Column(Boolean, default=False)

#     def __repr__(self):
#         return f"<Task ID={self.id}, Name='{self.name}', Completed={self.is_completed}>"

class UserViewedTrade(Base):
    __tablename__ = 'user_viewed_trades'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    trade_id = Column(Integer, ForeignKey('direct_trades.id'), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint('user_id', 'trade_id', name='_user_trade_uc'),)

class RequestLog(Base):
    __tablename__ = 'request_logs'

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey('direct_trades.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)

    # Связи (опционально)
    user = relationship("User", backref="request_logs")
    trade = relationship("DirectTrades", backref="request_logs")

    def __repr__(self):
        return f"<RequestLog(user_id={self.user_id}, trade_id={self.trade_id}, sent_at={self.sent_at})>"
    

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    trade_id = Column(BigInteger, ForeignKey('direct_trades.id'), nullable=False)
    name = Column(String(255))
    description = Column(Text)  # Для заметки
    deadline = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    trade = relationship("DirectTrades", backref="tasks")

    def __repr__(self):
        return f"<Task ID={self.id}, Name='{self.name}', Deadline={self.deadline}, Completed={self.is_completed}>"