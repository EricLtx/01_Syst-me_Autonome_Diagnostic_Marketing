"""
test_legitimite.py — diagnostic/collectors/legitimite.py (ADR 0004 D8, Retenu 2).

Aucune I/O : le collecteur ne fait jamais son propre fetch, il consomme
`_website_signals` injecté (même patron que seo.py/social.py).
"""

from __future__ import annotations

from diagnostic.collectors.legitimite import LegitimiteCollector
from diagnostic.models import Company

MOTIFS = {
    "licence_professionnelle": ["licence rbq", "maître mécanicien"],
    "programme_subvention": ["chauffez vert"],
}


def _company() -> Company:
    return Company(nom="Test HVAC", url="https://exemple.test")


class TestTroisEtats:
    def test_site_injoignable_produit_none_partout_jamais_false(self):
        """Échec technique ≠ observation négative (même règle que _places.py)."""
        c = LegitimiteCollector(motifs=MOTIFS)
        c._website_signals = {"reachable": False, "status": 0}
        result = c.collect(_company())
        assert result == {"licence_professionnelle": None, "programme_subvention": None}

    def test_signaux_non_injectes_produit_none_partout(self):
        """Avant l'injection par le pipeline (_website_signals = None)."""
        c = LegitimiteCollector(motifs=MOTIFS)
        result = c.collect(_company())
        assert result == {"licence_professionnelle": None, "programme_subvention": None}

    def test_motifs_non_configures_produit_dict_vide(self):
        """Aucun motif pour ce marché/secteur → aucune clé, jamais un `False`
        fabriqué (anti-fuite B5, même discipline que mentions_offre)."""
        c = LegitimiteCollector(motifs=None)
        c._website_signals = {"reachable": True, "_seo_text": "licence rbq 12345"}
        assert c.collect(_company()) == {}

    def test_categorie_avec_liste_vide_reste_none(self):
        c = LegitimiteCollector(motifs={"licence_professionnelle": []})
        c._website_signals = {"reachable": True, "_seo_text": "peu importe"}
        assert c.collect(_company()) == {"licence_professionnelle": None}

    def test_reachable_true_mais_motif_absent_du_texte_donne_false(self):
        """Observation NÉGATIVE réelle : le site a été lu, le motif n'y est pas."""
        c = LegitimiteCollector(motifs=MOTIFS)
        c._website_signals = {"reachable": True, "_seo_text": "installation thermopompe"}
        result = c.collect(_company())
        assert result == {"licence_professionnelle": False, "programme_subvention": False}

    def test_motif_present_donne_true(self):
        c = LegitimiteCollector(motifs=MOTIFS)
        c._website_signals = {
            "reachable": True,
            "_seo_text": "Entreprise licenciée — Licence RBQ 5678-1234, membre Chauffez Vert",
        }
        result = c.collect(_company())
        assert result == {"licence_professionnelle": True, "programme_subvention": True}

    def test_detection_insensible_a_la_casse(self):
        c = LegitimiteCollector(motifs=MOTIFS)
        c._website_signals = {"reachable": True, "_seo_text": "LICENCE RBQ affichée"}
        assert c.collect(_company())["licence_professionnelle"] is True


class TestInjectionPipeline:
    def test_website_signals_par_defaut_none(self):
        c = LegitimiteCollector()
        assert c._website_signals is None

    def test_hasattr_website_signals_pour_injection_pipeline(self):
        """DiagnosticPipeline injecte `_website_signals` sur tout collecteur
        qui porte cet attribut — vérifié ici pour ne jamais régresser."""
        c = LegitimiteCollector()
        assert hasattr(c, "_website_signals")
