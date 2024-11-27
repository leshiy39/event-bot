import os
import requests
from config import API_URL, TOKEN
from participants import update_participant
import time
from tg import send_message

def save_resume(chat_id, tg_id, tg_nickname, file_id):
    try:
        # Получаем информацию о файле
        file_info_url = API_URL + "getFile"
        file_info_response = requests.get(file_info_url, params={"file_id": file_id})
        file_info = file_info_response.json()

        if file_info.get("ok"):
            file_path = file_info["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"

            # Задаём путь для сохранения файла
            file_extension = file_path.split('.')[-1]
            resume_dir = "/app/resumes"
            os.makedirs(resume_dir, exist_ok=True)  # Создаём директорию, если её нет

            # Уникальное имя для файла
            resume_file_name = f"{tg_nickname}_{int(time.time())}.{file_extension}"
            resume_file_path = os.path.join(resume_dir, resume_file_name)
            resume_description_path = os.path.join(resume_dir, 'resume_urls.txt')

            with open(resume_description_path, 'a') as file:
                file.write(f'{tg_nickname} - {file_url}\n')

            # Скачиваем файл
            resume_file_response = requests.get(file_url)
            with open(resume_file_path, "wb") as f:
                f.write(resume_file_response.content)

            # Сохраняем путь к файлу в базе данных
            update_participant(tg_id, "resume", resume_file_path)

            send_message(chat_id, f"Вашe резюме успешно сохранено")

        else:
            send_message(chat_id, "Произошла ошибка при получении файла. Попробуйте снова.")

    except Exception as e:
        print(f"Ошибка при сохранении резюме: {e}")
        send_message(chat_id, "Произошла ошибка при обработке вашего файла. Попробуйте позже.")
