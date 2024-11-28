import os
import random
import requests
import time
import json
from datetime import datetime
import psycopg2
from psycopg2 import sql
from config import TOKEN, POSTGRES_URL, d1_questions, admin_ids
from db import *
from participants import *
from quiz import start_quiz
from tg import *
from files import *


def init(chat_id, user_states):
    user_states = {}
    user_states.pop(chat_id, None)
    welcome_message = ("Привет! Это твой бот для участия в розыгрыше ☺️\n"
                    "Мы попросим тебя ответить на несколько вопросов, чтобы зафиксировать твою активность.\n"
                    "В 14:00 с помощью генератора случайных чисел мы выберем победителей.\n"
                    "Поехали?")
    send_message_with_button(chat_id, welcome_message, [
        {"text": "Да", "action": "continue_dialog"},
        {"text": "Нет", "action": "decline_dialog"}
    ])

# Основной цикл бота
def main():
    print("Инициализация базы данных...")
    init_db()

    print("Бот запущен...")
    offset = None
    chat_id=''
    user_states = {}
    waiting_for_quiz = {}
    while True:
        try:    
            try:
                updates = get_updates(offset)
                print(updates)
            except RequestException as e:
                print(f"Ошибка при запросе к Telegram API: {e}")
            if updates.get("ok"):
                for update in updates.get("result", []):
                    offset = update["update_id"] + 1
                    # Обработка callback_query
                    if "kicked" in str(update):
                        print(f"Бот был заблокирован {update}")
                        break
                    if "edited_message" in update:
                        chat_id = update["edited_message"]["chat"]["id"]
                        print('edited')
                        send_message(chat_id, "Простите, но я не умею работать с отредактированными сообщениями. Вынужден сбросить нашу сессию и давайте начнем заново через /start")
                        break
                    if "callback_query" in update:
                        print('callback_query')
                        callback_query = update["callback_query"]
                        chat_id = callback_query["message"]["chat"]["id"]
                        tg_id = callback_query["from"]["id"]
                        tg_nickname = callback_query["from"].get("username", "None")
                        data = callback_query["data"]
                        if user_exists(chat_id, tg_id): 
                            break
                        else:
                            print(update)
                            if "/start" in str(update):
                                init(chat_id, user_states)
                            if chat_id in waiting_for_quiz:
                                process_answer, quiz_state = waiting_for_quiz[chat_id]
                                result = process_answer(data)
                                if result == "completed":  # Удаляем состояние после завершения квиза
                                    waiting_for_quiz.pop(chat_id)

                            if data == "continue_dialog":
                                start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                counter = count_users()
                                save_participant(tg_id, chat_id, tg_nickname, start_time, counter)
                                send_message(chat_id, "Отлично! \nНапиши свои Фамилию и Имя 👤")
                                user_states[chat_id] = {"state": "waiting_for_name", "tg_id": tg_id}

                            elif data == "decline_dialog":
                                send_message(chat_id, "Хорошо, если передумаешь — напиши /start 😊")
                                user_states.pop(chat_id, None)

                            elif data.startswith("interest_"):
                                interest = data.replace("interest_", "")
                                tg_id = user_states[chat_id]["tg_id"]
                                if interest == "other":
                                    send_message(chat_id, "Укажите свое интересующее направление:")
                                    user_states[chat_id]["state"] = "waiting_for_interest_other"
                                else:
                                    update_participant(tg_id, "interests", interest)
                                    # send_message(chat_id, "Спасибо! Все данные записаны. 🎉")
                                    # Начинаем квиз
                                    process_answer, quiz_state = start_quiz(chat_id, tg_id)
                                    waiting_for_quiz[chat_id] = (process_answer, quiz_state)
                                    user_states.pop(chat_id, None)
                            # elif data.startswith("d1_"):

                    elif "document" in update["message"]:
                        # chat_id = update["message"]["chat"]["id"]
                        tg_id = update["message"]["from"]["id"]
                        tg_nickname = update["message"]["from"].get("username", "None")
                        file_id = update["message"]["document"]["file_id"]

                        # Сохраняем файл и обновляем информацию о пользователе
                        try: 
                            save_resume(tg_id, tg_id, tg_nickname, file_id)
                        except Exception as e:
                            print(f"Ошибка при сохранении резюме: {e}")
                            send_message(chat_id, "Произошла ошибка при сохранении резюме. Пожалуйста, попробуйте ещё раз.")
                    elif any(key in update["message"] for key in ["photo", "video", "audio", "voice", "animation", "sticker", "location", "contact", "document"]):
                        chat_id = update["message"]["chat"]["id"]
                        tg_id = update["message"]["from"]["id"]
                        send_message(chat_id, "Пожалуйста, отправьте ваш резюме в виде файла.")
                    # Обработка текстовых сообщений
                    elif "message" in update:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"].get("text", "").strip()
                        if text == "/start":
                            init(chat_id, user_states)
                        elif text == "/count" and chat_id in admin_ids:
                            users_amount = count_users()
                            send_message(chat_id, f"Количество участников: {users_amount}")

                        elif "/winner" in text and chat_id in admin_ids:
                            try:
                                chat_id = update["message"]["chat"]["id"]
                                if text == "/winner":
                                    send_message(chat_id, "Не указан номер победителя")
                                else:
                                    counter = text.split()[1]
                                    winner_nickname, winner_chat_id, winner_name = get_winner(counter)
                                    send_message(f"{chat_id}", f"Победитель: {winner_name} (@{winner_nickname})")
                                    # send_message(f"{winner_chat_id}", f"Поздравляем! Вы победили! Ваш номер: {counter}")
                            except Exception as e:
                                print(f"Произошла ошибка: {e}")
                                chat_id = update["message"]["chat"]["id"]
                                user_states.pop(chat_id, None)
                        elif chat_id in user_states:
                            state_info = user_states[chat_id]
                            tg_id = state_info["tg_id"]
                            state = state_info["state"]

                            if state == "waiting_for_name":
                                update_participant(tg_id, "tg_user", text)
                                send_message(chat_id, "Укажи почту 📧")
                                state_info["state"] = "waiting_for_email"

                            elif state == "waiting_for_email":
                                update_participant(tg_id, "email", text)
                                send_message(chat_id, "Программу обучения 🎓")
                                state_info["state"] = "waiting_for_education"

                            elif state == "waiting_for_education":
                                update_participant(tg_id, "education", text)
                                send_message_with_button(chat_id, "Что интересно?", [
                                    {"text": "Проектный менеджмент", "action": "interest_project_management"},
                                    {"text": "Юриспруденция", "action": "interest_law"},
                                    {"text": "SMM", "action": "interest_smm"},
                                    {"text": "HR", "action": "interest_hr"},
                                    {"text": "Разработка ПО", "action": "interest_software"},
                                    {"text": "Другое", "action": "interest_other"}
                                ])
                                state_info["state"] = "waiting_for_interest"

                            elif state == "waiting_for_interest_other":
                                update_participant(tg_id, "interests", text)
                            elif chat_id in waiting_for_quiz:
                                process_answer = waiting_for_quiz[chat_id]
                                process_answer(data)
                                if current_question["index"] >= len(d1_questions):
                                    waiting_for_quiz.pop(chat_id)

                        else:
                            send_message(chat_id, "Я не знаю такой команды 😢")
                    else:
                        print(f"Произошла ошибка: {e}")
                        user_states.pop(chat_id, None)
            time.sleep(1)
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            user_states.pop(chat_id, None)

if __name__ == "__main__":
    main()
