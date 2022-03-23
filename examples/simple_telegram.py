import requests
from time import sleep

from settings import telegram_token, telegram_chatid

session = requests.Session()


def send_message(chat_id, message):
    for _ in range(3):
        try:
            requests.post(
                f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                data={"chat_id": chat_id, "text": message}, timeout=10
                )
            break
        except:
            print("Telegram sendMessage Failed, trying again")
        sleep(10)


def get_updates():
    resp = session.get(
        f"https://api.telegram.org/bot{telegram_token}/getUpdates", timeout=10)
    print(resp.json())
    return resp.json()


if __name__ == "__main__":
    send_message(telegram_chatid, "hello world")
    get_updates()
