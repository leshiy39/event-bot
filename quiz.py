from config import POSTGRES_URL, d1_questions
import psycopg2
from psycopg2 import sql
from tg import send_message, send_message_with_button, send_blockquoute
from db import get_results

max_index = len(d1_questions)

# Функция для запуска квиза
def start_quiz(chat_id, tg_id):
    print(f"User {tg_id} started quiz.")
    # Словарь для состояния текущего квиза
    quiz_state = {
        "current_index": 0,
        "user_answers": {}  # Хранение ответов пользователя
    }

    def ask_question():
        """Задаёт текущий вопрос из словаря."""
        index = quiz_state["current_index"]
        if index < len(d1_questions):
            question_data = d1_questions[index]
            send_message_with_button(chat_id, question_data["question"], question_data["buttons"])
        else:
            save_quiz_results(tg_id, quiz_state["user_answers"])
            correct_answers = get_results(tg_id)
            if correct_answers <= 2:
                text = f"Ничего страшного! Ты можешь спросить все интересующие тебя вопросы у коллег за стендом, мы обязательно расскажем Тебе о НИИАС! ❤️"
            else:
                text = f"Отличный результат! Рады, что удалось чуть больше узнать про нашу компанию ❤️\n"
                text += f"Если у тебя еще остались вопросы, обязательно обращайся к коллегам за стойкой"
            message = f"Твой результат: {correct_answers} / {max_index}\n{text}"
            message += "\nА если ты в поисках стажировки, то можешь скинуть свое резюме в этот бот, мы вернемся с обратной связью в ближайшее время"
            # Завершаем квиз
            send_message(chat_id, f"{message}")
            return "completed"  # Сигнализируем, что квиз завершён

    def process_answer(callback_data):
        """Обрабатывает ответ пользователя."""
        index = quiz_state["current_index"]
        question_data = d1_questions[index]

        # Проверка ответа
        if callback_data in question_data["correct"]:
            send_message(chat_id, question_data["success_message"])
            is_correct = True
        else:
            send_message(chat_id, question_data["failure_message"])
            is_correct = False

        # Информационный пост
        send_blockquoute(chat_id, question_data["info_post"])

        # Сохраняем результат (True/False) в зависимости от правильности ответа
        quiz_state["user_answers"][f"question_{index + 1}"] = is_correct

        # Переходим к следующему вопросу
        quiz_state["current_index"] += 1
        return ask_question()  # Переход к следующему вопросу

    # Задаём первый вопрос
    ask_question()

    return process_answer, quiz_state  # Возвращаем обработчик и состояние

# Функция для сохранения результатов квиза
def save_quiz_results(tg_id, answers):
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()

        # Формируем запрос на обновление
        query = """
        INSERT INTO questions_day_1 (tg_id, question_1, question_2, question_3, question_4, question_5, finished)
        VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        ON CONFLICT (tg_id) DO UPDATE SET
            question_1 = EXCLUDED.question_1,
            question_2 = EXCLUDED.question_2,
            question_3 = EXCLUDED.question_3,
            question_4 = EXCLUDED.question_4,
            question_5 = EXCLUDED.question_5,
            finished = TRUE;
        """
        # Преобразуем ответы в TRUE/FALSE
        cursor.execute(query, (
            tg_id,
            answers.get("question_1"),
            answers.get("question_2"),
            answers.get("question_3"),
            answers.get("question_4"),
            answers.get("question_5"),
        ))

        conn.commit()
        cursor.close()
        conn.close()
        print(f"Результаты квиза для {tg_id} успешно сохранены.")
    except Exception as e:
        print(f"Ошибка при сохранении результатов квиза: {e}")