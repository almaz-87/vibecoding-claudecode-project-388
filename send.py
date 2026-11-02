"""Отправка сообщения в Telegram.

Использование: python send.py "текст"
Токен и chat id берутся из файла .env рядом со скриптом:
  TELEGRAM_BOT_TOKEN=...
  TELEGRAM_CHAT_ID=...
Только стандартная библиотека Python, без внешних зависимостей.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent / ".env"
MAX_LEN = 4096  # лимит Telegram на длину одного сообщения


def load_env(path):
    env = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def split_text(text):
    """Делит длинный текст на части не длиннее MAX_LEN, по границам строк."""
    chunks, current = [], ""
    for line in text.splitlines(keepends=True):
        while len(line) > MAX_LEN:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:MAX_LEN])
            line = line[MAX_LEN:]
        if len(current) + len(line) > MAX_LEN:
            chunks.append(current)
            current = ""
        current += line
    if current:
        chunks.append(current)
    return chunks


def send(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode()
    with urllib.request.urlopen(url, data=data, timeout=30) as resp:
        return json.load(resp)


def main():
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        sys.exit('Использование: python send.py "текст"')
    if not ENV_PATH.exists():
        sys.exit(f"Нет файла {ENV_PATH}")
    env = load_env(ENV_PATH)
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        sys.exit("В .env не заданы TELEGRAM_BOT_TOKEN и/или TELEGRAM_CHAT_ID")

    for chunk in split_text(sys.argv[1]):
        try:
            result = send(token, chat_id, chunk)
        except urllib.error.HTTPError as e:
            # Тело ответа Telegram объясняет причину; токен в него не попадает.
            sys.exit(f"Ошибка Telegram {e.code}: {e.read().decode(errors='replace')}")
        except urllib.error.URLError as e:
            sys.exit(f"Не удалось подключиться к Telegram: {e.reason}")
        if not result.get("ok"):
            sys.exit(f"Ошибка Telegram: {result}")
        print(f"Отправлено, message_id={result['result']['message_id']}")


if __name__ == "__main__":
    main()
