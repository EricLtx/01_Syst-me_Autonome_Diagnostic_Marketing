"""
test_greenit.py — tests de la couche d'efficience (FinOps / GreenIT).

Couvre :
  §G1 — chargement de config : YAML réel, YAML absent, YAML invalide, YAML partiel
  §G2 — routage déterministe : défaut frugal, escalade par règle, idempotence
  §G3 — estimation d'empreinte : croissance avec les tokens, intensité régionale
  §G4 — troncature de contexte (levier de frugalité n°1)
  §G5 — cache-hit = coût 0, énergie ~0, CO2e ~0 dans le grand livre
  §G6 — rétro-compatibilité LedgerEntry (anciennes lignes JSONL sans champs GreenIT)
  §G7 — câblage synthesis : routage appliqué, repli déterministe intact hors ligne

Aucun réseau réel, aucune clé API : le module anthropic est simulé via sys.modules.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from diagnostic import greenit
from diagnostic.api_io import ApiIO, estimer_octets
from diagnostic.api_schema import LedgerEntry

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

PRICING = {
    "devise": "USD",
    "fournisseurs": {
        "anthropic": {
            "unite": "token",
            "endpoints": {
                "messages": {
                    "prix_par_unite": {"input_tokens": 0.000003, "output_tokens": 0.000015}
                }
            },
        },
        "serp": {"unite": "requete", "endpoints": {"search": {"prix_par_unite": {"requetes": 0.01}}}},
        "http": {"unite": "requete", "endpoints": {"get": {"prix_par_unite": {"requetes": 0.0}}}},
    },
}


@pytest.fixture()
def config() -> dict:
    """Config réelle du dépôt (knowledge/greenit.yaml)."""
    return greenit.charger_config()


def _io(tmp_path: Path, **kwargs) -> tuple[ApiIO, Path]:
    ledger = tmp_path / "api_usage.log"
    return ApiIO(PRICING, ledger, cache_dir=tmp_path / "cache", **kwargs), ledger


def _lignes(ledger: Path) -> list[dict]:
    return [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# §G1 — Chargement de configuration
# ---------------------------------------------------------------------------

class TestChargerConfig:
    def test_yaml_reel_charge(self, config):
        assert "profils" in config and "routage" in config
        assert "empreinte" in config and "frugalite" in config

    def test_profils_attendus_presents(self, config):
        for profil in ("frugal", "standard", "qualite"):
            assert profil in config["profils"]
            assert config["profils"][profil]["modele"]

    def test_fichier_absent_retourne_defauts(self, tmp_path):
        cfg = greenit.charger_config(tmp_path / "inexistant.yaml")
        assert cfg["profils"] == greenit.CONFIG_DEFAUT["profils"]

    def test_yaml_invalide_ne_crashe_pas(self, tmp_path):
        mauvais = tmp_path / "greenit.yaml"
        mauvais.write_text("profils: [ceci n'est pas: un mapping\n", encoding="utf-8")
        cfg = greenit.charger_config(mauvais)
        assert cfg["profils"] == greenit.CONFIG_DEFAUT["profils"]

    def test_yaml_scalaire_retourne_defauts(self, tmp_path):
        plat = tmp_path / "greenit.yaml"
        plat.write_text("42\n", encoding="utf-8")
        assert greenit.charger_config(plat)["routage"]["profil_defaut"] == "standard"

    def test_yaml_partiel_fusionne_avec_defauts(self, tmp_path):
        """Une config partielle hérite du reste : pas de trou de configuration."""
        partiel = tmp_path / "greenit.yaml"
        partiel.write_text(
            "frugalite:\n  max_tokens_sortie: 120\n", encoding="utf-8"
        )
        cfg = greenit.charger_config(partiel)
        assert cfg["frugalite"]["max_tokens_sortie"] == 120
        assert cfg["frugalite"]["troncature_contexte_caracteres"] > 0  # hérité
        assert "qualite" in cfg["profils"]                              # hérité

    def test_config_par_defaut_est_frugale(self):
        """Sans YAML, on dégrade vers le petit modèle — jamais vers le gros."""
        defaut = greenit.CONFIG_DEFAUT
        profil = defaut["routage"]["profil_defaut"]
        assert "haiku" in defaut["profils"][profil]["modele"]


# ---------------------------------------------------------------------------
# §G2 — Routage déterministe
# ---------------------------------------------------------------------------

class TestChoisirModele:
    def test_defaut_est_le_petit_modele(self, config):
        modele, profil = greenit.choisir_modele(
            {"nb_failles": 2, "score_global": 30, "quality_check_echoue": False}, config
        )
        assert modele == "claude-haiku-4-5-20251001"
        assert profil == "standard"

    def test_deterministe_memes_entrees_meme_sortie(self, config):
        contexte = {"nb_failles": 3, "score_global": 41.5, "quality_check_echoue": False}
        resultats = {greenit.choisir_modele(dict(contexte), config) for _ in range(20)}
        assert len(resultats) == 1

    def test_escalade_sur_quality_check_echoue(self, config):
        modele, profil = greenit.choisir_modele(
            {"nb_failles": 1, "score_global": 10, "quality_check_echoue": True}, config
        )
        assert profil == "qualite"
        assert modele == "claude-sonnet-4-5"

    def test_escalade_sur_failles_nombreuses(self, config):
        _, profil = greenit.choisir_modele(
            {"nb_failles": 9, "score_global": 10, "quality_check_echoue": False}, config
        )
        assert profil == "qualite"

    def test_pas_d_escalade_juste_sous_le_seuil(self, config):
        seuil = next(
            r["valeur"] for r in config["routage"]["regles_escalade"]
            if r["champ"] == "nb_failles"
        )
        _, profil = greenit.choisir_modele(
            {"nb_failles": seuil - 1, "score_global": 10, "quality_check_echoue": False}, config
        )
        assert profil == "standard"

    def test_escalade_sur_score_eleve(self, config):
        _, profil = greenit.choisir_modele(
            {"nb_failles": 1, "score_global": 92, "quality_check_echoue": False}, config
        )
        assert profil == "qualite"

    def test_contexte_vide_ne_crashe_pas(self, config):
        modele, profil = greenit.choisir_modele({}, config)
        assert modele and profil == "standard"

    def test_profil_force_par_le_contexte(self, config):
        modele, profil = greenit.choisir_modele({"profil": "frugal", "nb_failles": 99}, config)
        assert profil == "frugal"
        assert "haiku" in modele

    def test_profil_force_inconnu_ignore(self, config):
        _, profil = greenit.choisir_modele({"profil": "inexistant"}, config)
        assert profil == "standard"

    def test_mode_et_exige_toutes_les_regles(self, config):
        cfg = greenit.charger_config()
        cfg["routage"] = dict(cfg["routage"], mode="et")
        # une seule règle vraie → pas d'escalade en mode "et"
        _, profil = greenit.choisir_modele(
            {"nb_failles": 99, "score_global": 0, "quality_check_echoue": False}, cfg
        )
        assert profil == "standard"
        # toutes vraies → escalade
        _, profil = greenit.choisir_modele(
            {"nb_failles": 99, "score_global": 99, "quality_check_echoue": True}, cfg
        )
        assert profil == "qualite"

    def test_regle_sur_champ_absent_n_escalade_pas(self, config):
        _, profil = greenit.choisir_modele({"champ_inconnu": 12345}, config)
        assert profil == "standard"

    def test_types_incomparables_n_escaladent_pas(self, config):
        """Un contexte mal typé ne doit pas déclencher le modèle cher par accident."""
        _, profil = greenit.choisir_modele(
            {"nb_failles": "beaucoup", "score_global": None}, config
        )
        assert profil == "standard"

    def test_evaluer_escalade_expose_les_motifs(self, config):
        motifs = greenit.evaluer_escalade(
            {"nb_failles": 9, "score_global": 99, "quality_check_echoue": True}, config
        )
        assert "quality_check_echoue" in motifs
        assert "failles_nombreuses" in motifs

    def test_aucun_llm_dans_le_routage(self):
        """Garde-fou : greenit.py est un module pur (aucun réseau, aucun SDK)."""
        source = (Path(greenit.__file__)).read_text(encoding="utf-8")
        assert "import anthropic" not in source
        assert "import requests" not in source


class TestMaxTokens:
    def test_max_tokens_du_profil(self, config):
        assert greenit.max_tokens_du_profil("frugal", config) <= 600

    def test_plafond_frugalite_ecrase_le_profil(self):
        cfg = greenit.charger_config()
        cfg["frugalite"] = dict(cfg["frugalite"], max_tokens_sortie=100)
        assert greenit.max_tokens_du_profil("qualite", cfg) == 100

    def test_plafond_absent_laisse_le_profil_decider(self):
        cfg = greenit.charger_config()
        cfg["frugalite"] = dict(cfg["frugalite"], max_tokens_sortie=None)
        assert greenit.max_tokens_du_profil("qualite", cfg) == cfg["profils"]["qualite"]["max_tokens"]

    def test_profil_inconnu_valeur_de_repli(self, config):
        assert greenit.max_tokens_du_profil("nawak", config) > 0


# ---------------------------------------------------------------------------
# §G3 — Estimation d'empreinte
# ---------------------------------------------------------------------------

class TestEstimerEmpreinte:
    def test_croit_avec_les_tokens(self, config):
        e1, _ = greenit.estimer_empreinte({"input_tokens": 1000, "output_tokens": 200}, 0, None, config)
        e2, _ = greenit.estimer_empreinte({"input_tokens": 2000, "output_tokens": 400}, 0, None, config)
        assert e2 > e1

    def test_sortie_plus_couteuse_que_entree(self, config):
        e_in, _ = greenit.estimer_empreinte({"input_tokens": 1000}, 0, None, config)
        e_out, _ = greenit.estimer_empreinte({"output_tokens": 1000}, 0, None, config)
        assert e_out > e_in

    def test_cache_lecture_moins_couteux_que_entree_pleine(self, config):
        e_cache, _ = greenit.estimer_empreinte({"cache_read_input_tokens": 1000}, 0, None, config)
        e_in, _ = greenit.estimer_empreinte({"input_tokens": 1000}, 0, None, config)
        assert 0 < e_cache < e_in

    def test_unites_vides_empreinte_nulle(self, config):
        assert greenit.estimer_empreinte({}, 0, None, config) == (0.0, 0.0)

    def test_unites_none_ne_crashe_pas(self, config):
        assert greenit.estimer_empreinte(None, 0, None, config) == (0.0, 0.0)

    def test_octets_transferes_comptent(self, config):
        e0, _ = greenit.estimer_empreinte({"requetes": 1}, 0, None, config)
        e1, _ = greenit.estimer_empreinte({"requetes": 1}, 50_000_000, None, config)
        assert e1 > e0

    def test_requetes_http_comptent(self, config):
        e1, _ = greenit.estimer_empreinte({"requetes": 1}, 0, None, config)
        e10, _ = greenit.estimer_empreinte({"requetes": 10}, 0, None, config)
        assert e10 > e1 > 0

    def test_co2_varie_avec_l_intensite_regionale(self, config):
        unites = {"input_tokens": 5000, "output_tokens": 800}
        e_qc, co2_qc = greenit.estimer_empreinte(unites, 0, "Québec, QC", config)
        e_fr, co2_fr = greenit.estimer_empreinte(unites, 0, "Paris, France", config)
        e_none, co2_def = greenit.estimer_empreinte(unites, 0, None, config)
        # même énergie, CO2e différent : seul le mix électrique change
        assert e_qc == e_fr == e_none
        assert co2_qc < co2_fr < co2_def

    def test_region_inconnue_utilise_le_defaut(self, config):
        unites = {"output_tokens": 1000}
        _, co2_inconnue = greenit.estimer_empreinte(unites, 0, "Atlantide", config)
        _, co2_defaut = greenit.estimer_empreinte(unites, 0, None, config)
        assert co2_inconnue == co2_defaut

    def test_accents_et_casse_normalises(self, config):
        assert greenit.intensite_carbone("QUÉBEC", config) == greenit.intensite_carbone("quebec", config)

    def test_co2_proportionnel_a_l_energie(self, config):
        e, co2 = greenit.estimer_empreinte({"output_tokens": 1000}, 0, "France", config)
        intensite = greenit.intensite_carbone("France", config)
        assert co2 == pytest.approx(e / 1000.0 * intensite)

    def test_facteurs_documentes_comme_estimations(self):
        """Exigence anti-hallucination : l'avertissement doit rester dans le YAML."""
        yaml_src = greenit.CHEMIN_CONFIG_DEFAUT.read_text(encoding="utf-8")
        assert "ORDRES DE GRANDEUR" in yaml_src
        assert "certifi" in yaml_src.lower()


