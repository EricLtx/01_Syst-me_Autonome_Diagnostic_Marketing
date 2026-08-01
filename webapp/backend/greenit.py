"""
greenit.py — lecture et agrégation « efficience » du grand livre `api_usage.log`.

Pourquoi un module dédié plutôt qu'une extension de services.py :

1. **Parsing défensif volontaire.** Le chantier GreenIT enrichit le ledger avec
   des champs OPTIONNELS (`octets_entrants`, `octets_sortants`, `duree_ms`,
   `energie_wh`, `co2e_g`, `modele`, `profil`). Les anciennes lignes ne les ont
   pas, et `diagnostic.api_schema.LedgerEntry` est en `extra="forbid"` : valider
   avec lui ferait *rejeter* les lignes enrichies tant que le schéma amont n'a
   pas atterri. On lit donc le JSONL brut et on applique des défauts (0 / None).
   Conséquence : cette vue fonctionne avec un ledger absent, ancien, enrichi, ou
   panaché des trois.

2. **Suivi incrémental.** Le flux SSE a besoin d'un tail par offset d'octets,
   qui n'a rien à faire dans une couche d'agrégats.

STRICTEMENT EN LECTURE : ce module ouvre `api_usage.log` en lecture seule. Aucune
écriture, aucun réseau, aucun `api_io`, aucune transition d'état.

⚠️ Les valeurs `energie_wh` et `co2e_g` sont des ESTIMATIONS issues des facteurs
paramétrables de `knowledge/greenit.yaml` (ordres de grandeur, pas des mesures
certifiées). Toute réponse de ce module les étiquette comme telles.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# Champs GreenIT ajoutés au ledger par le chantier d'instrumentation. Ils sont
# tous facultatifs : `normaliser()` garantit une forme complète en sortie.
CHAMPS_NUMERIQUES_GREENIT = (
    "octets_entrants",
    "octets_sortants",
    "duree_ms",
    "energie_wh",
    "co2e_g",
)

NOTE_ESTIMATION = (
    "energie_wh et co2e_g sont des ESTIMATIONS calculées à partir des facteurs "
    "paramétrables de knowledge/greenit.yaml (ordres de grandeur destinés à "
    "comparer des scénarios). Ce ne sont pas des mesures certifiées et elles ne "
    "constituent pas un bilan carbone opposable."
)


# ---------------------------------------------------------------------------
# Normalisation d'une ligne
# ---------------------------------------------------------------------------

def _nombre(valeur: Any, defaut: float = 0.0) -> float:
    """Convertit en float ; tout ce qui n'est pas numérique retombe sur `defaut`.

    Le ledger est un fichier append-only écrit par plusieurs agents : une valeur
    `null`, une chaîne ou un champ manquant ne doit jamais faire tomber la vue.
    """
    if valeur is None or isinstance(valeur, bool):
        return defaut
    if isinstance(valeur, (int, float)):
        return float(valeur)
    try:
        return float(str(valeur))
    except (TypeError, ValueError):
        return defaut


def _texte(valeur: Any) -> str | None:
    if valeur is None:
        return None
    texte = str(valeur).strip()
    return texte or None


def normaliser(obj: dict) -> dict:
    """Ramène une ligne JSONL brute à une forme complète et typée.

    Les champs GreenIT absents valent 0 (numériques) ou None (modele/profil) :
    une ancienne ligne produit donc une empreinte nulle plutôt qu'une erreur.
    """
    unites_brutes = obj.get("unites")
    unites: dict[str, float] = {}
    if isinstance(unites_brutes, dict):
        for cle, val in unites_brutes.items():
            unites[str(cle)] = _nombre(val)

    # « tokens » = toute unité dont le nom contient "token" (input/output/cache).
    tokens = sum(v for k, v in unites.items() if "token" in k.lower())

    ligne = {
        "ts": _texte(obj.get("ts")),
        "fournisseur": _texte(obj.get("fournisseur")) or "inconnu",
        "endpoint": _texte(obj.get("endpoint")) or "",
        "unites": unites,
        "tokens": tokens,
        "cout_estime": _nombre(obj.get("cout_estime")),
        "devise": _texte(obj.get("devise")) or "USD",
        "fiche": _texte(obj.get("fiche")),
        "cache_hit": bool(obj.get("cache_hit", False)),
        "resultat": _texte(obj.get("resultat")) or "ok",
        "detail": obj.get("detail") or "",
        # --- champs GreenIT (optionnels côté ledger) ---
        "modele": _texte(obj.get("modele")),
        "profil": _texte(obj.get("profil")),
    }
    for champ in CHAMPS_NUMERIQUES_GREENIT:
        ligne[champ] = _nombre(obj.get(champ))
    ligne["octets"] = ligne["octets_entrants"] + ligne["octets_sortants"]
    # Vrai seulement si la ligne porte au moins un champ d'empreinte : permet
    # d'afficher honnêtement le taux de couverture de l'instrumentation.
    ligne["greenit_instrumente"] = any(
        champ in obj and obj.get(champ) is not None
        for champ in CHAMPS_NUMERIQUES_GREENIT
    )
    return ligne


def _date_de_ligne(ligne: dict) -> str:
    """Extrait la partie AAAA-MM-JJ du ts (comparable lexicographiquement)."""
    ts = ligne.get("ts") or ""
    return ts[:10]


# ---------------------------------------------------------------------------
# Lecture du ledger
# ---------------------------------------------------------------------------

def lire_ledger(path: Path, depuis: date | None = None) -> tuple[list[dict], int]:
    """Lit `api_usage.log` (JSONL). Retourne (lignes normalisées, nb illisibles).

    Ne lève jamais : fichier absent → ([], 0) ; ligne corrompue → ignorée et
    comptée. C'est un journal append-only lu à chaud, une ligne tronquée en
    cours d'écriture est un cas normal, pas une erreur.
    """
    if not path.is_file():
        return [], 0
    try:
        brut = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], 0

    lignes: list[dict] = []
    illisibles = 0
    borne = depuis.isoformat() if depuis else None

    for raw in brut.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            illisibles += 1
            continue
        if not isinstance(obj, dict):
            illisibles += 1
            continue
        ligne = normaliser(obj)
        if borne is not None and _date_de_ligne(ligne) < borne:
            continue
        lignes.append(ligne)
    return lignes, illisibles


# ---------------------------------------------------------------------------
# Agrégation
# ---------------------------------------------------------------------------

_CHAMPS_CUMULES = ("cout", "energie_wh", "co2e_g", "octets", "duree_ms", "tokens")


def _bucket() -> dict[str, float]:
    b: dict[str, float] = {c: 0.0 for c in _CHAMPS_CUMULES}
    b["nb_appels"] = 0.0
    return b


def _cumuler(bucket: dict[str, float], ligne: dict) -> None:
    bucket["nb_appels"] += 1
    bucket["cout"] += ligne["cout_estime"]
    bucket["energie_wh"] += ligne["energie_wh"]
    bucket["co2e_g"] += ligne["co2e_g"]
    bucket["octets"] += ligne["octets"]
    bucket["duree_ms"] += ligne["duree_ms"]
    bucket["tokens"] += ligne["tokens"]


def _moyennes_par_cle(reels: Iterable[dict]) -> dict[tuple[str, str], dict[str, float]]:
    """Moyenne coût/énergie/CO2e des appels RÉELS, par (fournisseur, endpoint).

    Sert à estimer ce qu'un cache-hit a évité : on ne connaît pas le coût d'un
    appel qui n'a jamais eu lieu, on l'approche par la moyenne de ses jumeaux.
    """
    agg: dict[tuple[str, str], dict[str, float]] = {}
    for ligne in reels:
        for cle in (
            (ligne["fournisseur"], ligne["endpoint"]),
            (ligne["fournisseur"], "*"),
            ("*", "*"),
        ):
            b = agg.setdefault(cle, {"n": 0.0, "cout": 0.0, "energie_wh": 0.0, "co2e_g": 0.0})
            b["n"] += 1
            b["cout"] += ligne["cout_estime"]
            b["energie_wh"] += ligne["energie_wh"]
            b["co2e_g"] += ligne["co2e_g"]
    return agg


def agreger(lignes: list[dict], *, nb_illisibles: int = 0) -> dict:
    """Calcule l'agrégat d'efficience exposé par `GET /api/greenit`.

    Conventions alignées sur `diagnostic.usage.agreger` (contrat cohérent entre
    /api/usage et /api/greenit) :
      - un cache-hit n'est PAS un appel : il alimente `nb_cache_hits` ;
      - un appel `budget_depasse` compte dans `nb_appels` mais n'a rien dépensé,
        donc il n'alimente ni coût ni empreinte.
    """
    nb_appels = 0
    nb_cache_hits = 0
    nb_erreurs = 0
    nb_instrumentes = 0

    totaux = _bucket()
    par_modele: dict[str, dict[str, float]] = {}
    par_fournisseur: dict[str, dict[str, float]] = {}
    reels: list[dict] = []
    cache_hits: list[dict] = []

    for ligne in lignes:
        if ligne["cache_hit"]:
            nb_cache_hits += 1
            cache_hits.append(ligne)
            continue

        nb_appels += 1
        if ligne["resultat"] == "erreur":
            nb_erreurs += 1
        if ligne["resultat"] == "budget_depasse":
            # Refusé par le garde-fou : aucun octet n'a circulé.
            continue
        if ligne["greenit_instrumente"]:
            nb_instrumentes += 1

        reels.append(ligne)
        _cumuler(totaux, ligne)
        _cumuler(par_fournisseur.setdefault(ligne["fournisseur"], _bucket()), ligne)
        modele = ligne["modele"] or "non-llm"
        _cumuler(par_modele.setdefault(modele, _bucket()), ligne)

    # --- Économies attribuées au cache (ESTIMATION par moyenne des jumeaux) ---
    moyennes = _moyennes_par_cle(reels)
    eco_cout = eco_energie = eco_co2 = 0.0
    for hit in cache_hits:
        for cle in (
            (hit["fournisseur"], hit["endpoint"]),
            (hit["fournisseur"], "*"),
            ("*", "*"),
        ):
            b = moyennes.get(cle)
            if b and b["n"] > 0:
                eco_cout += b["cout"] / b["n"]
                eco_energie += b["energie_wh"] / b["n"]
                eco_co2 += b["co2e_g"] / b["n"]
                break
        # Aucun appel réel comparable → on ne peut rien estimer : 0, pas d'invention.

    total_tentatives = nb_appels + nb_cache_hits
    taux_cache = nb_cache_hits / total_tentatives if total_tentatives else 0.0

    def _liste(source: dict[str, dict[str, float]], cle_nom: str) -> list[dict]:
        out = []
        for nom, b in source.items():
            out.append(
                {
                    cle_nom: nom,
                    "nb_appels": int(b["nb_appels"]),
                    "tokens": round(b["tokens"], 3),
                    "cout": round(b["cout"], 6),
                    "energie_wh": round(b["energie_wh"], 6),
                    "co2e_g": round(b["co2e_g"], 6),
                    "octets": int(b["octets"]),
                    "duree_ms": round(b["duree_ms"], 3),
                }
            )
        # Tri par coût décroissant puis nom : ordre stable et lisible.
        out.sort(key=lambda d: (-d["cout"], d[cle_nom]))
        return out

    return {
        "cout_total_usd": round(totaux["cout"], 6),
        "devise": "USD",
        "energie_wh_total": round(totaux["energie_wh"], 6),
        "co2e_g_total": round(totaux["co2e_g"], 6),
        "octets_total": int(totaux["octets"]),
        "duree_ms_totale": round(totaux["duree_ms"], 3),
        "nb_appels": nb_appels,
        "nb_cache_hits": nb_cache_hits,
        "nb_erreurs": nb_erreurs,
        "nb_lignes_illisibles": nb_illisibles,
        "taux_cache": round(taux_cache, 4),
        "economies": {
            "appels_evites": nb_cache_hits,
            "cout_evite_usd": round(eco_cout, 6),
            "energie_wh_evitee": round(eco_energie, 6),
            "co2e_evite_g": round(eco_co2, 6),
            "methode": (
                "ESTIMATION — chaque cache-hit est valorisé à la moyenne des appels "
                "réels de même (fournisseur, endpoint). Sans appel réel comparable, "
                "l'économie est comptée à 0 plutôt qu'extrapolée."
            ),
        },
        "par_modele": _liste(par_modele, "modele"),
        "par_fournisseur": _liste(par_fournisseur, "fournisseur"),
        "estimation": True,
        "note_estimation": NOTE_ESTIMATION,
        "source_facteurs": "knowledge/greenit.yaml",
        "couverture_greenit": (
            round(nb_instrumentes / len(reels), 4) if reels else 0.0
        ),
        "ledger_present": True,  # écrasé par l'appelant si le fichier manque
    }


# ---------------------------------------------------------------------------
# Tail incrémental (support du flux SSE)
# ---------------------------------------------------------------------------

class LedgerTail:
    """Suit `api_usage.log` par offset d'octets, à la manière de `tail -f`.

    Points d'attention traités :
      - **ligne partielle** : une ligne sans `\\n` final est en cours d'écriture,
        on la garde en tampon et on ne la publie qu'une fois terminée ;
      - **troncature / rotation** : si le fichier rétrécit, on repart de 0 ;
      - **fichier absent** : offset 0, aucune ligne, aucune exception.
    """

    def __init__(self, path: Path, *, depuis_debut: bool = False) -> None:
        self.path = path
        self._tampon = ""
        self.offset = 0 if depuis_debut else self.taille()

    def taille(self) -> int:
        try:
            return os.path.getsize(self.path)
        except OSError:
            return 0

    def lire_nouvelles(self) -> list[dict]:
        """Retourne les lignes complètes apparues depuis le dernier appel."""
        taille = self.taille()
        if taille < self.offset:
            # Fichier tronqué ou remplacé : on recommence proprement.
            self.offset = 0
            self._tampon = ""
        if taille == self.offset:
            return []
        try:
            with self.path.open("r", encoding="utf-8", errors="replace") as fh:
                fh.seek(self.offset)
                bloc = fh.read()
                self.offset = taille
        except OSError:
            return []

        self._tampon += bloc
        *completes, self._tampon = self._tampon.split("\n")

        lignes: list[dict] = []
        for raw in completes:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                lignes.append(normaliser(obj))
        return lignes


def dernieres_lignes(path: Path, n: int) -> list[dict]:
    """Les `n` dernières lignes normalisées (les plus anciennes d'abord)."""
    if n <= 0:
        return []
    lignes, _ = lire_ledger(path)
    return lignes[-n:]


def horodatage() -> str:
    return datetime.now(timezone.utc).isoformat()
