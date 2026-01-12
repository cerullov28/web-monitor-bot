import requests
import json
import hashlib
import os
from telegram import Bot

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

bot = Bot(token=TOKEN)

def get_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

with open("sites.json") as f:
    sites = json.load(f)["sites"]

hashes = {}
if os.path.exists("hashes.json"):
    with open("hashes.json") as f:
        hashes = json.load(f)

updated = False

for site in sites:
   try:
    r = requests.get(
        site["url"],
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    r.raise_for_status()
except Exception as e:
    print(f"Errore su {site['url']}: {e}")
    continue
    current_hash = get_hash(r.text)

    if site["url"] not in hashes:
        hashes[site["url"]] = current_hash
        continue

    if hashes[site["url"]] != current_hash:
        bot.send_message(
            chat_id=CHAT_ID,
            text=f"🔔 Aggiornamento rilevato!\n{site['name']}\n{site['url']}"
        )
        hashes[site["url"]] = current_hash
        updated = True

with open("hashes.json", "w") as f:
    json.dump(hashes, f)

