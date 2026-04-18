import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
import config
from handlers import router

async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    if not config.BOT_TOKEN:
        logging.error("BOT_TOKEN is missing in .env!")
        return
        
    if not config.ADMIN_IDS:
        logging.warning("ADMIN_IDS is empty! No one can use the bot.")

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    
    # Include the router with all handlers
    dp.include_router(router)
    
    logging.info("🤖 Bot started! Waiting for commands...")
    try:
        await dp.start_polling(bot)
    finally:
         await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
