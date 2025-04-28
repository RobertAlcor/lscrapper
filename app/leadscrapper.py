# app/leadscrapper.py
import os
import time
import logging
import csv
from datetime import datetime
from dotenv import load_dotenv

from flask import (
    Flask, render_template, request,
    send_file, redirect, url_for, flash
)
import pandas as pd

from .utils import OUTPUT_DIR, LOG_DIR, HISTORY_FILE
from .utils import init_history, log_search
from .scraper import scrape_bs4

# -------------------------------------------------------------------
# 1) .env laden
# -------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT     = os.path.abspath(os.path.join(BASE_DIR, '..'))
load_dotenv(os.path.join(ROOT, '.env'))

# -------------------------------------------------------------------
# 2) App & Logging
# -------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.secret_key = os.getenv('FLASK_SECRET', 'dev_secret')

# -------------------------------------------------------------------
# 3) History & Output vorbereiten
# -------------------------------------------------------------------
init_history()

# -------------------------------------------------------------------
# 4) Routen
# -------------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        site   = request.form['website'].strip()
        pages  = int(request.form['seiten'])
        fields = request.form.getlist('felder')

        # Scraping
        leads = scrape_bs4(
            base_url=site,
            fields=fields,
            pages=pages,
            user_agents=eval(os.getenv('USER_AGENTS', '[]'))
        )
        if not leads:
            flash('❌ Keine Leads gefunden!', 'danger')
            return redirect(url_for('index'))

        # CSV erzeugen
        ts       = int(time.time())
        filename = f"leads_{ts}.csv"
        filepath = os.path.join(OUTPUT_DIR, filename)
        pd.DataFrame(leads).to_csv(filepath, index=False, sep=';')

        # in History protokollieren
        log_search(site, pages, fields, filename)

        # Dateidownload
        return send_file(filepath, as_attachment=True)

    # GET: Such-History auslesen (neueste zuerst)
    with open(HISTORY_FILE, newline='', encoding='utf-8') as f:
        reader  = csv.DictReader(f)
        history = list(reader)[::-1]

    return render_template('index.html', history=history)


@app.route('/history/<filename>')
def history_detail(filename):
    """Detail-Ansicht einer gespeicherten CSV."""
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        flash('Datei nicht gefunden.', 'warning')
        return redirect(url_for('index'))

    df   = pd.read_csv(path, sep=';')
    cols = list(df.columns)
    records = df.to_dict(orient='records')
    return render_template(
        'history_detail.html',
        filename=filename,
        cols=cols,
        records=records
    )


if __name__ == '__main__':
    app.run(debug=True)
