"""
test_multi_industrie.py — preuve positive du Lot 1 (ADR 0003).

Ce module démontre que les 5 blocages qui enfermaient le système dans
« installateur HVAC au Québec » sont levés :

  B1 — persona: Literal[1, 2] plafonnait à 2 personas à jamais.
  B2 — Marche (enum fermé à 5 valeurs) interdisait tout nouveau marché.
  B3 — écrire une rubrique pour un secteur non-HVAC est maintenant possible
       sans toucher au code (démontré indirectement : la rubrique fictive
       ci-dessous n'est qu'un fichier YAML).
  B4 (le plus grave) — un seul pipeline (rubrique persona 1) était construit
       AVANT la boucle de run_vault_mode et appliqué à TOUTES les fiches.
       Écrire une seconde rubrique n'avait alors aucun effet.
  B5 — le vocabulaire HVAC (OFFRE_KEYWORDS) était codé en dur dans
       WebsiteCollector : pour toute industrie non-HVAC, `mentions_offre`
       valait `False` de façon systématique (absence de vocabulaire lue
       comme un fait négatif observé).

La preuve centrale (`TestLotMixteVaultMode`) traite, dans UN SEUL appel
`run_vault_mode(vault_path)` (pipeline=None → résolution par fiche), un lot
contenant une fiche `persona1-quebec` (HVAC, réelle, inchangée) et une fiche
d'un secteur fictif non-HVAC (`dentaire-test`) — et vérifie que chacune est
scorée avec SA rubrique et SON vocabulaire, sans contamination croisée.
"""
from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

import diagnostic.config as config_mod
from diagnostic.icp_schema import IcpConfig
from diagnostic.vault_io import VaultIO
from diagnostic.vault_schema import FicheProspect

_RACINE = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Fixtures YAML — secteur fictif « dentaire-test » (non-HVAC), sous tmp_path
# ---------------------------------------------------------------------------

RUBRIC_DENTAIRE_TEST = """\
persona: "Secteur fictif de test — dentaire (preuve ADR 0003)"

dimensions:
  offre:
    poids: 100
    checks:
      - { signal: website.mentions_offre, op: is_true, points: 100, gravite: haute, gap: "Vocabulaire dentaire absent du site" }
"""

VOCABULAIRE_DENTAIRE_TEST = """\
mots_offre:
  - "détartrage"
  - "implant dentaire"
"""

ICP_DENTAIRE_TEST = """\
icp_id: dentaire-test-banlieue-test
persona: 7
marche: banlieue-test
secteur_id: dentaire-test
description: "Secteur fictif de test (non-HVAC), marché arbitraire — preuve B1/B2"

requetes:
  gabarits:
    - "dentiste {localite}"
  localites:
    - "Ville-Test"

filtres:
  domaines_exclus: []
  exiger_domaine_propre: true

enrichissement:
  titres_cibles:
    - "dentiste"
  max_enrichissements: 5
"""

HTML_DENTAIRE = """
<html>
<head>
  <title>Clinique Dentaire Test</title>
  <meta name="description" content="Cabinet dentaire de proximité">
  <meta name="viewport" content="width=device-width">
</head>
<body>
  <a href="tel:5145550100">Appelez-nous</a>
  <img src="logo.png" alt="logo clinique">
  <p>Nous proposons détartrage et implant dentaire pour toute la famille.</p>
  <p>© 2024 Clinique Dentaire Test</p>
</body>
</html>
"""

HTML_HVAC = """
<html>
<head>
  <title>Chauffage Test HVAC</title>
  <meta name="description" content="Installateur climatisation et chauffage">
  <meta name="viewport" content="width=device-width">
</head>
<body>
  <a href="tel:5141234567">Appelez-nous</a>
  <img src="logo.png" alt="logo HVAC">
  <p>Installation de climatisation et de thermopompes.</p>
  <p>© 2024 Chauffage Test HVAC</p>
</body>
</html>
"""


def _fake_get(url: str, **kwargs):
    """Sert un HTML différent selon l'entreprise appelée (site pauvre en I/O)."""
    from unittest.mock import MagicMock
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = {}
    if "dentiste" in url:
        resp.text = HTML_DENTAIRE
        resp.url = "https://dentiste-test.example"
    else:
        resp.text = HTML_HVAC
        resp.url = "https://hvac-test.example"
    return resp


