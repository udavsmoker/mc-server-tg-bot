import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
import config
from handlers import router

async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    if not config.BOT_TOKEN:
        logging.error("Не указан BOT_TOKEN в файле .env!")
        return
        
    if not config.ADMIN_IDS:
        logging.warning("Список ADMIN_IDS пуст! Никто не сможет пользоваться ботом.")

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    
    # Подключаем роутер со всеми хендлерами
    dp.include_router(router)
    
    logging.info("🤖 Бот запущен! Ожидание команд...")
    try:
        await dp.start_polling(bot)
    finally:
         await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
