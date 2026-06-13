"""
discovery.py — DiscoveryCollector (phase 1a, §5.2 de la spec J4).

ICP → produit cartésien gabarits × localités → requêtes SERP → candidates filtrées.
Déduplication intra-lot par domaine normalisé (une seule Candidate par domaine).
Aucune écriture vault : ce module découvre uniquement, run_discovery.py écrit.
Tout le réseau passe par api_io.call() — jamais d'import requests au niveau module.
"""

from __future__ import annotations

from datetime import date
from urllib.parse import urlparse

from diagnostic.api_io import ApiIO, BudgetExceeded
from diagnostic.icp_schema import Candidate, IcpConfig

# Plateformes d'hébergement mutualisé : un sous-domaine de ces racines
# signifie que l'entreprise n'a pas son propre domaine.
_PLATEFORMES_HEBERGEES = frozenset({
    "wix.com",
    "wixsite.com",
    "squarespace.com",
    "wordpress.com",
    "weebly.com",
    "jimdo.com",
    "webnode.fr",
    "webnode.com",
    "site123.me",
    "myshopify.com",
    "strikingly.com",
    "business.site",
    "godaddysites.com",
})


class DiscoveryCollector:
    """Transforme un ICP en liste de candidates via des requêtes SERP métrées.

    Propage BudgetExceeded proprement (run_discovery.py gère l'arrêt propre).
    Isole toutes les autres exceptions par requête — une requête en erreur
    n'interrompt pas les suivantes.
    """

    def __init__(self, api_io: ApiIO, icp: IcpConfig) -> None:
        self._api_io = api_io
        self.icp = icp

    def discover(self) -> list[Candidate]:
        """Retourne les candidates uniques (dédup intra-lot par domaine normalisé)."""
        seen: dict[str, Candidate] = {}  # domaine normalisé → première Candidate rencontrée

        for requete in self.icp.generer_requetes():
            try:
                data = self._api_io.call(
                    "serp",
                    "search",
                    lambda r=requete: self._serp_search(r),
                    cache_key=requete,
                )
            except BudgetExceeded:
                raise  # arrêt propre — l'appelant journalise
            except Exception:
                continue  # requête isolée en erreur, on continue

            for item in (data.get("organic_results") or [])[: self.icp.requetes.max_resultats_par_requete]:
                url = item.get("link", "")
                if not url or not self._passe_filtres(url):
                    continue
                domaine = _normaliser_domaine(url)
                if not domaine or domaine in seen:
                    continue
                seen[domaine] = Candidate(
                    nom=_extraire_nom(item.get("title", "")),
                    site_web=_normaliser_url(url),
                    icp_id=self.icp.icp_id,
                    source=f"serp:{requete}",
                    date_decouverte=date.today(),
                )

        return list(seen.values())

    # --- I/O réseau (via bus api_io uniquement) ----------------------------

    def _serp_search(self, requete: str) -> dict:
        import os
        import requests as _req  # lazy : toujours via api_io bus (§9.6)

        resp = _req.get(
            "https://serpapi.com/search",
            params={
                "q": requete,
                "api_key": os.getenv("SERP_API_KEY", ""),
                "engine": "google",
                "num": self.icp.requetes.max_resultats_par_requete,
            },
            timeout=15,
        )
        return resp.json()

    # --- Filtres -----------------------------------------------------------

    def _passe_filtres(self, url: str) -> bool:
        if not url:
            return False
        try:
            netloc = urlparse(url).netloc.lower()
        except Exception:
            return False

        if not netloc:
            return False

        for exclu in self.icp.filtres.domaines_exclus:
            if exclu in netloc:
                return False

        if self.icp.filtres.exiger_domaine_propre and _est_heberge(netloc):
            return False

        return True


# ---------------------------------------------------------------------------
# Fonctions pures de normalisation (exposées pour les tests unitaires)
# ---------------------------------------------------------------------------

def _normaliser_domaine(url: str) -> str:
    """Domaine minuscule sans www., servant de clé de déduplication intra-lot."""
    try:
        netloc = urlparse(url.lower()).netloc
        return netloc.removeprefix("www.")
    except Exception:
        return ""


def _normaliser_url(url: str) -> str:
    """URL canonique : scheme https, pas de www., pas de trailing slash."""
    try:
        p = urlparse(url)
        netloc = p.netloc.lower().removeprefix("www.")
        path = p.path.rstrip("/")
        return f"https://{netloc}{path}" if path else f"https://{netloc}"
    except Exception:
        return url


def _extraire_nom(title: str) -> str:
    """Extrait le nom de l'entreprise depuis le titre d'un résultat SERP.

    Les séparateurs courants (|, —, -, –, ·, :) délimitent le nom du reste
    de l'accroche (ville, slogan, type de service).
    """
    for sep in (" | ", " — ", " - ", " – ", " · ", " : "):
        if sep in title:
            title = title.split(sep)[0]
    return title.strip()


def _est_heberge(netloc: str) -> bool:
    """True si le netloc est un sous-domaine d'une plateforme d'hébergement mutualisé.

    Ex : tremblay.wixsite.com → True  (root = wixsite.com)
         tremblay-hvac.ca   → False (domaine propre)
    """
    parts = netloc.split(".")
    if len(parts) >= 3:
        root = ".".join(parts[-2:])
        return root in _PLATEFORMES_HEBERGEES
    return False
