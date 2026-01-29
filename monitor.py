import requests
import json
import hashlib
import os
from datetime import datetime
from telegram import Bot

# === CONFIG DA ENV (GitHub Secrets) ===
TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

bot = Bot(token=TOKEN)

# === FUNZIONE HASH CONTENUTO ===
def page_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# === DATA E ORA FORMATTATE ===
def now_str() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")

# === CARICO SITI ===
with open("sites.json", "r", encoding="utf-8") as f:
    sites = json.load(f)["sites"]

# === CARICO HASH PRECEDENTI (SE ESISTONO) ===
hashes = {}
if os.path.exists("hashes.json"):
    try:
        with open("hashes.json", "r", encoding="utf-8") as f:
            hashes = json.load(f)
    except Exception:
        hashes = {}

# === CICLO PRINCIPALE ===
for site in sites:
    url = site.get("url")
    name = site.get("name", url)

    try:
        response = requests.get(
            url,
            timeout=25,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; WebMonitorBot/1.0)"
            }
        )
        response.raise_for_status()
        content = response.text
    except Exception as e:
        # NON crasha mai: logga e passa oltre
        print(f"[{now_str()}] Errore su {url}: {e}")
        continue

    current_hash = page_hash(content)

    # Primo avvio: salva e NON notifica
    if url not in hashes:
        hashes[url] = current_hash
        print(f"[{now_str()}] Inizializzato: {url}")
        continue

    # Contenuto cambiato
    if hashes[url] != current_hash:
        message = (
            f"🔔 AGGIORNAMENTO RILEVATO\n\n"
            f"📌 Sito: {name}\n"
            f"🌐 URL: {url}\n"
            f"🕒 Data: {now_str()}"
        )

        try:
            bot.send_message(chat_id=CHAT_ID, text=message)
            print(f"[{now_str()}] Notifica inviata per {url}")
        except Exception as e:
            print(f"[{now_str()}] Errore Telegram: {e}")

        hashes[url] = current_hash

# === SALVO HASH AGGIORNATI ===
with open("hashes.json", "w", encoding="utf-8") as f:
    json.dump(hashes, f, indent=2, ensure_ascii=False)

print(f"[{now_str()}] Controllo completato")
