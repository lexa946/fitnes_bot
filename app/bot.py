from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.handlers.main import router as main_router
from app.handlers.trainer import router as trainer_router
from app.handlers.user import router as user_router

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode='HTML'),
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_router(main_router)
dp.include_router(user_router)
dp.include_router(trainer_router)
