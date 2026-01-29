import requests
import json
import os
import hashlib
from datetime import datetime
from telegram import Bot
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# === CONFIG TELEGRAM ===
TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

bot = Bot(token=TOKEN)

# === FORMATTARE DATA/ORA ===
def now():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

# === FUNZIONE HASH HTML ===
def page_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# === HEADERS "UMANI" ===
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9"
}

# === CARICO CONFIG SITI ===
# Esempio sites.json:
# {
#   "sites": [
#       {"name": "ADISUR Avvisi", "url": "https://www.adisurcampania.it/avvisi", "type": "pdf"},
#       {"name": "Altro sito", "url": "https://www.altrosito.it/notizie", "type": "html"}
#   ]
# }
with open("sites.json", "r", encoding="utf-8") as f:
    sites = json.load(f)["sites"]

# === CARICO HASH E PDF NOTI ===
hashes_file = "hashes.json"
pdfs_file = "pdfs.json"

hashes = {}
if os.path.exists(hashes_file):
    try:
        with open(hashes_file, "r", encoding="utf-8") as f:
            hashes = json.load(f)
    except:
        hashes = {}

known_pdfs = set()
if os.path.exists(pdfs_file):
    try:
        with open(pdfs_file, "r", encoding="utf-8") as f:
            known_pdfs = set(json.load(f))
    except:
        known_pdfs = set()

# === CICLO PRINCIPALE ===
for site in sites:
    name = site.get("name", site.get("url"))
    url = site.get("url")
    stype = site.get("type", "html")  # html o pdf

    try:
        r = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        r.raise_for_status()
        content = r.text
    except Exception as e:
        print(f"[{now()}] Errore su {url}: {e}")
        continue

    # --- PDF ---
    if stype.lower() == "pdf":
        soup = BeautifulSoup(content, "html.parser")
        found_pdfs = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ".pdf" in href.lower():
                full_url = urljoin(url, href)
                found_pdfs.add(full_url)

        new_pdfs = found_pdfs - known_pdfs
        for pdf in sorted(new_pdfs):
            filename = pdf.split("/")[-1]
            message = (
                f"📄 NUOVO PDF - {name}\n\n"
                f"📎 File: {filename}\n"
                f"🌐 Link: {pdf}\n"
                f"🕒 Data: {now()}"
            )
            try:
                bot.send_message(chat_id=CHAT_ID, text=message)
            except Exception as e:
                print(f"[{now()}] Errore Telegram: {e}")
            print(f"[{now()}] Notifica PDF inviata: {filename}")

        known_pdfs.update(found_pdfs)

    # --- HTML ---
    elif stype.lower() == "html":
        current_hash = page_hash(content)
        if url not in hashes:
            hashes[url] = current_hash
            print(f"[{now()}] Inizializzato HTML: {url}")
            continue

        if hashes[url] != current_hash:
            message = (
                f"🔔 PAGINA HTML AGGIORNATA - {name}\n\n"
                f"🌐 URL: {url}\n"
                f"🕒 Data: {now()}"
            )
            try:
                bot.send_message(chat_id=CHAT_ID, text=message)
            except Exception as e:
                print(f"[{now()}] Errore Telegram: {e}")
            print(f"[{now()}] Notifica HTML inviata: {url}")
            hashes[url] = current_hash

# === SALVO HASH E PDF ===
with open(hashes_file, "w", encoding="utf-8") as f:
    json.dump(hashes, f, indent=2, ensure_ascii=False)

with open(pdfs_file, "w", encoding="utf-8") as f:
    json.dump(sorted(known_pdfs), f, indent=2, ensure_ascii=False)

print(f"[{now()}] Controllo completato")
