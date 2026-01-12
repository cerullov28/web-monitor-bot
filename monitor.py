import requests
import json
import hashlib
import os
from telegram import Bot

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

bot = Bot(token=TOKEN)

def page_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# --- carico siti ---
with open("sites.json") as f:
    sites = json.load(f)["sites"]

# --- carico hash precedenti ---
hashes = {}
if os.path.exists("hashes.json"):
    with open("hashes.json") as f:
        hashes = json.load(f)

# --- ciclo principale sui siti ---
for site in sites:
    try:
        r = requests.get(
            site["url"],
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        r.raise_for_status()
        content = r.text
    except Exception as e:
        print(f"Errore su {site['url']}: {e}")
        continue

    current = page_hash(content)

    if site["url"] not in hashes:
        hashes[site["url"]] = current
        continue

    if hashes[site["url"]] != current:
        bot.send_message(
            chat_id=CHAT_ID,
            text=f"🔔 Pagina aggiornata!\n{site['name']}\n{site['url']}"
        )
        hashes[site["url"]] = current

# --- salvo hash aggiornati ---
with open("hashes.json", "w") as f:
    json.dump(hashes, f)
