from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from typing import List, Dict, Any

# Главное меню (Reply-кнопки внизу экрана)
def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="➕ Добавить подписку / триал"),
        ],
        [
            KeyboardButton(text="📋 Мои подписки"),
            KeyboardButton(text="⏳ Пробные периоды"),
        ],
        [
            KeyboardButton(text="📊 Статистика трат"),
            KeyboardButton(text="ℹ️ Помощь"),
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие из меню..."
    )

# Выбор типа подписки
def get_sub_type_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="⏳ Пробный период (триал)", callback_data="type_trial"),
        ],
        [
            InlineKeyboardButton(text="💳 Регулярная подписка", callback_data="type_regular"),
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Популярные сервисы (для быстрого ввода)
def get_popular_services_keyboard() -> InlineKeyboardMarkup:
    services = [
        ("Яндекс Плюс", "Яндекс Плюс"),
        ("Telegram Premium", "Telegram Premium"),
        ("Личный VPN", "Личный VPN"),
        ("YouTube Premium", "YouTube Premium"),
        ("Premier", "Premier"),
        ("Иви", "Иви"),
    ]
    
    rows = []
    # По 2 в ряд
    for i in range(0, len(services), 2):
        row = [InlineKeyboardButton(text=services[i][0], callback_data=f"preset_{services[i][1]}")]
        if i + 1 < len(services):
            row.append(InlineKeyboardButton(text=services[i+1][0], callback_data=f"preset_{services[i+1][1]}"))
        rows.append(row)
        
    rows.append([InlineKeyboardButton(text="✏️ Ввести другое название", callback_data="custom_title")])
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# Быстрый выбор срока окончания триала
def get_trial_dates_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="3 дня", callback_data="days_3"),
            InlineKeyboardButton(text="7 дней", callback_data="days_7"),
            InlineKeyboardButton(text="14 дней", callback_data="days_14"),
        ],
        [
            InlineKeyboardButton(text="30 дней", callback_data="days_30"),
            InlineKeyboardButton(text="60 дней", callback_data="days_60"),
        ],
        [
            InlineKeyboardButton(text="✏️ Ввести точную дату", callback_data="custom_date"),
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Период для постоянной подписки
def get_regular_period_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="📅 1 месяц", callback_data="period_months_1"),
            InlineKeyboardButton(text="📆 3 месяца", callback_data="period_months_3"),
            InlineKeyboardButton(text="🗓 6 месяцев", callback_data="period_months_6"),
        ],
        [
            InlineKeyboardButton(text="📅 1 год", callback_data="period_months_12"),
            InlineKeyboardButton(text="⏱ 1 неделя", callback_data="period_days_7"),
        ],
        [
            InlineKeyboardButton(text="✏️ Ввести свой срок", callback_data="period_custom"),
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Кнопка отмены
def get_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]]
    )

# Клавиатура списка подписок
def get_subscriptions_list_keyboard(subs: List[Dict[str, Any]], is_trial: bool = False) -> InlineKeyboardMarkup:
    rows = []
    for sub in subs:
        title = sub["title"]
        price = sub["price"]
        currency = sub["currency"]
        date_str = sub["next_date"]
        
        # Формируем текст кнопки, например: "Okko • 399 ₽ (до 28.10)"
        btn_text = f"{title} • {int(price) if price.is_integer() else price} {currency} ({date_str})"
        rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"view_sub_{sub['id']}")])
        
    rows.append([InlineKeyboardButton(text="➕ Добавить ещё", callback_data="start_add_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# Детали одной подписки (с кнопками действий)
def get_sub_detail_keyboard(sub_id: int, is_trial: bool) -> InlineKeyboardMarkup:
    rows = []
    if is_trial:
        rows.append([
            InlineKeyboardButton(text="🔄 Сделать постоянной", callback_data=f"convert_sub_{sub_id}")
        ])
    
    rows.append([
        InlineKeyboardButton(text="📅 Продлить дату", callback_data=f"extend_sub_{sub_id}"),
        InlineKeyboardButton(text="🗑 Удалить / Отменил", callback_data=f"delete_sub_{sub_id}"),
    ])
    rows.append([
        InlineKeyboardButton(text="◀️ Назад к списку", callback_data="back_to_list")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# Кнопки под уведомлением
def get_notification_keyboard(sub_id: int, is_trial: bool) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="✅ Отменил подписку", callback_data=f"notif_cancel_{sub_id}"),
            InlineKeyboardButton(text="👍 Продлил дату", callback_data=f"notif_extend_{sub_id}"),
        ]
    ]
    if is_trial:
        rows.append([
            InlineKeyboardButton(text="🔄 Оставить как постоянную", callback_data=f"convert_sub_{sub_id}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
