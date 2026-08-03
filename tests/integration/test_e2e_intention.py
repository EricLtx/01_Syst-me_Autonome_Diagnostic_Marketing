"""
test_e2e_intention.py — axe intention (ADR 0004), bout en bout, persona HVAC.

Chaîne réellement exercée : fiche `decouvert` → WebsiteCollector (vrai GET
HTTP, escalade réelle vers une page carrières) → LegitimiteCollector (dérivé,
zéro réseau) → scoring de besoin (inchangé) → `diagnostic/intent.py`
(évaluation de l'axe intention, zéro agrégation) → sérialisation vault.

Preuve centrale (§ tâche) : deux prospects de BESOIN IDENTIQUE (même gabarit
HTML `html_site()` « pauvre » côté faux serveur), l'un affichant un
recrutement daté, l'autre non, ressortent avec un `evenements_intention`
strictement différent — jamais un `score_global` différent pour autant.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from diagnostic.models import Company
from diagnostic.vault_io import VaultIO


def _pipeline(api_io):
    import run_diagnostic
    return run_diagnostic._build_pipeline(api_io=api_io)


# ---------------------------------------------------------------------------
# 1. Discrimination à besoin égal — LA preuve du Lot 1/2
# ---------------------------------------------------------------------------

class TestDiscriminationABesoinEgal:
    def test_evenements_intention_diffusent_entre_jumeaux_de_besoin(
        self, env_faux_api, journal_vierge, api_io, serveur
    ):
        """Climatisation Tremblay (recrute=False) et Thermo Marchand
        (recrute=True) partagent EXACTEMENT le même gabarit `html_site()`
        « pauvre » (même besoin) — seule la présence d'un recrutement daté
        distingue les deux. C'est la preuve exigée par l'ADR 0004 (D12.3)."""
        pipeline = _pipeline(api_io)

        sans_recrutement = pipeline.run(Company(
            nom="Climatisation Tremblay",
            url=serveur.url_site("climatisation-tremblay"),
            region="quebec",
        ))
        avec_recrutement = pipeline.run(Company(
            nom="Thermo Marchand",
            url=serveur.url_site("thermo-marchand"),
            region="quebec",
        ))

        # Même besoin : même gabarit HTML "pauvre" ⇒ même score global.
        assert sans_recrutement.scores["global"] == avec_recrutement.scores["global"]

        # Intention strictement différente.
        assert sans_recrutement.evenements_intention == []
        assert len(avec_recrutement.evenements_intention) == 1

        evt = avec_recrutement.evenements_intention[0]
        assert evt.dimension == "recrutement_production"
        assert evt.citable is True
        assert evt.date_evenement == date.today() - timedelta(days=12)
        assert "{jours}" not in evt.preuve  # gabarit bien interpolé, pas laissé tel quel
        assert "12" in evt.preuve

    def test_signal_intention_derive_uniquement_pour_le_recruteur(
        self, env_faux_api, journal_vierge, api_io, serveur
    ):
        from diagnostic.serializers import diagnostic_to_fiche
        from diagnostic.vault_schema import FicheProspect

        pipeline = _pipeline(api_io)
        base = dict(persona=1, marche="quebec", statut="decouvert",
                     date_creation=date.today())

        diag_a = pipeline.run(Company(
            nom="Climatisation Tremblay",
            url=serveur.url_site("climatisation-tremblay"), region="quebec"))
        diag_b = pipeline.run(Company(
            nom="Thermo Marchand",
            url=serveur.url_site("thermo-marchand"), region="quebec"))

        fiche_a = diagnostic_to_fiche(diag_a, FicheProspect(nom="Climatisation Tremblay", **base))
        fiche_b = diagnostic_to_fiche(diag_b, FicheProspect(nom="Thermo Marchand", **base))

        assert fiche_a.signal_intention is None
        assert fiche_b.signal_intention is not None
        assert fiche_b.date_intention == date.today() - timedelta(days=12)
        assert fiche_b.intention_expire_le is not None


# ---------------------------------------------------------------------------
# 2. Décroissance — même fait, pondération différente selon l'âge
# ---------------------------------------------------------------------------

class TestDecroissance:
    def test_intensite_decroit_avec_l_age_mais_le_fait_ne_se_deforme_pas(self):
        """Un même événement daté d'aujourd'hui vs. daté d'il y a 6 mois :
        l'intensité décroissante diminue, mais la PREUVE FACTUELLE (la date
        elle-même) ne se déforme jamais — seule la pondération change."""
        from diagnostic.collectors._decay import decroissance

        config = {"demi_vie_jours": 45, "plancher": 0.1}
        recent = date.today() - timedelta(days=5)
        vieux = date.today() - timedelta(days=180)

        facteur_recent = decroissance(recent, config)
        facteur_vieux = decroissance(vieux, config)
        assert facteur_recent > facteur_vieux

        # Le fait (la date) est immuable, quel que soit le facteur calculé :
        # decroissance() ne modifie jamais date_evenement.
        assert recent == date.today() - timedelta(days=5)
        assert vieux == date.today() - timedelta(days=180)

    def test_evenement_intention_reste_factuel_quel_que_soit_l_age(
        self, env_faux_api, journal_vierge, api_io, serveur
    ):
        """Le pipeline réel : la preuve textuelle contient le nombre de jours
        RÉEL, jamais un facteur de décroissance déformé."""
        pipeline = _pipeline(api_io)
        diag = pipeline.run(Company(
            nom="Thermo Marchand",
            url=serveur.url_site("thermo-marchand"), region="quebec"))
        assert len(diag.evenements_intention) == 1
        # jours_offre=12 dans le catalogue faux_api → interpolé tel quel.
        assert "il y a 12 jours" in diag.evenements_intention[0].preuve


# ---------------------------------------------------------------------------
# 3. Trois états — aucune fabrication
# ---------------------------------------------------------------------------

class TestTroisEtatsBoutEnBout:
    def test_site_injoignable_ne_fabrique_aucun_evenement(self, api_io):
        """Site injoignable (jamais résolvable, domaine .test RFC 6761) :
        offre_detectee=None, aucun EvenementIntention fabriqué."""
        pipeline = _pipeline(api_io)
        diag = pipeline.run(Company(nom="Inconnu", url="https://inexistant.test", region="quebec"))
        assert diag.signaux["website"].get("offre_detectee") is None
        assert diag.evenements_intention == []

    def test_vocabulaire_non_configure_ne_fabrique_aucun_evenement(
        self, env_faux_api, journal_vierge, api_io, serveur
    ):
        """Secteur sans vocabulaire d'intention configuré : le collecteur est
        instancié avec vocabulaire_intention=None → offre_detectee=None,
        même si le site affiche un vrai recrutement."""
        from diagnostic.collectors.website import WebsiteCollector
        c = WebsiteCollector(api_io=api_io, vocabulaire_intention=None)
        signaux = c.collect(Company(
            nom="Thermo Marchand", url=serveur.url_site("thermo-marchand"), region="quebec"))
        assert signaux["offre_detectee"] is None


# ---------------------------------------------------------------------------
# 4. Citabilité
# ---------------------------------------------------------------------------

class TestCitabiliteBoutEnBout:
    def test_check_citable_false_jamais_signal_intention(
        self, env_faux_api, journal_vierge, api_io, serveur
    ):
        from diagnostic.intent import evaluer_intention
        from diagnostic.serializers import diagnostic_to_fiche
        from diagnostic.vault_schema import FicheProspect
        from diagnostic.collectors.website import WebsiteCollector
        from diagnostic.config import load_rubrique_intention

        c = WebsiteCollector(api_io=api_io, vocabulaire_intention=["nous recrutons"])
        signaux = {"website": c.collect(Company(
            nom="Thermo Marchand", url=serveur.url_site("thermo-marchand"), region="quebec"))}

        rubrique = load_rubrique_intention(1)
        # Rendre le check non citable pour cette évaluation (sans modifier le
        # fichier de production) : preuve que la contrainte dure est bien
        # respectée quelle que soit la déclaration YAML.
        rubrique_non_citable = {
            "dimensions": {
                dim: {"checks": [dict(c, citable=False) for c in d["checks"]]}
                for dim, d in rubrique["dimensions"].items()
            }
        }
        evenements = evaluer_intention(rubrique_non_citable, signaux)
        assert len(evenements) == 1
        assert evenements[0].citable is False

        from diagnostic.models import Diagnostic, Company as _Company
        diag = Diagnostic(
            entreprise=_Company(nom="Thermo Marchand", url=""),
            scores={"global": 40.0}, failles=[], mini_audit="x", accroche="y",
            evenements_intention=evenements,
        )
        fiche = diagnostic_to_fiche(diag, FicheProspect(
            nom="Thermo Marchand", persona=1, marche="quebec", statut="decouvert",
            date_creation=date.today(),
        ))
        assert fiche.signal_intention is None


# ---------------------------------------------------------------------------
# 5. Non-contamination inter-secteurs (même patron que test_multi_industrie.py)
# ---------------------------------------------------------------------------

class TestNonContaminationIntersecteurs:
    def test_secteur_sans_vocabulaire_intention_ne_fuit_pas_le_vocabulaire_hvac(
        self, tmp_path, monkeypatch, api_io
    ):
        """Un secteur fictif AVEC une rubrique de besoin mais SANS
        knowledge/vocabulaire_intention_{secteur}.yaml ne doit JAMAIS hériter
        du lexique HVAC — même patron que TestLotMixteVaultMode (ADR 0003) :
        `make_pipeline_for_secteur` résout le vocabulaire PAR SECTEUR, jamais
        par un défaut partagé."""
        import diagnostic.config as config_mod
        from diagnostic.config import load_vocabulaire_intention
        from diagnostic.vault_runner import make_pipeline_for_secteur

        knowledge_dir = tmp_path / "knowledge"
        knowledge_dir.mkdir()
        (knowledge_dir / "rubric_secteur-fictif.yaml").write_text(
            "persona: \"Secteur fictif de test\"\n"
            "dimensions:\n"
            "  offre:\n"
            "    poids: 100\n"
            "    checks:\n"
            "      - { signal: website.mentions_offre, op: is_true, points: 100, "
            "gravite: haute, gap: \"Offre absente\" }\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(config_mod, "KNOWLEDGE_DIR", knowledge_dir)

        assert load_vocabulaire_intention("secteur-fictif") == {}

        pipeline_fictif = make_pipeline_for_secteur("secteur-fictif", api_io=api_io)
        website_fictif = next(c for c in pipeline_fictif.collectors if c.name == "website")
        assert website_fictif.vocabulaire_intention is None
        assert pipeline_fictif.rubrique_intention is None

    def test_secteur_hvac_reel_a_bien_son_vocabulaire_intention(self, api_io):
        """Contre-épreuve, sans monkeypatch : le secteur HVAC réel (persona1)
        garde son vocabulaire — la preuve ci-dessus n'est pas un simple None
        par défaut partout, c'est une résolution PAR SECTEUR."""
        from diagnostic.vault_runner import make_pipeline_for_secteur

        pipeline_hvac = make_pipeline_for_secteur("persona1", api_io=api_io)
        website_hvac = next(c for c in pipeline_hvac.collectors if c.name == "website")
        assert website_hvac.vocabulaire_intention is not None
        assert pipeline_hvac.rubrique_intention is not None


