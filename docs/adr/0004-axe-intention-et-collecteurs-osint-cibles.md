# ADR 0004 — Axe `intention` (événement daté et périssable) + collecteurs OSINT ciblés

- **Statut** : **proposée** — conception uniquement, aucune ligne de code
  livrée par cette ADR. À implémenter par `agent-dev-python`, revue par
  `agent-revue` avant tout commit.
- **Date** : 2026-08-03. **Révisée le même jour**, avant toute implémentation,
  après réception de deux apports qui corrigent des points substantiels du
  premier jet : une note de cadrage métier (CMO) et une note de recherche
  documentaire (académique + professionnelle). Le §« Note de révision »
  ci-dessous dit précisément ce qui a changé et pourquoi — la transparence sur
  ce point compte plus que l'élégance d'un document qui prétendrait avoir été
  juste du premier coup.
- **Remplace** : —
- **Remplacée par** : —
- **Se situe dans** : socle J1 (scoring, modèle de sortie), en capitalisant
  sur l'ADR 0003 (`secteur_id` comme clé de configuration multi-industrie).
  Ne touche pas l'orchestrateur (ADR 0001) ni le routage GreenIT (ADR 0002),
  si ce n'est comme point d'extension optionnel documenté et différé.
  Distincte du chantier « deux axes besoin × capacité » esquissé dans
  `docs/strategie/ETUDE-osint-api-architecture.md` §3.4 (Lot 3) : voir
  §Contexte pour la démarcation exacte entre les deux.

## Note de révision — ce qui a changé depuis le premier jet, et pourquoi

Le premier jet de cette ADR traitait l'intention comme un **second score
0-100**, produit par le même moteur générique que le besoin
(`ScoringEngine(rubrique_intention).score(signaux)` renvoyant un dict de
scores). Deux apports reçus avant tout commit d'implémentation ont corrigé ce
point, et je les intègre plutôt que de les ignorer par confort :

1. **Note de cadrage CMO** : « Un score n'a pas de date ; or la date EST
   l'information. » Un score composite écrase deux histoires opposées
   (besoin 90 × intention 10 et besoin 30 × intention 30 donnent le même
   produit). Mais l'erreur ne s'arrête pas au produit : **même stocker
   l'intention comme un second score /100, séparé du besoin, est déjà une
   erreur de modélisation**, parce que le mécanisme de renormalisation et de
   couverture de `ScoringEngine` a été pensé pour une grandeur qui ne se
   périme pas. Ma conclusion initiale — « le moteur se réutilise à l'identique
   pour l'axe intention » — était donc **fausse dans son ambition**, même si
   la lecture technique qui l'accompagnait (voir plus bas) reste, elle,
   correcte et utile.
2. **Note de recherche documentaire** (caveat impératif : dans cette session,
   `WebFetch` était bloqué par la politique d'egress — 403 systématique sur
   toutes les sources. **Aucun texte intégral n'a été lu.** Les références
   citées ci-dessous sont identifiées de façon fiable (titre, auteurs, revue,
   année, DOI si disponible) mais vérifiées **au seul niveau du résumé**.
   Marquées `[NON LU]` partout où elles apparaissent — ce ne sont jamais des
   preuves lues, seulement des références dont l'existence et le sujet sont
   correctement rapportés) a apporté deux corrections et une validation
   majeure, détaillées au §Fondement théorique et intégrées dans la décision.

**Ce qui reste vrai du premier jet, et qui n'est pas remis en cause** : la
démonstration par lecture de `scoring.py` que le moteur **jette aujourd'hui
l'information « ce check est passé »** (branche `if resultat:` de
`ScoringEngine.score()`, ligne 140, qui n'émet rien), qui est précisément
l'information dont l'intention a besoin. Cette lecture reste le bon
diagnostic technique ; ce qui change, c'est la conclusion qu'on en tire :
pas « on peut réutiliser `.score()` », mais « on ne réutilise QUE les deux
fonctions primitives (`_resolve`, `_check_passes`), jamais l'agrégation ».
Voir §Décision D4.

## Contexte

La commanditaire demande deux choses couplées :

