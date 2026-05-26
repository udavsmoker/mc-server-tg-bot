import asyncio
import logging
from aiogram import Bot, Dispatcher
import config
from server_registry import ServerRegistry
from handlers import router as handlers_router
from handlers.middleware import AdminMiddleware, ActiveServerMiddleware

async def main():
    # Setup structured logging
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if not config.BOT_TOKEN:
        logging.error("BOT_TOKEN is missing in .env!")
        return
        
    if not config.ADMIN_IDS:
        logging.warning("ADMIN_IDS is empty! No one can use the bot.")

    # Initialize the server registry with validated config
    registry = ServerRegistry(config.SERVERS)
    
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    
    # Pass registry context globally to middlewares and handlers
    dp["registry"] = registry
    
    # Register outer middlewares (run before filters - ideal for authentication)
    handlers_router.message.outer_middleware(AdminMiddleware())
    handlers_router.callback_query.outer_middleware(AdminMiddleware())
    
    # Register inner middlewares (run after filters - ideal for injecting active server context)
    handlers_router.message.middleware(ActiveServerMiddleware())
    handlers_router.callback_query.middleware(ActiveServerMiddleware())
    
    # Include all aggregated handler routers
    dp.include_router(handlers_router)
    
    logging.info("🤖 Bot started! Waiting for commands...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
