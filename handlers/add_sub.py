from __future__ import annotations
import re
from datetime import datetime, date, timedelta
from typing import Optional, Union
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import add_subscription
from keyboards import (
    get_sub_type_keyboard,
    get_popular_services_keyboard,
    get_trial_dates_keyboard,
    get_regular_period_keyboard,
    get_cancel_keyboard,
    get_main_menu_keyboard,
)

router = Router()

class AddSubStates(StatesGroup):
    select_type = State()
    select_title = State()
    custom_title = State()
    enter_price = State()
    select_period = State()
    custom_period = State()
    select_date = State()
    custom_date = State()

# Кнопка отмены
@router.callback_query(F.data == "cancel_action")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Добавление подписки отменено.")
    await callback.answer()

# Запуск добавления через текстовую кнопку меню или callback
@router.message(F.text == "➕ Добавить подписку / триал")
@router.callback_query(F.data == "start_add_sub")
async def start_add_sub(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(AddSubStates.select_type)
    
    text = "👉 **Что вы хотите добавить?**\n\n" \
           "• ⏳ **Пробный период (триал)** — бесплатный доступ на 7–30 дней, чтобы не забыть отменить.\n" \
           "• 💳 **Регулярная подписка** — повторяющееся списание (раз в месяц или год)."
           
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_sub_type_keyboard(), parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_sub_type_keyboard(), parse_mode="Markdown")

# Выбор типа: триал или регулярная
@router.callback_query(AddSubStates.select_type, F.data.in_(["type_trial", "type_regular"]))
async def process_sub_type(callback: CallbackQuery, state: FSMContext):
    is_trial = (callback.data == "type_trial")
    await state.update_data(is_trial=is_trial)
    await state.set_state(AddSubStates.select_title)
    
    type_name = "пробного периода" if is_trial else "подписки"
    text = f"🎯 Выберите сервис для {type_name} из популярных или введите своё название:"
    await callback.message.edit_text(text, reply_markup=get_popular_services_keyboard())
    await callback.answer()

# Выбор из пресета
@router.callback_query(AddSubStates.select_title, F.data.startswith("preset_"))
async def process_preset_title(callback: CallbackQuery, state: FSMContext):
    title = callback.data.replace("preset_", "")
    await state.update_data(title=title)
    await ask_price(callback.message, state, is_callback=True)
    await callback.answer()

# Нажатие "Ввести другое название"
@router.callback_query(AddSubStates.select_title, F.data == "custom_title")
async def process_custom_title_btn(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddSubStates.custom_title)
    await callback.message.edit_text(
        "✏️ Напишите название сервиса (например: _Adobe Creative Cloud_ или _Фитнес_):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Ввод кастомного названия текстом
@router.message(AddSubStates.custom_title)
async def process_custom_title_text(message: Message, state: FSMContext):
    title = message.text.strip()
    if not title:
        await message.answer("Название не может быть пустым. Попробуйте еще раз:")
        return
    await state.update_data(title=title)
    await ask_price(message, state, is_callback=False)

# Шаг запроса цены
async def ask_price(message: Message, state: FSMContext, is_callback: bool = False):
    data = await state.get_data()
    is_trial = data.get("is_trial", False)
    await state.set_state(AddSubStates.enter_price)
    
    if is_trial:
        text = f"💰 **Сколько спишут за {data['title']}, если забыть отменить?**\n" \
               "_(Введите сумму в рублях, например `399`. Если бесплатно или не знаете — введите `0`)_"
    else:
        text = f"💰 **Какова стоимость подписки на {data['title']}?**\n" \
               "_(Введите сумму в рублях, например `299` или `1490`)_"
               
    if is_callback:
        await message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="Markdown")

# Обработка ввода цены
@router.message(AddSubStates.enter_price)
async def process_price(message: Message, state: FSMContext):
    raw_text = message.text.strip().replace(",", ".").replace("₽", "").replace("руб", "").strip()
    try:
        price = float(raw_text)
        if price < 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите число (например: `299` или `399.50`):", parse_mode="Markdown")
        return
        
    await state.update_data(price=price)
    data = await state.get_data()
    is_trial = data.get("is_trial", False)
    
    if is_trial:
        await state.set_state(AddSubStates.select_date)
        text = f"⏳ **Когда заканчивается пробный период для {data['title']}?**\n" \
               "Выберите срок кнопкой или нажмите «Ввести точную дату»:"
        await message.answer(text, reply_markup=get_trial_dates_keyboard(), parse_mode="Markdown")
    else:
        await state.set_state(AddSubStates.select_period)
        text = "📅 **Как часто происходит оплата?**"
        await message.answer(text, reply_markup=get_regular_period_keyboard(), parse_mode="Markdown")

