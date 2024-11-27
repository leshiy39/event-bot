from config import API_URL
import requests
import json
from tenacity import retry, stop_after_attempt, wait_exponential
from requests.exceptions import RequestException

@retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=10))
def get_updates(offset):
    url = f"{API_URL}getUpdates?timeout=100&offset={offset}"
    response = requests.get(url)
    response.raise_for_status()  # Поднимет исключение, если код ответа != 200
    return response.json()

def send_message_with_button(chat_id, text, keyboard_array):
    url = API_URL + "sendMessage"
    reply_markup = {
        "inline_keyboard": [
            [{"text": btn['text'], "callback_data": btn['action']}] for btn in keyboard_array
        ]
    }
    params = {"chat_id": chat_id, "text": text, "reply_markup": json.dumps(reply_markup)}
    response = requests.post(url, json=params)
    if not response.ok:
        print(f"Error sending message with button: {response.text}")

def send_message(chat_id, text, reply_markup=None):
    url = API_URL + "sendMessage"
    params = {"chat_id": chat_id, "text": text}
    if reply_markup:
        params['reply_markup'] = json.dumps(reply_markup)
    response = requests.post(url, json=params)
    if not response.ok:
        print(f"Error sending message: {response.text}")

def send_blockquoute(chat_id, text, reply_markup=None):
    url = API_URL + "sendMessage"
    params = {"chat_id": chat_id, "text": f"<blockquote>{text}</blockquote>", 'parse_mode': 'HTML'}
    if reply_markup:
        params['reply_markup'] = json.dumps(reply_markup)
    response = requests.post(url, json=params)
    if not response.ok:
        print(f"Error sending message: {response.text}")
