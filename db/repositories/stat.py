from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from dataclasses import dataclass
from db.models.user import User

@dataclass
class StatDTO:
    total_users: int
    new_today: int
    new_this_week: int
    new_this_month: int
    active_today: int
    active_this_week: int
    active_this_month: int
    active_users: int
    inactive_users: int

class StatRepository:
    async def get_users_stat(self, session: AsyncSession) -> StatDTO:
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today - timedelta(days=now.weekday())
        month_start = today.replace(day=1)

        total_users = await session.scalar(select(func.count(User.id)))

        new_today = await session.scalar(select(func.count(User.id)).where(User.registered_at >= today))
        new_this_week = await session.scalar(select(func.count(User.id)).where(User.registered_at >= week_start))
        new_this_month = await session.scalar(select(func.count(User.id)).where(User.registered_at >= month_start))

        active_today = await session.scalar(select(func.count(User.id)).where(User.last_used_at >= today))
        active_this_week = await session.scalar(select(func.count(User.id)).where(User.last_used_at >= week_start))
        active_this_month = await session.scalar(select(func.count(User.id)).where(User.last_used_at >= month_start))

        active_users = await session.scalar(select(func.count(User.id)).where(User.is_active == True))
        inactive_users = await session.scalar(select(func.count(User.id)).where(User.is_active == False))

        return StatDTO(
            total_users=total_users or 0,
            new_today=new_today or 0,
            new_this_week=new_this_week or 0,
            new_this_month=new_this_month or 0,
            active_today=active_today or 0,
            active_this_week=active_this_week or 0,
            active_this_month=active_this_month or 0,
            active_users=active_users or 0,
            inactive_users=inactive_users or 0
        )
