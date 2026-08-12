from db.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence
from datetime import datetime
from sqlalchemy import update


class UserRepository:
    async def get(self, session: AsyncSession, id: int) -> User | None:
        result = await session.execute(select(User).where(User.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, session: AsyncSession) -> Sequence[User]:
        result = await session.execute(select(User))
        return result.scalars().all()

    async def get_admins(self, session: AsyncSession) -> Sequence[User]:
        result = await session.execute(select(User).where(User.is_admin == True))
        return result.scalars().all()

    async def create(
        self,
        session: AsyncSession,
        id: int,
        first_name: str,
        username: str | None = None,
        last_name: str | None = None,
    ) -> User:
        user = User(
            id=id,
            first_name=first_name,
            username=username,
            last_name=last_name,
        )
        session.add(user)
        await session.commit()
        return user

    async def delete(self, session: AsyncSession, id: int) -> None:
        user = await self.get(session, id)
        if user:
            await session.delete(user)
            await session.commit()

    async def update(self, session: AsyncSession, user: User) -> User:
        session.add(user)
        await session.commit()
        return user

    async def update_last_used(self, session: AsyncSession, id: int) -> None:
        await session.execute(update(User).where(User.id == id).values(last_used_at=datetime.now()))
        await session.commit()
