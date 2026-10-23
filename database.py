import aiosqlite
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from config import DB_PATH

async def init_db():
    """Инициализация базы данных и создание таблиц."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                notify_hour INTEGER DEFAULT 10,
                created_at TEXT NOT NULL
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT DEFAULT '₽',
                next_date TEXT NOT NULL,
                is_trial INTEGER NOT NULL DEFAULT 0,
                period TEXT DEFAULT 'monthly',
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        """)
        await db.commit()

async def upsert_user(user_id: int, username: Optional[str], first_name: Optional[str]):
    """Добавить или обновить пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        """, (user_id, username, first_name, now))
        await db.commit()

async def add_subscription(
    user_id: int,
    title: str,
    price: float,
    currency: str,
    next_date: str,
    is_trial: bool,
    period: str = "monthly"
) -> int:
    """Добавить новую подписку или пробный период."""
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()
        cursor = await db.execute("""
            INSERT INTO subscriptions (user_id, title, price, currency, next_date, is_trial, period, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, title, price, currency, next_date, 1 if is_trial else 0, period, now))
        await db.commit()
        return cursor.lastrowid

async def get_user_subscriptions(user_id: int, is_trial: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Получить список подписок пользователя с сортировкой по ближайшей дате."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if is_trial is None:
            query = "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY next_date ASC"
            params = (user_id,)
        else:
            query = "SELECT * FROM subscriptions WHERE user_id = ? AND is_trial = ? ORDER BY next_date ASC"
            params = (user_id, 1 if is_trial else 0)
        
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_subscription(sub_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Получить конкретную подписку."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM subscriptions WHERE id = ? AND user_id = ?",
            (sub_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def delete_subscription(sub_id: int, user_id: int) -> bool:
    """Удалить подписку."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM subscriptions WHERE id = ? AND user_id = ?",
            (sub_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0

async def convert_trial_to_regular(sub_id: int, user_id: int, period: str = "monthly") -> bool:
    """Перевести триал в постоянную платную подписку."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Продлеваем дату на месяц вперед от текущей
        sub = await get_subscription(sub_id, user_id)
        if not sub:
            return False
        
        try:
            curr_date = datetime.strptime(sub["next_date"], "%Y-%m-%d").date()
        except ValueError:
            curr_date = date.today()
            
        # Следующая дата через месяц
        next_date = (curr_date + timedelta(days=30)).strftime("%Y-%m-%d")
        
        cursor = await db.execute("""
            UPDATE subscriptions
            SET is_trial = 0, period = ?, next_date = ?
            WHERE id = ? AND user_id = ?
        """, (period, next_date, sub_id, user_id))
        await db.commit()
        return cursor.rowcount > 0

async def update_next_date(sub_id: int, new_date: str):
    """Обновить дату следующего списания."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE subscriptions SET next_date = ? WHERE id = ?",
            (new_date, sub_id)
        )
        await db.commit()

async def get_upcoming_notifications(target_date_str: str) -> List[Dict[str, Any]]:
    """Получить все подписки, у которых списание выпадает на target_date_str."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT s.*, u.first_name, u.username
            FROM subscriptions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.next_date = ?
        """, (target_date_str,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Собрать финансовую статистику по подпискам пользователя."""
    subs = await get_user_subscriptions(user_id)
    
    total_monthly = 0.0
    trials_count = 0
    regulars_count = 0
    nearest_sub = None
    
    today = date.today()
    
    for s in subs:
        if s["is_trial"]:
            trials_count += 1
        else:
            regulars_count += 1
            if s["period"] == "yearly":
                total_monthly += s["price"] / 12.0
            else:
                total_monthly += s["price"]
                
        try:
            sub_date = datetime.strptime(s["next_date"], "%Y-%m-%d").date()
            if sub_date >= today:
                if nearest_sub is None:
                    nearest_sub = s
        except ValueError:
            pass

    return {
        "total_subs": len(subs),
        "regulars_count": regulars_count,
        "trials_count": trials_count,
        "total_monthly": round(total_monthly, 2),
        "total_yearly": round(total_monthly * 12, 2),
        "nearest_sub": nearest_sub
    }
