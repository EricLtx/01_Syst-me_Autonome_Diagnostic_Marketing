"""
test_vault_schema.py — critères d'acceptation Phase A.

Couvre les 4 propriétés fondamentales de FicheProspect :
  1. Validation OK (champs valides acceptés)
  2. Validation KO (valeurs illégales → erreur explicite)
  3. Round-trip YAML (sérialiser → YAML → re-parser → objet identique)
  4. Préservation des champs extra (annotations humaines jamais effacées)
"""

from __future__ import annotations

from datetime import date

import pytest
import yaml
from pydantic import ValidationError

from diagnostic.vault_schema import (
    TRANSITIONS_AGENT,
    TRANSITIONS_LEGALES,
    FicheProspect,
    Marche,
    Statut,
)

# ---------------------------------------------------------------------------
# Fixture partagée
# ---------------------------------------------------------------------------

FICHE_MINIMALE = dict(
    persona=1,
    marche="quebec",
    statut="decouvert",
    nom="Chauffage ABC inc.",
    date_creation="2026-06-09",
)


# ---------------------------------------------------------------------------
# 1. Validation OK
# ---------------------------------------------------------------------------

def test_fiche_minimale_valide():
    fiche = FicheProspect(**FICHE_MINIMALE)
    assert fiche.nom == "Chauffage ABC inc."
    assert fiche.statut == "decouvert"   # use_enum_values=True → str
    assert fiche.marche == "quebec"
    assert fiche.persona == 1
    assert fiche.type == "prospect"


def test_fiche_complete_valide():
    fiche = FicheProspect(
        **FICHE_MINIMALE,
        site_web="https://chauffage-abc.ca",
        score_global=42,
        gaps_majeurs=["site_web", "avis"],
        source_decouverte="apollo",
        date_diagnostic=date(2026, 6, 10),
        rapport="[[30-Diagnostics/chauffage-abc-inc]]",
    )
    assert fiche.score_global == 42
    assert fiche.gaps_majeurs == ["site_web", "avis"]


def test_score_global_bornes_extremes():
    FicheProspect(**FICHE_MINIMALE, score_global=0)
    FicheProspect(**FICHE_MINIMALE, score_global=100)


# ---------------------------------------------------------------------------
# 2. Validation KO
# ---------------------------------------------------------------------------

def test_statut_inconnu_leve_erreur():
    with pytest.raises(ValidationError) as exc_info:
        FicheProspect(**{**FICHE_MINIMALE, "statut": "en_cours"})
    assert "statut" in str(exc_info.value).lower()


def test_persona_positif_ou_absent_est_valide():
    """Encodait B1 (ADR 0003) : `persona: Literal[1, 2]` plafonnait le système
    à deux personas à jamais — `persona=3` levait `ValidationError`. Ce n'est
    pas une régression silencieuse : c'est le changement de contrat que
    l'ADR 0003 documente explicitement (persona devient un champ legacy,
    `int | None` borné `ge=1`, sans rôle de sélection — c'est `secteur_id`/
    `icp_id` qui porte désormais le choix de rubrique/vocabulaire). Ce test
    encode maintenant l'invariant inverse : positif si fourni, ou absent —
    jamais négatif/nul."""
    fiche = FicheProspect(**{**FICHE_MINIMALE, "persona": 3})
    assert fiche.persona == 3

    sans_persona = {k: v for k, v in FICHE_MINIMALE.items() if k != "persona"}
    assert FicheProspect(**sans_persona).persona is None

    with pytest.raises(ValidationError):
        FicheProspect(**{**FICHE_MINIMALE, "persona": 0})


def test_marche_slug_libre_est_valide():
    """Encodait B2 (ADR 0003) : `Marche` était un enum fermé à cinq valeurs —
    `marche="australie"` (absente de l'enum) levait `ValidationError`, tout
    comme `marche="ontario"` l'aurait fait alors que c'est un marché légitime.
    C'est le changement de contrat documenté par l'ADR 0003 : `marche` devient
    un slug libre (motif générique), pas une régression silencieuse. Ce test
    encode maintenant l'invariant inverse : tout slug bien formé est accepté,
    seul un format illégal (majuscule, espace) est refusé."""
    fiche = FicheProspect(**{**FICHE_MINIMALE, "marche": "australie"})
    assert fiche.marche == "australie"

    with pytest.raises(ValidationError):
        FicheProspect(**{**FICHE_MINIMALE, "marche": "Ontario"})  # majuscule interdite


