"""
test_e2e_diagnostic.py — flux de diagnostic J1/J2, de bout en bout.

Chaîne réellement exercée :
  fiche `decouvert` → WebsiteCollector (vrai GET HTTP) → Google Places (vrai
  GET) → collecteurs dérivés (seo/social) → scoring sur la rubrique YAML →
  synthèse par le SDK Anthropic (vrai POST sur /v1/messages) → QA → rapport
  Markdown + frontmatter + transition `decouvert → diagnostique`.

Le LLM est exercé SANS clé réelle : `ANTHROPIC_BASE_URL` pointe le faux
serveur, qui répond au format exact de l'API Messages. Le faux modèle rédige
uniquement à partir des failles présentes dans le prompt — il passe donc le
`quality_check` de synthesis.py sans rien inventer.
"""

from __future__ import annotations

import pytest

from diagnostic.models import Company
from diagnostic.vault_io import VaultIO

def _sdk_anthropic_present() -> bool:
    """Le SDK est une dépendance OPTIONNELLE (cf. requirements.txt).

    Sans lui, `synthesis.py` retombe sur le repli déterministe : tous les tests
    de ce fichier restent valides, seul celui qui exerce le POST /v1/messages
    n'a plus rien à observer.
    """
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


sans_sdk_anthropic = pytest.mark.skipif(
    not _sdk_anthropic_present(),
    reason="SDK anthropic absent (pip install anthropic) — chemin LLM non exerçable",
)


def _pipeline(api_io):
    import run_diagnostic
    return run_diagnostic._build_pipeline(api_io=api_io)


# ---------------------------------------------------------------------------
# 1. Collecte réelle d'un site pauvre
# ---------------------------------------------------------------------------

class TestCollecteReelle:

    def test_site_pauvre_produit_de_vraies_failles(
        self, env_faux_api, journal_vierge, api_io, serveur
    ):
        from diagnostic.collectors.website import WebsiteCollector

        url = serveur.url_site("climatisation-tremblay")  # HTTP → pas de HTTPS
        signaux = WebsiteCollector(api_io=api_io).collect(
            Company(nom="Climatisation Tremblay", url=url, region="quebec"))

        assert signaux["reachable"] is True
        assert signaux["status"] == 200
        assert signaux["https"] is False           # servi en clair
        assert signaux["has_meta_description"] is False
        assert signaux["has_viewport"] is False
        assert signaux["has_logo"] is False
        assert signaux["has_contact"] is False
        assert signaux["image_count"] == 0
        assert signaux["mentions_offre"] is True   # le métier est bien décrit
        assert signaux["copyright_year"] == 2017   # site figé
        assert signaux["fraicheur_mois"] and signaux["fraicheur_mois"] > 12

    def test_site_correct_est_le_contre_exemple(
        self, env_faux_api, journal_vierge, api_io, serveur
    ):
        from diagnostic.collectors.website import WebsiteCollector

        signaux = WebsiteCollector(api_io=api_io).collect(Company(
            nom="Clim Rive-Sud", url=serveur.url_site("clim-rive-sud"), region="quebec"))

        assert signaux["has_meta_description"] is True
        assert signaux["has_viewport"] is True
        assert signaux["has_logo"] is True
        assert signaux["has_contact"] is True
        assert signaux["image_count"] >= 3
        assert set(signaux["social_links"]) >= {"facebook", "instagram"}

    def test_places_gbp_et_reviews_partagent_le_cache(
        self, env_faux_api, journal_vierge, api_io, serveur, chemins, ledger
    ):
        """Les deux collecteurs palier 1 utilisent la même cache_key :
        un seul appel réseau text_search pour les deux."""
        from diagnostic.collectors.gbp import GbpCollector
        from diagnostic.collectors.reviews import ReviewsCollector

        company = Company(nom="Clim Rive-Sud", url="", region="quebec")
        gbp = GbpCollector(api_io=api_io).collect(company)
        avis = ReviewsCollector(api_io=api_io).collect(company)

        assert gbp == {"verified": True, "has_photos": True}
        assert avis["count"] == 118
        assert avis["avg"] == 4.7
        assert avis["repond_aux_avis"] is True
        assert avis["date_dernier_avis"]

        assert serveur.compter("/maps/api/place/textsearch/json") == 1
        assert serveur.compter("/maps/api/place/details/json") == 1

        places = ledger.pour(chemins["ledger"], "google_places")
        assert any(l.get("cache_hit") for l in places), "le 2e text_search doit être un cache hit"
        assert sum(l["cout_estime"] for l in places) > 0


