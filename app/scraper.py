import random
import logging
import requests
from bs4 import BeautifulSoup
from .utils import make_absolute

def scrape_bs4(base_url: str, fields: list[str], pages: int, user_agents: list[str]) -> list[dict]:
    """
    Scrape mit BeautifulSoup:
    - Holt Seite für Seite
    - Öffnet Detailseite nur, wenn Telefon/Email/Adresse/PLZ/Ort benötigt
    """
    leads = []
    for p in range(1, pages + 1):
        url = f"{base_url}?page={p}"
        logging.info(f"Fetching page {p}: {url}")
        try:
            resp = requests.get(
                url,
                headers={'User-Agent': random.choice(user_agents)},
                timeout=10
            )
            resp.raise_for_status()
        except Exception as e:
            logging.error(f"Seite {p} konnte nicht geladen werden: {e}")
            continue

        soup = BeautifulSoup(resp.text, 'html.parser')
        cards = soup.select('li.location-search-result')
        logging.info(f"Seite {p}: {len(cards)} Einträge gefunden")

        for card in cards:
            lead = {}
            # Firma
            el = card.select_one('span[itemprop="name"]') or card.select_one('h2')
            lead['Firma'] = el.get_text(strip=True) if el else "-"

            # Detailseite nur holen, falls weitere Felder benötigt
            dsoup = None
            if set(fields) & {'telefon','email','adresse','plz','ortname'}:
                a = card.select_one("a[href*='/gelbe-seiten/']")
                if a and (href := a.get('href')):
                    try:
                        dr = requests.get(
                            make_absolute(href),
                            headers={'User-Agent': random.choice(user_agents)},
                            timeout=10
                        )
                        dr.raise_for_status()
                        dsoup = BeautifulSoup(dr.text, 'html.parser')
                    except Exception as e:
                        logging.error(f"Detailseite {href} fehlgeschlagen: {e}")

            # Telefon
            if 'telefon' in fields:
                t = dsoup.select_one("a[href^='tel:']") if dsoup else None
                lead['Telefon'] = t.get_text(strip=True) if t else "-"

            # E-Mail
            if 'email' in fields:
                m = dsoup.select_one("a[href^='mailto:']") if dsoup else None
                lead['Email'] = m.get('href').split('mailto:')[1] if m else "-"

            # Adresse, PLZ, Ort
            if dsoup:
                if 'adresse' in fields:
                    st = dsoup.select_one("meta[itemprop='streetAddress']")
                    lead['Adresse'] = st.get('content') if st else "-"
                if 'plz' in fields:
                    pc = dsoup.select_one("meta[itemprop='postalCode']")
                    lead['PLZ'] = pc.get('content') if pc else "-"
                if 'ortname' in fields:
                    rg = dsoup.select_one("meta[itemprop='addressRegion']")
                    lead['Ort'] = rg.get('content') if rg else "-"
            else:
                # Fülle fehlende Felder mit "-"
                for f in ('adresse','plz','ortname'):
                    if f in fields:
                        key = f.capitalize() if f!='ortname' else 'Ort'
                        lead[key] = "-"

            leads.append(lead)
    return leads
