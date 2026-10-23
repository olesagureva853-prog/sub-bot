from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from database import upsert_user
from keyboards import get_main_menu_keyboard

router = Router()

START_TEXT = (
    "👋 **Привет! Я бот-трекер подписок и пробных периодов.**\n\n"
    "Я помогу тебе:\n"
    "• ⏳ **Не забывать отменять триалы** до того, как с карты спишут деньги.\n"
    "• 💳 **Вести учет регулярных подписок** и видеть реальную сумму трат в месяц и год.\n"
    "• 🔔 **Получать уведомления** за 3 дня, за 1 день и в день списания.\n\n"
    "💡 _Нажми кнопку ниже, чтобы добавить первую подписку или пробный период!_"
)

HELP_TEXT = (
    "📖 **Как пользоваться ботом:**\n\n"
    "1️⃣ **Добавить подписку или триал:**\n"
    "Нажмите `➕ Добавить подписку / триал`. Выберите тип (пробный или регулярная), название сервиса, стоимость и дату окончания.\n\n"
    "2️⃣ **Уведомления:**\n"
    "Бот пришлет оповещение за 3 дня и за 1 день до списания с кнопками: «Отменил», «Продлил» или «Сделать постоянной».\n\n"
    "3️⃣ **Управление:**\n"
    "В разделах `📋 Мои подписки` и `⏳ Пробные периоды` можно просматривать активные сервисы и удалять ненужные.\n\n"
    "4️⃣ **Статистика:**\n"
    "Покажет, сколько денег в месяц и в год уходит на все сервисы."
)

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    if user:
        await upsert_user(user.id, user.username, user.first_name)
    
    await message.answer(
        START_TEXT,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )

@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    await message.answer(
        HELP_TEXT,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )

@router.message(Command("id", "myid"))
async def cmd_myid(message: Message):
    from config import ADMIN_ID
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "нет"
    is_admin = (user_id == ADMIN_ID)
    await message.answer(
        f"🆔 **Ваш профиль в Telegram:**\n"
        f"• Telegram ID: `{user_id}`\n"
        f"• Username: {username}\n"
        f"• Доступ администратора: {'✅ Да' if is_admin else '❌ Нет'}",
        parse_mode="Markdown"
    )

@router.message(Command("backup"))
async def cmd_backup(message: Message):
    """Отправляет файл базы данных в чат владельца бота."""
    import os
    from datetime import datetime
    from aiogram.types import FSInputFile
    from config import ADMIN_ID, DB_PATH
    from database import get_admin_stats

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
    import os
    from config import ADMIN_ID, DB_PATH
    from database import get_admin_stats

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