# ---------------------------------------------------------------------------
# §G4 — Troncature de contexte
# ---------------------------------------------------------------------------

class TestTronquerContexte:
    def test_texte_court_inchange(self, config):
        assert greenit.tronquer_contexte("court", config) == "court"

    def test_texte_long_tronque(self, config):
        limite = config["frugalite"]["troncature_contexte_caracteres"]
        long = "x" * (limite * 3)
        resultat = greenit.tronquer_contexte(long, config)
        assert len(resultat) < len(long)
        assert resultat.startswith("x" * 100)

    def test_marqueur_visible(self, config):
        limite = config["frugalite"]["troncature_contexte_caracteres"]
        resultat = greenit.tronquer_contexte("y" * (limite + 500), config)
        assert "tronqué" in resultat
        assert "caractères omis" in resultat

    def test_resultat_ne_depasse_jamais_la_borne(self, config):
        """La borne inclut le marqueur : sinon la garantie de coût saute."""
        limite = config["frugalite"]["troncature_contexte_caracteres"]
        for exces in (1, 5, 500, 50_000):
            resultat = greenit.tronquer_contexte("y" * (limite + exces), config)
            assert len(resultat) <= limite, f"dépassement pour exces={exces}"

    def test_limite_exacte_non_tronquee(self, config):
        limite = config["frugalite"]["troncature_contexte_caracteres"]
        texte = "z" * limite
        assert greenit.tronquer_contexte(texte, config) == texte

    def test_cle_alternative_prompt(self, config):
        limite = config["frugalite"]["troncature_prompt_caracteres"]
        assert limite > config["frugalite"]["troncature_contexte_caracteres"]
        texte = "a" * (limite + 10)
        assert len(greenit.tronquer_contexte(texte, config, cle="troncature_prompt_caracteres")) < len(texte)

    def test_non_str_retourne_chaine_vide(self, config):
        assert greenit.tronquer_contexte(None, config) == ""

    def test_limite_absente_laisse_passer(self):
        assert greenit.tronquer_contexte("abc", {"frugalite": {}}) == "abc"

    def test_config_vide_laisse_passer(self):
        assert greenit.tronquer_contexte("abc", {}) == "abc"


# ---------------------------------------------------------------------------
# §G5 — Grand livre : durée, volume, empreinte, cache-hit à zéro
# ---------------------------------------------------------------------------

class TestLedgerGreenIT:
    def test_champs_greenit_presents(self, tmp_path):
        io, ledger = _io(tmp_path)
        io.call("http", "get", lambda: {"ok": True})
        e = _lignes(ledger)[0]
        for champ in ("octets_entrants", "octets_sortants", "duree_ms",
                      "energie_wh", "co2e_g", "modele", "profil"):
            assert champ in e, f"champ {champ} absent du grand livre"

    def test_duree_mesuree(self, tmp_path):
        io, ledger = _io(tmp_path)
        io.call("http", "get", lambda: {"ok": True})
        assert _lignes(ledger)[0]["duree_ms"] >= 0.0

    def test_octets_entrants_estimes(self, tmp_path):
        io, ledger = _io(tmp_path)
        io.call("http", "get", lambda: {"donnees": "x" * 500})
        assert _lignes(ledger)[0]["octets_entrants"] > 400

    def test_octets_sortants_transmis(self, tmp_path):
        io, ledger = _io(tmp_path)
        io.call("http", "get", lambda: {}, octets_sortants=1234)
        assert _lignes(ledger)[0]["octets_sortants"] == 1234

    def test_energie_non_nulle_sur_appel_reel(self, tmp_path):
        io, ledger = _io(tmp_path)
        io.call("serp", "search", lambda: {"hits": 3})
        e = _lignes(ledger)[0]
        assert e["energie_wh"] > 0
        assert e["co2e_g"] > 0

    def test_modele_et_profil_traces(self, tmp_path):
        io, ledger = _io(tmp_path)
        reponse = SimpleNamespace(usage=SimpleNamespace(input_tokens=100, output_tokens=50))
        io.call("anthropic", "messages", lambda: reponse,
                modele="claude-haiku-4-5-20251001", profil="standard")
        e = _lignes(ledger)[0]
        assert e["modele"] == "claude-haiku-4-5-20251001"
        assert e["profil"] == "standard"

    def test_cache_hit_empreinte_nulle(self, tmp_path):
        """Le cœur de la démonstration : un cache-hit ne coûte rien, ni $ ni Wh."""
        io, ledger = _io(tmp_path)
        io.call("serp", "search", lambda: {"r": 1}, cache_key="q1")
        io.call("serp", "search", lambda: {"r": 1}, cache_key="q1")
        lignes = _lignes(ledger)
        assert lignes[0]["cache_hit"] is False and lignes[0]["energie_wh"] > 0
        hit = lignes[1]
        assert hit["cache_hit"] is True
        assert hit["cout_estime"] == 0.0
        assert hit["energie_wh"] == 0.0
        assert hit["co2e_g"] == 0.0
        assert hit["octets_entrants"] == 0  # rien n'a transité par le réseau

    def test_budget_depasse_empreinte_nulle(self, tmp_path):
        from diagnostic.api_io import BudgetExceeded
        io, ledger = _io(tmp_path, budgets={"serp": {"unites_max": {"requetes": 1}}})
        io.call("serp", "search", lambda: {})
        with pytest.raises(BudgetExceeded):
            io.call("serp", "search", lambda: {})
        bloque = _lignes(ledger)[-1]
        assert bloque["resultat"] == "budget_depasse"
        assert bloque["energie_wh"] == 0.0  # appel jamais émis

    def test_region_influe_sur_le_co2_du_ledger(self, tmp_path):
        io, ledger = _io(tmp_path)
        io.call("serp", "search", lambda: {}, region="Québec, QC")
        io.call("serp", "search", lambda: {}, region="Berlin, Europe")
        qc, eu = _lignes(ledger)
        assert qc["energie_wh"] == pytest.approx(eu["energie_wh"])
        assert qc["co2e_g"] < eu["co2e_g"]

    def test_erreur_journalisee_avec_duree(self, tmp_path):
        io, ledger = _io(tmp_path)
        def fn():
            raise ValueError("timeout")
        with pytest.raises(ValueError):
            io.call("http", "get", fn)
        e = _lignes(ledger)[0]
        assert e["resultat"] == "erreur"
        assert e["duree_ms"] >= 0.0

    def test_config_greenit_injectable(self, tmp_path):
        """Les facteurs sont une donnée : on peut les injecter (tests, simulation)."""
        cfg = greenit.charger_config()
        cfg["empreinte"] = dict(cfg["empreinte"], wh_par_requete_http=10.0)
        io, ledger = _io(tmp_path, greenit_config=cfg)
        io.call("serp", "search", lambda: {})
        assert _lignes(ledger)[0]["energie_wh"] >= 10.0


