import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from bot.handlers import router






async def main() -> None:
    bot = Bot(token=BOT_TOKEN)

    storage = MemoryStorage()

    dp = Dispatcher(storage=storage)

    dp.include_router(router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)

        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())