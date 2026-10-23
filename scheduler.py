import logging
from datetime import date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from database import get_upcoming_notifications
from keyboards import get_notification_keyboard
from config import DEFAULT_NOTIFY_HOUR

logger = logging.getLogger(__name__)

async def check_and_send_notifications(bot: Bot):
    """
    Проверяет базу данных на наличие списаний:
    - через 3 дня
    - через 1 день (завтра)
    - сегодня
    """
    today = date.today()
    check_dates = [
        (today + timedelta(days=3), 3),
        (today + timedelta(days=1), 1),
        (today, 0),
    ]

    for target_date, days_left in check_dates:
        date_str = target_date.strftime("%Y-%m-%d")
        subs = await get_upcoming_notifications(date_str)

        for sub in subs:
            user_id = sub["user_id"]
            title = sub["title"]
            price = sub["price"]
            currency = sub["currency"]
            is_trial = bool(sub["is_trial"])
            sub_id = sub["id"]

            if is_trial:
                if days_left == 3:
                    alert_header = "⚠️ **Напоминание о пробном периоде (триале)**"
                    time_desc = "через **3 дня**"
                elif days_left == 1:
                    alert_header = "🚨 **Внимание: триал заканчивается ЗАВТРА!**"
                    time_desc = "**завтра**"
                else:
                    alert_header = "🔔 **СЕГОДНЯ последний день триала!**"
                    time_desc = "**сегодня**"

                msg_text = (
                    f"{alert_header}\n\n"
                    f"Сервис: **{title}**\n"
                    f"Бесплатный период истекает {time_desc}.\n"
                    f"Если не отменить, спишут: **{price:.2f} {currency}**.\n\n"
                    f"💡 _Если вы не планируете пользоваться сервисом дальше, отмените подписку в настройках аккаунта прямо сейчас._"
                )
            else:
                if days_left == 3:
                    alert_header = "💳 **Напоминание о регулярном платеже**"
                    time_desc = "через **3 дня**"
                elif days_left == 1:
                    alert_header = "🚨 **Внимание: оплата ЗАВТРА!**"
                    time_desc = "**завтра**"
                else:
                    alert_header = "🔔 **СЕГОДНЯ день списания за подписку!**"
                    time_desc = "**сегодня**"

                msg_text = (
                    f"{alert_header}\n\n"
                    f"Сервис: **{title}**\n"
                    f"Списание {time_desc} на сумму: **{price:.2f} {currency}**."
                )

            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=msg_text,
                    reply_markup=get_notification_keyboard(sub_id, is_trial),
                    parse_mode="Markdown"
                )
                logger.info(f"Уведомление отправлено пользователю {user_id} для подписки {title}")
            except TelegramAPIError as e:
                logger.warning(f"Не удалось отправить уведомление пользователю {user_id}: {e}")

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Настройка и запуск планировщика."""
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    
    # Запуск каждый день в заданный час (по умолчанию 10:00)
    scheduler.add_job(
        check_and_send_notifications,
        trigger=CronTrigger(hour=DEFAULT_NOTIFY_HOUR, minute=0),
        args=[bot],
        id="daily_subscription_check",
        replace_existing=True
    )
    
    return scheduler