class TestEstimerOctets:
    def test_dict(self):
        assert estimer_octets({"a": "bb"}) > 0

    def test_str(self):
        assert estimer_octets("abcde") == 5

    def test_bytes(self):
        assert estimer_octets(b"1234") == 4

    def test_objet_avec_text(self):
        assert estimer_octets(SimpleNamespace(text="hello")) == 5

    def test_objet_non_mesurable_retourne_zero(self):
        assert estimer_octets(MagicMock()) == 0

    def test_none_retourne_zero(self):
        assert estimer_octets(None) == 0


# ---------------------------------------------------------------------------
# §G6 — Rétro-compatibilité du grand livre
# ---------------------------------------------------------------------------

class TestRetroCompatLedger:
    LIGNE_ANCIENNE = (
        '{"ts": "2025-01-15T10:00:00+00:00", "fournisseur": "serp", "endpoint": "search", '
        '"unites": {"requetes": 1.0}, "cout_estime": 0.01, "devise": "USD", '
        '"fiche": "chauffage-tremblay.md", "cache_hit": false, "resultat": "ok", "detail": ""}'
    )

    def test_ancienne_ligne_se_relit(self):
        entry = LedgerEntry.from_jsonl(self.LIGNE_ANCIENNE)
        assert entry.fournisseur == "serp"
        assert entry.cout_estime == 0.01

    def test_champs_greenit_ont_des_defauts(self):
        entry = LedgerEntry.from_jsonl(self.LIGNE_ANCIENNE)
        assert entry.octets_entrants == 0
        assert entry.octets_sortants == 0
        assert entry.duree_ms == 0.0
        assert entry.energie_wh == 0.0
        assert entry.co2e_g == 0.0
        assert entry.modele is None
        assert entry.profil is None

    def test_registres_recalcules_depuis_ancien_ledger(self, tmp_path):
        """Un api_usage.log antérieur à l'extension reste exploitable au démarrage."""
        ledger = tmp_path / "api_usage.log"
        ledger.write_text(self.LIGNE_ANCIENNE + "\n", encoding="utf-8")
        io = ApiIO(PRICING, ledger, cache_dir=tmp_path / "cache")
        assert io._registres["serp"]["cout"] == pytest.approx(0.01)

    def test_round_trip_avec_champs_greenit(self):
        entry = LedgerEntry.maintenant(
            fournisseur="anthropic", endpoint="messages",
            unites={"input_tokens": 1200.0}, cout_estime=0.0036, devise="USD",
            octets_entrants=2048, octets_sortants=512, duree_ms=812.5,
            energie_wh=0.42, co2e_g=0.2, modele="claude-haiku-4-5-20251001", profil="standard",
        )
        restaure = LedgerEntry.from_jsonl(entry.to_jsonl())
        assert restaure.modele == "claude-haiku-4-5-20251001"
        assert restaure.profil == "standard"
        assert restaure.duree_ms == 812.5
        assert restaure.energie_wh == 0.42

    def test_champ_inconnu_toujours_interdit(self):
        """extra='forbid' reste actif : le contrat du ledger ne se relâche pas."""
        with pytest.raises(Exception):
            LedgerEntry.maintenant(
                fournisseur="http", endpoint="get", unites={}, cout_estime=0.0,
                devise="USD", resultat="ok", champ_inconnu="x",
            )


