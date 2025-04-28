import os
import random
import time
import logging
import requests
from bs4 import BeautifulSoup

# Pfad zur proxies-Datei (im root-Verzeichnis)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROXIES_FILE = os.path.join(ROOT, 'valid_proxies.txt')

def _load_proxies() -> list[str]:
    """
    Einmaliges Laden der Proxies aus valid_proxies.txt.
    Leerzeilen und Kommentare (# ...) werden ignoriert.
    """
    if not hasattr(_load_proxies, '_cache'):
        proxies = []
        try:
            with open(PROXIES_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        proxies.append(line)
        except FileNotFoundError:
            logging.warning(f"Proxy-Liste nicht gefunden: {PROXIES_FILE}")
        _load_proxies._cache = proxies
    return _load_proxies._cache

def _get_proxy_dict() -> dict[str,str] | None:
    """
    Wählt zufällig einen Proxy aus der Liste und formatiert
    ihn für requests (http/https).
    """
    proxies = _load_proxies()
    if not proxies:
        return None
    p = random.choice(proxies)
    # Wir gehen davon aus, dass die Einträge im Format "host:port" vorliegen
    proxy_url = f"http://{p}"
    return {'http': proxy_url, 'https': proxy_url}

def _fetch_url(
    url: str,
    user_agents: list[str],
    timeout: int,
    max_retries: int
) -> requests.Response | None:
    """
    Listenseiten laden mit Retries und Proxy.
    """
    for attempt in range(1, max_retries + 1):
        try:
            proxy_dict = _get_proxy_dict()
            r = requests.get(
                url,
                headers={'User-Agent': random.choice(user_agents) if user_agents else 'Mozilla/5.0'},
                timeout=timeout,
                proxies=proxy_dict
            )
            r.raise_for_status()
            return r
        except Exception as e:
            logging.warning(f"Fetch list {attempt}/{max_retries} fehlgeschlagen: {e}")
            if attempt == max_retries:
                logging.error(f"List-URL nicht erreichbar: {url}")
                return None
            time.sleep(2 ** attempt)

def _fetch_url_detail(
    url: str,
    user_agents: list[str],
    timeout: int,
    max_retries: int
) -> requests.Response | None:
    """
    Detailseiten laden mit Referer, Retries und Proxy.
    """
    for attempt in range(1, max_retries + 1):
        try:
            proxy_dict = _get_proxy_dict()
            r = requests.get(
                url,
                headers={
                    'User-Agent': random.choice(user_agents) if user_agents else 'Mozilla/5.0',
                    'Referer': 'https://www.herold.at/'
                },
                timeout=timeout,
                proxies=proxy_dict
            )
            r.raise_for_status()
            return r
        except Exception as e:
            logging.warning(f"Fetch detail {attempt}/{max_retries} fehlgeschlagen: {e}")
            if attempt == max_retries:
                logging.error(f"Detail-URL nicht erreichbar: {url}")
                return None
            time.sleep(2 ** attempt)

def scrape_bs4(
    base_url: str,
    fields: list[str],
    pages: int,
    user_agents: list[str],
    timeout: int = 10,
    max_retries: int = 3
) -> list[dict]:
    """
    Komfort-Funktion, die Seiten iteriert und alle Leads sammelt.
    (Kann in leadscrapper.py verwendet werden.)
    """
    all_leads = []
    for p in range(1, pages + 1):
        list_url = f"{base_url}?page={p}"
        logging.info(f"Scraping Seite {p}: {list_url}")
        resp = _fetch_url(list_url, user_agents, timeout, max_retries)
        if not resp:
            continue

        soup = BeautifulSoup(resp.text, 'html.parser')
        cards = soup.select('li.location-search-result')
        logging.info(f"Seite {p}: {len(cards)} Einträge gefunden")

        for card in cards:
            lead = {'Firma':'-','Telefon':'-','Email':'-','Adresse':'-','PLZ':'-','Ort':'-','Homepage':'-'}
            el = card.select_one('span[itemprop="name"]') or card.select_one('h2')
            lead['Firma'] = el.get_text(strip=True) if el else '-'

            # Detailseite nur laden, wenn tiefe Felder angefragt
            dsoup = None
            if set(fields) & {'telefon','email','adresse','plz','ortname','homepage'}:
                a = card.select_one("a[href*='/gelbe-seiten/']")
                if a and (href := a.get('href')):
                    full = make_absolute(href)
                    dr   = _fetch_url_detail(full, user_agents, timeout, max_retries)
                    if dr:
                        dsoup = BeautifulSoup(dr.text, 'html.parser')

            if dsoup:
                if 'telefon' in fields:
                    t = dsoup.select_one("a[href^='tel:']")
                    lead['Telefon'] = t.get_text(strip=True) if t else '-'
                if 'email' in fields:
                    m = dsoup.select_one("a[href^='mailto:']")
                    lead['Email'] = m.get('href').split('mailto:')[1] if m else '-'
                if 'adresse' in fields:
                    st = dsoup.select_one("meta[itemprop='streetAddress']")
                    lead['Adresse'] = st.get('content') if st else '-'
                if 'plz' in fields:
                    pc = dsoup.select_one("meta[itemprop='postalCode']")
                    lead['PLZ'] = pc.get('content') if pc else '-'
                if 'ortname' in fields:
                    rg = dsoup.select_one("meta[itemprop='addressRegion']")
                    lead['Ort'] = rg.get('content') if rg else '-'
                if 'homepage' in fields:
                    h = dsoup.select_one("a[href^='http']:not([href*='herold.at'])")
                    if h and (u := h.get('href')):
                        lead['Homepage'] = u

            all_leads.append(lead)

    return all_leads
