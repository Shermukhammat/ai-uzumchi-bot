from loader import dp, bot, db
from utils.command import set_default_commands
import middlewares, handlers, logging, asyncio

logging.basicConfig(level=logging.INFO)

async def main():
    db.bot = await bot.get_me()
    dp['db'] = db
    await set_default_commands(bot)
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    asyncio.run(main())