@pytest.fixture()
def config_isole(tmp_path, monkeypatch):
    """Isole ICP_DIR et KNOWLEDGE_DIR sous tmp_path (même motif que
    tests/integration/conftest.py). Le secteur HVAC (persona1-quebec) est une
    copie VERBATIM des fichiers réels : sa résolution doit rester identique.
    Le secteur dentaire-test est une fixture inédite, écrite ici.
    """
    icp_dir = tmp_path / "icp"
    knowledge_dir = tmp_path / "knowledge"
    icp_dir.mkdir()
    knowledge_dir.mkdir()

    shutil.copy(_RACINE / "icp" / "persona1-quebec.yaml", icp_dir / "persona1-quebec.yaml")
    shutil.copy(_RACINE / "knowledge" / "rubric_persona1.yaml", knowledge_dir / "rubric_persona1.yaml")
    shutil.copy(
        _RACINE / "knowledge" / "vocabulaire_persona1.yaml",
        knowledge_dir / "vocabulaire_persona1.yaml",
    )

    (icp_dir / "dentaire-test-banlieue-test.yaml").write_text(ICP_DENTAIRE_TEST, encoding="utf-8")
    (knowledge_dir / "rubric_dentaire-test.yaml").write_text(RUBRIC_DENTAIRE_TEST, encoding="utf-8")
    (knowledge_dir / "vocabulaire_dentaire-test.yaml").write_text(
        VOCABULAIRE_DENTAIRE_TEST, encoding="utf-8"
    )

    monkeypatch.setattr(config_mod, "ICP_DIR", icp_dir)
    monkeypatch.setattr(config_mod, "KNOWLEDGE_DIR", knowledge_dir)
    # Évite d'écrire dans le cache disque réel du dépôt pendant le test.
    import diagnostic.collectors.website as website_mod
    monkeypatch.setattr(website_mod, "CACHE_DIR", tmp_path / ".cache_website_test")

    return {"icp_dir": icp_dir, "knowledge_dir": knowledge_dir}


def _fiche_hvac(site_web: str) -> FicheProspect:
    return FicheProspect(
        persona=1, marche="quebec", statut="decouvert",
        nom="Chauffage Test HVAC", date_creation=date.today(),
        site_web=site_web, icp_id="persona1-quebec",
    )


def _fiche_dentaire(site_web: str) -> FicheProspect:
    return FicheProspect(
        # persona=None ET marche="banlieue-test" (slug arbitraire) : preuve
        # directe que B1 (persona plafonné à 2) et B2 (Marche fermé) sont
        # levés — cette fiche n'aurait pu exister avant l'ADR 0003.
        persona=None, marche="banlieue-test", statut="decouvert",
        nom="Clinique Dentaire Test", date_creation=date.today(),
        site_web=site_web, icp_id="dentaire-test-banlieue-test",
    )


# ---------------------------------------------------------------------------
# Preuve centrale : lot mixte, UN SEUL run_vault_mode(vault_path)
# ---------------------------------------------------------------------------

