import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from config import BOT_TOKEN
from database import init_db
from handlers import setup_routers
from scheduler import setup_scheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def set_bot_commands(bot: Bot):
    """Регистрирует список команд в меню Telegram."""
    commands = [
        BotCommand(command="start", description="Запустить бота и главное меню"),
        BotCommand(command="help", description="Инструкция и помощь"),
    ]
    await bot.set_my_commands(commands)

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error(
            "❌ ОШИБКА: Токен бота не указан!\n"
            "Пожалуйста, добавьте ваш токен бота в файл .env в папке bot2:\n"
            "BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        )
        sys.exit(1)

    logger.info("Инициализация базы данных...")
    await init_db()

    # Создание бота и диспетчера
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Подключение обработчиков (роутеров)
    dp.include_router(setup_routers())

    # Настройка командного меню
    await set_bot_commands(bot)

    # Настройка и запуск планировщика уведомлений
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Планировщик фоновых уведомлений запущен.")

    logger.info("Бот успешно запущен и ожидает сообщений!")
    
    try:
        # Удаляем вебхуки и запускаем polling
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Бот остановлен.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Работа бота завершена пользователем.")
