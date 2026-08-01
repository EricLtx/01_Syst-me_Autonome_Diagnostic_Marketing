"""
dataset.py — dataset minimal et reproductible pour les tests d'intégration.

Ce que ce module fabrique, et rien de plus :
  1. un vault Obsidian initialisé (via `diagnostic.vault_init.init_vault`,
     donc exactement le scaffold de production) ;
  2. des fiches prospect couvrant TOUS les états utiles à l'aval :
     `decouvert` (à diagnostiquer), `diagnostique` (en attente de la porte
     humaine), `valide` (exportable), `valide` + `opt_out` (à exclure
     absolument), `valide` sans email (anomalie d'export), `rejete` ;
  3. les chemins des fixtures : grille tarifaire de test et ICP de test.

Règle d'or : idempotent. Semer deux fois ne récrit aucune fiche existante —
c'est ce qui rend `scripts/seed_dataset.py` rejouable sans détruire un état
déjà diagnostiqué (même esprit que `init_vault.py`).

Aucune écriture directe : tout passe par `VaultIO` (bus de stockage J2).
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Callable, Iterable

from diagnostic.vault_init import init_vault
from diagnostic.vault_io import VaultIO
from diagnostic.vault_schema import FicheProspect

DOSSIER_FIXTURES = Path(__file__).resolve().parent / "fixtures"
PRICING_TEST = DOSSIER_FIXTURES / "api_pricing_test.yaml"
ICP_DIR_TEST = DOSSIER_FIXTURES / "icp"
ICP_TEST = "persona1-quebec"


# ---------------------------------------------------------------------------
# Définition des fiches semées (données, pas code)
# ---------------------------------------------------------------------------

_HIER = date.today() - timedelta(days=1)
_AVANT_HIER = date.today() - timedelta(days=2)

# slug du catalogue faux_api → frontmatter de la fiche.
# `site_web` est ajouté à la volée : il dépend de l'adresse du faux serveur.
FICHES_SEED: tuple[dict, ...] = (
    {
        "_slug": "climatisation-tremblay",
        "nom": "Climatisation Tremblay",
        "statut": "decouvert",
        "source_decouverte": "seed:integration",
        "contact_nom": "Marc Tremblay",
        "contact_titre": "Propriétaire",
        "contact_email": "marc@climatisation-tremblay.test",
        "contact_email_source": "verified",
    },
    {
        "_slug": "chauffage-lachance",
        "nom": "Chauffage Lachance",
        "statut": "decouvert",
        "source_decouverte": "seed:integration",
    },
    {
        "_slug": "cvac-gagnon-fils",
        "nom": "CVAC Gagnon et Fils",
        "statut": "diagnostique",
        "score_global": 41,
        "gaps_majeurs": ["site_web", "presence_locale"],
        "date_diagnostic": _HIER,
        "signal_chaud": "Site non optimisé pour mobile",
        "accroche": "Votre site n'est pas lisible sur mobile.",
        "contact_nom": "Nathalie Gagnon",
        "contact_titre": "Propriétaire",
        "contact_email": "n.gagnon@cvac-gagnon.test",
        "contact_email_source": "likely",
    },
    {
        "_slug": "clim-rive-sud",
        "nom": "Clim Rive-Sud",
        "statut": "valide",
        "score_global": 78,
        "gaps_majeurs": ["seo_local"],
        "date_diagnostic": _AVANT_HIER,
        "signal_chaud": "Pas de mots-clés géolocalisés détectés",
        "accroche": "Vos pages ne ciblent aucune ville.",
        "contact_nom": "Karine Meunier",
        "contact_titre": "Présidente",
        "contact_email": "karine@clim-rive-sud.test",
        "contact_email_source": "verified",
        "contact_linkedin": "https://www.linkedin.com/in/karine-meunier-fictif",
    },
    {
        # Cas critique RGPD/CASL/nLPD : validée MAIS opt_out → jamais exportée.
        "_slug": "hvac-saguenay",
        "nom": "HVAC Saguenay",
        "statut": "valide",
        "opt_out": True,
        "score_global": 82,
        "gaps_majeurs": ["identite_visuelle"],
        "date_diagnostic": _AVANT_HIER,
        "signal_chaud": "Très peu de visuels",
        "accroche": "Votre identité visuelle est peu incarnée.",
        "contact_nom": "Alain Simard",
        "contact_titre": "General Manager",
        "contact_email": "alain@hvac-saguenay.test",
        "contact_email_source": "verified",
    },
    {
        # Validée mais sans email : alimente le rapport d'anomalies de l'export.
        "_slug": "aeroclim-beauce",
        "nom": "Aéroclim Beauce",
        "statut": "valide",
        "score_global": 55,
        "gaps_majeurs": ["avis"],
        "date_diagnostic": _AVANT_HIER,
        "signal_chaud": "Moins de 10 avis — preuve sociale faible",
        "accroche": "Votre preuve sociale est trop mince.",
    },
    {
        "_slug": "froid-boreal",
        "nom": "Froid Boréal",
        "statut": "rejete",
        "source_decouverte": "seed:integration",
    },
)


def _url_inerte(slug: str) -> str:
    """URL par défaut : domaine `.test` (RFC 6761) — jamais résolvable.

    Garantit qu'un dataset semé hors test ne pointe accidentellement sur
    aucun site réel.
    """
    return f"https://{slug}.test"


def fiche_depuis_seed(seed: dict, url_site: Callable[[str], str]) -> FicheProspect:
    """Construit la FicheProspect (validée Pydantic) depuis une entrée de seed."""
    champs = {k: v for k, v in seed.items() if not k.startswith("_")}
    champs.setdefault("persona", 1)
    champs.setdefault("marche", "quebec")
    champs.setdefault("icp_id", ICP_TEST)
    champs.setdefault("date_creation", _AVANT_HIER)
    champs.setdefault("source_decouverte", "seed:integration")
    champs["site_web"] = url_site(seed["_slug"])
    return FicheProspect(**champs)


# ---------------------------------------------------------------------------
# Semis
# ---------------------------------------------------------------------------

def initialiser_vault(vault_path: Path) -> dict:
    """Scaffold du vault via le code de production (idempotent)."""
    return init_vault(Path(vault_path))


def semer(
    vault_path: Path,
    *,
    url_site: Callable[[str], str] | None = None,
    seeds: Iterable[dict] | None = None,
    forcer: bool = False,
) -> dict[str, list[str]]:
    """Écrit les fiches du dataset dans le vault. Idempotent par défaut.

    Une fiche dont le `nom` existe déjà est laissée telle quelle (statut,
    annotations humaines et diagnostics conservés) sauf si `forcer=True`.
    Retourne {"crees": [...], "existants": [...]}.
    """
    vault_path = Path(vault_path)
    initialiser_vault(vault_path)
    io = VaultIO(vault_path)
    resolveur = url_site or _url_inerte

    crees: list[str] = []
    existants: list[str] = []
    for seed in (seeds if seeds is not None else FICHES_SEED):
        if not forcer and io.exists(nom=seed["nom"]) is not None:
            existants.append(seed["nom"])
            continue
        io.write_fiche(fiche_depuis_seed(seed, resolveur))
        crees.append(seed["nom"])
    return {"crees": crees, "existants": existants}


def resume(vault_path: Path) -> dict[str, int]:
    """Compte les fiches par statut — utile aux assertions et au CLI."""
    io = VaultIO(Path(vault_path))
    compte: dict[str, int] = {}
    for _, fiche in io.query():
        compte[str(fiche.statut)] = compte.get(str(fiche.statut), 0) + 1
    return compte