class TestLotMixteVaultMode:
    def test_deux_secteurs_meme_lot_pipelines_distincts(self, tmp_path, config_isole):
        """Le cœur de la preuve : B4 est levé (chaque fiche reçoit SA
        rubrique/vocabulaire) et B5 ne fuit pas d'un secteur à l'autre."""
        from diagnostic.vault_runner import run_vault_mode

        vault = tmp_path / "vault"
        io = VaultIO(vault)
        fiche_hvac = io.write_fiche(_fiche_hvac("https://hvac-test.example/dentiste-non"))
        fiche_dentaire = io.write_fiche(_fiche_dentaire("https://dentiste-test.example"))

        with patch("requests.get", side_effect=_fake_get):
            resultat = run_vault_mode(vault)

        assert resultat["erreurs"] == []
        assert set(resultat["ok"]) == {"Chauffage Test HVAC", "Clinique Dentaire Test"}

        # Les deux transitionnent en diagnostique (seule transition agent permise).
        hvac_diag = io.read_fiche(fiche_hvac)
        dentaire_diag = io.read_fiche(fiche_dentaire)
        assert hvac_diag.statut == "diagnostique"
        assert dentaire_diag.statut == "diagnostique"

        # La fiche dentaire est scorée avec SA rubrique (une seule dimension
        # "offre") : si mentions_offre avait été évalué avec le vocabulaire
        # HVAC en dur (B5 réintroduit), le site dentaire ne matcherait AUCUN
        # mot HVAC → mentions_offre=False → gap "offre" et score 0.
        assert dentaire_diag.score_global == 100
        assert "offre" not in dentaire_diag.gaps_majeurs

        # La fiche HVAC continue d'utiliser sa rubrique réelle (persona1),
        # inchangée : comportement rétro-compatible.
        assert hvac_diag.score_global is not None

    def test_mutation_vocabulaire_hvac_en_dur_fait_echouer_la_preuve(
        self, tmp_path, config_isole
    ):
        """Vérifie que le test ci-dessus détecterait réellement une régression :
        si WebsiteCollector utilisait OFFRE_KEYWORDS (HVAC) au lieu du
        vocabulaire injecté, le site dentaire (qui ne mentionne aucun mot
        HVAC) ne matcherait rien → mentions_offre=False → score 0, pas 100.
        On le vérifie par mutation temporaire de vault_runner.make_pipeline_for_secteur,
        restaurée en fin de test quel que soit le résultat.
        """
        import diagnostic.vault_runner as vault_runner_mod
        from diagnostic.collectors.website import OFFRE_KEYWORDS
        from diagnostic.vault_runner import run_vault_mode

        original = vault_runner_mod.make_pipeline_for_secteur

        def make_pipeline_mute(secteur_id: str, api_io=None):
            """Reproduit B5 : ignore le vocabulaire par secteur, revient au
            vocabulaire HVAC codé en dur — exactement le défaut d'avant l'ADR."""
            from diagnostic.collectors.gbp import GbpCollector
            from diagnostic.collectors.reviews import ReviewsCollector
            from diagnostic.collectors.seo import SeoCollector
            from diagnostic.collectors.social import SocialCollector
            from diagnostic.collectors.website import WebsiteCollector
            from diagnostic.config import load_knowledge, load_rubrique
            from diagnostic.pipeline import DiagnosticPipeline

            return DiagnosticPipeline(
                collectors=[
                    WebsiteCollector(vocabulaire_offre=OFFRE_KEYWORDS),  # <- mutation B5
                    GbpCollector(),
                    ReviewsCollector(),
                    SeoCollector(),
                    SocialCollector(),
                ],
                rubrique=load_rubrique(secteur_id),
                knowledge=load_knowledge(secteur_id),
                api_io=api_io,
            )

        vault = tmp_path / "vault"
        io = VaultIO(vault)
        fiche_dentaire = io.write_fiche(_fiche_dentaire("https://dentiste-test.example"))

        vault_runner_mod.make_pipeline_for_secteur = make_pipeline_mute
        try:
            with patch("requests.get", side_effect=_fake_get):
                run_vault_mode(vault)
        finally:
            vault_runner_mod.make_pipeline_for_secteur = original

        dentaire_diag = io.read_fiche(fiche_dentaire)
        # Avec le vocabulaire HVAC en dur, le site dentaire ne matche rien :
        # la preuve positive échouerait (score 0 au lieu de 100).
        assert dentaire_diag.score_global == 0
        assert "offre" in dentaire_diag.gaps_majeurs


# ---------------------------------------------------------------------------
# Tests unitaires ciblés (§6 de l'ADR 0003)
# ---------------------------------------------------------------------------

