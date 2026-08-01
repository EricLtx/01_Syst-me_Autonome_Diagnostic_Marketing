"""
greenit.py — stratégie d'efficience des appels IA et de la consommation de données.

Module PUR : aucune I/O réseau, aucun import `requests` / `anthropic`, aucun état
global mutable. Il ne fait que trois choses, toutes déterministes :

  1. `choisir_modele`   — quel modèle pour quel travail (routage if/else piloté par YAML)
  2. `tronquer_contexte`— borner ce qu'on envoie (levier de frugalité n°1)
  3. `estimer_empreinte`— chiffrer énergie + CO2e d'un appel (observabilité)

Pourquoi un module séparé plutôt que des constantes dans synthesis.py :
le choix de modèle est une décision d'exploitation (coût, énergie), pas une
décision métier. Elle doit pouvoir changer sans toucher au code qui rédige —
d'où la config en YAML (`knowledge/greenit.yaml`) et un module sans dépendance.

Pourquoi zéro LLM dans le routage : faire arbitrer un modèle par un autre modèle
coûte un appel supplémentaire pour une décision qu'un `if` tranche exactement.
"""
from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any

import yaml

# Résolu depuis l'emplacement de ce fichier : diagnostic/ -> racine -> knowledge/
CHEMIN_CONFIG_DEFAUT = Path(__file__).resolve().parent.parent / "knowledge" / "greenit.yaml"


# ---------------------------------------------------------------------------
# Configuration de repli — le système doit tourner même sans le YAML
# ---------------------------------------------------------------------------
# Pourquoi dupliquer le YAML ici : un fichier de config absent ou corrompu ne doit
# jamais faire tomber le pipeline. On dégrade vers le profil le plus frugal, ce qui
# est aussi le comportement le plus sûr côté budget.
CONFIG_DEFAUT: dict[str, Any] = {
    "version": 1,
    "profils": {
        "frugal": {"modele": "claude-haiku-4-5-20251001", "max_tokens": 400},
        "standard": {"modele": "claude-haiku-4-5-20251001", "max_tokens": 600},
        "qualite": {"modele": "claude-sonnet-4-5", "max_tokens": 900},
    },
    "routage": {
        "profil_defaut": "standard",
        "profil_escalade": "qualite",
        "mode": "ou",
        "regles_escalade": [
            {"nom": "quality_check_echoue", "champ": "quality_check_echoue",
             "operateur": "==", "valeur": True},
            {"nom": "failles_nombreuses", "champ": "nb_failles",
             "operateur": ">=", "valeur": 6},
            {"nom": "prospect_a_fort_score", "champ": "score_global",
             "operateur": ">=", "valeur": 75},
        ],
    },
    "frugalite": {
        "troncature_contexte_caracteres": 4000,
        "troncature_prompt_caracteres": 8000,
        "max_tokens_sortie": 600,
        "cache_ttl_jours": 30,
        "activer_prompt_caching": False,
    },
    "empreinte": {
        "wh_par_1k_tokens_entree": 0.05,
        "wh_par_1k_tokens_sortie": 0.30,
        "wh_par_1k_tokens_cache_lecture": 0.005,
        "wh_par_requete_http": 0.10,
        "wh_par_mo_transfere": 0.06,
        "intensite_carbone_g_par_kwh": {"defaut": 475},
    },
}

# Marqueur inséré à la place du texte coupé : rend la troncature visible dans
# les logs et dans le prompt (le LLM sait qu'il ne voit pas tout).
MARQUEUR_TRONCATURE = "\n[…contexte tronqué : {n} caractères omis…]"


# ---------------------------------------------------------------------------
# Chargement de la configuration
# ---------------------------------------------------------------------------

def _fusion_profonde(base: dict, surcouche: dict) -> dict:
    """Fusionne `surcouche` dans une copie de `base`, récursivement.

    Pourquoi : un YAML partiel (l'opératrice ne renseigne que `profils:`) doit
    hériter des valeurs par défaut au lieu de laisser des trous.
    """
    resultat = dict(base)
    for cle, valeur in (surcouche or {}).items():
        if isinstance(valeur, dict) and isinstance(resultat.get(cle), dict):
            resultat[cle] = _fusion_profonde(resultat[cle], valeur)
        else:
            resultat[cle] = valeur
    return resultat


