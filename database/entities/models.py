from sqlalchemy import BigInteger, DateTime, Boolean, String, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, timezone, UTC
from database.entities.core import Base
from bot.enums.status_enums import Status

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # ✅ Убираем `tzinfo`
    )

    clients = relationship("Client", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    supplyes = relationship("Supply", back_populates="user")

class Client(Base):
    __tablename__ = 'clients'
    __table_args__ = {"schema": "public"}

    client_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)  # ✅ Автоинкремент
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)  # ✅ Поиск по name
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('public.users.tg_id'), nullable=False)
    cookies: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="clients")
    supplyes = relationship("Supply", back_populates="client")


class Supply(Base):
    __tablename__ = 'supplyes'
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('public.users.tg_id'), nullable=False)
    client_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('public.clients.client_id'), nullable=False)
    status: Mapped[str] = mapped_column(Enum(Status), default=Status.RECEIVED)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=lambda: datetime.now(UTC), nullable=True)

    user = relationship("User", back_populates="supplyes")
    client = relationship("Client", back_populates="supplyes")

class Subscription(Base):
    __tablename__ = 'subscriptions'
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('public.users.tg_id'), nullable=False)
    tariff_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('public.tariffs.id'), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User", back_populates="subscriptions")
    tariff = relationship("Tariff")

class Tariff(Base):
    __tablename__ = 'tariffs'
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=True)  # Если null, то разовый отлов
    is_subscription: Mapped[bool] = mapped_column(Boolean, default=True)
