from datetime import datetime, date
from aiogram import Router, F
from aiogram.types import Message
from database import get_user_stats
from keyboards import get_main_menu_keyboard

router = Router()

@router.message(F.text == "📊 Статистика трат")
async def show_stats(message: Message):
    user_id = message.from_user.id
    stats = await get_user_stats(user_id)
    
    if stats["total_subs"] == 0:
        await message.answer(
            "📊 **Статистика расходов пока пуста.**\n\n"
            "Добавьте свои подписки и триалы, чтобы видеть общие затраты!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        return
        
    nearest_text = "—"
    if stats["nearest_sub"]:
        n = stats["nearest_sub"]
        try:
            n_date = datetime.strptime(n["next_date"], "%Y-%m-%d").date()
            days_left = (n_date - date.today()).days
            if days_left == 0:
                time_str = "сегодня"
            elif days_left == 1:
                time_str = "завтра"
            else:
                time_str = f"через {days_left} дн."
            nearest_text = f"{n['title']} ({n['price']:.0f} {n['currency']}) — {n_date.strftime('%d.%m.%Y')} ({time_str})"
        except ValueError:
            nearest_text = f"{n['title']} ({n['next_date']})"

    text = (
        "📊 **Финансовая аналитика ваших подписок:**\n\n"
        f"• 💳 **Регулярных подписок:** {stats['regulars_count']}\n"
        f"• ⏳ **Активных триалов:** {stats['trials_count']}\n\n"
        f"💸 **Сумма в месяц:** `{stats['total_monthly']:.2f} ₽`\n"
        f"💰 **Сумма в год:** `{stats['total_yearly']:.2f} ₽`\n\n"
        f"⏰ **Ближайшее списание:**\n"
        f"└ {nearest_text}\n"
    )
    
    await message.answer(text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
