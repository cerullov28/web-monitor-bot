import requests
import json
import hashlib
import os
from telegram import Bot

TOKEN = os.environ["8208166634:AAG_QnIMtIdbhqqakl68Iv6g4PIxwz3QKJA"]
CHAT_ID = os.environ["881859415"]

bot = Bot(token=TOKEN)

def page_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

with open("sites.json") as f:
    sites = json.load(f)["sites"]

hashes = {}
if os.path.exists("hashes.json"):
    with open("hashes.json") as f:
        hashes = json.load(f)

for site in sites:
    r = requests.get(site["url"], timeout=20)
    current = page_hash(r.text)

    if site["url"] not in hashes:
        hashes[site["url"]] = current
        continue

    if hashes[site["url"]] != current:
        bot.send_message(
            chat_id=CHAT_ID,
            text=f"🔔 Pagina aggiornata!\n{site['name']}\n{site['url']}"
        )
        hashes[site["url"]] = current

with open("hashes.json", "w") as f:
    json.dump(hashes, f)
