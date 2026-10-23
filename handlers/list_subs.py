from __future__ import annotations
from datetime import datetime, date
from typing import Optional, Union
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import (
    get_user_subscriptions,
    get_subscription,
    delete_subscription,
    convert_trial_to_regular,
    update_next_date,
)
from keyboards import (
    get_subscriptions_list_keyboard,
    get_sub_detail_keyboard,
    get_main_menu_keyboard,
)

router = Router()

# Просмотр всех подписок (кнопка меню)
@router.message(F.text == "📋 Мои подписки")
@router.callback_query(F.data == "back_to_list")
async def show_all_subscriptions(event: Message | CallbackQuery):
    user_id = event.from_user.id
    subs = await get_user_subscriptions(user_id)
    
    if not subs:
        text = "🤷‍♂️ У вас пока нет добавленных подписок или триалов.\n\n" \
               "Нажмите кнопку ниже, чтобы добавить первую!"
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text, parse_mode="Markdown")
            await event.answer()
        else:
            await event.answer(text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
        return

    text = "📋 **Ваши подписки и сервисы:**\n" \
           "_(Нажмите на сервис, чтобы просмотреть подробности или удалить)_"
    
    keyboard = get_subscriptions_list_keyboard(subs)
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard, parse_mode="Markdown")

# Просмотр только пробных периодов (кнопка меню)
@router.message(F.text == "⏳ Пробные периоды")
async def show_trial_subscriptions(message: Message):
    user_id = message.from_user.id
    subs = await get_user_subscriptions(user_id, is_trial=True)
    
    if not subs:
        await message.answer(
            "🎉 **Активных пробных периодов нет!**\n\n"
            "Все триалы завершены, или вы еще не добавляли новые.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        return

    text = "⏳ **Ваши активные пробные периоды:**\n" \
           "_(Следите за датами, чтобы успеть отменить до списания)_"
    keyboard = get_subscriptions_list_keyboard(subs, is_trial=True)
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

# Карточка деталей подписки
@router.callback_query(F.data.startswith("view_sub_"))
async def view_sub_detail(callback: CallbackQuery):
    sub_id = int(callback.data.replace("view_sub_", ""))
    user_id = callback.from_user.id
    
    sub = await get_subscription(sub_id, user_id)
    if not sub:
        await callback.answer("Подписка не найдена или уже удалена.", show_alert=True)
        return
        
    today = date.today()
    try:
        sub_date = datetime.strptime(sub["next_date"], "%Y-%m-%d").date()
        days_diff = (sub_date - today).days
        if days_diff > 0:
            days_str = f"⏳ Осталось: **{days_diff} дн.**"
        elif days_diff == 0:
            days_str = "🚨 **Списание СЕГОДНЯ!**"
        else:
            days_str = f"⚠️ Дата списания уже прошла ({abs(days_diff)} дн. назад)"
        formatted_date = sub_date.strftime("%d.%m.%Y")
    except ValueError:
        days_str = ""
        formatted_date = sub["next_date"]

    sub_type = "⏳ Пробный период (триал)" if sub["is_trial"] else "💳 Регулярная подписка"
    period_str = "Ежемесячно" if sub["period"] == "monthly" else ("Ежегодно" if sub["period"] == "yearly" else "Разово")

    text = (
        f"📌 **{sub['title']}**\n\n"
        f"• **Тип:** {sub_type}\n"
        f"• **Стоимость:** {sub['price']:.2f} {sub['currency']}\n"
        f"• **Периодичность:** {period_str}\n"
        f"• **Дата списания:** {formatted_date}\n"
        f"• {days_str}\n"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_sub_detail_keyboard(sub_id, bool(sub["is_trial"])),
        parse_mode="Markdown"
    )
    await callback.answer()

# Удаление подписки
@router.callback_query(F.data.startswith("delete_sub_"))
async def delete_sub_handler(callback: CallbackQuery):
    sub_id = int(callback.data.replace("delete_sub_", ""))
    user_id = callback.from_user.id
    
    deleted = await delete_subscription(sub_id, user_id)
    if deleted:
        await callback.answer("✅ Подписка успешно удалена!", show_alert=True)
        await show_all_subscriptions(callback)
    else:
        await callback.answer("Не удалось найти подписку.", show_alert=True)

# Перевод триала в регулярную подписку
@router.callback_query(F.data.startswith("convert_sub_"))
async def convert_sub_handler(callback: CallbackQuery):
    sub_id = int(callback.data.replace("convert_sub_", ""))
    user_id = callback.from_user.id
    
    success = await convert_trial_to_regular(sub_id, user_id, period="monthly")
    if success:
        await callback.answer("🎉 Триал переведен в постоянную подписку на 1 месяц!", show_alert=True)
        await view_sub_detail(callback)
    else:
        await callback.answer("Ошибка при изменении подписки.", show_alert=True)

# Продлить дату на 30 дней вперед
@router.callback_query(F.data.startswith("extend_sub_"))
async def extend_sub_handler(callback: CallbackQuery):
    sub_id = int(callback.data.replace("extend_sub_", ""))
    user_id = callback.from_user.id
    
    sub = await get_subscription(sub_id, user_id)
    if not sub:
        await callback.answer("Подписка не найдена.", show_alert=True)
        return
        
    try:
        curr_date = datetime.strptime(sub["next_date"], "%Y-%m-%d").date()
    except ValueError:
        curr_date = date.today()
        
    from datetime import timedelta
    new_date = (curr_date + timedelta(days=30)).strftime("%Y-%m-%d")
    await update_next_date(sub_id, new_date)
    
    await callback.answer("📅 Дата продлена на 30 дней!", show_alert=True)
    await view_sub_detail(callback)

# Обработка действий прямо из уведомлений
@router.callback_query(F.data.startswith("notif_cancel_"))
async def notif_cancel_handler(callback: CallbackQuery):
    sub_id = int(callback.data.replace("notif_cancel_", ""))
    user_id = callback.from_user.id
    
    deleted = await delete_subscription(sub_id, user_id)
    if deleted:
        await callback.message.edit_text("✅ Отлично! Вы отменили подписку, она удалена из базы.", parse_mode="Markdown")
        await callback.answer()
    else:
        await callback.answer("Подписка уже не найдена.", show_alert=True)

@router.callback_query(F.data.startswith("notif_extend_"))
async def notif_extend_handler(callback: CallbackQuery):
    sub_id = int(callback.data.replace("notif_extend_", ""))
    user_id = callback.from_user.id
    
    sub = await get_subscription(sub_id, user_id)
    if not sub:
        await callback.answer("Подписка не найдена.", show_alert=True)
        return
        
    try:
        curr_date = datetime.strptime(sub["next_date"], "%Y-%m-%d").date()
    except ValueError:
        curr_date = date.today()
        
    from datetime import timedelta
    new_date = (curr_date + timedelta(days=30)).strftime("%Y-%m-%d")
    await update_next_date(sub_id, new_date)
    
    await callback.message.edit_text(
        f"👍 Дата списания для **{sub['title']}** успешно перенесена на 30 дней (до {new_date}).",
        parse_mode="Markdown"
    )
    await callback.answer()

