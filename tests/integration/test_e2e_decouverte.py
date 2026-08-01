"""
test_e2e_decouverte.py — flux de découverte J4, de bout en bout.

Chaîne réellement exercée (aucun mock Python) :
  ICP (donnée) → requêtes SERP HTTP → filtres → dédup → Apollo HTTP →
  FicheProspect → écriture atomique vault → grand livre api_usage.log.

Le seul artifice est la destination : `SERP_BASE_URL` / `APOLLO_BASE_URL`
pointent le faux serveur local au lieu de la production.
"""

from __future__ import annotations

from urllib.parse import urlparse

from diagnostic.vault_io import VaultIO
from tests.integration.dataset import ICP_TEST


def _lancer_decouverte(chemins, api_io, **kwargs):
    import run_discovery
    run_discovery.run(icp_id=ICP_TEST, vault=chemins["vault"], api_io=api_io, **kwargs)
    return VaultIO(chemins["vault"])


# ---------------------------------------------------------------------------
# 1. SERP → candidates → fiches `decouvert`
# ---------------------------------------------------------------------------

class TestFluxDecouverte:

    def test_serp_produit_des_fiches_decouvert(
        self, env_faux_api, journal_vierge, vault_vide, chemins, api_io
    ):
        serveur = journal_vierge
        io = _lancer_decouverte(chemins, api_io)

        # 2 gabarits × 2 localités = 4 requêtes SERP réellement émises.
        assert serveur.compter("/search") == 4

        fiches = io.query(statut="decouvert")
        assert len(fiches) >= 4, "la découverte doit produire plusieurs fiches"
        for _, fiche in fiches:
            assert fiche.statut == "decouvert"
            assert fiche.icp_id == ICP_TEST
            assert fiche.persona == 1
            assert fiche.marche == "quebec"
            assert fiche.site_web and fiche.site_web.startswith("https://")

    def test_filtres_icp_ecartent_annuaires_et_plateformes(
        self, env_faux_api, journal_vierge, vault_vide, chemins, api_io
    ):
        io = _lancer_decouverte(chemins, api_io)
        domaines = {urlparse(f.site_web).netloc for _, f in io.query()}

        # Ces trois résultats sont servis à CHAQUE requête par le faux SERP :
        # s'ils apparaissent, c'est que les filtres ICP ne s'appliquent pas.
        for exclu in ("pagesjaunes.ca", "facebook.com", "wixsite.com"):
            assert not any(exclu in d for d in domaines), f"{exclu} aurait dû être filtré"

    def test_dedup_intra_lot_par_domaine(
        self, env_faux_api, journal_vierge, vault_vide, chemins, api_io
    ):
        io = _lancer_decouverte(chemins, api_io)
        domaines = [urlparse(f.site_web).netloc for _, f in io.query()]
        # Les fenêtres de résultats se chevauchent d'une requête à l'autre :
        # sans dédup, on aurait des doublons.
        assert len(domaines) == len(set(domaines))

    def test_apollo_enrichit_le_contact(
        self, env_faux_api, journal_vierge, vault_vide, chemins, api_io
    ):
        serveur = journal_vierge
        io = _lancer_decouverte(chemins, api_io)

        assert serveur.compter("/v1/people/search") >= 1
        avec_contact = [f for _, f in io.query() if f.contact_email]
        assert avec_contact, "au moins une fiche doit porter un contact Apollo"
        for fiche in avec_contact:
            # contact_email_source est obligatoire dès qu'un email existe (audit RGPD).
            assert fiche.contact_email_source

    def test_minimisation_rgpd_aucun_champ_apollo_en_trop(
        self, env_faux_api, journal_vierge, vault_vide, chemins, api_io
    ):
        """Le faux Apollo renvoie téléphone, ville et organisation : rien ne doit
        atterrir dans le vault (Contact est en extra='forbid')."""
        io = _lancer_decouverte(chemins, api_io)
        for path, _ in io.query():
            brut = path.read_text(encoding="utf-8")
            for interdit in ("phone_numbers", "418-555-0101", "employees", "organization"):
                assert interdit not in brut

    def test_grand_livre_recoit_serp_et_apollo_avec_cout_non_nul(
        self, env_faux_api, journal_vierge, vault_vide, chemins, api_io, ledger
    ):
        _lancer_decouverte(chemins, api_io)

        serp = ledger.pour(chemins["ledger"], "serp")
        apollo = ledger.pour(chemins["ledger"], "apollo")
        assert serp, "aucune ligne serp dans api_usage.log"
        assert apollo, "aucune ligne apollo dans api_usage.log"

        # On n'inspecte QUE les clés qui nous concernent : le schéma du grand
        # livre peut gagner des champs optionnels sans casser ce test.
        appels_serp = [l for l in serp if not l.get("cache_hit")]
        assert all(l["endpoint"] == "search" for l in appels_serp)
        assert sum(l["cout_estime"] for l in appels_serp) > 0
        assert sum(l["unites"].get("requetes", 0) for l in appels_serp) == 4

        appels_apollo = [l for l in apollo if not l.get("cache_hit")]
        assert sum(l["cout_estime"] for l in appels_apollo) > 0
        assert all(l["resultat"] == "ok" for l in appels_apollo)


# ---------------------------------------------------------------------------
# 2. Idempotence et dry-run
# ---------------------------------------------------------------------------

class TestIdempotenceDecouverte:

    def test_relance_ne_cree_aucun_doublon(
        self, env_faux_api, journal_vierge, vault_vide, chemins, api_io
    ):
        io = _lancer_decouverte(chemins, api_io)
        avant = {p.name for p, _ in io.query()}
        assert avant

        io = _lancer_decouverte(chemins, api_io)
        apres = {p.name for p, _ in io.query()}
        assert apres == avant, "la dédup inter-runs doit empêcher tout doublon"

    def test_dry_run_n_ecrit_rien(
        self, env_faux_api, journal_vierge, vault_vide, chemins, api_io
    ):
        serveur = journal_vierge
        io = _lancer_decouverte(chemins, api_io, dry_run=True)
        assert io.query() == []
        # Le SERP est bien exécuté et métré (le cache reste utile au run réel).
        assert serveur.compter("/search") == 4
        assert serveur.compter("/v1/people/search") == 0

    def test_sans_contact_ne_consomme_aucun_credit_apollo(
        self, env_faux_api, journal_vierge, vault_vide, chemins, api_io, ledger
    ):
        serveur = journal_vierge
        io = _lancer_decouverte(chemins, api_io, sans_contact=True)
        assert io.query(statut="decouvert")
        assert serveur.compter("/v1/people/search") == 0
        assert ledger.pour(chemins["ledger"], "apollo") == []
