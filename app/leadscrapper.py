import os
import json
import csv
import logging
import logging.handlers
import webbrowser
from urllib.parse import urlparse, unquote
from datetime import datetime
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request,
    send_file, Response, stream_with_context,
    flash, redirect, url_for
)
from flask_mail import Mail, Message
from jinja2 import Environment, FileSystemLoader
import pandas as pd

from .utils import (
    OUTPUT_DIR, LOG_DIR,
    init_history, log_search, make_absolute
)
from .scraper import _fetch_url, _fetch_url_detail

# --- 1) .env laden -----------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT     = os.path.abspath(os.path.join(BASE_DIR, '..'))
load_dotenv(os.path.join(ROOT, '.env'))

# --- 2) Flask-App & Logging --------------------------
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'),
)
app.secret_key = os.getenv('FLASK_SECRET')

os.makedirs(LOG_DIR, exist_ok=True)
handler = logging.handlers.RotatingFileHandler(
    os.path.join(LOG_DIR, 'app.log'),
    maxBytes=1_000_000, backupCount=3, encoding='utf-8'
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s %(name)s: %(message)s'
))
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# --- 3) Context-Processor für Email-Dashboard-Dropdown ---
@app.context_processor
def inject_email_dashboards():
    hist_file = os.path.join(LOG_DIR, 'search_history.csv')
    filenames = []
    if os.path.exists(hist_file):
        with open(hist_file, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            raw = [r['Filename'] for r in reader]
            # nur eindeutige, neueste zuerst
            filenames = list(dict.fromkeys(raw[::-1]))
    return dict(email_dashboard_files=filenames)

# --- 4) Mail-Konfiguration ---------------------------
app.config.update(
    MAIL_SERVER   = os.getenv('SMTP_HOST'),
    MAIL_PORT     = int(os.getenv('SMTP_PORT', '587')),
    MAIL_USERNAME = os.getenv('SMTP_USER'),
    MAIL_PASSWORD = os.getenv('SMTP_PASSWORD'),
    MAIL_USE_TLS  = False,
    MAIL_USE_SSL  = True
)
mail = Mail(app)

# --- 5) History & Output vorbereiten -----------------
os.makedirs(OUTPUT_DIR, exist_ok=True)
init_history()

# --- Jinja2 für Email-Templates ----------------------
EMAIL_TPL_DIR = os.path.join(BASE_DIR, 'email_templates')
j2env = Environment(loader=FileSystemLoader(EMAIL_TPL_DIR))
TEMPLATES = {
    'Erstansprache': 'first_contact.txt',
    'Follow-Up':     'follow_up.txt',
    'Abschluss':     'closing.txt'
}

# --- 5a) Startseite mit Search-History ---------------
@app.route('/', methods=['GET'])
def index():
    history = []
    hist_file = os.path.join(LOG_DIR, 'search_history.csv')
    try:
        with open(hist_file, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            history = list(reader)[::-1]
    except FileNotFoundError:
        logger.warning("History-Datei nicht gefunden, wird neu angelegt.")
    return render_template('index.html', history=history)

# --- 5b) CSV-Download ---------------------------------
@app.route('/download', methods=['POST'])
def download():
    data     = request.get_json()
    filename = data.get('filename')
    path     = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return {'error': 'Datei nicht gefunden.'}, 404
    return send_file(path, as_attachment=True)

# --- 5c) Detail-Ansicht gespeicherter CSV ------------
@app.route('/history/<filename>', methods=['GET'])
def history_detail(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        flash('Datei nicht gefunden.', 'warning')
        return redirect(url_for('index'))
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        cols    = reader.fieldnames or []
        records = list(reader)
    return render_template(
        'history_detail.html',
        filename=filename,
        cols=cols,
        records=records
    )

# --- 5d) Live-Scraping mit SSE -----------------------
@app.route('/scrape-stream', methods=['GET'])
def scrape_stream():
    site   = request.args.get('site','').strip()
    pages  = int(request.args.get('pages','1'))
    fields = request.args.get('fields','').split(',')

    def generate():
        leads_accum = []
        for p in range(1, pages+1):
            url = f"{site}?page={p}"
            logger.info(f"Seite {p}: {url}")
            resp = _fetch_url(
                url,
                eval(os.getenv('USER_AGENTS','[]')),
                timeout=int(os.getenv('REQUEST_TIMEOUT','10')),
                max_retries=3
            )
            cards = []
            if resp:
                from bs4 import BeautifulSoup
                soup  = BeautifulSoup(resp.text, 'html.parser')
                cards = soup.select('li.location-search-result')
            found = len(cards)
            yield f"event: progress\ndata: {json.dumps({'page':p,'total':pages,'found':found})}\n\n"

            for card in cards:
                lead = dict.fromkeys(['Firma','Telefon','Email','Adresse','PLZ','Ort','Homepage'],'-')
                el   = card.select_one('span[itemprop="name"]') or card.select_one('h2')
                lead['Firma'] = el.get_text(strip=True) if el else '-'

                dsoup = None
                if set(fields) & {'telefon','email','adresse','plz','ortname','homepage'}:
                    a = card.select_one("a[href*='/gelbe-seiten/']")
                    if a and (href:=a.get('href')):
                        full = make_absolute(href)
                        dr   = _fetch_url_detail(
                            full,
                            eval(os.getenv('USER_AGENTS','[]')),
                            timeout=int(os.getenv('REQUEST_TIMEOUT','10')),
                            max_retries=3
                        )
                        if dr:
                            from bs4 import BeautifulSoup
                            dsoup = BeautifulSoup(dr.text, 'html.parser')

                if dsoup:
                    if 'telefon'  in fields:
                        t = dsoup.select_one("a[href^='tel:']")
                        lead['Telefon'] = t.get_text(strip=True) if t else '-'
                    if 'email'    in fields:
                        m = dsoup.select_one("a[href^='mailto:']")
                        lead['Email'] = m.get('href').split('mailto:')[1] if m else '-'
                    if 'adresse'  in fields:
                        st = dsoup.select_one("meta[itemprop='streetAddress']")
                        lead['Adresse'] = st.get('content') if st else '-'
                    if 'plz'      in fields:
                        pc = dsoup.select_one("meta[itemprop='postalCode']")
                        lead['PLZ'] = pc.get('content') if pc else '-'
                    if 'ortname'  in fields:
                        rg = dsoup.select_one("meta[itemprop='addressRegion']")
                        lead['Ort'] = rg.get('content') if rg else '-'
                    if 'homepage' in fields:
                        h = dsoup.select_one("a[href^='http']:not([href*='herold.at'])")
                        if h and (u:=h.get('href')):
                            lead['Homepage'] = f'=HYPERLINK(\"{u}\",\"Website\")'

                leads_accum.append(lead)
                yield f"event: lead\ndata: {json.dumps(lead)}\n\n"

        # CSV erst nach Abschluss aller Seiten schreiben
        now    = datetime.now()
        parsed = urlparse(site)
        parts  = parsed.path.strip('/').split('/')
        term   = unquote(parts[2] if len(parts)>2 else 'leads')
        city   = unquote(parts[1] if len(parts)>1 else 'wien')
        safe   = lambda s: (
            s.lower()
             .replace('ä','ae').replace('ö','oe')
             .replace('ü','ue').replace('ß','ss')
             .replace(' ','-')
        )
        fn    = f"leads-{safe(term)}-{safe(city)}-{now.strftime('%Y-%m-%d')}.csv"
        out   = os.path.join(OUTPUT_DIR, fn)
        try:
            cols = ['Firma','Telefon','Email','Adresse','PLZ','Ort','Homepage']
            df   = pd.DataFrame(leads_accum)
            for c in cols:
                if c not in df.columns:
                    df[c] = '-'
            df = df[cols]
            df.to_csv(out, index=False, sep=';', encoding='utf-8-sig')
            logger.info(f"CSV gespeichert: {fn}")
            log_search(site, pages, fields, fn)
        except Exception as e:
            logger.error(f"Fehler beim Speichern der CSV: {e}")

        yield f"event: done\ndata: {json.dumps({'filename': fn})}\n\n"

    return Response(
        stream_with_context(generate()),
        headers={
            'Content-Type':'text/event-stream',
            'Cache-Control':'no-cache',
            'Connection':'keep-alive'
        }
    )

# --- 5e) E-Mail versenden via SMTP -------------------
@app.route('/send-email', methods=['POST'])
def send_email():
    data    = request.get_json()
    to      = data['to']
    subject = data['subject']
    body    = data['body']
    msg = Message(
        subject,
        recipients=[to],
        html=body,
        sender=app.config['MAIL_USERNAME']
    )
    try:
        mail.send(msg)
        return {'status':'ok'}, 200
    except Exception as e:
        logger.error(f"SMTP-Fehler: {e}")
        return {'status':'error','message':str(e)}, 500

# --- 6a) Email-Dashboard -----------------------------
@app.route('/email-dashboard/<filename>', methods=['GET'])
def email_dashboard(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        flash('Datei nicht gefunden.', 'warning')
        return redirect(url_for('index'))
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        leads  = list(reader)
    return render_template('email_dashboard.html',
                           filename=filename,
                           leads=leads,
                           template_names=list(TEMPLATES.keys()))

# --- 6b) Email-Preview ------------------------------
@app.route('/email-preview/<filename>/<int:idx>/<tpl>', methods=['GET'])
def email_preview(filename, idx, tpl):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        flash('Datei nicht gefunden.', 'warning')
        return redirect(url_for('index'))
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        leads  = list(reader)
    if idx<0 or idx>=len(leads) or tpl not in TEMPLATES:
        flash('Ungültige Anfrage.', 'warning')
        return redirect(url_for('email_dashboard', filename=filename))

    lead     = leads[idx]
    template = j2env.get_template(TEMPLATES[tpl])
    body     = template.render(
        contact_name     = lead.get('Robert Alchimowicz'),
        company          = lead.get('Firma',''),
        service          = "Professionelle Webdesign- und SEO-Lösungen",
        your_name        = "Robert Alchimowicz",
        your_company     = "EliteSites | Webdesign-Alcor Group",
        industry         = "Webdesign & SEO",
        city             = lead.get('Ort',''),
        benefit          = "Ihre Anfragen um 20 % steigern",
        booking_link     = "https://calendly.com/elitesites",
        unsubscribe_link = "mailto:office@elitesites.at",
        contact_id       = f"{filename}-{idx}"
    )
    subject = body.splitlines()[0].replace("Betreff: ","")
    return render_template('email_preview.html',
                           filename=filename,
                           idx=idx,
                           tpl=tpl,
                           subject=subject,
                           body=body)

# --- 7a) Tracking-Pixel (Open) -----------------------
@app.route('/track/open/<contact_id>')
def track_open(contact_id):
    gif = (b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00'
           b'\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00'
           b'\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02'
           b'\x44\x01\x00\x3b')
    return Response(gif, mimetype='image/gif')

# --- 7b) Tracking-Link (Click) -----------------------
@app.route('/track/click/<contact_id>')
def track_click(contact_id):
    target = request.args.get('url','/')
    return redirect(target)

# --- 8) Server starten -------------------------------
if __name__ == '__main__':
    host = os.getenv('FLASK_HOST','127.0.0.1')
    port = int(os.getenv('FLASK_PORT','5000'))
    # Browser nur einmal öffnen, nicht im Reloader
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        try: webbrowser.open(f"http://{host}:{port}")
        except: pass
    app.run(host=host, port=port, debug=True)