# ---------------------------------------------------------------------------
# §G7 — Câblage synthesis.py (routage + frugalité + repli hors-ligne)
# ---------------------------------------------------------------------------

class _FauxClientAnthropic:
    """Client anthropic simulé : enregistre les paramètres reçus, ne fait rien."""

    appels: list[dict] = []

    def __init__(self, *a, **kw) -> None:
        self.messages = self

    def create(self, **kwargs):
        _FauxClientAnthropic.appels.append(kwargs)
        texte = (
            "ACCROCHE: Votre fiche Google est absente.\n"
            "# Mini-audit — Chauffage Tremblay\nAucune fiche Google Business détectée."
        )
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=texte)],
            usage=SimpleNamespace(input_tokens=800, output_tokens=200),
        )


@pytest.fixture()
def faux_anthropic(monkeypatch):
    _FauxClientAnthropic.appels = []
    module = SimpleNamespace(Anthropic=_FauxClientAnthropic)
    monkeypatch.setitem(sys.modules, "anthropic", module)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "cle-de-test")
    return _FauxClientAnthropic


class TestSynthesisGreenIT:
    def _entrees(self, nb_failles=2, score=40):
        from diagnostic.models import Company, Gap
        company = Company(nom="Chauffage Tremblay", url="https://x.ca", region="Québec, QC")
        gaps = [
            Gap(dimension="presence_locale", gravite="haute",
                preuve="Aucune fiche Google Business détectée pour cette entreprise.")
        ] * nb_failles
        return company, {"global": score}, gaps

    def test_repli_deterministe_sans_cle_api(self, monkeypatch):
        """Le système doit tourner hors-ligne, à l'identique."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from diagnostic.synthesis import synthesize
        company, scores, gaps = self._entrees()
        accroche, audit = synthesize(company, {}, scores, gaps)
        assert "Chauffage Tremblay" in audit
        assert accroche == gaps[0].preuve

    def test_modele_frugal_par_defaut(self, faux_anthropic):
        from diagnostic.synthesis import synthesize
        company, scores, gaps = self._entrees(nb_failles=2, score=40)
        synthesize(company, {}, scores, gaps)
        assert faux_anthropic.appels, "le LLM aurait dû être appelé"
        assert faux_anthropic.appels[0]["model"] == "claude-haiku-4-5-20251001"

    def test_escalade_sur_fiche_a_fort_score(self, faux_anthropic):
        from diagnostic.synthesis import synthesize
        company, scores, gaps = self._entrees(nb_failles=2, score=95)
        synthesize(company, {}, scores, gaps)
        assert faux_anthropic.appels[0]["model"] == "claude-sonnet-4-5"

    def test_max_tokens_borne_par_la_frugalite(self, faux_anthropic, config):
        from diagnostic.synthesis import synthesize
        company, scores, gaps = self._entrees()
        synthesize(company, {}, scores, gaps)
        plafond = config["frugalite"]["max_tokens_sortie"]
        assert faux_anthropic.appels[0]["max_tokens"] <= plafond

    def test_prompt_borne_meme_avec_beaucoup_de_failles(self, faux_anthropic, config):
        from diagnostic.synthesis import synthesize
        company, scores, gaps = self._entrees(nb_failles=400, score=10)
        synthesize(company, {}, scores, gaps)
        prompt = faux_anthropic.appels[0]["messages"][0]["content"]
        assert len(prompt) <= config["frugalite"]["troncature_prompt_caracteres"]

    def test_appel_llm_journalise_avec_modele_et_empreinte(self, faux_anthropic, tmp_path):
        from diagnostic.synthesis import synthesize
        io, ledger = _io(tmp_path)
        company, scores, gaps = self._entrees()
        synthesize(company, {}, scores, gaps, api_io=io)
        e = _lignes(ledger)[0]
        assert e["fournisseur"] == "anthropic"
        assert e["modele"] == "claude-haiku-4-5-20251001"
        assert e["profil"] == "standard"
        assert e["energie_wh"] > 0
        assert e["octets_sortants"] > 0

    def test_une_seule_passe_si_qa_ok(self, faux_anthropic):
        from diagnostic.synthesis import synthesize
        company, scores, gaps = self._entrees()
        synthesize(company, {}, scores, gaps)
        assert len(faux_anthropic.appels) == 1, "pas de seconde passe inutile"

    def test_escalade_apres_echec_qa(self, faux_anthropic, monkeypatch):
        """QA rejetée → une seule seconde passe, sur le modèle fort."""
        import diagnostic.synthesis as synth
        monkeypatch.setattr(synth, "quality_check", lambda *a, **k: (False, ["ko"]))
        company, scores, gaps = self._entrees(nb_failles=1, score=10)
        synth.synthesize(company, {}, scores, gaps)
        modeles = [a["model"] for a in faux_anthropic.appels]
        assert modeles == ["claude-haiku-4-5-20251001", "claude-sonnet-4-5"]

    def test_pas_de_seconde_passe_si_deja_sur_le_gros_modele(self, faux_anthropic, monkeypatch):
        """Si la 1re passe était déjà escaladée, on ne repaie pas le même échec."""
        import diagnostic.synthesis as synth
        monkeypatch.setattr(synth, "quality_check", lambda *a, **k: (False, ["ko"]))
        company, scores, gaps = self._entrees(nb_failles=1, score=99)  # escalade dès la 1re passe
        synth.synthesize(company, {}, scores, gaps)
        assert len(faux_anthropic.appels) == 1

    def test_echec_llm_retombe_sur_le_repli(self, monkeypatch):
        class ClientQuiPlante:
            def __init__(self, *a, **kw):
                self.messages = self
            def create(self, **kw):
                raise RuntimeError("réseau indisponible")

        monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=ClientQuiPlante))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "cle-de-test")
        from diagnostic.synthesis import synthesize
        company, scores, gaps = self._entrees()
        accroche, audit = synthesize(company, {}, scores, gaps)
        assert "Mini-audit de marque" in audit  # gabarit du repli déterministe