# Выбор периода регулярной подписки
@router.callback_query(AddSubStates.select_period, F.data.startswith("period_"))
async def process_period(callback: CallbackQuery, state: FSMContext):
    if callback.data == "period_custom":
        await state.set_state(AddSubStates.custom_period)
        await callback.message.edit_text(
            "✏️ **Укажите свой период списания:**\n\n"
            "Например:\n"
            "• `45 дней` (или просто число: `45`)\n"
            "• `2 месяца` (или `3 мес`)\n"
            "• `2 недели`\n"
            "• `2 года`\n\n"
            "_(Напишите текстом)_:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    if callback.data.startswith("period_months_"):
        months = int(callback.data.replace("period_months_", ""))
        period = f"months:{months}"
    elif callback.data.startswith("period_days_"):
        days = int(callback.data.replace("period_days_", ""))
        period = f"days:{days}"
    elif callback.data == "period_yearly":
        period = "months:12"
    else:
        period = "months:1"

    await state.update_data(period=period)
    await ask_next_payment_date(callback.message, state, is_callback=True)
    await callback.answer()

@router.message(AddSubStates.custom_period)
async def process_custom_period_text(message: Message, state: FSMContext):
    parsed = parse_period_string(message.text)
    if not parsed:
        await message.answer(
            "⚠️ Не удалось распознать срок.\n"
            "Пожалуйста, напишите, например: `45 дней`, `2 месяца` или `2 недели` (или просто число дней):",
            parse_mode="Markdown"
        )
        return
        
    await state.update_data(period=parsed)
    await ask_next_payment_date(message, state, is_callback=False)

async def ask_next_payment_date(message: Message, state: FSMContext, is_callback: bool = False):
    await state.set_state(AddSubStates.custom_date)
    text = (
        "📆 **Введите дату следующего списания** в формате `ДД.ММ` или `ДД.ММ.ГГГГ`\n"
        "_(Например: `15.11` или `01.12.2026`)_:"
    )
    if is_callback:
        await message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="Markdown")


# Быстрый выбор даты триала кнопками
@router.callback_query(AddSubStates.select_date, F.data.startswith("days_"))
async def process_quick_days(callback: CallbackQuery, state: FSMContext):
    days = int(callback.data.replace("days_", ""))
    target_date = date.today() + timedelta(days=days)
    await state.update_data(next_date=target_date.strftime("%Y-%m-%d"), period="once")
    await save_and_finish(callback.message, state, is_callback=True)
    await callback.answer()

