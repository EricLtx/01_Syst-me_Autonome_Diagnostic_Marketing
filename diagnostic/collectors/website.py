"""
website.py — LE collecteur implémenté pour le J1.

C'est celui que tu testes tout de suite sur ton client québécois.
Les quatre autres (gbp, reviews, seo, social) sont des stubs : tu les
implémenteras en J3, idéalement en binôme avec Claude Code.

Bonnes manières de scraping câblées dès le départ :
  - User-Agent honnête,
  - timeout strict,
  - cache disque (idempotence : on ne re-télécharge pas pour rien),
  - une seule requête par entreprise.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from diagnostic.collectors.base import Collector
from diagnostic.models import Company

CACHE_DIR = Path(".cache/website")
USER_AGENT = "DiagnosticMarque/0.1 (+prospection responsable ; contact@exemple.com)"
TIMEOUT = 10

# Mots-clés de l'offre du persona 1 (HVAC). En J3, ça migrera dans la rubrique.
OFFRE_KEYWORDS = [
    "climatisation", "climatiseur", "chauffage", "pompe à chaleur",
    "thermopompe", "ventilation", "installation", "entretien", "cvac", "hvac",
]
SOCIAL_DOMAINS = ["facebook.", "instagram.", "linkedin.", "youtube.", "tiktok.", "x.com", "twitter."]


class WebsiteCollector(Collector):
    name = "website"

    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache

    def collect(self, company: Company) -> dict[str, Any]:
        if not company.url:
            return {"reachable": False, "_note": "Aucune URL fournie"}

        html, final_url, status = self._fetch(company.url)
        if html is None:
            return {"reachable": False, "status": status, "https": False}

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True).lower()

        return {
            "reachable": True,
            "status": status,
            "final_url": final_url,
            "https": final_url.startswith("https://"),
            "has_title": bool(soup.title and soup.title.get_text(strip=True)),
            "title_len": len(soup.title.get_text(strip=True)) if soup.title else 0,
            "has_meta_description": self._has_meta_description(soup),
            "has_viewport": bool(soup.find("meta", attrs={"name": "viewport"})),
            "image_count": len(soup.find_all("img")),
            "has_logo": self._has_logo(soup),
            "has_contact": self._has_contact(soup, text),
            "mentions_offre": any(k in text for k in OFFRE_KEYWORDS),
            "social_links": self._social_links(soup),
            "copyright_year": self._copyright_year(text),
        }

    # --- I/O réseau (la seule partie "sale", isolée ici) -------------------

    def _fetch(self, url: str) -> tuple[str | None, str, int]:
        cached = self._read_cache(url)
        if cached is not None:
            return cached["html"], cached["final_url"], cached["status"]
        try:
            resp = requests.get(
                url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, allow_redirects=True
            )
            html, final_url, status = resp.text, resp.url, resp.status_code
            self._write_cache(url, html, final_url, status)
            return html, final_url, status
        except requests.RequestException:
            return None, url, 0

    # --- petits extracteurs de signaux -------------------------------------

    @staticmethod
    def _has_meta_description(soup: BeautifulSoup) -> bool:
        tag = soup.find("meta", attrs={"name": "description"})
        return bool(tag and tag.get("content", "").strip())

    @staticmethod
    def _has_logo(soup: BeautifulSoup) -> bool:
        for img in soup.find_all("img"):
            attrs = " ".join(str(img.get(a, "")) for a in ("alt", "class", "id", "src")).lower()
            if "logo" in attrs:
                return True
        return False

    @staticmethod
    def _has_contact(soup: BeautifulSoup, text: str) -> bool:
        if soup.find("a", href=re.compile(r"^(tel:|mailto:)")):
            return True
        return bool(re.search(r"\b\d{3}[\s.\-]?\d{3}[\s.\-]?\d{4}\b", text))

    @staticmethod
    def _social_links(soup: BeautifulSoup) -> list[str]:
        found = set()
        for a in soup.find_all("a", href=True):
            host = urlparse(a["href"]).netloc.lower()
            for dom in SOCIAL_DOMAINS:
                if dom in host:
                    found.add(dom.rstrip("."))
        return sorted(found)

    @staticmethod
    def _copyright_year(text: str) -> int | None:
        years = re.findall(r"©\s*(20\d{2})|(20\d{2})\s*©", text)
        flat = [int(y) for pair in years for y in pair if y]
        return max(flat) if flat else None

    # --- cache disque (idempotence) ----------------------------------------

    def _key(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode()).hexdigest()[:16]
        return CACHE_DIR / f"{digest}.json"

    def _read_cache(self, url: str) -> dict | None:
        if not self.use_cache:
            return None
        path = self._key(url)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return None

    def _write_cache(self, url: str, html: str, final_url: str, status: int) -> None:
        if not self.use_cache:
            return
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._key(url).write_text(
            json.dumps({"html": html, "final_url": final_url, "status": status}, ensure_ascii=False),
            encoding="utf-8",
        )
