import asyncio
import logging
from app.bot import bot, dp
from app.shedulers import scheduler

logging.basicConfig(level=logging.INFO)


async def on_startup():
    logging.info("Запуск шедулеров")
    scheduler.start()
    logging.info("Бот успешно запущен")


async def bot_start():
    await on_startup()
    await dp.start_polling(bot)


if __name__ == '__main__':
    import sys

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(bot_start())