def charger_config(path: str | Path | None = None) -> dict[str, Any]:
    """Charge knowledge/greenit.yaml, fusionné sur CONFIG_DEFAUT.

    Ne lève jamais : fichier absent, YAML invalide ou racine non-dict → on retourne
    CONFIG_DEFAUT. Une config d'efficience qui casse la production serait un comble.
    """
    chemin = Path(path) if path is not None else CHEMIN_CONFIG_DEFAUT
    try:
        brut = yaml.safe_load(chemin.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — fichier absent, illisible, YAML invalide…
        return dict(CONFIG_DEFAUT)
    if not isinstance(brut, dict):
        return dict(CONFIG_DEFAUT)
    return _fusion_profonde(CONFIG_DEFAUT, brut)


# ---------------------------------------------------------------------------
# Routage de modèle — déterministe, piloté par les règles YAML
# ---------------------------------------------------------------------------

def _compare(valeur: Any, operateur: str, reference: Any) -> bool:
    """Applique un opérateur de comparaison. Retourne False si incomparable.

    Pourquoi tolérer l'incomparable plutôt que lever : une règle mal saisie dans le
    YAML ne doit pas escalader par accident (le silence coûte moins cher que le
    gros modèle).
    """
    try:
        if operateur == "==":
            return valeur == reference
        if operateur == "!=":
            return valeur != reference
        if operateur == "in":
            return valeur in reference
        if valeur is None:
            return False
        if operateur == ">=":
            return valeur >= reference
        if operateur == ">":
            return valeur > reference
        if operateur == "<=":
            return valeur <= reference
        if operateur == "<":
            return valeur < reference
    except TypeError:
        return False
    return False


def evaluer_escalade(contexte: dict[str, Any], config: dict[str, Any]) -> list[str]:
    """Retourne les noms des règles d'escalade satisfaites (dans l'ordre du YAML).

    Exposé publiquement pour la traçabilité : on veut pouvoir journaliser POURQUOI
    un appel a coûté trois fois plus cher.
    """
    routage = config.get("routage") or {}
    declenchees: list[str] = []
    for regle in routage.get("regles_escalade") or []:
        if not isinstance(regle, dict):
            continue
        champ = regle.get("champ")
        if champ is None or champ not in contexte:
            continue
        if _compare(contexte.get(champ), str(regle.get("operateur", "==")), regle.get("valeur")):
            declenchees.append(str(regle.get("nom", champ)))
    return declenchees


def choisir_modele(contexte: dict[str, Any], config: dict[str, Any]) -> tuple[str, str]:
    """Choisit (modele, profil) pour un appel LLM. Purement déterministe.

    Ordre de décision :
      1. `contexte["profil"]` force un profil existant (échappatoire explicite).
      2. sinon profil par défaut du YAML (le moins cher).
      3. escalade vers `profil_escalade` si les règles sont satisfaites
         (mode "ou" : une suffit ; mode "et" : toutes requises).

    Mêmes entrées → même sortie. Aucun appel réseau, aucun LLM dans la boucle.
    """
    profils = config.get("profils") or CONFIG_DEFAUT["profils"]
    routage = config.get("routage") or {}

    profil_force = (contexte or {}).get("profil")
    if isinstance(profil_force, str) and profil_force in profils:
        return _modele_du_profil(profil_force, profils), profil_force

    profil = str(routage.get("profil_defaut") or "standard")
    if profil not in profils:
        profil = next(iter(profils), "standard")

    profil_escalade = str(routage.get("profil_escalade") or "")
    if profil_escalade in profils:
        declenchees = evaluer_escalade(contexte or {}, config)
        regles = [r for r in (routage.get("regles_escalade") or []) if isinstance(r, dict)]
        mode = str(routage.get("mode") or "ou").lower()
        if regles and (
            (mode == "et" and len(declenchees) == len(regles))
            or (mode != "et" and declenchees)
        ):
            profil = profil_escalade

    return _modele_du_profil(profil, profils), profil


def _modele_du_profil(profil: str, profils: dict[str, Any]) -> str:
    entree = profils.get(profil) or {}
    modele = entree.get("modele") if isinstance(entree, dict) else None
    return str(modele or CONFIG_DEFAUT["profils"]["frugal"]["modele"])


def max_tokens_du_profil(profil: str, config: dict[str, Any]) -> int:
    """max_tokens effectif : minimum entre le profil et le plafond de frugalité.

    Pourquoi un minimum et pas le profil seul : `frugalite.max_tokens_sortie` est un
    plafond global d'exploitation. On peut le baisser pour tout le système d'un seul
    réglage, sans réécrire chaque profil.
    """
    profils = config.get("profils") or CONFIG_DEFAUT["profils"]
    entree = profils.get(profil) or {}
    valeur = entree.get("max_tokens") if isinstance(entree, dict) else None
    try:
        max_tokens = int(valeur)
    except (TypeError, ValueError):
        max_tokens = 600

    plafond = (config.get("frugalite") or {}).get("max_tokens_sortie")
    try:
        if plafond is not None:
            max_tokens = min(max_tokens, int(plafond))
    except (TypeError, ValueError):
        pass
    return max(1, max_tokens)


# ---------------------------------------------------------------------------
# Frugalité — borner l'entrée
# ---------------------------------------------------------------------------

def tronquer_contexte(
    texte: str,
    config: dict[str, Any],
    cle: str = "troncature_contexte_caracteres",
) -> str:
    """Borne la taille d'un bloc de contexte injecté dans un prompt.

    Levier de frugalité n°1 : les tokens d'entrée sont facturés et consommés même
    quand le modèle n'en a pas besoin. Une fiche pathologique (30 failles) ne doit
    pas coûter dix fois une fiche normale.

    On garde le DÉBUT du texte : les failles sont déjà triées par gravité en amont,
    donc le début porte l'essentiel. Le marqueur explicite indique au modèle (et à
    l'auditeur) qu'une partie a été coupée.
    """
    if not isinstance(texte, str):
        return ""
    limite = (config.get("frugalite") or {}).get(cle)
    try:
        limite = int(limite)
    except (TypeError, ValueError):
        return texte
    if limite <= 0 or len(texte) <= limite:
        return texte

    # La borne porte sur le résultat FINAL, marqueur inclus : « borner » doit
    # vouloir dire « ne dépasse jamais », sinon la garantie de coût saute.
    garde = limite
    while True:
        marqueur = MARQUEUR_TRONCATURE.format(n=len(texte) - garde)
        depassement = garde + len(marqueur) - limite
        if depassement <= 0 or garde <= 0:
            break
        garde = max(0, garde - depassement)
    return texte[:garde] + marqueur


# ---------------------------------------------------------------------------
# Empreinte — estimation transparente (⚠️ ordres de grandeur, pas des mesures)
# ---------------------------------------------------------------------------

def _normaliser(texte: str) -> str:
    """minuscule + sans accent : 'Québec, QC' → 'quebec, qc'."""
    decompose = unicodedata.normalize("NFD", texte)
    sans_accent = "".join(c for c in decompose if unicodedata.category(c) != "Mn")
    return sans_accent.lower()


def intensite_carbone(region: str | None, config: dict[str, Any]) -> float:
    """gCO2e/kWh du mix électrique associé à une région.

    Recherche par fragment (le champ `region` d'une fiche vaut « Québec, QC » ou
    « Genève, Suisse romande » — on ne peut pas exiger une clé exacte).
    Retourne `defaut` si rien ne correspond.
    """
    table = (config.get("empreinte") or {}).get("intensite_carbone_g_par_kwh") or {}
    defaut = table.get("defaut", 475)
    try:
        defaut = float(defaut)
    except (TypeError, ValueError):
        defaut = 475.0
    if not region:
        return defaut

    cible = _normaliser(str(region))
    # Ordre déterministe : fragments les plus longs d'abord ("etats-unis" avant "usa"),
    # sinon un fragment court pourrait masquer une clé plus spécifique.
    for cle in sorted((k for k in table if k != "defaut"), key=lambda k: (-len(str(k)), str(k))):
        if _normaliser(str(cle)) in cible:
            try:
                return float(table[cle])
            except (TypeError, ValueError):
                return defaut
    return defaut


def estimer_empreinte(
    unites: dict[str, float] | None,
    octets: int,
    region: str | None,
    config: dict[str, Any],
) -> tuple[float, float]:
    """Estime (energie_wh, co2e_g) d'un appel externe.

    ⚠️ ESTIMATION, pas une mesure. Les facteurs viennent de `knowledge/greenit.yaml`
    et sont documentés comme ordres de grandeur. La valeur d'usage est comparative :
    « ce run a coûté 3x le précédent », « le cache a évité 40 % de l'énergie ».

    `unites` accepte les mêmes clés que le grand livre :
      input_tokens / output_tokens / cache_read_input_tokens (LLM)
      requetes / credits (APIs à la requête)
    Les clés inconnues sont ignorées (pas de crash sur un fournisseur nouveau).
    """
    facteurs = config.get("empreinte") or CONFIG_DEFAUT["empreinte"]
    unites = unites or {}

    def _f(cle: str, defaut: float) -> float:
        try:
            return float(facteurs.get(cle, defaut))
        except (TypeError, ValueError):
            return defaut

    def _u(cle: str) -> float:
        try:
            return float(unites.get(cle, 0.0) or 0.0)
        except (TypeError, ValueError):
            return 0.0

    energie_wh = 0.0
    energie_wh += _u("input_tokens") / 1000.0 * _f("wh_par_1k_tokens_entree", 0.05)
    energie_wh += _u("output_tokens") / 1000.0 * _f("wh_par_1k_tokens_sortie", 0.30)
    energie_wh += (
        (_u("cache_read_input_tokens") + _u("cache_creation_input_tokens"))
        / 1000.0
        * _f("wh_par_1k_tokens_cache_lecture", 0.005)
    )
    energie_wh += (_u("requetes") + _u("credits")) * _f("wh_par_requete_http", 0.10)

    try:
        mo = max(0.0, float(octets or 0)) / 1_000_000.0
    except (TypeError, ValueError):
        mo = 0.0
    energie_wh += mo * _f("wh_par_mo_transfere", 0.06)

    # kWh × (g/kWh) = g
    co2e_g = (energie_wh / 1000.0) * intensite_carbone(region, config)
    return energie_wh, co2e_g