1. Rendre le système « intent-based » : à côté du score de **besoin** (l'état
   constaté d'une entreprise), faire apparaître un signal d'**intention**
   marketing — un événement daté dont la valeur commerciale décroît avec le
   temps.
2. Ajouter les modules OSINT nécessaires pour compléter le socle de données
   avant qualification et scoring, parmi des candidats déjà étudiés (registre
   légal, WHOIS/RDAP, Wayback Machine, PageSpeed, offres d'emploi,
   certifications métier).

Une étude préexistante (`docs/strategie/ETUDE-osint-api-architecture.md`) a
déjà traité une partie de ce terrain : un schéma OSINT à 9 blocs / ~90 champs
et une feuille de route à ~10 collecteurs ont été **explicitement rejetés**
par la revue d'architecture (taux 55,2 %, aval `false`), réduits à **3 blocs
et 4 collecteurs** (§0 et §3.3 de cette étude). Cette ADR ne ressuscite pas ce
qui a été rejeté : elle vérifie, module par module, ce qui reste rejeté, ce
qui reste valide, et ce que la demande d'intention change réellement.

### Trois axes, pas deux — nommer le troisième pour ne pas le perdre

Le système, une fois cette ADR posée, distingue **trois natures de mesure**,
et il importe de ne jamais les confondre entre elles :

| Axe | Nature | Décroît avec le temps ? | Statut |
|---|---|---|---|
| **Besoin** | État (permanent) | Non — une faille reste une faille tant qu'elle est vraie | Existant, inchangé |
| **Capacité** | État (posture, quasi permanente) | Non | Absent — trou nommé, non traité ici (Lot 3 de l'étude, seuils `[À CALIBRER]`, non implémenté) |
| **Intention** | Événement (daté) | **Oui, par construction** | Objet de cette ADR |

**Démarcation avec le Lot 3 de l'étude.** L'étude propose déjà un second axe
« capacité » (`reviews.count` comme proxy de taille, `website.fraicheur_mois`,
`reviews.repond_aux_avis`, qualité de l'email). Ce n'est **pas** l'axe que la
commanditaire demande ici : la capacité est une **posture**, stable sur
plusieurs mois, sans notion d'événement qui expire. L'intention est un
**événement** daté. Ce sont deux axes distincts, qui ne se substituent pas
l'un à l'autre et ne se fusionnent pas entre eux — la même prudence que
celle appliquée entre besoin et intention (§Décision D1) s'applique à
capacité vs intention. `score_capacite` (Lot 3 de l'étude, non implémenté) et
l'axe intention (cette ADR) resteront deux extensions indépendantes.

### Fondement théorique (littérature, niveau résumé uniquement)

Caveat à ne jamais perdre en cours de lecture : **aucune des sources
ci-dessous n'a pu être ouverte dans cette session** (blocage d'egress sur les
outils de récupération web). Chaque référence est identifiée avec suffisamment
de précision pour être vérifiée par un tiers, mais elle est reproduite **au
niveau du résumé rapporté**, jamais comme un texte lu. `[NON LU]` est apposé
systématiquement.

**A. La validation majeure — le scoring déterministe piloté par YAML n'est pas
un pis-aller, à cette échelle c'est le choix le mieux soutenu.**

- Dawes, *The robust beauty of improper linear models in decision making*,
  American Psychologist 34(7), 1979 `[NON LU]` : des modèles à poids non
  optimisés (voire unitaires) battent le jugement clinique non structuré et
  rivalisent avec une régression optimisée sur données petites et bruitées —
  ce qui compte est d'inclure les bonnes variables, pas de bien les pondérer.
- Jung, Concannon, Shroff, Goel & Goldstein, *Simple rules to guide expert
  classifications*, JRSS-A, 2020 `[NON LU]` : des checklists à poids arrondis
  atteignent ~86 % de précision moyenne sur 22 jeux de données, à parité avec
  des random forests entraînées sur toutes les variables.
- Littérature EPV (Peduzzi 1996 ; Vittinghoff & McCulloch 2007 ; van Smeden
  2016) `[NON LU]` : à quelques dizaines de prospects/mois et quelques
  conversions par an, on ne dispose pas d'assez d'événements positifs pour
  ajuster un modèle appris de façon crédible — un tel modèle serait du bruit
  présenté comme un score.
- D'Haen, Van den Poel, Thorleuchter & Benoit, *Integrating expert knowledge
  and multilingual web crawling data in a lead qualification system*,
  Decision Support Systems, 2016, DOI 10.1016/j.dss.2015.12.002 `[NON LU]` —
  la référence la plus proche de l'architecture de ce projet : les données
  commerciales achetées sont chères et lacunaires, **les données de crawl web
  sont gratuites et de meilleure qualité** parce que produites par les
  entreprises elles-mêmes qui ont intérêt à leur exactitude, et l'intégration
  de connaissance experte améliore le système, validé en conditions réelles.
- Kinne & Lenz, PLOS ONE 2021 `[NON LU]` : le texte des sites web prédit des
  caractéristiques réelles de la firme, validé contre l'enquête d'innovation
  allemande CIS.

**Conséquence à écrire noir sur blanc, parce qu'elle change le ton du
document** : les collecteurs palier 0 (HTML déjà en mémoire) ne sont **pas**
un mode dégradé en attendant des clés API payantes — au vu de cette
littérature (sous la réserve `[NON LU]` ci-dessus), c'est **le socle
légitime** de ce système, à cette échelle de volumétrie. Cela renforce, sans
la conditionner, la décision déjà prise au §Décision D8 de privilégier deux
extensions palier 0 plutôt qu'un collecteur payant.

**B. Deux corrections de conception, retenues telles quelles.**

- **B1 — la décroissance ne s'applique qu'aux événements datés, jamais aux
  états.** « Une note Google basse ne "vieillit" pas ; elle est vraie tant
  qu'elle est vraie. » Conséquence directe et vérifiée contre le code actuel :
  `reviews.repond_aux_avis`, une éventuelle « dégradation de la cadence
  d'avis », l'immatriculation ou l'ouverture d'établissement sont des **états**
  (changements structurels, décroissance très longue voire nulle), donc de
  l'axe **besoin**, jamais de l'axe intention. C'est la raison technique pour
  laquelle la typologie `evenement`/`etat` introduite au §Décision D2 est
  obligatoire, pas cosmétique.
- **B2 — un seul axe de fiabilité de source, pas une matrice à deux axes.**
  Baker, McKendry & Mace (US Army Research Institute, TRN 200, 1968)
  `[NON LU]` : les analystes utilisant l'échelle Admiralty/OTAN (fiabilité de
  source A–F × crédibilité de l'information 1–6) cotent presque toujours sur
  la diagonale (A1, B2, C3) — l'échelle à deux axes s'effondre sur un seul en
  pratique. Traduit au §Décision D6 : un **axe unique**, déterministe, déclaré
  explicitement par check dans la rubrique (pas dérivé par jugement humain),
  plus la métrique de complétude déjà existante (`_couverture`).

**C. Ce que ça change pour le choix des signaux (détaillé au §Décision D7).**

- **L'offre d'emploi est le signal externe le mieux étayé** : Gutierrez,
  Lourie, Nekrasov & Shevlin, *Are Online Job Postings Informative to
  Investors?*, Management Science, 2020 `[NON LU]` — les offres d'emploi sont
  une information avancée sur effectifs, chiffre d'affaires et résultats.
  Réserve honnête et importante : établi sur des sociétés **cotées**, pas sur
  des PME de 5-50 salariés — le saut vers « cette PME va acheter du branding »
  n'est **pas** dans la source.
- **Les avis relèvent de l'axe besoin, pas intention** — cohérent avec B1.
  Luca (Harvard Business School) et Anderson & Magruder (Economic Journal)
  `[NON LU]` établissent par régression sur discontinuité que +1 étoile ⇒
  +5 à 9 % de chiffre d'affaires, chez les indépendants. C'est un argument
  commercial chiffrable pour la consultante — ce n'est **pas** une prédiction
  d'achat, et ce n'est **pas** un événement daté.
- **La forme fonctionnelle de la décroissance** (`poids = 2^(−t / demi_vie)`,
  demi-vie déclarée par type de signal en YAML) est une **convention
  d'outillage, pas un résultat empirique** : les demi-vies annoncées par les
  fournisseurs commerciaux se contredisent d'un facteur 4 à 6 et aucune n'est
  traçable. À documenter avec le même vocabulaire d'honnêteté que celui déjà
  employé dans ce projet pour `energie_wh`/`co2e_g` (GreenIT, ADR 0002) :
  **estimation, jamais une mesure certifiée.**
- **Aucune source ne relie à un achat** la refonte de site, l'apparition d'un
  pixel publicitaire, un changement de dirigeant, une levée de fonds, une
  certification ou l'ouverture d'un établissement — `[NON TROUVÉ]` en
  académique pour chacun. Implémentables plus tard comme des **hypothèses
  testables à poids faible**, explicitement étiquetées comme telles — jamais
  présentées comme des faits validés.
- **Le point aveugle central, à écrire noir sur blanc** : aucune source ne
  franchit le dernier pas entre « signal ouvert observé » et « cette PME va
  acheter du conseil en branding ». **Cette hypothèse appartient à la
  consultante, pas à la recherche.** Elle doit vivre explicitement dans le
  YAML de rubrique (§Décision D7, champ `hypothese:`), jamais comme un fait
  assumé par le code.

## Décision

### D1. Verdict sur l'hypothèse deux/trois-axes — révisé

**L'hypothèse est retenue, et durcie par rapport au premier jet : l'intention
n'est pas un second score, c'est une liste d'événements datés et
périssables.** Trois raisons, vérifiées dans le code, pas seulement
argumentées :

1. **Non-monotonie.** Le besoin est déjà pensé comme l'inverse d'une note de
   satisfaction (`knowledge/rubric_persona1.yaml:11-15` : « Un score BAS = un
   prospect CHAUD »). Un événement d'intention est positif par nature (sa
   présence est bonne) : le fusionner dans le même total ferait dépendre le
   sens du nombre final du hasard de la combinaison — besoin bas + recrutement
   n'a pas le même sens commercial que besoin haut + recrutement. Un score
   composite écrase cette différence, exactement l'erreur anticipée par la
   commanditaire (« besoin 90 × intention 10 » et « 30 × 30 » donnant le même
   produit pour deux prospects opposés).
2. **La classe de défaut est déjà connue et déjà corrigée une fois dans ce
   projet**, pour une raison structurellement identique : fusionner « non
   observé » et « échec » a produit des scores fabriqués (`scoring.py:11-36`).
   Fusionner « pas de besoin pressant » et « pas d'événement détecté » dans un
   seul nombre — ou même les stocker comme deux scores comparables — reproduit
   la même perte d'information sous une forme différente.
3. **Une date n'est pas une magnitude.** Un score /100 n'a pas de champ pour
   « ceci expire le [date] ». Le premier jet de cette ADR le contournait en
   pré-décroissant la valeur avant de la faire passer par `gte` — techniquement
   correct, mais cela **cache** l'information la plus importante (la date et
   son échéance) dans un flottant sans en garder trace exploitable ailleurs
   que dans l'accroche. La correction du CMO est donc retenue : **l'objet de
   sortie de l'axe intention est une liste d'événements datés
   (`EvenementIntention`), jamais un dict de scores.**

**Troisième axe nommé, non traité** : la capacité (état, posture) — voir
§Contexte. Cette ADR ne construit ni son schéma ni ses collecteurs.

**Nuance conservée du premier jet, et toujours valide** : séparer les axes
n'implique pas de calculer une priorité algorithmique à partir d'eux. Voir D5 :
la mise en relation besoin/intention passe par une **table de correspondance
déterministe** sur deux libellés discrets, jamais par un calcul (produit,
somme pondérée). Cohérent avec l'invariant « l'orchestrateur ordonnance, il
ne décide rien », étendu par analogie : **le système signale, il ne priorise
pas à la place de l'opératrice.**

### D2. Typologie `evenement` / `etat` et modèle de données

**Chaque check d'une rubrique (besoin ou intention) déclare sa nature.**
Défaut `etat` (rétro-compatible : les rubriques de besoin existantes,
`rubric_persona1.yaml`, n'ont rien à modifier, tous leurs checks sont
implicitement `etat`). Un check `evenement` **doit** déclarer un champ
`date_signal` (chemin pointé vers une date fournie par le collecteur) et une
`demi_vie_jours` ; s'il ne peut pas être daté au moment de l'observation, il
est **écarté**, pas dégradé en état permanent — c'est la correction directe
du candidat exclu « page carrières sans offre datée, souvent permanente,
n'indique rien » (§Décision D7).

```python
# diagnostic/models.py — nouveau dataclass, à côté de Gap (positivité inverse,
# ET nature temporelle distincte — pas un simple "Gap positif").
@dataclass
class EvenementIntention:
    dimension: str
    preuve: str            # phrase factuelle, date déjà interpolée (ex. "offre du 12/07")
    date_evenement: date   # date du fait observé — jamais None (un événement non daté est écarté en amont)
    expire_le: date        # péremption calculée UNE FOIS à l'évaluation (voir D2 "péremption")
    intensite: str         # "haute" | "moyenne" | "basse" — jugement commercial déclaré en YAML
    citable: bool          # True SEULEMENT si le prospect a publié ce fait pour être vu (voir D6)
    fiabilite: str         # axe UNIQUE de fiabilité de source, déclaré en YAML (voir D6)
```

`Diagnostic` (`diagnostic/models.py`) gagne **un seul** champ nouveau, en fin
de dataclass, valeur par défaut, aucun champ existant modifié :

```python
evenements_intention: list[EvenementIntention] = field(default_factory=list)
```

**Explicitement retiré du premier jet** : `scores_intention: dict[str, float]`.
Il n'y a pas de score d'intention. Vérifié à nouveau contre
`tests/test_j1_smoke.py` : aucune assertion n'exige une égalité stricte sur
`Diagnostic.to_dict()`/ses clés — l'ajout d'un seul champ optionnel ne casse
aucune des six assertions de ce fichier.

**Péremption automatique, sans intervention.** `expire_le` est calculé **une
seule fois**, au moment où l'événement est détecté (à la date de diagnostic),
comme `date_evenement + fenetre_jours` (donnée YAML, typiquement un multiple
de la demi-vie déclarée). C'est une **date stockée**, pas une valeur qui
continue de se recalculer : n'importe quel lecteur ultérieur (export,
cockpit, requête Dataview) peut se demander « `date.today() > expire_le` ? »
— une comparaison de dates triviale, sans aucune logique métier dupliquée,
exactement du même ordre que vérifier `opt_out` avant un export. C'est ce
mécanisme, et lui seul, qui permet à une fiche de retomber en priorité basse
**sans qu'aucun code métier ne s'exécute à nouveau** : la donnée porte sa
propre date de péremption, le lecteur ne fait qu'une comparaison.

