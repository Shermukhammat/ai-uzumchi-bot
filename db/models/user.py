from sqlalchemy import BigInteger, String, DateTime, Boolean, func 
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True, server_default=None)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True, server_default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')

    registered_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now(), nullable=False, server_default=func.now())
    last_used_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now(), nullable=False, server_default=func.now())
