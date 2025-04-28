import os
import time
import json
import logging
import logging.handlers
import webbrowser
from urllib.parse import urlparse, unquote
from datetime import datetime
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request,
    send_file, Response, stream_with_context
)
import pandas as pd

from .utils import OUTPUT_DIR, LOG_DIR, init_history, log_search
from .scraper import _fetch_url

# .env laden
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
load_dotenv(os.path.join(ROOT, '.env'))

# App & Logging
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, 'app.log')
handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'),
    static_url_path='/static'
)
app.secret_key = os.getenv('FLASK_SECRET', 'dev_secret')

# History & Output
os.makedirs(OUTPUT_DIR, exist_ok=True)
init_history()

# Index-Route
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# CSV Download-Route
@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    filename = data.get('filename')
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        return {'error': 'Datei nicht gefunden.'}, 404
    return send_file(filepath, as_attachment=True)

# Scrape-Stream Route
@app.route('/scrape-stream', methods=['GET'])
def scrape_stream():
    site = request.args.get('site', '').strip()
    pages = int(request.args.get('pages', 1))
    fields = request.args.get('fields', '').split(',')

    leads_accum = []

    def generate():
        total = pages

        for p in range(1, total + 1):
            url = f"{site}?page={p}"
            logger.info(f"Scrape Seite {p}: {url}")
            resp = _fetch_url(
                url,
                eval(os.getenv('USER_AGENTS', '[]')),
                timeout=int(os.getenv('REQUEST_TIMEOUT', '10')),
                max_retries=3
            )
            cards = []
            if resp:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')
                cards = soup.select('li.location-search-result')

            # Fortschritt senden
            yield f"event: progress\ndata: {json.dumps({'page': p, 'total': total, 'found': len(cards)})}\n\n"

            for card in cards:
                lead = {}
                el = card.select_one('span[itemprop=\"name\"]') or card.select_one('h2')
                lead['Firma'] = el.get_text(strip=True) if el else '-'
                leads_accum.append(lead)
                yield f"event: lead\ndata: {json.dumps(lead)}\n\n"

        # Jetzt, nach allen Seiten: CSV erstellen
        now = datetime.now()
        parsed_url = urlparse(site)
        path_parts = parsed_url.path.strip('/').split('/')
        suchbegriff = path_parts[2] if len(path_parts) > 2 else "leads"
        stadt = path_parts[1] if len(path_parts) > 1 else "wien"
        suchbegriff = unquote(suchbegriff).lower().replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss').replace(' ', '-')
        stadt = unquote(stadt).lower().replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss').replace(' ', '-')

        filename = f"leads-{suchbegriff}-{stadt}-{now.strftime('%Y-%m-%d')}.csv"
        filepath = os.path.join(OUTPUT_DIR, filename)

        try:
            columns_order = ['Firma', 'Telefon', 'Email', 'Adresse', 'PLZ', 'Ort', 'Homepage']
            df = pd.DataFrame(leads_accum)
            for col in columns_order:
                if col not in df.columns:
                    df[col] = "-"
            df = df[columns_order]
            df.to_csv(filepath, index=False, sep=';')
            logger.info(f"CSV gespeichert: {filename}")
            log_search(site, pages, fields, filename)
        except Exception as e:
            logger.error(f"Fehler beim Speichern der CSV: {e}")

        # Datei ist fertig => Event senden
        yield f"event: done\ndata: {json.dumps({'filename': filename})}\n\n"

    headers = {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
    }
    return Response(stream_with_context(generate()), headers=headers)

# App-Start
if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    try:
        webbrowser.open(f"http://{host}:{port}")
    except Exception:
        pass
    app.run(host=host, port=port)