# ---------------------------------------------------------------------------
# 2. Pipeline complet sur le vault
# ---------------------------------------------------------------------------

class TestFluxDiagnosticVault:

    def test_fiches_decouvert_deviennent_diagnostique(
        self, env_faux_api, journal_vierge, vault_seme, chemins, api_io
    ):
        from diagnostic.vault_runner import run_vault_mode

        io = VaultIO(chemins["vault"])
        avant = {f.nom for _, f in io.query(statut="decouvert")}
        assert avant, "le dataset doit contenir des fiches decouvert"

        resultat = run_vault_mode(chemins["vault"], _pipeline(api_io))

        assert resultat["erreurs"] == []
        assert set(resultat["ok"]) == avant
        assert io.query(statut="decouvert") == []

        for _, fiche in io.query(statut="diagnostique"):
            if fiche.nom not in avant:
                continue  # fiche déjà diagnostiquée par le dataset
            assert fiche.score_global is not None and 0 <= fiche.score_global <= 100
            assert fiche.gaps_majeurs, "un site pauvre doit produire des gaps"
            assert fiche.date_diagnostic is not None
            assert fiche.rapport and fiche.rapport.startswith("[[30-Diagnostics/")
            assert fiche.signal_chaud
            assert fiche.accroche

    def test_rapport_markdown_ecrit_dans_le_vault(
        self, env_faux_api, journal_vierge, vault_seme, chemins, api_io
    ):
        from diagnostic.vault_runner import run_vault_mode
        run_vault_mode(chemins["vault"], _pipeline(api_io))

        rapports = sorted((chemins["vault"] / "30-Diagnostics").glob("*.md"))
        assert len(rapports) >= 2
        contenu = rapports[0].read_text(encoding="utf-8")
        assert "# Rapport de diagnostic" in contenu
        assert "## Gaps détectés" in contenu

    @sans_sdk_anthropic
    def test_synthese_passe_par_le_faux_endpoint_anthropic(
        self, env_faux_api, journal_vierge, vault_seme, chemins, api_io, ledger
    ):
        from diagnostic.vault_runner import run_vault_mode
        serveur = journal_vierge
        run_vault_mode(chemins["vault"], _pipeline(api_io))

        # Le SDK Anthropic a bien émis un POST /v1/messages par fiche.
        appels = serveur.requetes("/v1/messages")
        assert len(appels) >= 2
        assert appels[0].corps["model"]
        assert "FAILLES CONSTATÉES" in appels[0].corps["messages"][0]["content"]

        # Le mini-audit vient bien du (faux) modèle, pas du repli déterministe.
        rapport = next((chemins["vault"] / "30-Diagnostics").glob("*.md"))
        assert "Analyse factuelle de la presence digitale" in rapport.read_text("utf-8")

        # Tokens métrés dans le grand livre, coût non nul.
        lignes = ledger.pour(chemins["ledger"], "anthropic")
        assert lignes
        appels_reels = [l for l in lignes if not l.get("cache_hit")]
        assert all(l["endpoint"] == "messages" for l in appels_reels)
        assert all(l["unites"]["input_tokens"] > 0 for l in appels_reels)
        assert all(l["unites"]["output_tokens"] > 0 for l in appels_reels)
        assert sum(l["cout_estime"] for l in appels_reels) > 0

    def test_sans_cle_anthropic_repli_deterministe_et_zero_appel(
        self, env_faux_api, journal_vierge, vault_seme, chemins, api_io, monkeypatch
    ):
        """Sans clé, le système doit tourner hors-ligne — c'est le contrat J1."""
        from diagnostic.vault_runner import run_vault_mode
        serveur = journal_vierge
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        resultat = run_vault_mode(chemins["vault"], _pipeline(api_io))

        assert resultat["erreurs"] == []
        assert serveur.compter("/v1/messages") == 0
        rapport = next((chemins["vault"] / "30-Diagnostics").glob("*.md"))
        assert "# Mini-audit de marque" in rapport.read_text("utf-8")

    def test_relance_est_idempotente(
        self, env_faux_api, journal_vierge, vault_seme, chemins, api_io
    ):
        from diagnostic.vault_runner import run_vault_mode
        run_vault_mode(chemins["vault"], _pipeline(api_io))
        second = run_vault_mode(chemins["vault"], _pipeline(api_io))
        # Plus aucune fiche `decouvert` : le second passage ne fait rien.
        assert second == {"ok": [], "erreurs": []}
