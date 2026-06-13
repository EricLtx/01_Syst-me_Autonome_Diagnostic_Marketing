"""
website.py — collecteur site web (palier 0).

Bonnes manières de scraping :
  - User-Agent honnête, timeout strict, une seule requête par entreprise.
  - Cache disque idempotent (fallback sans api_io) ou via bus api_io.
  - Pas d'import requests au niveau module : centralisé dans api_io quand injecté,
    ou chargé localement (lazy) en mode autonome (rétrocompatibilité tests J1/J2).

Signaux produits (palier 0 enrichi §8.1) :
  - reachable, https, status, title/meta/viewport/contact/logo/images
  - social_links : plateformes liées depuis le site (source pour social.py)
  - copyright_year : année © extraite du pied de page
  - derniere_maj : date ISO (YYYY-MM-DD) ou année (YYYY) la plus récente parmi
      Last-Modified HTTP, lastmod sitemap.xml, balises <time>, copyright_year
  - fraicheur_mois : ancienneté en mois depuis derniere_maj (int) ou None
  - _seo_text : texte consolidé (titre + meta-desc + corps tronqué) pour SeoCollector
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from diagnostic.collectors.base import Collector
from diagnostic.models import Company

CACHE_DIR = Path(".cache/website")
USER_AGENT = "DiagnosticMarque/0.1 (+prospection responsable ; contact@exemple.com)"
TIMEOUT = 10

OFFRE_KEYWORDS = [
    "climatisation", "climatiseur", "chauffage", "pompe à chaleur",
    "thermopompe", "ventilation", "installation", "entretien", "cvac", "hvac",
]
SOCIAL_DOMAINS = ["facebook.", "instagram.", "linkedin.", "youtube.", "tiktok.", "x.com", "twitter."]


class WebsiteCollector(Collector):
    name = "website"

    def __init__(self, use_cache: bool = True, api_io=None):
        self.use_cache = use_cache
        self._api_io = api_io

    def collect(self, company: Company) -> dict[str, Any]:
        if not company.url:
            return {"reachable": False, "_note": "Aucune URL fournie"}

        fetched = self._fetch(company.url)
        html = fetched.get("html")
        final_url = fetched.get("final_url", company.url)
        status = fetched.get("status", 0)
        last_modified = fetched.get("last_modified")

        if html is None:
            return {"reachable": False, "status": status, "https": False}

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True).lower()

        copyright_year = self._copyright_year(text)
        sitemap_date = self._try_sitemap(final_url)
        derniere_maj = self._derniere_maj(soup, last_modified, sitemap_date, copyright_year)

        title_text = soup.title.get_text(strip=True) if soup.title else ""
        meta_desc = self._meta_desc_content(soup)
        seo_text = f"{title_text} {meta_desc} {text[:2000]}"

        return {
            "reachable": True,
            "status": status,
            "final_url": final_url,
            "https": final_url.startswith("https://"),
            "has_title": bool(soup.title and soup.title.get_text(strip=True)),
            "title_len": len(title_text),
            "has_meta_description": self._has_meta_description(soup),
            "has_viewport": bool(soup.find("meta", attrs={"name": "viewport"})),
            "image_count": len(soup.find_all("img")),
            "has_logo": self._has_logo(soup),
            "has_contact": self._has_contact(soup, text),
            "mentions_offre": any(k in text for k in OFFRE_KEYWORDS),
            "social_links": self._social_links(soup),
            "copyright_year": copyright_year,
            "derniere_maj": derniere_maj,
            "fraicheur_mois": self._fraicheur_mois(derniere_maj),
            "_seo_text": seo_text,
        }

    # --- I/O réseau -------------------------------------------------------

    def _fetch(self, url: str) -> dict:
        """Retourne {"html", "final_url", "status", "last_modified"} ; html=None si échec."""
        if self._api_io is not None:
            try:
                data = self._api_io.call(
                    "http", "get",
                    lambda: self._do_get(url),
                    cache_key=url if self.use_cache else None,
                )
                return {
                    "html": data.get("html"),
                    "final_url": data.get("final_url", url),
                    "status": data.get("status", 0),
                    "last_modified": data.get("last_modified"),
                }
            except Exception:
                return {"html": None, "final_url": url, "status": 0}

        # Fallback autonome (rétrocompatibilité J1/J2, pas de bus injecté)
        cached = self._read_cache(url)
        if cached is not None:
            return {
                "html": cached.get("html"),
                "final_url": cached.get("final_url", url),
                "status": cached.get("status", 0),
                "last_modified": cached.get("last_modified"),
            }
        try:
            import requests as _req  # lazy : propriété du bus quand disponible
            resp = _req.get(
                url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, allow_redirects=True
            )
            html, final_url, status = resp.text, resp.url, resp.status_code
            lm = resp.headers.get("Last-Modified")
            last_modified = str(lm) if isinstance(lm, str) else None
            self._write_cache(url, {"html": html, "final_url": final_url, "status": status, "last_modified": last_modified})
            return {"html": html, "final_url": final_url, "status": status, "last_modified": last_modified}
        except Exception:
            return {"html": None, "final_url": url, "status": 0}

    def _do_get(self, url: str) -> dict:
        """Exécute le GET HTTP et retourne un dict JSON-sérialisable pour le cache api_io."""
        import requests as _req  # lazy : propriété du bus quand disponible
        resp = _req.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, allow_redirects=True
        )
        lm = resp.headers.get("Last-Modified")
        return {
            "html": resp.text,
            "final_url": resp.url,
            "status": resp.status_code,
            "last_modified": str(lm) if isinstance(lm, str) else None,
        }

    def _try_sitemap(self, final_url: str) -> str | None:
        """Cherche /sitemap.xml et retourne la date <lastmod> la plus récente (ou None)."""
        try:
            parsed = urlparse(final_url)
            sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"
            if self._api_io is not None:
                data = self._api_io.call(
                    "http", "get",
                    lambda: self._do_get(sitemap_url),
                    cache_key=sitemap_url if self.use_cache else None,
                )
                xml = data.get("html", "")
            else:
                import requests as _req
                resp = _req.get(sitemap_url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
                if not isinstance(resp.status_code, int) or resp.status_code != 200:
                    return None
                xml = resp.text
            return self._parse_sitemap_lastmod(xml)
        except Exception:
            return None

    # --- Calcul dernière mise à jour --------------------------------------

    def _derniere_maj(
        self,
        soup: BeautifulSoup,
        last_modified: str | None,
        sitemap_date: str | None,
        copyright_year: int | None,
    ) -> str | None:
        candidates: list[str] = []

        if last_modified:
            try:
                from email.utils import parsedate
                t = parsedate(last_modified)
                if t:
                    candidates.append(f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}")
            except Exception:
                pass

        html_date = self._parse_dates_html(soup)
        if html_date:
            candidates.append(html_date)
        if sitemap_date:
            candidates.append(sitemap_date)
        if copyright_year:
            candidates.append(str(copyright_year))

        if not candidates:
            return None
        # Normaliser pour comparaison (YYYY → YYYY-01-01)
        return max(candidates, key=lambda s: s + "-01-01" if len(s) == 4 else s)

    @staticmethod
    def _fraicheur_mois(derniere_maj: str | None) -> int | None:
        """Ancienneté en mois depuis derniere_maj jusqu'à aujourd'hui."""
        if not derniere_maj:
            return None
        try:
            if len(derniere_maj) >= 10:
                d = datetime.date.fromisoformat(derniere_maj[:10])
            else:
                d = datetime.date(int(derniere_maj), 1, 1)
            today = datetime.date.today()
            return (today.year - d.year) * 12 + (today.month - d.month)
        except Exception:
            return None

    @staticmethod
    def _parse_sitemap_lastmod(xml: str) -> str | None:
        """Extrait la date <lastmod> la plus récente d'un sitemap XML."""
        dates = re.findall(r"<lastmod>(\d{4}-\d{2}-\d{2}(?:T[^<]*)?)</lastmod>", xml)
        return max((d[:10] for d in dates), default=None)

    @staticmethod
    def _parse_dates_html(soup: BeautifulSoup) -> str | None:
        """Date la plus récente parmi les balises <time datetime='YYYY-MM-DD…'>."""
        dates = []
        for tag in soup.find_all("time"):
            dt = tag.get("datetime", "")
            if isinstance(dt, str) and re.match(r"\d{4}-\d{2}-\d{2}", dt):
                dates.append(dt[:10])
        return max(dates) if dates else None

    # --- extracteurs de signaux -------------------------------------------

    @staticmethod
    def _has_meta_description(soup: BeautifulSoup) -> bool:
        tag = soup.find("meta", attrs={"name": "description"})
        return bool(tag and tag.get("content", "").strip())

    @staticmethod
    def _meta_desc_content(soup: BeautifulSoup) -> str:
        tag = soup.find("meta", attrs={"name": "description"})
        return tag.get("content", "").strip() if tag else ""

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

    # --- cache disque (fallback autonome) ---------------------------------

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

    def _write_cache(self, url: str, data: dict) -> None:
        if not self.use_cache:
            return
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._key(url).write_text(
            json.dumps(data, ensure_ascii=False),
            encoding="utf-8",
        )
