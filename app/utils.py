import os
import csv
import logging
from datetime import datetime
from dotenv import load_dotenv

HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
load_dotenv(os.path.join(ROOT, '.env'))

OUTPUT_DIR   = os.path.join(ROOT, 'output')
LOG_DIR      = os.path.join(ROOT, 'logs')
HISTORY_FILE = os.path.join(LOG_DIR, 'search_history.csv')

def init_history() -> None:
    """Legt OUTPUT_DIR, LOG_DIR und History-CSV (mit BOM) an, falls nicht vorhanden."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        # 'utf-8-sig' schreibt einen BOM an den Anfang der Datei
        with open(HISTORY_FILE, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp','Website','Pages','Fields','Filename'])
        logging.info(f"History-Datei angelegt: {HISTORY_FILE}")

def log_search(
    website: str,
    pages: int,
    fields: list[str],
    filename: str
) -> None:
    """Schreibt eine neue Zeile in die History-CSV (UTF-8-SIG ohne weitere BOM)."""
    # Beim Anhängen schreibt Python den BOM nicht erneut
    with open(HISTORY_FILE, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(timespec='seconds'),
            website,
            pages,
            ';'.join(fields),
            filename
        ])

def make_absolute(href: str) -> str:
    """Korrigiert relative Herold-Links in absolute URLs."""
    if href.startswith('/'):
        return 'https://www.herold.at' + href
    return href
