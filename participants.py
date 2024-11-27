
import psycopg2
from psycopg2 import sql
from config import POSTGRES_URL

# Функция для сохранения участника
def save_participant(tg_id, chat_id, tg_nickname, start_time, counter):
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO participants (tg_id, chat_id, tg_nickname, start_time, counter)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (tg_id) DO NOTHING;
        """, (tg_id, chat_id, tg_nickname, start_time, counter + 1))

        conn.commit()
        cursor.close()
        conn.close()
        print(f"Участник {tg_id} сохранен в базу данных.")
    except Exception as e:
        print(f"Ошибка при сохранении участника: {e}")

# Функция для обновления участника
def update_participant(tg_id, field, value):
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()

        cursor.execute(
            sql.SQL("UPDATE participants SET {} = %s WHERE tg_id = %s;").format(sql.Identifier(field)),
            (value, tg_id)
        )

        conn.commit()
        cursor.close()
        conn.close()
        print(f"Обновлено поле {field} для участника {tg_id}.")
    except Exception as e:
        print(f"Ошибка при обновлении участника: {e}")