### D3. Le verrou : historique et série temporelle

**C'est la décision d'architecture centrale de ce chantier**, au sens où elle
conditionne quels signaux d'intention seront un jour observables — même si les
deux collecteurs retenus au Lot 1 de cette ADR (D8) n'en ont pas besoin.

**Le problème.** Une partie des signaux d'intention plausibles ne sont pas
observables en une seule lecture : ce sont des **changements d'état entre deux
dates** — apparition ou disparition d'un pixel publicitaire, refonte de site
engagée (avant/après). On ne peut pas savoir qu'un pixel « est apparu » sans
une observation antérieure à comparer. `FicheProspect` ne conserve aujourd'hui
aucune série temporelle : `date_diagnostic` est un champ unique, écrasé à
chaque diagnostic (vérifié dans `vault_schema.py` : aucun champ de type liste
horodatée n'existe, en dehors de `gaps_majeurs`, qui n'est pas daté par
entrée).

**Contrainte contractuelle à traiter AVANT, pas après.** Les Maps Platform
Terms plafonnent la conservation de la plupart des champs Google Places à
30 jours (déjà noté par l'étude, §2.1 : « ne persister que `place_id` + des
dérivés non reconstituables »). Toute historisation de signaux Places doit
donc **exclure les valeurs brutes** (note, nombre d'avis) et ne stocker que
des **dérivés non reconstituables** : `avis_bucket` (ex. `"10-24"`),
`note_bucket` (ex. `"4-4.5"`), `cadence_avis_par_mois` (un flottant calculé,
pas une liste d'avis). Cette règle n'est pas spécifique à l'intention : elle
s'applique à toute historisation future, y compris pour l'axe besoin.

**Où vit l'historique.** Un nouveau fichier par fiche, **append-only**,
**écrit exclusivement par `VaultIO`** — un nouveau petit mécanisme, pas un
nouvel écrivain : `vault/40-Historique/<slug>.jsonl`. Une ligne JSONL par
observation dérivée :

```json
{"ts": "2026-08-03T10:00:00Z", "dimension": "avis", "cle": "cadence_avis_par_mois", "valeur": 1.2, "source": "reviews"}
```

Ce n'est **pas** une réécriture du corollaire de l'invariant #1 (« aucun autre
module n'appelle `os.replace()` ») : comme `runs.log` aujourd'hui,
l'append-only n'a jamais besoin de `os.replace()` — un simple `open(path,
"a")` suffit, exactement le mécanisme déjà en place pour
`VaultIO._journal()` (`vault_io.py:136-146`, vérifié par lecture). Une
nouvelle méthode `VaultIO.append_historique(slug, dimension, cle, valeur,
source)` suit ce précédent à l'identique — un ajout au bus, pas une exception
à son unicité.

**Pourquoi dans le vault et pas dans `.cache/`** : ce n'est pas un cache
technique reconstituable par un nouvel appel réseau (contrairement au HTML
brut) — c'est la **seule** trace de faits dérivés qui, pour beaucoup d'entre
eux, ne seront plus observables une fois la fenêtre Places de 30 jours passée.
Le perdre équivaut à perdre définitivement la possibilité de détecter un
« changement ». Il appartient donc au même régime que les fiches elles-mêmes
(versionné, sous le contrôle exclusif de `VaultIO`), pas au disque de travail.

**Rétention** : donnée, pas code — un champ `retention_historique_jours` (ex.
730) dans un futur `knowledge/historique.yaml`. La purge est une tâche de
maintenance périodique (script, pas un chemin temps réel), hors périmètre de
cette ADR.

**Ce que cette ADR NE construit PAS maintenant** : aucun collecteur qui a
réellement besoin de cet historique (détection de pixel publicitaire, refonte
de site en cours). Les deux collecteurs retenus (D8) portent chacun leur
propre date dans une seule observation et n'ont pas besoin de comparer deux
lectures. L'infrastructure est posée ici parce qu'elle est structurante et que
la CMO a raison de la nommer maintenant — mais rien n'est bâti dessus dans ce
lot. Voir §Ce que je refuse de faire maintenant.

### D4. Réutilisation du `ScoringEngine` — démontrée, corrigée par rapport au premier jet

Vérification faite en lisant `diagnostic/scoring.py` en entier (187 lignes).

**Ce qui se réutilise, et rien de plus** : les deux fonctions primitives et
pures `_resolve` (ligne 61) et `_check_passes` (ligne 67) — l'évaluateur de
check à trois états (`ok`/`echec`/`inconnu`), indépendant de toute agrégation.
C'est la seule chose dont l'axe intention a besoin : savoir si UN check est
observé et vrai, avec la même discipline de trois états que le besoin.

**Ce qui NE se réutilise PAS, corrigé par rapport au premier jet** :
`ScoringEngine.score()` — sa boucle d'agrégation, sa renormalisation par
poids, son `_couverture`, son score global. Réutiliser `.score()` pour
l'intention forcerait la donnée dans le moule du besoin — précisément l'erreur
que la CMO a identifiée et que je retiens : un événement daté n'a pas de poids
relatif à renormaliser contre d'autres événements, il a une date et une
échéance.

**Le point qui reste le meilleur apport du premier jet, inchangé** :
`ScoringEngine.score()` (lignes 132-155) ne produit un objet que dans la
branche `else` (`resultat` faux) — un `Gap`. Dans la branche `if resultat:`
(ligne 140), rien n'est capturé au-delà du score : **le moteur jette
aujourd'hui l'information « ce check est passé »**, précisément celle dont
l'intention a besoin. Ce diagnostic reste vrai et utile ; ce qui change, c'est
qu'on ne le résout plus en réutilisant `.score()`, on le résout en **rejouant
les checks indépendamment**, sans jamais agréger :

```python
# diagnostic/intent.py — nouveau, ~35 lignes. N'importe QUE les deux primitives
# de scoring.py, jamais ScoringEngine ni sa méthode score().
from datetime import date, timedelta
from diagnostic.models import EvenementIntention
from diagnostic.scoring import _resolve, _check_passes

def evaluer_intention(rubrique_intention: dict, signaux: dict) -> list[EvenementIntention]:
    """Rejoue les checks d'une rubrique d'intention un par un, SANS agrégation
    ni renormalisation : pas de score composite (ADR 0004, correction CMO)."""
    evenements: list[EvenementIntention] = []
    for dim_name, dim in rubrique_intention["dimensions"].items():
        for c in dim["checks"]:
            if c.get("nature", "etat") != "evenement":
                continue  # un check "etat" n'a rien à faire dans l'axe intention (correction B1)
            value = _resolve(signaux, c["signal"])
            if _check_passes(value, c["op"], c.get("value")) is not True:
                continue  # False ou None : ni faille inversée, ni évènement fabriqué
            date_evenement = _resolve(signaux, c["date_signal"])
            if date_evenement is None:
                continue  # non daté : écarté, jamais traité comme permanent (correction D7)
            fenetre = c.get("fenetre_jours", c.get("demi_vie_jours", 30) * 3)
            evenements.append(EvenementIntention(
                dimension=dim_name,
                preuve=c["preuve"].format(jours=(date.today() - date_evenement).days),
                date_evenement=date_evenement,
                expire_le=date_evenement + timedelta(days=fenetre),
                intensite=c.get("intensite", "moyenne"),
                citable=c.get("citable", False),   # sécurité par défaut : jamais citable sans déclaration explicite
                fiabilite=c.get("fiabilite", "D_derive"),
            ))
    evenements.sort(key=lambda e: e.date_evenement, reverse=True)
    return evenements
```

**`scoring.py` n'est pas modifié : zéro ligne.** `_resolve`/`_check_passes`
sont déjà des fonctions pures sans effet de bord, importées telles quelles
dans le même package. `agent-revue` peut vérifier par `git diff
diagnostic/scoring.py` qu'il est vide après implémentation du Lot 1.

**Défaut vérifié séparément, à traiter par un mécanisme apparenté mais
distinct** : le check `entretien.website.fraicheur_mois <= 18` (gravité
`haute`) est binaire — 2 ans et 7,5 ans produisent exactement le même
résultat (dimension à 40,0, gravité `haute`). C'est le même mode de
défaillance que celui déjà corrigé pour le besoin ce matin (une norme
sectorielle qualifiée de faille grave), à un autre endroit. La solution ne
touche PAS non plus `scoring.py` : elle suit le **même principe** que la
décroissance d'intention — **graduer en amont du moteur, dans le collecteur,
via un barème déclaré en YAML, puis comparer avec l'opérateur `gte` déjà
existant.**

```python
# diagnostic/collectors/_bareme.py — nouveau, fonction pure, aucun réseau.
def echelle(valeur: float, paliers: list[dict]) -> float:
    """paliers = [{"max": 12, "points": 1.0}, {"max": 36, "points": 0.6}, ...],
    triés par max croissant. Retourne un flottant dans [0, 1]."""
```

`website.py` gagnerait un champ dérivé `fraicheur_score: float | None` calculé
via `echelle(fraicheur_mois, paliers)`, `paliers` étant injecté depuis
`knowledge/rubric_{secteur}.yaml` (un bloc `bareme:` par check gradué,
donnée). Le check de la rubrique passe de `{signal: website.fraicheur_mois,
op: lte, value: 18}` à `{signal: website.fraicheur_score, op: gte, value:
0.5}` — **zéro nouvel opérateur, zéro ligne dans `scoring.py`**, mais **ce
n'est PAS un ajout strictement additif** : il change le comportement d'un
check déjà en production, donc le score `entretien` de tout prospect déjà
diagnostiqué. Traité comme son **propre petit lot** (D11, Lot 0bis), pas
fondu dans le Lot 1 intention, précisément pour que la preuve « `scoring.py`
non modifié » du Lot 1 (D12) reste isolée et vérifiable sans bruit.

### D5. Matrice de priorité — table de correspondance, jamais un calcul

**Décision explicite, en réponse directe à la mise en garde du CMO** : la mise
en relation besoin/intention est une **table de correspondance déterministe**
sur deux libellés discrets, jamais un produit ni une somme pondérée.

| | Intention forte | Intention faible / expirée |
|---|---|---|
| **Besoin fort** | **Q1 — Fenêtre** (priorité 1) | **Q3 — Réservoir** (veille, ne pas contacter maintenant) |
| **Besoin faible** | **Q2 — Concurrence** (budget prouvé, ticket supérieur) | **Q4** (rejet avec motif) |

`besoin_niveau` (fort/faible) : dérivé de `score_global` contre un seuil
`[À CALIBRER]` en YAML (même prudence que le Lot 3 de l'étude — aucune valeur
devinée). `intention_niveau` (fort/faible) : `"fort"` si au moins un
`EvenementIntention` avec `date.today() <= expire_le` existe, `"faible"`
sinon — un test booléen trivial, pas un score. Le quadrant est un
**champ informationnel** (`FicheProspect.quadrant: str | None`, Lot 3,
§D11), jamais utilisé pour trier ou disqualifier automatiquement — la
disqualification automatique reste hors périmètre, comme pour le Lot 3 de
l'étude.

Un système purement besoin-based classe Q2 en dernier (score haut = pas de
faille visible) et Q3 en premier (score bas = beaucoup de failles) — l'inverse
exact de la valeur commerciale quand une intention forte est disponible. La
table ci-dessus rend Q2 atteignable, ce qui est tout l'objet de la demande.

### D6. Signal jointif, citabilité, fiabilité de source

**Citabilité — contrainte dure.** Certains signaux sont excellents pour
prioriser en interne et désastreux à prononcer devant le prospect (une
modification au registre, une chute de cadence d'avis, la disparition d'un
pixel se lisent comme de la surveillance, pas comme de l'observation
publique). Règle : **on ne cite que ce que le prospect a publié
délibérément pour être vu.** `EvenementIntention.citable` défaut à `False` —
un check ne devient citable que par déclaration explicite en YAML. Contrainte
dure côté `serializers.py`, **même patron que la règle déjà en vigueur** pour
`signal_chaud` (jamais dérivé d'un signal inconnu) : `signal_intention` ne
peut être dérivé que d'un `EvenementIntention` avec `citable=True`. Un
événement non citable peut alimenter le quadrant de priorité (D5), jamais une
phrase envoyée au prospect.

Les deux collecteurs retenus (D8) sont, par construction, **entièrement
citables** : une offre d'emploi publiée par l'entreprise et une certification
affichée sur son propre site sont déjà rendues publiques par le prospect
lui-même. La contrainte dure protège les extensions **futures** (pixel,
registre, cadence d'avis) qui, elles, ne le seraient pas nécessairement.

**Fiabilité de source — un seul axe, pas une matrice.** Conformément à B2 :
chaque check déclare un `fiabilite:` explicite (donnée, pas dérivée par
jugement humain), parmi un vocabulaire fermé — `A_registre` (registre officiel,
non utilisé tant que `registre.py` reste hors périmètre) · `B_site_officiel`
(le site du prospect — les deux collecteurs retenus ici) · `C_api_commerciale`
(Google Places…) · `D_derive` (dérivation automatique seo/social) ·
`E_serp_non_confirme` · `F_synthese_llm` (jamais utilisé pour un fait,
puisque le LLM ne collecte jamais — voir invariant projet). Combiné à
`_couverture`, déjà existant côté besoin, cela couvre l'intégralité du besoin
de confiance sans construire une seconde échelle.

**Signal jointif — à privilégier dans le classement des accroches.** Un fait
simultanément **daté** (un événement d'intention) ET **absent du site**
(une faille de besoin) fait les deux temps en une phrase et doit primer sur
les autres. Exemple concret, réalisable avec les deux collecteurs retenus
sans registre externe : « Recrute activement (offre du {jours} jours) mais
ne présente pas clairement son offre de service sur son site » — combine
l'événement `recrutement.offre_detectee` (intention) et le gap existant
`website.mentions_offre` (besoin, déjà dans `rubric_persona1.yaml:61`).
Mécanisme : un champ optionnel `sujet:` partagé entre un check de besoin et
un check d'intention ; `serializers.py` détecte l'intersection (un
`EvenementIntention` et un `Gap` partageant le même `sujet`) et le place en
tête de l'accroche. Spécifié ici, **non implémenté avant le Lot 2** (D11) —
un seul exemple concret ne justifie pas de bâtir la généralisation avant
qu'un second exemple existe.

### D7. Signaux retenus et écartés pour la rubrique d'intention

**Le signal le mieux étayé n'est pas celui attendu.** Une embauche
« marketing/communication » est rare dans une PME de 5-30 personnes — donc
statistiquement peu exploitable comme signal récurrent. **Une embauche de
production (technicien, installateur) est fréquente, datée, publique,
gratuite, et crée une obligation de répondre à la demande sous ~90 jours** —
c'est le signal retenu en priorité (converge avec le CMO ; appuyé, sous
réserve `[NON LU]` et réserve de portée, par Gutierrez et al. 2020, §Fondement
théorique C). Le vocabulaire de poste dans
`knowledge/vocabulaire_intention_{secteur}.yaml` doit donc couvrir **en
priorité les rôles de production du secteur**, avec les rôles
marketing/communication conservés comme **second bucket, poids plus faible,
volume attendu plus rare**.

**Hypothèse commerciale à déclarer, pas à coder en dur** : « une PME qui
embauche en production a besoin de remplir un carnet de commandes plus
grand, donc peut être disponible pour investir en marketing » n'est établie
par **aucune source académique identifiée** (§Fondement théorique, point
aveugle central). Chaque dimension de `intent_{secteur}.yaml` porte donc un
champ `hypothese: "texte, à valider par le pilote"` — même honnêteté que
`energie_wh` en GreenIT.

**Reclassé, en cohérence avec B1** : `reviews.date_dernier_avis` — suggéré
initialement côté intention, reclassé côté **besoin** (un proxy de fraîcheur
de la réputation, analogue à `website.fraicheur_mois`, ne décroît pas comme un
événement) — pur ajout YAML à `rubric_persona1.yaml`, zéro nouveau code,
zéro nouveau collecteur (le champ est déjà produit par `reviews.py`, déjà
jeté aujourd'hui).

**Écartés explicitement** (repris de la note de recherche, alignés sur ce que
l'architecture peut vérifier) : signaux tiers type « surge topics » (une PME
locale n'émet rien dans ces coopératives) · désanonymisation reverse-IP
(hors du périmètre déterministe et proportionné du projet) · déclencheurs
canoniques du B2B tech (levée de fonds, nomination d'un CRO — n'arrivent
jamais chez une PME de ce segment) · social listening (exigerait du scraping
au-delà des sources publiques déjà admises — hors invariants) · année de
copyright seule (asymétrique : une valeur ancienne est informative, une
valeur récente ne l'est pas, souvent générée dynamiquement par le CMS —
`website.copyright_year` reste utile au besoin, pas fiable seul pour un
événement) · page « nous recrutons » sans offre datée (souvent permanente,
n'indique rien — voir D2, un événement non daté est écarté, pas dégradé) ·
saisonnalité (n'est pas un signal de prospect mais une fenêtre de non-contact
à porter dans l'ICP, hors périmètre de cette ADR).

### D8. Les collecteurs OSINT retenus (2, pas dix)

Rappel des décisions déjà actées dans `ETUDE-osint-api-architecture.md`
(§0, §3.3, §3.6), que cette ADR **ne rouvre pas** : `domaine.py` (RDAP/DNS/MX)
supprimé du plan ; `archive.py` (Wayback), `perf.py` (PageSpeed), `emploi.py`
(API externe France Travail/Guichet-Emplois), `stack.py` payant écartés
(« quotas non sourcés, dépendances instables, rendement marginal ») ;
`registre.py` (REQ/Zefix/Sirene) reporté hors périmètre 6 mois (« effort
élevé, rapprochement d'entités sans faux positif = point dur non résolu »).
Ces motifs restent valables : aucun ne devient plus solide parce que la
finalité est l'intention plutôt que le besoin. **Maintenus rejetés, pas
ressuscités.**

#### Retenu 1 — Extension de `website.py` : signal de recrutement (production en priorité)

| | |
|---|---|
| Palier | 0 (dérivé) en Lot 1 ; 0+1 en Lot 2 |
| Source | HTML déjà téléchargé (Lot 1) ; une page carrières du même domaine, un seul appel de plus via le bus (Lot 2) |
| Apporte à | **Intention** — un `EvenementIntention` par offre détectée, jamais un score |
| Mode dégradé | `None` si site injoignable ou vocabulaire non configuré (même discipline que `mentions_offre`, ADR 0003) |
| Coût | 0 en Lot 1 ; marginal en Lot 2 (1 appel/cible, caché) |
| Conformité | Zéro donnée personnelle — une caractéristique de poste, jamais un nom, jamais un contact. Entièrement `citable` (le prospect l'a publié pour être vu). |

**Pourquoi lui plutôt qu'un `emploi.py` externe (rejeté)** : la version API
externe (France Travail temps réel, gratuite, excellente couverture France ;
Guichet-Emplois, dump mensuel, Québec ; **aucune source identifiée pour la
Suisse — trou documenté, pas résolu ici**) reste écartée pour asymétrie de
couverture entre marchés et dépendance à un fournisseur non maîtrisé. La
version retenue lit le site du **prospect lui-même** : symétrique sur les
trois marchés, zéro nouvelle dépendance externe, zéro nouveau point du bus
au-delà de ce que `website.py` fait déjà.

#### Retenu 2 — `legitimite.py` (nouveau module, palier 0)

| | |
|---|---|
| Palier | 0 |
| Source | HTML déjà en mémoire (regex : licence RBQ, mention RGE, suissetec, programme de subvention en vigueur) |
| Apporte à | **Besoin** (nouvelle dimension `legitimite_conformite`) — complète le socle avant scoring, comme demandé |
| Mode dégradé | `None` par check si le motif n'est pas configuré pour le secteur/marché |
| Coût | 0 |
| Conformité | Donnée publiée par l'entreprise sur elle-même (comme un badge), zéro donnée personnelle |

**Pourquoi lui** : déjà entièrement vetté par l'étude (§3.3, statut
« AJOUTER »), répond au candidat « certifications métier », complète le socle
de besoin avant scoring — sans toucher à l'intention, ce qui est correct
puisqu'une certification affichée est un **état**, pas un événement (B1).

#### Exclus explicitement (pas un report silencieux)

| Candidat | Décision | Motif |
|---|---|---|
| Registre légal (REQ/Zefix/Sirene) | Exclu, aligné sur l'étude | Reporté hors périmètre 6 mois (rapprochement d'entités = point dur non résolu). **Conformité aggravée** : Sirene applique un statut « partiellement diffusible » depuis 2023 avec obligation de respecter l'opposition à la prospection **dès la collecte**, pas seulement à l'export — une contrainte supplémentaire à traiter le jour où ce collecteur serait construit, pas aujourd'hui. |
| WHOIS/RDAP | Exclu, aligné sur l'étude (`domaine.py` supprimé) | Signal statique (âge du domaine) — ni un événement daté, ni un signal manquant côté besoin (`derniere_maj`/`fraicheur_mois` déjà collectés, gratuits). |
| Wayback Machine | Exclu, aligné sur l'étude (`archive.py` écarté) | `derniere_maj` déjà collecté est un proxy suffisant pour le besoin ; daterait une refonte (potentiel événement d'intention), mais une dépendance externe à quota non documenté pour un gain non mesuré n'est pas justifiée avant un pilote. |
| PageSpeed/Lighthouse | Exclu, aligné sur l'étude (`perf.py` écarté) | Qualité technique, pas intention marketing ; déjà classé rendement marginal. |
| Offres d'emploi (API externe) | Exclu | Voir Retenu 1 : remplacé par une version dérivée du site du prospect. |

### D9. Conformité — trois points qui touchent l'architecture

1. **La porte humaine est un mitigant juridique, pas une préférence de
   conception.** Art. 22 RGPD (décision fondée *exclusivement* sur un
   traitement automatisé) et la jurisprudence CJUE 2023 (SCHUFA, C-634/21)
   jugent que « exclusivement » couvre le cas où un humain signe formellement
   mais s'en remet en pratique à l'algorithme. **Recommandation, non exécutée
   par cette ADR** (hors du périmètre de fichiers de l'architecte pour
   `docs/strategie/`, mais `docs/architecture/invariants.md` en relève et
   reste modifiable) : inscrire cette justification dans les invariants, avec
   la conséquence opérationnelle directe pour ce chantier — **un cockpit ou un
   export qui laisserait deviner un tri implicite par quadrant (D5) sans que
   l'opératrice lise réellement chaque fiche rebasculerait le système dans le
   champ de l'art. 22.** Le quadrant reste un label informationnel affiché,
   jamais un ordre de traitement imposé.
2. **CASL/LCAP** : la charge de la preuve du consentement pèse sur
   l'expéditeur ; le CRTC interprète strictement la « publication bien en
   vue ». Recommandation peu coûteuse et hors du périmètre strict de cette
   ADR (touche `enrichment.py`, pas les modules ici conçus) : faire porter à
   `contact_email_source` l'URL exacte et l'horodatage de la publication, pas
   seulement le nom de la source.
3. **AI Act** : le scoring de prospects B2B ne figure pas à l'Annexe III
   (haut risque). `synthesis.py` (LLM génératif) porte le risque art. 50
   (transparence, applicable depuis le 2 août 2026) si un mini-audit rédigé
   par IA part chez un prospect. **L'axe intention, tel que conçu ici,
   n'ajoute AUCUNE exposition art. 50** : aucune étape n'implique de LLM, la
   détection et la phrase d'accroche sont entièrement déterministes (D2, D6).

### D10. Séquencement — arbitrage sur la recommandation du CMO

Le CMO place l'instrumentation du résultat (`motif_rejet` sur `→ rejete`,
états post-`contacte`) **avant tout ajout de signal**, au motif que sans
dénominateur commercial, le chantier intent est invérifiable — indistinguable
du folklore.

**Je suis cette recommandation sur le fond, avec une nuance d'exécution, pas
de désaccord.** Sur le fond : sans `motif_rejet` ni états `rdv`/`client`
(déjà spécifiés par l'étude, Lot 4, effort faible, indépendant de cette ADR),
il est impossible de mesurer si le quadrant Q1-Q4 améliore quoi que ce soit —
la note de recherche documentaire renforce cet argument (EPV : à ce volume,
seule une mesure directe compte, aucun modèle ajusté ne peut compenser
l'absence de dénominateur). **La nuance** : le Lot 1 de cette ADR (D11) est
bon marché et strictement additif (aucun réseau nouveau, aucun changement de
`scoring.py`) — le bloquer entièrement retarderait une preuve de câblage qui
ne coûte rien et n'engage rien. Je propose donc un **gate à deux vitesses** :
le squelette (Lot 1, D11) peut être construit en parallèle de l'étude Lot 4 ;
mais **aucune exploitation en conditions réelles** du quadrant ou d'une
accroche d'intention (un export livré, un run réel priorisé par Q1-Q4) ne
doit avoir lieu tant que `motif_rejet` et les états post-`contacte` ne sont
pas en place pour mesurer si Q1/Q2 convertissent mieux que Q3/Q4. Sans cette
mesure, l'hypothèse centrale (D7, point aveugle) reste une hypothèse de la
consultante, jamais un fait démontré — exactement ce que ce document répète
déjà à plusieurs reprises et qu'il serait incohérent de ne pas appliquer à
son propre résultat.

### D11. Lotissement

**Lot 0 (prérequis de mesure, hors périmètre technique de cette ADR, déjà
spécifié par l'étude — Lot 4)** : `motif_rejet`, jointure des journaux par
slug, états `rdv`/`client`. Recommandé **avant l'exploitation réelle** du
Lot 1+ (voir D10), pas avant sa construction.

**Lot 0bis — calibration graduée de `entretien.fraicheur_mois`** (D4, défaut
séparé) : `_bareme.py`, extension de `website.py`
(`fraicheur_score`), édition de `rubric_persona1.yaml`. Effort faible, risque
réel mais borné : **change un score déjà en production**, à valider par
`agent-revue` avec un test de non-régression explicite sur `signal_chaud`
(même précaution que celle déjà appliquée par l'étude pour ses propres
correctifs de gravité).

**Lot 1 — squelette de l'axe intention, zéro réseau supplémentaire, résultat
observable :**
- `models.py` : `EvenementIntention`, un seul champ nouveau sur `Diagnostic`.
- `diagnostic/intent.py` (nouveau, ~35 lignes, D4) — n'importe QUE
  `_resolve`/`_check_passes`, jamais `ScoringEngine.score()`.
- `collectors/website.py` : + `vocabulaire_intention: list[str] | None = None`
  (constructeur, même motif que `vocabulaire_offre`) ; + 1 champ dérivé
  `offre_detectee: bool | None` et sa date si extractible du texte déjà
  téléchargé (souvent absente en Lot 1 — un événement non daté est alors
  écarté, D2, pas fabriqué comme permanent).
- `config.py` : `load_rubrique_intention(secteur_id) -> dict | None`.
- `pipeline.py`, `vault_runner.py` : câblage (un paramètre optionnel, une
  ligne d'injection — voir Impact sur les contrats).
- `vault_schema.py` : `signal_intention`, `date_intention`,
  `intention_expire_le` (tous optionnels, défaut `None`).
- `serializers.py` : dérivation, contrainte `citable=True` (D6).
- `knowledge/intent_persona1.yaml` + `vocabulaire_intention_persona1.yaml` :
  **donnée, rédigée par la consultante/`agent-produit`, pas par cette ADR**
  (schéma fourni, contenu métier hors périmètre architecture, invariant #4).

**Effort** : moyen. **Risque** : faible — `scoring.py` non touché, aucun
nouveau chemin réseau, tout est un ajout optionnel à défaut neutre.
**Résultat observable, et d'où il vient** : deux prospects de même score de
besoin, l'un affichant un vocabulaire de recrutement sur sa page d'accueil
(déjà téléchargée par `website.py` pour calculer le besoin — **aucun appel
réseau de plus**), l'autre non, ressortent avec des `signal_intention`
différents, visibles en CLI et dans le rapport vault. Le signal vient donc
de la **relecture** d'un texte déjà en mémoire pour une autre raison, pas
d'une nouvelle source.

**Lot 2 — datation réelle + décroissance effective + `legitimite.py` +
verrou historique (posé, pas exploité) :**
- `collectors/_decay.py` si un affichage continu de décroissance est
  souhaité (optionnel — la péremption D2 fonctionne déjà sans lui, par simple
  comparaison de dates).
- `website.py` : escalade conditionnelle — si `offre_detectee` et un lien
  carrières identifié, **un** appel de plus via `api_io.call()` (même
  convention que `_try_sitemap`, déjà présente dans le fichier), avec
  politesse (`robots.txt`, cache par hôte — même rigueur que celle déjà
  identifiée par l'étude pour `contact_site.py`).
- `legitimite.py` (nouveau collecteur, palier 0).
- `VaultIO.append_historique()` + `vault/40-Historique/` (D3) — infrastructure
  posée, aucun collecteur ne l'exploite encore.
- `intent.py` : interpolation `{jours}` réelle dans le gabarit d'accroche.

**Effort** : moyen. **Risque** : faible à moyen — le point d'attention réel
est la politesse du fetch supplémentaire, déjà identifié par l'étude pour un
module voisin.

**Lot 3 — surface et présentation :**
- `export_kemana.yaml` : colonne(s) intention (donnée pure).
- Cockpit : exposition en lecture (`services.py`, types frontend).
- `vault_init.py::_dashboard_md()` : quatrième requête Dataview croisant
  `score_global`/`signal_intention` — la matrice, dans Obsidian, pas dans le
  code.
- `FicheProspect.quadrant` (D5), seuils `[À CALIBRER]`, jamais disqualifiant.

**Effort** : faible. **Risque** : faible — rien ici ne touche le bus, la
machine à états, ou la porte humaine.

**Ce qui n'est un lot d'aucune version de cette ADR** : les collecteurs qui
ont réellement besoin du verrou historique (pixel publicitaire, refonte de
site en cours). Voir §Ce que je refuse de faire maintenant.

### D12. Stratégie de test

1. **Non-régression** : `pytest tests/ -v` intégralement vert après chaque
   lot.
2. **Preuve négative sur `scoring.py`** : `git diff --stat
   diagnostic/scoring.py` vide après le Lot 1 (le Lot 0bis, séparé, le
   modifie légitimement — la preuve porte sur le Lot 1 spécifiquement).
3. **Preuve positive — l'intention discrimine réellement**
   (`test_intention_discrimine_a_besoin_egal`) : deux `Company` dont le HTML
   ne diffère QUE par la présence d'un vocabulaire de recrutement sur la page
   d'accueil (même structure de besoin par ailleurs) → même
   `diag.scores["global"]`, mais `diag.evenements_intention` strictement
   différent (vide d'un côté, un `EvenementIntention` de l'autre).
4. **Péremption** : un événement dont `date_evenement` dépasse `fenetre_jours`
   produit un `expire_le` dans le passé ; un test vérifie que
   `date.today() > expire_le` bascule `intention_niveau` de "fort" à
   "faible" sans qu'aucune fonction de scoring ne soit rappelée — preuve que
   la péremption est une comparaison, pas un recalcul.
5. **Citabilité** : un `EvenementIntention` avec `citable=False` ne peut
   jamais apparaître dans `FicheProspect.signal_intention` — test direct sur
   `serializers.py`.
6. **Typologie** : un check déclaré `nature: etat` dans une rubrique
   d'intention est ignoré par `evaluer_intention()` (jamais transformé en
   événement) — test de garde contre une confusion future.
7. **Trois états préservés** : un site injoignable produit `offre_detectee is
   None` (jamais `False`), et aucun `EvenementIntention` n'est fabriqué à
   partir d'un signal `None` — miroir de
   `test_pipeline_stubs_ne_fabriquent_aucune_faille` existant.
8. **Historique append-only** (D3, dès que construit) : deux appels successifs
   à `VaultIO.append_historique()` produisent deux lignes JSONL distinctes,
   jamais un écrasement — aucun appel à `os.replace()` dans ce chemin (test
   AST, même famille que le test existant sur `vault_io.py`).
9. **Garde-fous bus inchangés** : aucun nouveau module (`intent.py`,
   `_bareme.py`, `legitimite.py`) n'importe `requests`/`anthropic` au niveau
   module — déjà couvert par le test générique `rglob` de
   `tests/test_api_io.py`.
10. **Rétro-compatibilité** : une fiche vault écrite avant cette ADR (sans les
    nouveaux champs) se relit sans erreur de validation Pydantic.

### D13. Ce que je refuse de faire maintenant

- **Je ne construis pas de score composite besoin×intention, ni de tri de
  priorité automatique.** Voir D1/D5 — c'est l'erreur explicitement mise en
  garde par la commanditaire et confirmée par la note de cadrage CMO.
- **Je ne construis pas les collecteurs qui ont réellement besoin du verrou
  historique** (apparition/disparition de pixel publicitaire, refonte de site
  en cours). L'infrastructure (D3) est posée parce qu'elle est structurante ;
  rien ne l'exploite dans ce lot.
- **Je ne câble pas la mesure de conversion** (`motif_rejet`, états
  `rdv`/`client`) — déjà spécifiée par l'étude (Lot 4), hors périmètre direct
  de cette ADR, mais posée comme **gate d'exploitation réelle** (D10), pas
  comme un blocage de la construction du squelette.
- **Je ne construis pas de modèle appris** (machine learning), malgré la
  tentation qu'aurait pu créer un chantier « intent-based » — la littérature
  citée (§Fondement théorique, réserve `[NON LU]`) va dans le sens inverse à
  ce volume de données : un modèle appris serait moins défendable qu'une
  rubrique YAML à poids déclarés.
- **Je n'introduis aucun classificateur d'intention par LLM**, à aucun stade —
  propriété durable de la conception, pas une limitation transitoire.
- **Je ne ressuscite pas** `domaine.py` (RDAP), `archive.py` (Wayback),
  `perf.py` (PageSpeed), `emploi.py` (API externe) ni `registre.py` — tous
  déjà tranchés par l'étude, motifs rappelés en D8.
- **Je n'écris pas le contenu métier** de `knowledge/intent_persona1.yaml` ni
  `vocabulaire_intention_persona1.yaml` — jugement métier, invariant #4.
- **Je ne câble pas le hook GreenIT** (routage de modèle influencé par
  l'intention) — mentionné comme extension possible, non spécifié.
- **Je n'implémente rien.** Ce document est une conception ; le code montré
  est illustratif (signatures, pas des diffs prêts à appliquer).

## Conséquences

**Positives**

- L'intention devient un objet de première classe (`EvenementIntention`),
  daté, périssable, jamais confondu avec le besoin — la matrice Q1-Q4 rend
  Q2 (« budget prouvé, ticket supérieur ») atteignable, ce qu'un score
  composite ou un scoring purement besoin-based ne permettait pas.
- Le Lot 1 ne coûte aucun nouvel appel réseau et capitalise entièrement sur
  ce qui est déjà en mémoire (`website.py`).
- `scoring.py` reste un moteur générique, inchangé, dont la portée ne s'est
  pas élargie pour accueillir une notion de calendrier qu'il n'a pas vocation
  à porter.
- Le verrou historique (D3) est posé avant qu'un collecteur en ait besoin,
  évitant de le découvrir a posteriori sous contrainte (comme le TTL Places
  30 jours l'a déjà été).
- La citabilité (D6) protège structurellement contre le risque réputationnel
  qu'un signal d'intention se lise comme de la surveillance.

**Négatives / risques résiduels**

- **Trois axes à maintenir désormais** (besoin, capacité nommée-non-traitée,
  intention) — davantage de vocabulaire à tenir cohérent dans la
  documentation et la formation de tout futur agent.
- **`EvenementIntention` et `Gap` sont structurellement proches** (dimension,
  intensité/gravité, preuve) sans hériter l'un de l'autre — décision
  délibérée (D1, D4) mais qui laisse deux dataclasses très voisines dans
  `models.py`, à surveiller en revue pour ne pas les faire diverger sans
  raison.
- **Le verrou historique n'est pas exploité par le Lot 1/2** : il représente
  un coût d'implémentation payé par anticipation d'un besoin réel mais non
  encore observé — assumé, parce que le revenir sur ce choix plus tard serait
  plus coûteux (cf. le TTL Places, déjà découvert trop tard une fois).
- **L'hypothèse commerciale centrale (D7) reste non validée** — le pilote
  devra la tester, pas la confirmer par construction.
- **Le Lot 0bis (calibration `fraicheur_mois`) change un score déjà en
  production** — pas un ajout neutre, contrairement au reste de cette ADR ;
  nécessite un test de non-régression explicite sur `signal_chaud`.

## Alternatives écartées

1. **Un score composite besoin×intention (produit ou somme pondérée).**
   Rejeté — D1, mise en garde de la commanditaire confirmée par le CMO.
2. **Un second score /100 pour l'intention, séparé mais de même nature que le
   besoin** (position du premier jet de cette ADR). Rejeté après correction
   du CMO — une date n'est pas une magnitude ; l'objet de sortie doit être
   une liste d'événements, pas un score.
3. **Faire porter la décroissance par `ScoringEngine` lui-même** (nouvel
   opérateur dans `_check_passes`). Rejeté : couplerait le moteur générique à
   une notion de calendrier dont aucune rubrique de besoin n'a besoin.
4. **Faire de `ScoringEngine.score()` un triplet `(scores, gaps,
   evenements)`.** Rejeté : changerait l'arité de retour d'une fonction
   appelée directement par `pipeline.py` et par `test_scoring.py` — risque de
   casse mesurable contre un gain qu'un module séparé (`intent.py`) obtient
   sans aucune casse.
5. **Appliquer une décroissance temporelle aux signaux d'état** (avis,
   immatriculation). Rejeté explicitement (B1) : un fait d'état reste vrai
   tant qu'il l'est, le faire « vieillir » serait une erreur de modélisation,
   pas une nuance.
6. **Une échelle de fiabilité de source à deux axes** (façon Admiralty
   complet, fiabilité × crédibilité). Rejeté (B2) : la littérature rapportée
   montre un effondrement diagonal en pratique — un seul axe déterministe,
   plus `_couverture`, couvre le besoin sans construire une matrice qui ne
   sera jamais utilisée en dehors de sa diagonale.
7. **Historiser dans le frontmatter de `FicheProspect`** (un champ liste
   grandissant, plutôt qu'un fichier séparé). Rejeté : un frontmatter qui
   grandit indéfiniment complique chaque lecture/écriture de la fiche pour un
   usage que seule une minorité de signaux nécessite ; un fichier
   `40-Historique/<slug>.jsonl` séparé, append-only, suit exactement le
   précédent déjà établi par `runs.log`.
8. **Un modèle de machine learning pour prioriser les prospects.** Rejeté
   (§Fondement théorique, réserve `[NON LU]`) : à ce volume (quelques
   dizaines de prospects/mois, quelques conversions/an), aucun ajustement
   crédible n'est possible ; la littérature rapportée soutient au contraire
   le choix déjà fait par ce projet (règles à poids déclarés).
9. **Système de plugins par type de signal.** Rejeté pour la même raison que
   l'alternative équivalente déjà écartée par l'ADR 0003 : sur-ingénierie pour
   une consultante solo, bus factor 1.
10. **Recalcul de la décroissance à la lecture (cockpit/Obsidian).** Non
    retenu comme mécanisme central : la péremption (D2) est déjà résolue par
    une date stockée et une comparaison triviale à la lecture, sans dupliquer
    de logique de scoring — ce qui rend cette alternative largement sans
    objet plutôt que rejetée pour un défaut propre.

## Comment cette ADR sera vérifiée

- `pytest tests/ -v` intégralement vert après chaque lot.
- `git diff diagnostic/scoring.py` vide après le Lot 1 (Lot 0bis excepté,
  vérifié séparément).
- Le test de bout en bout D12.3 : deux prospects de même besoin, intentions
  différentes, `evenements_intention` strictement différent.
- Le test de péremption D12.4 et de citabilité D12.5.
- AST walk existant (`tests/test_api_io.py`, `rglob` sur `diagnostic/**`) :
  toujours vert.
- Une fiche vault antérieure à cette ADR se relit sans erreur.
- Aucun appel à `os.replace()` dans le chemin `append_historique()` (test AST
  dédié, dès que ce chemin existe).
