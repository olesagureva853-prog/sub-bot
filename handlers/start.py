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
