from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, DateTime, func, Boolean, Integer
from db.base import Base
from datetime import datetime


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(255))
    request_join: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )