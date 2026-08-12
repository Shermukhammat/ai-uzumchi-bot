from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence
from db.models.channel import Channel


class ChannelRepository:
    async def get(self, session: AsyncSession, id: int) -> Channel | None:
        result = await session.execute(select(Channel).where(Channel.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, session: AsyncSession) -> Sequence[Channel]:
        result = await session.execute(select(Channel))
        return result.scalars().all()

    async def add(self, session: AsyncSession, id: int, title: str, url: str, request_join: bool = False) -> Channel:
        channel = Channel(id=id, title=title, url=url, request_join=request_join)
        session.add(channel)
        await session.commit()
        return channel

    async def delete(self, session: AsyncSession, id: int) -> bool:
        channel = await self.get(session, id)
        if channel:
            await session.delete(channel)
            await session.commit()
            return True
        return False
