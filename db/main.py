from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from .repositories import UserRepository, ChannelRepository, StatRepository
from aiogram import types

class DataBase:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=False)
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)
        self.bot : types.User = None
        
        self.users = UserRepository()
        self.channels = ChannelRepository()
        self.stats = StatRepository()
