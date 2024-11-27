
import psycopg2
from config import POSTGRES_URL, d1_questions
from psycopg2 import sql
from tg import send_message
# Инициализация подключения к базе данных
def init_db():
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()

        # Создание таблицы participants
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            tg_id BIGINT PRIMARY KEY,
            chat_id BIGINT,
            counter INTEGER,
            tg_nickname TEXT,
            tg_user TEXT,
            email TEXT,
            education TEXT,
            interests TEXT,    
            start_time TEXT,
            resume TEXT
        );
        """)

        # Создание таблицы questions_day_1
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions_day_1 (
            tg_id BIGINT PRIMARY KEY,
            question_1 TEXT,
            question_2 TEXT,
            question_3 TEXT,
            question_4 TEXT,
            question_5 TEXT,
            finished BOOLEAN DEFAULT FALSE
        );
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("Таблицы успешно инициализированы.")
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")


def user_exists(chat_id, tg_id):
    exists = False
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()

        # Выполняем запрос для проверки статуса пользователя
        query = """
        SELECT finished
        FROM questions_day_1
        WHERE tg_id = %s;
        """
        cursor.execute(query, (tg_id,))
        result = cursor.fetchone()

        # Если запись найдена и статус finished равен true
        if result and result[0]:
            correct_answers = get_results(tg_id)
            max_index = len(d1_questions)
            send_message(chat_id, f"Ой, кажется ты уже знаешь все ответы ({correct_answers}/{max_index}) 🙈\n"
                                  "Прости, но пройти КВИЗ можно только один раз, но зато теперь ты можешь скинуть в этот чат свое резюме!")
            exists = True
        cursor.close()
        conn.close()
        return exists

    except Exception as e:
        print(f"Ошибка при проверке пользователя: {e}")

def get_results(tg_id):
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()

        # Формируем SQL-запрос, чтобы получить все значения для пользователя с tg_id
        query = """
        SELECT * FROM questions_day_1 WHERE tg_id = %s;
        """
        cursor.execute(query, (tg_id,))
        result = cursor.fetchone()

        # Если пользователь с таким tg_id и finished=True найден
        if result:
            print(f"Результаты для пользователя {tg_id}: {result}")
            # Перебираем все колонки с вопросами (например, question_1, question_2, ...)
            count_true = 0
            for i in range(0, len(d1_questions)):
                if result[i+1] == "true":  # Индекс 0 - tg_id, 1 - остальные колонки
                    count_true += 1
            print(f"Правильных ответов: {count_true}")
            # Закрываем курсор и соединение с базой данных
            cursor.close()
            conn.close()

            # Возвращаем количество правильных ответов
            return count_true

        else:
            cursor.close()
            conn.close()
            print(f"Пользователь с tg_id {tg_id} не найден или квиз не завершён.")
            return 0  # Если пользователь не найден или квиз не завершён

    except Exception as e:
        print(f"Ошибка при получении результатов: {e}")
        return 0
    
def count_users():
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()

        # SQL-запрос для получения максимального значения в столбце "counter"
        query = """
        SELECT MAX(counter) FROM participants;
        """
        cursor.execute(query)
        result = cursor.fetchone()

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        # Возвращаем максимальное значение
        if result and result[0] is not None:
            return result[0]
        else:
            print("В таблице participants нет значений в столбце counter.")
            return 0

    except Exception as e:
        print(f"Ошибка при получении максимального значения: {e}")
        return 0
    
def get_winner(counter):
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()

        # SQL-запрос для получения максимального значения в столбце "counter"
        query = """
        SELECT chat_id, tg_nickname FROM participants where counter = %s;
        """
        cursor.execute(query, counter)
        result = cursor.fetchone()
        print(result)

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        # Возвращаем максимальное значение
        if result:
            return result[1], result[0]
        else:
            print("В таблице participants нет значений в столбце counter.")
            return 0

    except Exception as e:
        print(f"Ошибка при поиске победителя: {e}")
        return 0
        