import os
import random
import time
import logging
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import urllib3

# 1) SSL-Warnungen unterdrücken, weil wir verify=False nutzen
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Pfad zur proxies-Datei (im root-Verzeichnis)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROXIES_FILE = os.path.join(ROOT, 'valid_proxies.txt')

def _load_proxies() -> list[str]:
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

def _get_proxy_dict() -> dict[str, str] | None:
    proxies = _load_proxies()
    if not proxies:
        return None
    p = random.choice(proxies)
    proxy_url = f"http://{p}"
    return {'http': proxy_url, 'https': proxy_url}

def _fetch_url(
    url: str,
    user_agents: list[str],
    timeout: int,
    max_retries: int
) -> str | None:
    """
    Laden der Listenseiten, SSL-Verif. ausgeschaltet, Proxy nur wenn verfügbar.
    Liefert text oder None.
    """
    for attempt in range(1, max_retries + 1):
        try:
            proxy = _get_proxy_dict()
            r = requests.get(
                url,
                headers={'User-Agent': random.choice(user_agents) if user_agents else 'Mozilla/5.0'},
                timeout=timeout,
                proxies=proxy,
                verify=False
            )
            r.raise_for_status()
            return r.text
        except Exception as e:
            logging.warning(f"Fetch list {attempt}/{max_retries} fehlgeschlagen: {e}")
            time.sleep(2 ** attempt)
    logging.error(f"List-URL nicht erreichbar: {url}")
    return None

def _fetch_url_detail(
    url: str,
    user_agents: list[str],
    timeout: int,
    max_retries: int
) -> str | None:
    """
    Laden der Detailseiten mit Referer, SSL aus, Proxy optional.
    """
    for attempt in range(1, max_retries + 1):
        try:
            proxy = _get_proxy_dict()
            r = requests.get(
                url,
                headers={
                    'User-Agent': random.choice(user_agents) if user_agents else 'Mozilla/5.0',
                    'Referer': 'https://www.herold.at/'
                },
                timeout=timeout,
                proxies=proxy,
                verify=False
            )
            r.raise_for_status()
            return r.text
        except Exception as e:
            logging.warning(f"Fetch detail {attempt}/{max_retries} fehlgeschlagen: {e}")
            time.sleep(2 ** attempt)
    logging.error(f"Detail-URL nicht erreichbar: {url}")
    return None

def scrape_bs4(
    base_url: str,
    fields: list[str],
    pages: int,
    user_agents: list[str],
    timeout: int = 10,
    max_retries: int = 3
) -> list[dict]:
    """
    Iteriert Seiten, sammelt Leads – jetzt mit verify=False.
    """
    all_leads = []
    for p in range(1, pages + 1):
        list_url = f"{base_url}?page={p}"
        logging.info(f"Scraping Seite {p}: {list_url}")
        html = _fetch_url(list_url, user_agents, timeout, max_retries)
        if not html:
            continue

        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.select('article[data-testid="search-result-card"]')
        logging.info(f"Seite {p}: {len(cards)} Einträge gefunden")

        if not cards:
            # Dump für Debug
            debug_file = os.path.join(ROOT, f"debug_page_{p}.html")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html)
            logging.debug(f"Debug-HTML für Seite {p} gespeichert: {debug_file}")

        for card in cards:
            lead = dict.fromkeys(['Firma','Telefon','Email','Adresse','PLZ','Ort','Homepage'], '-')
            # Firmenname
            el = card.select_one('span[itemprop="name"]') or card.select_one('h2')
            lead['Firma'] = el.get_text(strip=True) if el else '-'

            dsoup = None
            if set(fields) & {'telefon','email','adresse','plz','ortname','homepage'}:
                a = card.select_one("a[href*='/gelbe-seiten/'], a[href*='/branchenbuch/']")
                if a and (href := a.get('href')):
                    full_url = urljoin(list_url, href)
                    detail_html = _fetch_url_detail(full_url, user_agents, timeout, max_retries)
                    if detail_html:
                        dsoup = BeautifulSoup(detail_html, 'html.parser')

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
                    lead['Homepage'] = h.get('href') if h else '-'

            all_leads.append(lead)

    return all_leads
