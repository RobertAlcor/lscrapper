# LeadScrapper

Ein moderner Web-Scraper und Dashboard für die **Herold.at Gelbe Seiten**, umgesetzt als Flask-Web-App mit Download-Funktion und Windows-Installer.

---

## 📝 Features

- **Flexibles Scraping**: Wähle aus, welche Felder (Firma, Telefon, E-Mail, Adresse, PLZ, Ort) du sammeln möchtest.
- **Mehrseiten-Support**: Rufe automatisch mehrere Ergebnis-Seiten ab.
- **Search-History**: Jede Suchanfrage wird protokolliert und im Dashboard als Verlauf angezeigt.
- **CSV-Export**: Ergebnisse als CSV-Datei herunterladen.
- **Windows-Installer**: Erstelle eine portable EXE plus Setup mit PyInstaller & Inno Setup.

---

## 🚀 Schnellstart

### 1. Repository klonen

```bash
git clone https://github.com/RobertAlcor/LeadScrapper_Alcor.git
cd LeadScrapper_Alcor
2. Abhängigkeiten installieren
bash
Kopieren
Bearbeiten
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
3. Environment-Variablen
Kopiere die Beispiel-Datei:

bash
Kopieren
Bearbeiten
copy .env.example .env
Öffne .env und fülle die Werte aus:

dotenv
Kopieren
Bearbeiten
FLASK_SECRET=dein_geheimer_schluessel
APP_VERSION=1.0.0
USER_AGENTS=["Mozilla/...","Mozilla/...","Mozilla/..."]
GITHUB_REPO=RobertAlcor/LeadScrapper
4. App starten
bash
Kopieren
Bearbeiten
# Windows PowerShell
$env:FLASK_APP = "app.leadscrapper"
$env:FLASK_ENV = "development"
flask run

# macOS/Linux
export FLASK_APP=app.leadscrapper
export FLASK_ENV=development
flask run
Dann im Browser öffnen: http://127.0.0.1:5000

🏗️ Projekt-Struktur
csharp
Kopieren
Bearbeiten
LeadScrapper_Alcor/            # Projekt-Root
├── .env                      # Lokale Konfiguration (nicht ins Git!)
├── .env.example              # Vorlage für .env
├── README.md                 # Diese Datei
├── requirements.txt          # Python-Abhängigkeiten
├── install.bat               # Build- & Installer-Script
├── leadscrapper.spec         # PyInstaller-Spec (optional)
├── Installer/                # Inno-Setup Dateien
│   ├── LeadScrapperInstaller.iss
│   └── scraper.ico
└── app/                      # Haupt-App
    ├── __init__.py           # macht app/ zum Python-Paket
    ├── leadscrapper.py       # Flask-Entry-Point & Routing
    ├── scraper.py            # Scraping-Logik (BeautifulSoup)
    ├── utils.py              # Helper (Pfad, History, .env-Laden)
    ├── output/               # generierte CSVs
    ├── logs/                 # Such-History (search_history.csv)
    ├── static/               # Statische Assets
    │   ├── styles.css
    │   └── script.js
    └── templates/            # Jinja-Templates
        ├── base.html
        ├── index.html
        └── history_detail.html
📦 Windows-Installer erstellen
Voraussetzung: Inno Setup (iscc.exe im PATH).

bat
Kopieren
Bearbeiten
install.bat
Damit erzeugst du:

dist_installer\leadscrapper.exe

Installer\LeadScrapperInstaller.exe (Setup-Programm)

🔧 Weiterentwicklung & Tests
Modularisierung: Logik in scraper.py & utils.py gekapselt.

.env-Konfiguration: Alle Secrets und Versionen auslagerbar.

Unit-Tests: Mit pytest & Mock-Responses geplant.

⚖️ Lizenz & Autor
LeadScrapper – © 2025 Robert Alchimowicz
Lizenz: MIT
# lscrapper
