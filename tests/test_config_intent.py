"""
test_config_intent.py — chargeurs YAML de l'axe intention (ADR 0004).

`load_rubrique_intention`, `load_vocabulaire_intention`, `load_certifications` :
mêmes garanties de dégradation propre que les chargeurs J1/ADR 0003 déjà en
place (`load_rubrique`, `load_vocabulaire`).
"""

from __future__ import annotations

from diagnostic.config import (
    load_certifications,
    load_rubrique_intention,
    load_vocabulaire_intention,
)


class TestLoadRubriqueIntention:
    def test_secteur_reel_retourne_un_dict_avec_dimensions(self):
        rubrique = load_rubrique_intention(1)
        assert rubrique is not None
        assert "dimensions" in rubrique
        assert "recrutement_production" in rubrique["dimensions"]

    def test_secteur_inexistant_retourne_none_pas_dict_vide(self):
        """Distinction nécessaire : `None` = « pas d'axe intention pour ce
        secteur » (repli propre) ≠ `{}` = « axe vide » (configuration
        suspecte)."""
        assert load_rubrique_intention("secteur-totalement-inexistant") is None

    def test_check_recrutement_declare_nature_evenement(self):
        rubrique = load_rubrique_intention(1)
        check = rubrique["dimensions"]["recrutement_production"]["checks"][0]
        assert check["nature"] == "evenement"
        assert check["citable"] is True
        assert "date_signal" in check


class TestLoadVocabulaireIntention:
    def test_secteur_reel_contient_des_mots_de_recrutement(self):
        vocab = load_vocabulaire_intention(1)
        assert "mots_recrutement" in vocab
        assert any("recrut" in m for m in vocab["mots_recrutement"])

    def test_secteur_inexistant_retourne_dict_vide(self):
        """Même contrat que load_vocabulaire : jamais d'exception."""
        assert load_vocabulaire_intention("secteur-totalement-inexistant") == {}


class TestLoadCertifications:
    def test_marche_quebec_contient_licence_professionnelle(self):
        motifs = load_certifications("quebec")
        assert motifs is not None
        assert "licence rbq" in [m.lower() for m in motifs["licence_professionnelle"]]

    def test_marche_inexistant_retourne_none(self):
        assert load_certifications("marche-totalement-inexistant") is None
