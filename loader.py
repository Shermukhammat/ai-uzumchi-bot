from aiogram import Bot, Dispatcher
from db.main import DataBase
from config import DB_URL, BOT_TOKEN

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
db = DataBase(db_url=DB_URL)
