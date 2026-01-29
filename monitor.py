import requests
import json
import os
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# =====================
# CONFIG TELEGRAM (HTTP API)
# =====================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    }
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()

# =====================
# UTILS
# =====================
def now():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def page_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "it-IT,it;q=0.9"
}

# =====================
# SAFE REQUEST
# =====================
def safe_get(url, retries=3, timeout=40):
    for i in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            print(f"[{now()}] Tentativo {i} fallito per {url}: {e}")
    raise Exception("Errore definitivo")

# =====================
# LOAD SITES
# =====================
try:
    with open("sites.json", "r", encoding="utf-8") as f:
        sites = json.load(f)["sites"]
except Exception as e:
    print(f"[{now()}] Errore caricando sites.json: {e}")
    sites = []

# =====================
# LOAD STATE
# =====================
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

# =====================
# MAIN LOOP
# =====================
for site in sites:
    name = site.get("name", site["url"])
    url = site["url"]
    stype = site.get("type", "html").lower()
    keywords = [k.lower() for k in site.get("keywords", [])]

    try:
        r = safe_get(url)
        content = r.text
    except Exception:
        print(f"[{now()}] Errore definitivo su {url}, salto")
        continue

    # -----------------
    # PDF MONITOR
    # -----------------
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
            message = (
                f"📄 NUOVO PDF - {name}\n\n"
                f"📎 {pdf.split('/')[-1]}\n"
                f"🌐 {pdf}\n"
                f"🕒 {now()}"
            )
            try:
                send_telegram(message)
                print(f"[{now()}] PDF notificato: {pdf}")
            except Exception as e:
                print(f"[{now()}] Errore Telegram: {e}")

        known_pdfs.update(found_pdfs)

    # -----------------
    # HTML MONITOR
    # -----------------
    else:
        current_hash = page_hash(content)

        if url not in hashes:
            hashes[url] = current_hash
            print(f"[{now()}] Inizializzato HTML: {name} ({url})")
            continue

        if hashes[url] != current_hash:
            message = (
                f"🔔 PAGINA AGGIORNATA - {name}\n\n"
                f"🌐 {url}\n"
                f"🕒 {now()}"
            )
            try:
                send_telegram(message)
                print(f"[{now()}] HTML aggiornato: {url}")
            except Exception as e:
                print(f"[{now()}] Errore Telegram: {e}")

            hashes[url] = current_hash

# =====================
# SAVE STATE
# =====================
with open(hashes_file, "w", encoding="utf-8") as f:
    json.dump(hashes, f, indent=2, ensure_ascii=False)

with open(pdfs_file, "w", encoding="utf-8") as f:
    json.dump(sorted(known_pdfs), f, indent=2, ensure_ascii=False)

print(f"[{now()}] Controllo completato")