# ---------------------------------------------------------------------------
# 6. Chaîne complète — run_vault_mode sur un vault mixte
# ---------------------------------------------------------------------------

class TestChaineCompleteVault:
    def test_run_vault_mode_produit_besoin_et_intention(
        self, env_faux_api, journal_vierge, chemins, api_io, serveur
    ):
        from diagnostic.vault_runner import run_vault_mode
        from tests.integration import dataset

        seeds = (
            {
                "_slug": "climatisation-tremblay",
                "nom": "Climatisation Tremblay",
                "statut": "decouvert",
                "source_decouverte": "seed:integration",
            },
            {
                "_slug": "thermo-marchand",
                "nom": "Thermo Marchand",
                "statut": "decouvert",
                "source_decouverte": "seed:integration",
            },
        )
        dataset.semer(chemins["vault"], url_site=lambda slug: serveur.url_site(slug), seeds=seeds)

        resultat = run_vault_mode(
            chemins["vault"],
            lambda secteur_id: _pipeline(api_io),
        )
        assert resultat["erreurs"] == []
        assert set(resultat["ok"]) == {"Climatisation Tremblay", "Thermo Marchand"}

        io = VaultIO(chemins["vault"])
        fiches = {f.nom: f for _, f in io.query(statut="diagnostique")}

        # Les deux portent un diagnostic de BESOIN.
        assert fiches["Climatisation Tremblay"].score_global is not None
        assert fiches["Thermo Marchand"].score_global is not None

        # Seule Thermo Marchand porte un signal d'INTENTION.
        assert fiches["Climatisation Tremblay"].signal_intention is None
        assert fiches["Thermo Marchand"].signal_intention is not None
        assert fiches["Thermo Marchand"].date_intention is not None

        # Le rapport Markdown de la recruteuse porte la section dédiée.
        rapport_path = next(
            p for p in (chemins["vault"] / "30-Diagnostics").glob("*.md")
            if "marchand" in p.stem
        )
        assert "Signaux d'intention" in rapport_path.read_text(encoding="utf-8")