def test_score_global_hors_borne_haut():
    with pytest.raises(ValidationError):
        FicheProspect(**{**FICHE_MINIMALE, "score_global": 101})


def test_score_global_hors_borne_bas():
    with pytest.raises(ValidationError):
        FicheProspect(**{**FICHE_MINIMALE, "score_global": -1})


def test_champ_obligatoire_manquant():
    """nom est obligatoire."""
    data = {k: v for k, v in FICHE_MINIMALE.items() if k != "nom"}
    with pytest.raises(ValidationError):
        FicheProspect(**data)


# ---------------------------------------------------------------------------
# 3. Round-trip YAML (critère §8.1)
# ---------------------------------------------------------------------------

def test_round_trip_yaml_champs_identiques():
    """Sérialiser en YAML puis re-parser doit donner le même objet."""
    original = FicheProspect(
        **FICHE_MINIMALE,
        score_global=55,
        gaps_majeurs=["site_web"],
        date_diagnostic=date(2026, 6, 10),
    )

    # Sérialisation → YAML
    data_out = original.model_dump(mode="json")
    yaml_str = yaml.dump(data_out, allow_unicode=True, sort_keys=False)

    # Désérialisation ← YAML
    data_in = yaml.safe_load(yaml_str)
    restauree = FicheProspect.model_validate(data_in)

    assert restauree.nom == original.nom
    assert restauree.statut == original.statut
    assert restauree.marche == original.marche
    assert restauree.score_global == original.score_global
    assert restauree.gaps_majeurs == original.gaps_majeurs
    assert restauree.date_diagnostic == original.date_diagnostic


def test_round_trip_yaml_valeurs_nulles():
    """Les champs optionnels à null survivent au round-trip."""
    original = FicheProspect(**FICHE_MINIMALE)
    data_out = original.model_dump(mode="json")
    yaml_str = yaml.dump(data_out, allow_unicode=True)
    data_in = yaml.safe_load(yaml_str)
    restauree = FicheProspect.model_validate(data_in)

    assert restauree.score_global is None
    assert restauree.rapport is None
    assert restauree.date_diagnostic is None


# ---------------------------------------------------------------------------
# 4. Préservation des champs extra (annotations humaines)
# ---------------------------------------------------------------------------

def test_champs_extra_preserves_en_memoire():
    """Un champ non défini dans le schéma est stocké et restituable."""
    fiche = FicheProspect(**FICHE_MINIMALE, note_humaine="Très prometteur")
    data = fiche.model_dump()
    assert data.get("note_humaine") == "Très prometteur"


def test_champs_extra_survivent_au_round_trip_yaml():
    """Les annotations humaines ne sont pas perdues lors d'un round-trip YAML."""
    original = FicheProspect(
        **FICHE_MINIMALE,
        note_interne="rappeler en juillet",
        priorite=2,
    )
    data_out = original.model_dump(mode="json")
    yaml_str = yaml.dump(data_out, allow_unicode=True)
    data_in = yaml.safe_load(yaml_str)
    restauree = FicheProspect.model_validate(data_in)

    assert restauree.model_extra.get("note_interne") == "rappeler en juillet"
    assert restauree.model_extra.get("priorite") == 2


# ---------------------------------------------------------------------------
# 5. Machine à états — cohérence des constantes
# ---------------------------------------------------------------------------

def test_transitions_agent_sous_ensemble_legales():
    """Chaque transition agent doit être légale (cohérence TRANSITIONS_*)."""
    for depart, cibles_agent in TRANSITIONS_AGENT.items():
        cibles_legales = TRANSITIONS_LEGALES.get(depart, set())
        assert cibles_agent.issubset(cibles_legales), (
            f"Transition agent {depart} → {cibles_agent} "
            f"dépasse les transitions légales {cibles_legales}"
        )


def test_tous_statuts_couverts_dans_transitions_legales():
    """Chaque valeur de Statut a une entrée dans TRANSITIONS_LEGALES."""
    for s in Statut:
        assert s in TRANSITIONS_LEGALES, f"Statut {s} absent de TRANSITIONS_LEGALES"
