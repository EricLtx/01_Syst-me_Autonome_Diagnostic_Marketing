"""
test_decay.py — diagnostic/collectors/_decay.py (ADR 0004 D12.4).

Fonction pure : aucune I/O, aucun état, aucune dépendance cachée à l'horloge
système au-delà du paramètre explicite `aujourdhui`.
"""

from __future__ import annotations

from datetime import date, timedelta

from diagnostic.collectors._decay import decroissance

CONFIG = {"demi_vie_jours": 45, "plancher": 0.1}
AUJOURDHUI = date(2026, 8, 3)


class TestProprietesGarantiesADR0004D12_4:
    def test_vaut_1_a_j_plus_0(self):
        assert decroissance(AUJOURDHUI, CONFIG, aujourdhui=AUJOURDHUI) == 1.0

    def test_vaut_1_si_date_dans_le_futur(self):
        """Un événement daté d'aujourd'hui ou plus tard n'a pas encore décru."""
        futur = AUJOURDHUI + timedelta(days=5)
        assert decroissance(futur, CONFIG, aujourdhui=AUJOURDHUI) == 1.0

    def test_vaut_environ_0_5_a_la_demi_vie(self):
        evenement = AUJOURDHUI - timedelta(days=45)
        assert abs(decroissance(evenement, CONFIG, aujourdhui=AUJOURDHUI) - 0.5) < 1e-9

    def test_tend_vers_le_plancher_au_dela(self):
        tres_vieux = AUJOURDHUI - timedelta(days=3650)
        facteur = decroissance(tres_vieux, CONFIG, aujourdhui=AUJOURDHUI)
        assert facteur == CONFIG["plancher"]

    def test_ne_descend_jamais_sous_le_plancher(self):
        for age in (0, 10, 45, 90, 365, 3650, 36500):
            evenement = AUJOURDHUI - timedelta(days=age)
            facteur = decroissance(evenement, CONFIG, aujourdhui=AUJOURDHUI)
            assert facteur >= CONFIG["plancher"]

    def test_strictement_decroissante_avec_l_age(self):
        facteurs = [
            decroissance(AUJOURDHUI - timedelta(days=age), CONFIG, aujourdhui=AUJOURDHUI)
            for age in (0, 10, 30, 45, 90, 180)
        ]
        assert facteurs == sorted(facteurs, reverse=True)
        # Strictement décroissante tant qu'on n'a pas atteint le plancher.
        assert facteurs[0] > facteurs[1] > facteurs[2] > facteurs[3] > facteurs[4]

    def test_fonction_pure_deux_appels_identiques_meme_resultat(self):
        evenement = AUJOURDHUI - timedelta(days=30)
        a = decroissance(evenement, CONFIG, aujourdhui=AUJOURDHUI)
        b = decroissance(evenement, CONFIG, aujourdhui=AUJOURDHUI)
        assert a == b

    def test_plancher_zero_par_defaut_si_absent(self):
        vieux = AUJOURDHUI - timedelta(days=100000)
        assert decroissance(vieux, {"demi_vie_jours": 45}, aujourdhui=AUJOURDHUI) == 0.0

    def test_utilise_date_today_si_aujourdhui_non_fourni(self):
        # Un événement daté d'aujourd'hui (horloge système réelle) vaut 1.0.
        assert decroissance(date.today(), CONFIG) == 1.0