# Выбор ручного ввода даты триала
@router.callback_query(AddSubStates.select_date, F.data == "custom_date")
async def process_custom_date_btn(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddSubStates.custom_date)
    await callback.message.edit_text(
        "📆 **Введите дату окончания** в формате `ДД.ММ` или `ДД.ММ.ГГГГ`\n"
        "_(Например: `28.10` или `15.11.2026`)_:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Парсинг ручной даты
@router.message(AddSubStates.custom_date)
async def process_custom_date_text(message: Message, state: FSMContext):
    raw_date = message.text.strip()
    parsed_date = parse_date_string(raw_date)
    
    if not parsed_date:
        await message.answer(
            "⚠️ Неверный формат даты. Пожалуйста, напишите дату в виде `ДД.ММ` (например `12.11`) или `ДД.ММ.ГГГГ`:",
            parse_mode="Markdown"
        )
        return
        
    await state.update_data(next_date=parsed_date.strftime("%Y-%m-%d"))
    data = await state.get_data()
    if "period" not in data:
        await state.update_data(period="monthly" if not data.get("is_trial") else "once")
        
    await save_and_finish(message, state, is_callback=False)

def parse_date_string(date_str: str) -> date | None:
    """Парсит ДД.ММ.ГГГГ или ДД.ММ"""
    today = date.today()
    # Проверка формата DD.MM.YYYY
    match_full = re.match(r"^(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})$", date_str)
    if match_full:
        d, m, y = map(int, match_full.groups())
        try:
            return date(y, m, d)
        except ValueError:
            return None
            
    # Проверка формата DD.MM
    match_short = re.match(r"^(\d{1,2})[./\-](\d{1,2})$", date_str)
    if match_short:
        d, m = map(int, match_short.groups())
        try:
            target = date(today.year, m, d)
            if target < today:
                # Если дата в этом году уже прошла, переносим на следующий год
                target = date(today.year + 1, m, d)
            return target
        except ValueError:
            return None
            
    return None

def parse_period_string(text: str) -> str | None:
    """Парсит введенный пользователем срок в формат months:X или days:Y"""
    text = text.lower().strip()
    
    # Недели
    match_w = re.search(r"(\d+)\s*(нед|week)", text)
    if match_w:
        weeks = int(match_w.group(1))
        if weeks > 0:
            return f"days:{weeks * 7}"
            
    # Месяцы
    match_m = re.search(r"(\d+)\s*(мес|month)", text)
    if match_m:
        months = int(match_m.group(1))
        if months > 0:
            return f"months:{months}"
            
    # Года
    match_y = re.search(r"(\d+)\s*(год|лет|year)", text)
    if match_y:
        years = int(match_y.group(1))
        if years > 0:
            return f"months:{years * 12}"
            
    # Дни
    match_d = re.search(r"(\d+)\s*(дн|день|дня|дней|day)", text)
    if match_d:
        days = int(match_d.group(1))
        if days > 0:
            return f"days:{days}"
            
    # Просто число -> считаем как дни
    if text.isdigit():
        num = int(text)
        if num > 0:
            return f"days:{num}"
            
    return None

def format_period_human(period: str) -> str:
    """Красиво форматирует период для человека"""
    if period in ("monthly", "months:1"):
        return "1 месяц"
    elif period in ("yearly", "months:12"):
        return "1 год"
    elif period == "months:3":
        return "3 месяца"
    elif period == "months:6":
        return "6 месяцев"
    elif period.startswith("months:"):
        m = period.split(":")[1]
        return f"Каждые {m} мес."
    elif period == "days:7":
        return "1 неделя"
    elif period.startswith("days:"):
        d = period.split(":")[1]
        return f"Каждые {d} дн."
    elif period == "once":
        return "Разово (триал)"
    return period


async def save_and_finish(message: Message, state: FSMContext, is_callback: bool = False):
    """Сохранение в базу и поздравление"""
    data = await state.get_data()
    user_id = message.chat.id
    
    title = data["title"]
    price = data["price"]
    is_trial = data.get("is_trial", False)
    next_date = data["next_date"]
    period = data.get("period", "monthly")
    currency = "₽"
    
    await add_subscription(
        user_id=user_id,
        title=title,
        price=price,
        currency=currency,
        next_date=next_date,
        is_trial=is_trial,
        period=period
    )
    
    await state.clear()
    
    date_display = datetime.strptime(next_date, "%Y-%m-%d").strftime("%d.%m.%Y")
    days_left = (datetime.strptime(next_date, "%Y-%m-%d").date() - date.today()).days
    
    if is_trial:
        header = "✅ **Пробный период успешно добавлен!**"
        action_note = f"⚠️ Я напомню вам за 3 дня и за 1 день до списания, чтобы вы успели его отменить."
        period_line = ""
    else:
        header = "✅ **Регулярная подписка успешно добавлена!**"
        action_note = f"🔔 Я буду присылать напоминания перед каждым списанием."
        period_line = f"🗓 **Периодичность:** {format_period_human(period)}\n"
        
    text = (
        f"{header}\n\n"
        f"📌 **Сервис:** {title}\n"
        f"💰 **Сумма:** {price:.2f} {currency}\n"
        f"{period_line}"
        f"📅 **Дата следующего списания:** {date_display} (через {days_left} дн.)\n\n"
        f"{action_note}"
    )
    
    if is_callback:
        await message.edit_text(text, parse_mode="Markdown")
        await message.answer("Выберите действие:", reply_markup=get_main_menu_keyboard())
    else:
        await message.answer(text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
