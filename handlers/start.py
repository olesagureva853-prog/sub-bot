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
        from database import is_new_user, upsert_user
        from config import ADMIN_ID
        is_new = await is_new_user(user.id)
        await upsert_user(user.id, user.username, user.first_name)
        
        # Если пришел новый пользователь (и это не сам админ) — шлем алерт админу в личку!
        if is_new and user.id != ADMIN_ID:
            try:
                username_str = f"@{user.username}" if user.username else "нет юзернейма"
                await message.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=(
                        f"🎉 **Новый пользователь запустил бота!**\n\n"
                        f"• **Имя:** {user.first_name or 'Без имени'}\n"
                        f"• **Юзернейм:** {username_str}\n"
                        f"• **Telegram ID:** `{user.id}`"
                    ),
                    parse_mode="Markdown"
                )
            except Exception:
                pass
    
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
    from database import upsert_user
    user = message.from_user
    user_id = user.id if user else 0
    if user:
        await upsert_user(user.id, user.username, user.first_name)
    username = f"@{user.username}" if (user and user.username) else "нет"
    is_admin = (user_id == ADMIN_ID)
    await message.answer(
        f"🆔 **Ваш профиль в Telegram:**\n"
        f"• Telegram ID: `{user_id}`\n"
        f"• Username: {username}\n"
        f"• Доступ администратора: {'✅ Да' if is_admin else '❌ Нет'}",
        parse_mode="Markdown"
    )

@router.message(Command("users"))
async def cmd_users(message: Message):
    """Показывает список всех пользователей владельцу бота."""
    from config import ADMIN_ID
    from database import get_all_users

    if message.from_user.id != ADMIN_ID:
        return

    users = await get_all_users()
    if not users:
        await message.answer("👥 В базе пока нет зарегистрированных пользователей.")
        return

    lines = [f"👥 **Список пользователей бота (всего: {len(users)}):**\n"]
    for i, u in enumerate(users, 1):
        uname = f"@{u['username']}" if u.get("username") else "без юзернейма"
        fname = u.get("first_name") or "Пользователь"
        lines.append(f"{i}. **{fname}** ({uname}) — ID: `{u['user_id']}`")

    await message.answer("\n".join(lines), parse_mode="Markdown")

@router.message(Command("backup"))
async def cmd_backup(message: Message):
    """Отправляет файл базы данных в чат владельца бота."""
    import os
    from datetime import datetime
    from aiogram.types import FSInputFile
    from config import ADMIN_ID, DB_PATH
    from database import get_admin_stats, get_all_users

    if message.from_user.id != ADMIN_ID:
        return  # Не отвечаем обычным пользователям

    if not os.path.exists(DB_PATH):
        await message.answer("⚠️ Файл базы данных еще не создан.")
        return

    stats = await get_admin_stats()
    all_users = await get_all_users()
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    size_kb = os.path.getsize(DB_PATH) / 1024

    users_preview = []
    for u in all_users[:5]:
        uname = f"@{u['username']}" if u.get("username") else f"ID {u['user_id']}"
        users_preview.append(f"• {u.get('first_name') or 'User'} ({uname})")

    users_text = "\n".join(users_preview)
    if len(all_users) > 5:
        users_text += f"\n• ...и ещё {len(all_users) - 5}"

    caption = (
        f"📦 **Резервная копия базы данных SubTrack**\n\n"
        f"• 👥 **Пользователей в базе:** {stats['users_count']}\n"
        f"• 💳 **Всего подписок/триалов:** {stats['subs_count']}\n"
        f"• 📊 **Размер:** {size_kb:.1f} КБ\n"
        f"• 🕒 **Создан:** {now_str}\n\n"
        f"👤 **Пользователи:**\n{users_text}\n\n"
        f"💡 _Отправьте /users, чтобы посмотреть полный список людей._"
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
        f"👥 Напишите `/users` для просмотра списка людей.\n"
        f"📥 Напишите `/backup`, чтобы получить свежий файл базы данных."
    )
    await message.answer(text, parse_mode="Markdown")



