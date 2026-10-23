import os
from datetime import datetime
from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

from config import ADMIN_ID, DB_PATH
from database import get_admin_stats

router = Router()

@router.message(Command("backup"))
async def cmd_backup(message: Message):
    """Отправляет файл базы данных в чат владельца бота."""
    if message.from_user.id != ADMIN_ID:
        return  # Не отвечаем обычным пользователям

    if not os.path.exists(DB_PATH):
        await message.answer("⚠️ Файл базы данных еще не создан.")
        return

    stats = await get_admin_stats()
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    size_kb = os.path.getsize(DB_PATH) / 1024

    caption = (
        f"📦 **Резервная копия базы данных SubTrack**\n\n"
        f"• 👥 **Пользователей в базе:** {stats['users_count']}\n"
        f"• 💳 **Всего подписок/триалов:** {stats['subs_count']}\n"
        f"• 📊 **Размер:** {size_kb:.1f} КБ\n"
        f"• 🕒 **Создан:** {now_str}\n\n"
        f"💡 _Сохраните этот файл на компьютер или в «Избранное». Если что-то случится с сервером, вы всегда сможете восстановить данные._"
    )

    db_file = FSInputFile(DB_PATH, filename=f"subscriptions_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db")
    await message.answer_document(
        document=db_file,
        caption=caption,
        parse_mode="Markdown"
    )

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Показывает общую статистику бота администратору."""
    if message.from_user.id != ADMIN_ID:
        return

    stats = await get_admin_stats()
    size_kb = (os.path.getsize(DB_PATH) / 1024) if os.path.exists(DB_PATH) else 0

    text = (
        f"👑 **Панель владельца бота:**\n\n"
        f"• 👥 **Всего пользователей:** {stats['users_count']}\n"
        f"• 💳 **Всего подписок в базе:** {stats['subs_count']}\n"
        f"• 💾 **Размер базы:** {size_kb:.1f} КБ\n\n"
        f"📥 Отправьте команду `/backup`, чтобы получить свежий файл базы данных."
    )
    await message.answer(text, parse_mode="Markdown")
