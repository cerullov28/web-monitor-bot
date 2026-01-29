import requests
import json
import os
import hashlib
from datetime import datetime
from telegram import Bot
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# === TELEGRAM ===
TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
bot = Bot(token=TOKEN)

# === ORA ===
def now():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

# === HASH ===
def page_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# === HEADERS ===
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "it-IT,it;q=0.9"
}

# === CARICO SITI ===
try:
    with open("sites.json", "r", encoding="utf-8") as f:
        sites = json.load(f)["sites"]
except Exception as e:
    print(f"[{now()}] Errore caricando sites.json: {e}")
    sites = []

# === STATO ===
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

# === FUNZIONE REQUEST CON RETRY ===
def safe_get(url, retries=3, timeout=40):
    for i in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            print(f"[{now()}] Tentativo {i} fallito per {url}: {e}")
    raise Exception("Errore definitivo")

# === CICLO ===
for site in sites:
    name = site["name"]
    url = site["url"]
    stype = site["type"]
    keywords = [k.lower() for k in site.get("keywords", [])]

    try:
        r = safe_get(url)
        content = r.text
    except Exception as e:
        print(f"[{now()}] Errore definitivo su {url}, salto")
        continue

    # === PDF ===
    if stype == "pdf":
        soup = BeautifulSoup(content, "html.parser")
        found = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ".pdf" in href.lower():
                full = urljoin(url, href)
                if keywords and not any(k in full.lower() for k in keywords):
                    continue
                found.add(full)

        new_pdfs = found - known_pdfs

        for pdf in sorted(new_pdfs):
            msg = (
                f"📄 NUOVO PDF - {name}\n\n"
                f"📎 {pdf.split('/')[-1]}\n"
                f"🌐 {pdf}\n"
                f"🕒 {now()}"
            )
            bot.send_message(chat_id=CHAT_ID, text=msg)
            print(f"[{now()}] PDF notificato: {pdf}")

        known_pdfs.update(found)

    # === HTML ===
    else:
        h = page_hash(content)
        if url not in hashes:
            hashes[url] = h
            print(f"[{now()}] Inizializzato HTML: {name} ({url})")
            continue

        if hashes[url] != h:
            msg = (
                f"🔔 PAGINA AGGIORNATA - {name}\n\n"
                f"🌐 {url}\n"
                f"🕒 {now()}"
            )
            bot.send_message(chat_id=CHAT_ID, text=msg)
            print(f"[{now()}] HTML aggiornato: {url}")
            hashes[url] = h

# === SALVO ===
with open(hashes_file, "w", encoding="utf-8") as f:
    json.dump(hashes, f, indent=2)

with open(pdfs_file, "w", encoding="utf-8") as f:
    json.dump(sorted(known_pdfs), f, indent=2)

print(f"[{now()}] Controllo completato")
