# client.py
import requests
import random
import time
import json
import os
import logging

class HTTPClient:
    def __init__(self, proxies_file, user_agents_file, verify_ssl=False, timeout=10):
        self.session = requests.Session()
        self.timeout = timeout
        self.verify = verify_ssl
        self.proxies = self._load_proxies(proxies_file)
        self.user_agents = self._load_user_agents(user_agents_file)
        self.proxy_index = 0

    def _load_proxies(self, path):
        proxies = []
        with open(path, 'r', encoding='utf-8') as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies

    def _load_user_agents(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    def _get_next_proxy(self):
        if not self.proxies:
            return None
        proxy_url = f"http://{self.proxies[self.proxy_index]}"
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return {"http": proxy_url, "https": proxy_url}

    def get(self, url, headers=None, referer=None, retries=3):
        for attempt in range(1, retries + 1):
            try:
                proxy = self._get_next_proxy()
                req_headers = headers or {}
                req_headers.setdefault('User-Agent', random.choice(self.user_agents))
                if referer:
                    req_headers['Referer'] = referer
                resp = self.session.get(
                    url, headers=req_headers, timeout=self.timeout, proxies=proxy, verify=self.verify
                )
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt}/{retries} failed for {url}: {e}")
                time.sleep(min(30, (2 ** attempt)) + random.uniform(0, 1))
        return None
