# 🕵️‍♂️ LeadScrapper

Einsteiger-Anleitung für „Dummy“-Nutzer – verständlich, Schritt für Schritt.

---

## 📋 Inhaltsverzeichnis

1. [🚀 Features](#-features)
2. [✅ Voraussetzungen](#-voraussetzungen)
3. [🔧 Installation](#-installation)
4. [⚙️ Konfiguration](#️-konfiguration)
5. [▶️ Anwendung starten](#️-anwendung-starten)
6. [🛠️ Nutzung](#️-nutzung)
   - [1. Scrapen](#1-scrapen)
   - [2. Historie](#2-historie)
   - [3. E-Mail-Dashboard](#3-e-mail-dashboard)
7. [📂 Projektstruktur](#-projektstruktur)
8. [🔒 Lizenz](#-lizenz)

---

## 🚀 Features

- **Seiten-Scraping**

  - Mehrere Seiten automatisch abfragen
  - Detail-Infos (Telefon, E-Mail, Adresse, PLZ, Ort, Homepage)
  - Proxy-Rotation über `valid_proxies.txt`

- **Live-Feedback**

  - Fortschrittsbalken & Logausgaben im Browser
  - Echtzeit-Zähler für gefundene Leads

- **CSV-Export**

  - Unicode (UTF-8-SIG) mit BOM
  - Automatisch optimierter Dateiname
    ```
    leads-{suchbegriff}-{stadt}-{YYYY-MM-DD}.csv
    ```

- **Such-Historie**

  - Protokollierung in `logs/search_history.csv`
  - Download & Detail-Ansicht jeder CSV

- **E-Mail-Dashboard**
  - TinyMCE WYSIWYG-Editor für Vorlagen
  - SMTP-Versand direkt aus der Web-App
  - Optionales Open-Pixel & Klick-Tracking

---

## ✅ Voraussetzungen

- **Python 3.12+**
- **pip** (Python-Paketmanager)

---

## 🔧 Installation

1. **Repo klonen**
   ```bash
   git clone https://github.com/RobertAlcor/lscrapper.git
   cd lscrapper
   Virtuelle Umgebung anlegen
   ```

bash
python3 -m venv venv

# Linux/macOS:

source venv/bin/activate

# Windows:

venv\Scripts\activate
Abhängigkeiten installieren

bash
pip install -r requirements.txt
(Optional) Proxies

valid_proxies.txt im Projekt-Root befüllen (je eine Adresse pro Zeile).

⚙️ Konfiguration
Lege im Projekt-Root eine Datei .env mit Platzhaltern (ohne echte Passwörter):

dotenv

# 🔒 Sicherheit

FLASK_SECRET=DeinGeheimerSessionKey

# 🌐 Flask

FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_ENV=development

# 🤖 Scraper

USER_AGENTS=["Mozilla/5.0","Safari/537.36"]
REQUEST_TIMEOUT=10

# ✉️ SMTP (E-Mail Versand)

SMTP_HOST=mail.example.com
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASSWORD=DeinSMTPPasswort
FLASK_SECRET: Zufälliger Schlüssel für Sessions/Flash-Meldungen.

USER_AGENTS: Liste von Browser-User-Agents.

REQUEST_TIMEOUT: Sekunden bis Timeout pro Anfrage.

SMTP\_\*: Zugangsdaten für Deinen Mailserver.

▶️ Anwendung starten
bash
export FLASK_APP=app.leadscrapper
export FLASK_ENV=development
flask run
Windows PowerShell:

powershell
$env:FLASK_APP = "app.leadscrapper"
$env:FLASK_ENV = "development"
flask run
→ Öffne im Browser: http://127.0.0.1:5000

🛠️ Nutzung

1. Scrapen
   URL und Seitenzahl eingeben.

Felder auswählen (Firma, Telefon, …).

Klick auf „Leads sammeln“.

Live-Fortschritt, Logs und Lead-Zähler beobachten.

CSV wird automatisch heruntergeladen und liegt in output/.

2. Historie
   Unter „Suchhistorie“ klickst Du auf eine CSV → Detail-Ansicht.

3. E-Mail-Dashboard
   Email-Dashboard oben rechts öffnen oder über Historie-Spalte.

PLZ-Filter zum Segmentieren nutzen.

Text im TinyMCE-Editor anpassen.

Vorschau ansehen.

Senden → direkt über SMTP.

📂 Projektstruktur

├── app/
│ ├── leadscrapper.py # Hauptrouten: Scrapen, CSV, History, E-Mail
│ ├── scraper.py # HTTP-Fetch mit Retry & Proxies
│ ├── utils.py # Pfade, History-Log, URL-Helper
│ ├── email_templates/ # Jinja2-Vorlagen für E-Mails
│ │ ├── first_contact.txt
│ │ ├── follow_up.txt
│ │ └── closing.txt
│ ├── templates/ # HTML-Templates
│ │ ├── base.html
│ │ ├── index.html
│ │ ├── history_detail.html
│ │ ├── email_dashboard.html
│ │ └── email_preview.html
│ └── static/
│ ├── script.js # Client: SSE, Logs, Download
│ └── styles.css # Eigene Styles (optional)
├── valid_proxies.txt # (Optional) Proxy-Liste
├── output/ # Generierte CSVs
├── logs/
│ ├── app.log # App-Log
│ └── search_history.csv # Suchhistorie
├── requirements.txt
├── README.md # Diese Datei
└── .env # Deine Konfiguration

🔒 Lizenz
© 2025 Robert Alchimowicz – Alle Rechte vorbehalten.
Diese Software ist ausschließlich für den persönlichen Gebrauch durch den Lizenzinhaber bestimmt.
Das Kopieren, Verbreiten oder Verändern ohne ausdrückliche Erlaubnis ist untersagt.
