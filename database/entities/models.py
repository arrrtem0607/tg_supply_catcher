import uuid
from datetime import datetime

from sqlalchemy import (
    Integer, Text, BigInteger, DateTime, ForeignKey, func, Enum, ARRAY,
    TIMESTAMP, String, Boolean, PrimaryKeyConstraint, ForeignKeyConstraint,
    Table, Column,  UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from database.entities.core import Base
from database.enums.status_enums import Status
from database.enums.mailing_status_enums import MailingStatus

mailing_users = Table(
    "mailing_users",
    Base.metadata,
    Column("mailing_id", UUID(as_uuid=True), ForeignKey("public.mailings.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", BigInteger, ForeignKey("public.users.tg_id", ondelete="CASCADE"), primary_key=True),
    schema="public"
)

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    clients = relationship("Client", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    supplyes = relationship("Supply", back_populates="user", overlaps="client,supplyes")

    mailings = relationship(
        "Mailing",
        secondary=mailing_users,
        back_populates="recipients"
    )


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (
        PrimaryKeyConstraint("client_id", "user_id", name="pk_clients"),
        {"schema": "public"},
    )

    client_id: Mapped[str] = mapped_column(String(100), nullable=False)  # теперь это строка от WB
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("public.users.tg_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cookies: Mapped[str] = mapped_column(String, nullable=False)
    refresh_token: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="clients")
    supplyes = relationship("Supply", back_populates="client", overlaps="user,supplyes")


class Supply(Base):
    __tablename__ = "supplyes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["client_id", "user_id"],
            ["public.clients.client_id", "public.clients.user_id"],
        ),
        UniqueConstraint("preorder_id", "user_id", "supply_id", name="uq_supplyes_combination"),
        {"schema": "public"},
    )

    # Новый surrogate PK
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    preorder_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    supply_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.RECEIVED, nullable=False)

    client_id: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("public.users.tg_id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now(), server_onupdate=func.now(), nullable=True)
    api_created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    start_catch_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_catch_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    skip_dates: Mapped[list[datetime]] = mapped_column(ARRAY(DateTime), nullable=True)
    coefficient: Mapped[float] = mapped_column(Integer, nullable=True)

    warehouse_name: Mapped[str] = mapped_column(String(255), nullable=True)
    warehouse_address: Mapped[str] = mapped_column(String(255), nullable=True)
    box_type: Mapped[str] = mapped_column(String(50), nullable=True)

    price: Mapped[int] = mapped_column(Integer, nullable=True)

    user = relationship("User", back_populates="supplyes", overlaps="client,supplyes")
    client = relationship("Client", back_populates="supplyes", overlaps="user,supplyes")

    def to_dict(self):
        return {
            "id": self.id,
            "supply_id": self.supply_id,
            "preorder_id": self.preorder_id,
            "user_id": self.user_id,
            "client_id": str(self.client_id),
            "status": self.status.name if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "api_created_at": self.api_created_at.isoformat() if self.api_created_at else None,
            "start_catch_date": self.start_catch_date.isoformat() if self.start_catch_date else None,
            "end_catch_date": self.end_catch_date.isoformat() if self.end_catch_date else None,
            "skip_dates": [d.isoformat() for d in self.skip_dates] if self.skip_dates else [],
            "coefficient": float(self.coefficient) if self.coefficient is not None else None,
            "warehouse_name": self.warehouse_name,
            "warehouse_address": self.warehouse_address,
            "box_type": self.box_type,
            "price": self.price,
            "client_name": self.client.name if self.client else None,
            "user_name": self.user.username if self.user else None
        }


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("public.users.tg_id"), nullable=False)
    tariff_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("public.tariffs.id"), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User", back_populates="subscriptions")
    tariff = relationship("Tariff")


class Tariff(Base):
    __tablename__ = "tariffs"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=True)  # Если null, то разовый отлов
    is_subscription: Mapped[bool] = mapped_column(Boolean, default=True)

class ClientBalance(Base):
    __tablename__ = "client_balances"
    __table_args__ = {"schema": "public"}

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("public.users.tg_id"), primary_key=True)
    balance: Mapped[float] = mapped_column(BigInteger, default=0)

    user = relationship("User", backref="balance")

class Mailing(Base):
    __tablename__ = "mailings"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    status: Mapped[MailingStatus] = mapped_column(Enum(MailingStatus, name="mailing_status"), default=MailingStatus.SCHEDULED)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 👇 связь с пользователями
    recipients = relationship(
        "User",
        secondary=mailing_users,
        back_populates="mailings"
    )



