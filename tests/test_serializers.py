"""
test_serializers.py — tests unitaires de diagnostic/serializers.py.

Aucune I/O : tout est en mémoire.
"""
from __future__ import annotations

from datetime import date

import pytest

from diagnostic.models import Company, Diagnostic, Gap
from diagnostic.serializers import diagnostic_to_fiche, diagnostic_to_rapport_md
from diagnostic.vault_schema import FicheProspect

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FICHE_BASE = dict(
    persona=1, marche="quebec", statut="decouvert",
    nom="Chauffage ABC inc.", date_creation="2026-06-09",
    site_web="https://chauffage-abc.ca",
)


def _fiche(**extra) -> FicheProspect:
    return FicheProspect(**{**FICHE_BASE, **extra})


_DEFAULT_FAILLES = [
    Gap(dimension="presence_locale", gravite="haute",   preuve="GBP non vérifié"),
    Gap(dimension="avis",            gravite="haute",   preuve="Aucun avis en ligne"),
    Gap(dimension="presence_locale", gravite="moyenne", preuve="Photos absentes"),
]


def _diag(
    score_global: float = 38.5,
    failles: list[Gap] | None = None,
    mini_audit: str = "Audit de test.",
    accroche: str = "Accroche de test.",
) -> Diagnostic:
    # Utiliser is not None pour ne pas traiter [] comme falsy
    failles_effectives = _DEFAULT_FAILLES if failles is None else failles
    return Diagnostic(
        entreprise=Company(nom="Chauffage ABC inc.", url="https://chauffage-abc.ca"),
        scores={
            "global": score_global,
            "site_web": 45.0,
            "presence_locale": 20.0,
            "avis": 15.0,
        },
        failles=failles_effectives,
        mini_audit=mini_audit,
        accroche=accroche,
        meta={"collecte_le": "2026-06-09T12:00:00+00:00",
              "collecteurs": ["website", "gbp", "reviews", "seo", "social"],
              "rubrique": 1},
    )


# ---------------------------------------------------------------------------
# diagnostic_to_fiche
# ---------------------------------------------------------------------------

class TestDiagnosticToFiche:
    def test_score_global_mappe_correctement(self):
        fiche = diagnostic_to_fiche(_diag(score_global=38.5), _fiche())
        # Python 3 utilise l'arrondi bancaire : round(38.5) = 38 (vers le pair)
        assert fiche.score_global == round(38.5)
        assert isinstance(fiche.score_global, int)

    def test_score_global_clampe_a_100(self):
        fiche = diagnostic_to_fiche(_diag(score_global=150.0), _fiche())
        assert fiche.score_global == 100

    def test_score_global_clampe_a_0(self):
        fiche = diagnostic_to_fiche(_diag(score_global=-5.0), _fiche())
        assert fiche.score_global == 0

    def test_gaps_majeurs_dedupliques(self):
        """Deux failles sur 'presence_locale' → une seule occurrence dans gaps_majeurs."""
        fiche = diagnostic_to_fiche(_diag(), _fiche())
        assert fiche.gaps_majeurs.count("presence_locale") == 1

    def test_gaps_majeurs_ordre_preserve(self):
        """L'ordre des dimensions de la première occurrence est conservé."""
        fiche = diagnostic_to_fiche(_diag(), _fiche())
        assert fiche.gaps_majeurs[0] == "presence_locale"
        assert fiche.gaps_majeurs[1] == "avis"

    def test_date_diagnostic_est_aujourd_hui(self):
        fiche = diagnostic_to_fiche(_diag(), _fiche())
        assert fiche.date_diagnostic == date.today()

    def test_identite_preservee(self):
        """nom, persona, marche, statut ne sont pas modifiés."""
        fiche = diagnostic_to_fiche(_diag(), _fiche())
        assert fiche.nom == "Chauffage ABC inc."
        assert fiche.persona == 1
        assert fiche.marche == "quebec"
        assert fiche.statut == "decouvert"  # statut inchangé par ce serializer

    def test_champs_extra_preserves(self):
        """Les annotations humaines survivent à la projection."""
        fiche = diagnostic_to_fiche(_diag(), _fiche(note_humaine="très prometteur"))
        assert fiche.model_extra.get("note_humaine") == "très prometteur"

    def test_aucune_faille_donne_liste_vide(self):
        fiche = diagnostic_to_fiche(_diag(failles=[]), _fiche())
        assert fiche.gaps_majeurs == []


# ---------------------------------------------------------------------------
# diagnostic_to_rapport_md
# ---------------------------------------------------------------------------

class TestDiagnosticToRapportMd:
    def _rapport(self, **kwargs) -> str:
        return diagnostic_to_rapport_md(_diag(**kwargs))

    def test_contient_nom_entreprise(self):
        assert "Chauffage ABC inc." in self._rapport()

    def test_contient_score_global(self):
        rapport = self._rapport(score_global=39.0)
        assert "39" in rapport

    def test_contient_mini_audit(self):
        rapport = self._rapport(mini_audit="Analyse détaillée ici.")
        assert "Analyse détaillée ici." in rapport

    def test_contient_accroche(self):
        rapport = self._rapport(accroche="Votre marque mérite mieux.")
        assert "Votre marque mérite mieux." in rapport

    def test_contient_dimensions_scores(self):
        rapport = self._rapport()
        assert "site_web" in rapport
        assert "presence_locale" in rapport

    def test_contient_gaps_detectes(self):
        rapport = self._rapport()
        assert "GBP non vérifié" in rapport
        assert "Aucun avis en ligne" in rapport

    def test_contient_barre_visuelle(self):
        """Le rapport inclut une représentation visuelle des scores."""
        rapport = self._rapport()
        assert "█" in rapport or "░" in rapport

    def test_frontmatter_yaml_present(self):
        """Le rapport commence par un frontmatter YAML valide."""
        rapport = self._rapport()
        assert rapport.startswith("---\n")
        assert "type: rapport" in rapport
        assert "score_global:" in rapport

    def test_wikilink_non_inclus(self):
        """diagnostic_to_rapport_md ne génère pas de wikilink (c'est vault_runner qui le fait)."""
        rapport = self._rapport()
        assert "[[" not in rapport
