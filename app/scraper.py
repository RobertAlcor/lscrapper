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
    user_agents = eval(os.getenv('USER_AGENTS', '[]'))
    timeout = int(os.getenv('REQUEST_TIMEOUT', '10'))

    leads_accum = []

    def generate():
        total = pages
        for p in range(1, total + 1):
            url = f"{site}?page={p}"
            logger.info(f"Scrape Seite {p}: {url}")
            resp = _fetch_url(
                url,
                user_agents,
                timeout=timeout,
                max_retries=3
            )
            if not resp:
                yield f"event: progress
data: {json.dumps({'page': p, 'total': total, 'found': 0})}

"
                continue
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            cards = soup.select('li.location-search-result')
            found = len(cards)
            # Fortschritt senden (Seitenbasiert)
            yield f"event: progress
data: {json.dumps({'page': p, 'total': total, 'found': found})}

"

            for card in cards:
                lead = {}
                # Firma
                el = card.select_one('span[itemprop="name"]') or card.select_one('h2')
                lead['Firma'] = el.get_text(strip=True) if el else '-'

                # Detailseite nur holen, falls weitere Felder benötigt
                dsoup = None
                if set(fields) & {'telefon','email','adresse','plz','ortname','homepage'}:
                    a = card.select_one("a[href*='/gelbe-seiten/']")
                    if a and (href := a.get('href')):
                        from .scraper import _fetch_url_detail
                        full_url = make_absolute(href)
                        dr = _fetch_url_detail(
                            full_url, user_agents,
                            timeout=timeout, max_retries=3
                        )
                        if dr:
                            dsoup = BeautifulSoup(dr.text, 'html.parser')

                # Telefon
                if 'telefon' in fields:
                    t = dsoup.select_one("a[href^='tel:' ]") if dsoup else None
                    lead['Telefon'] = t.get_text(strip=True) if t else '-'
                # Email
                if 'email' in fields:
                    m = dsoup.select_one("a[href^='mailto:' ]") if dsoup else None
                    lead['Email'] = m.get('href').split('mailto:')[1] if m else '-'
                # Adresse
                if 'adresse' in fields:
                    st = dsoup.select_one("meta[itemprop='streetAddress']") if dsoup else None
                    lead['Adresse'] = st.get('content') if st else '-'
                # PLZ
                if 'plz' in fields:
                    pc = dsoup.select_one("meta[itemprop='postalCode']") if dsoup else None
                    lead['PLZ'] = pc.get('content') if pc else '-'
                # Ort
                if 'ortname' in fields:
                    rg = dsoup.select_one("meta[itemprop='addressRegion']") if dsoup else None
                    lead['Ort'] = rg.get('content') if rg else '-'
                # Homepage
                if 'homepage' in fields:
                    h = dsoup.select_one("a[href^='http']:not([href*='herold.at'])") if dsoup else None
                    if h and h.get('href'):
                        url_h = h.get('href')
                        lead['Homepage'] = f'=HYPERLINK("{url_h}", "Website")'
                    else:
                        lead['Homepage'] = '-'

                leads_accum.append(lead)
                yield f"event: lead
data: {json.dumps(lead)}

"

        # CSV speichern (nach allen Seiten)
        now = datetime.now()
        parsed_url = urlparse(site)
        parts = parsed_url.path.strip('/').split('/')
        such = unquote(parts[2] if len(parts) > 2 else 'lead')
        city = unquote(parts[1] if len(parts) > 1 else 'wien')
        safe = lambda s: s.lower().replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('ß','ss').replace(' ', '-')
        filename = f"leads-{safe(such)}-{safe(city)}-{now.strftime('%Y-%m-%d')}.csv"
        filepath = os.path.join(OUTPUT_DIR, filename)
        try:
            cols = ['Firma','Telefon','Email','Adresse','PLZ','Ort','Homepage']
            df = pd.DataFrame(leads_accum)
            for c in cols:
                if c not in df.columns:
                    df[c] = '-'
            df = df[cols]
            df.to_csv(filepath, index=False, sep=';')
            logger.info(f"CSV gespeichert: {filename}")
            log_search(site, pages, fields, filename)
        except Exception as e:
            logger.error(f"Fehler beim Speichern CSV: {e}")

        # Fertig-Event
        yield f"event: done
data: {json.dumps({'filename': filename})}

"

    headers = {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
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
if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    try:
        webbrowser.open(f"http://{host}:{port}")
    except Exception:
        pass
    app.run(host=host, port=port)
