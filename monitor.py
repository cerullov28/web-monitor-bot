import requests
import json
import os
import hashlib
import time
from datetime import datetime
from telegram import Bot
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# === CONFIG TELEGRAM ===
TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
bot = Bot(token=TOKEN)

# === DATA/ORA FORMATTATA ===
def now():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

# === HASH HTML ===
def page_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# === HEADERS ===
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9"
}

# === SITI DA MONITORARE ===
try:
    with open("sites.json", "r", encoding="utf-8") as f:
        sites = json.load(f)["sites"]
except Exception as e:
    print(f"[{now()}] Errore caricando sites.json: {e}")
    sites = []

# === STATO HASH E PDF ===
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
    stype = site.get("type", "html").lower()  # html o pdf
    keywords = [k.lower() for k in site.get("keywords", [])]

    # === ADISUR: usa sitemap XML ===
    if "adisurcampania.it" in url:
        sitemap_url = "https://www.adisurcampania.it/sitemap.xml"
        try:
            r = requests.get(sitemap_url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "xml")
            found_links = set()
            for loc in soup.find_all("loc"):
                link = loc.text.strip()
                # filtra solo link utili (PDF o notizie)
                if link.lower().endswith(".pdf") or "/notizie" in link.lower():
                    found_links.add(link)
        except Exception as e:
            print(f"[{now()}] Errore sitemap ADISUR: {e}")
            continue

        new_pdfs = found_links - known_pdfs
        for pdf in sorted(new_pdfs):
            filename = pdf.split("/")[-1]
            message = (
                f"📄 NUOVO PDF / AVVISO - {name}\n"
                f"📎 File: {filename}\n"
                f"🌐 Link: {pdf}\n"
                f"🕒 Data: {now()}"
            )
            try:
                bot.send_message(chat_id=CHAT_ID, text=message)
            except Exception as e:
                print(f"[{now()}] Errore Telegram: {e}")
            print(f"[{now()}] Notifica ADISUR inviata: {filename}")

        known_pdfs.update(found_links)
        continue  # skip normale HTML

    # === HTML GENERICO (UNICampania, ecc.) ===
    # --- RETRY + TIMEOUT LUNGO ---
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=90, allow_redirects=True)
            r.raise_for_status()
            content = r.text
            break
        except Exception as e:
            print(f"[{now()}] Tentativo {attempt+1} fallito per {url}: {e}")
            time.sleep(5)
    else:
        print(f"[{now()}] Errore definitivo su {url}, passo al prossimo sito")
        continue

    # --- PDF ---
    if stype == "pdf":
        soup = BeautifulSoup(content, "html.parser")
        found_pdfs = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ".pdf" in href.lower():
                full_url = urljoin(url, href)
                if keywords and not any(k in full_url.lower() for k in keywords):
                    continue
                found_pdfs.add(full_url)

        new_pdfs = found_pdfs - known_pdfs
        for pdf in sorted(new_pdfs):