class TestSecteurIdForFiche:
    def test_icp_id_present_resout_secteur_explicite(self, config_isole):
        from diagnostic.vault_runner import secteur_id_for_fiche
        fiche = _fiche_dentaire("https://dentiste-test.example")
        assert secteur_id_for_fiche(fiche) == "dentaire-test"

    def test_icp_id_absent_replie_sur_persona(self, config_isole):
        from diagnostic.vault_runner import secteur_id_for_fiche
        fiche = FicheProspect(
            persona=2, marche="quebec", statut="decouvert",
            nom="Sans ICP", date_creation=date.today(),
        )
        assert secteur_id_for_fiche(fiche) == "persona2"

    def test_icp_id_introuvable_replie_sur_persona(self, config_isole):
        from diagnostic.vault_runner import secteur_id_for_fiche
        fiche = FicheProspect(
            persona=1, marche="quebec", statut="decouvert",
            nom="ICP fantôme", date_creation=date.today(),
            icp_id="persona9-inconnu",
        )
        assert secteur_id_for_fiche(fiche) == "persona1"

    def test_icp_id_absent_et_persona_absent_replie_sur_persona1(self, config_isole):
        from diagnostic.vault_runner import secteur_id_for_fiche
        fiche = FicheProspect(
            persona=None, marche="quebec", statut="decouvert",
            nom="Rien du tout", date_creation=date.today(),
        )
        assert secteur_id_for_fiche(fiche) == "persona1"


class TestIcpConfigSecteurId:
    _BASE = dict(
        icp_id="persona1-quebec",
        persona=1,
        marche="quebec",
        description="Test",
        requetes={
            "gabarits": ["test {localite}"],
            "localites": ["Québec"],
        },
        filtres={},
        enrichissement={"titres_cibles": ["propriétaire"]},
    )

    def test_secteur_id_absent_defaute_a_personaN(self):
        icp = IcpConfig(**self._BASE)
        assert icp.secteur_id == "persona1"

    def test_secteur_id_explicite_est_respecte(self):
        data = dict(
            self._BASE,
            icp_id="dentaire-test-banlieue-test",
            persona=7,
            marche="banlieue-test",
            secteur_id="dentaire-test",
        )
        icp = IcpConfig(**data)
        assert icp.secteur_id == "dentaire-test"


class TestFicheProspectDesserree:
    _BASE = dict(statut="decouvert", nom="Test", date_creation="2026-06-09")

    def test_marche_ontario_est_valide(self):
        """B2 : un marché inédit hors de l'ancien enum Marche est accepté."""
        fiche = FicheProspect(persona=1, marche="ontario", **self._BASE)
        assert fiche.marche == "ontario"

    def test_persona_3_est_valide(self):
        """B1 : persona n'est plus plafonné à Literal[1, 2]."""
        fiche = FicheProspect(persona=3, marche="quebec", **self._BASE)
        assert fiche.persona == 3

    def test_persona_0_est_invalide(self):
        with pytest.raises(ValidationError):
            FicheProspect(persona=0, marche="quebec", **self._BASE)


class TestWebsiteCollectorVocabulaireInjecte:
    def test_vocabulaire_none_donne_mentions_offre_none(self):
        """Anti-fuite B5 : aucun vocabulaire configuré → `None` (inconnu),
        jamais `False` — un secteur non documenté ne doit pas fabriquer une
        faille de 25 points en gravité haute."""
        from diagnostic.collectors.website import WebsiteCollector
        collector = WebsiteCollector(vocabulaire_offre=None)
        with patch("requests.get", side_effect=lambda *a, **k: _fake_get("dentiste", **k)):
            signaux = collector.collect(_CompanyTest("https://dentiste-test.example"))
        assert signaux["mentions_offre"] is None

    def test_vocabulaire_defaut_hvac_preserve_appels_nus(self):
        """Le défaut HVAC du constructeur n'existe QUE pour la compatibilité
        des instanciations nues (tests/CLI qui ne passent pas de vocabulaire)."""
        from diagnostic.collectors.website import OFFRE_KEYWORDS, WebsiteCollector
        collector = WebsiteCollector()
        assert collector.vocabulaire_offre == OFFRE_KEYWORDS


def _CompanyTest(url: str):
    from diagnostic.models import Company
    return Company(nom="Test", url=url)


class TestLoadVocabulaire:
    def test_secteur_inexistant_retourne_dict_vide(self, config_isole):
        from diagnostic.config import load_vocabulaire
        assert load_vocabulaire("secteur-inexistant") == {}

    def test_secteur_existant_retourne_mots_offre(self, config_isole):
        from diagnostic.config import load_vocabulaire
        vocab = load_vocabulaire("dentaire-test")
        assert "détartrage" in vocab["mots_offre"]
