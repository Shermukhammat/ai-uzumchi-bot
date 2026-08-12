from loader import dp, bot, db
import middlewares, handlers, logging, asyncio

logging.basicConfig(level=logging.INFO)

async def main():
    db.bot = await bot.get_me()
    dp['db'] = db
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    asyncio.run(main())