import os
import csv
from datetime import datetime
from dotenv import load_dotenv

# Pfade ermitteln
HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))

# .env laden
load_dotenv(os.path.join(ROOT, '.env'))

# Output- & Log-Verzeichnisse
OUTPUT_DIR   = os.path.join(HERE, 'output')
LOG_DIR      = os.path.join(HERE, 'logs')
HISTORY_FILE = os.path.join(LOG_DIR, 'search_history.csv')

def init_history():
    """Legt Ordner und CSV mit Header an, falls noch nicht vorhanden."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp','Website','Pages','Fields','Filename'])

def log_search(website, pages, fields, filename):
    """Schreibt eine Historien-Zeile in die CSV."""
    with open(HISTORY_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(timespec='seconds'),
            website,
            pages,
            ';'.join(fields),
            filename
        ])

def make_absolute(href: str) -> str:
    """Macht relative Herold-Links absolut."""
    if href.startswith('/'):
        return 'https://www.herold.at' + href
    return href
