# ADR 0004 — Axe `intention` (second axe daté et décroissant) + collecteurs OSINT ciblés

- **Statut** : **proposée** — conception uniquement, aucune ligne de code
  livrée par cette ADR. À implémenter par `agent-dev-python`, revue par
  `agent-revue` avant tout commit.
- **Date** : 2026-08-03
- **Remplace** : —
- **Remplacée par** : —
- **Se situe dans** : socle J1 (scoring, modèle de sortie), en capitalisant
  sur l'ADR 0003 (`secteur_id` comme clé de configuration multi-industrie).
  Ne touche pas l'orchestrateur (ADR 0001) ni le routage GreenIT (ADR 0002),
  si ce n'est comme point d'extension optionnel documenté et différé.
  Distincte du chantier « deux axes besoin × capacité » esquissé dans
  `docs/strategie/ETUDE-osint-api-architecture.md` §3.4 (Lot 3) : voir
  §Contexte pour la démarcation exacte entre les deux.

## Contexte

La commanditaire demande deux choses couplées :

1. Rendre le système « intent-based » : à côté du score de **besoin**
   (l'état constaté d'une entreprise), faire apparaître un score d'**intention**
   marketing — un événement daté (ex. recrutement d'un·e chargé·e de
   communication) dont la valeur commerciale décroît avec le temps.
2. Ajouter les modules OSINT nécessaires pour compléter le socle de données
   avant qualification et scoring, en choisissant parmi des candidats déjà
   étudiés (registre légal, WHOIS/RDAP, Wayback Machine, PageSpeed,
   offres d'emploi, certifications métier).

Une étude préexistante (`docs/strategie/ETUDE-osint-api-architecture.md`) a
déjà traité une partie de ce terrain : un schéma OSINT à 9 blocs / ~90 champs
et une feuille de route à ~10 collecteurs ont été **explicitement rejetés**
par la revue d'architecture (taux 55,2 %, aval `false`), et réduits à
**3 blocs et 4 collecteurs** (§0 et §3.3 de cette étude). Cette ADR ne
ressuscite pas ce qui a été rejeté : elle vérifie, module par module, ce qui
reste rejeté, ce qui reste valide, et ce que la demande d'intention change
réellement au calcul.

**Démarcation avec le Lot 3 de l'étude (« deux axes besoin × capacité »).**
L'étude propose déjà un second axe, mais ce n'est **pas** celui que la
commanditaire demande ici. Son axe « capacité » (`reviews.count` comme proxy
de taille, `website.fraicheur_mois`, `reviews.repond_aux_avis`, qualité de
l'email) est une **posture** — un ensemble de proxies globalement stables sur
plusieurs mois, sans notion d'événement daté qui expire. L'axe « intention »
demandé ici est un **événement** : il apparaît à une date précise et perd sa
valeur commerciale avec le temps, ce qui n'est vrai d'aucun signal du Lot 3.
**Ce sont deux axes distincts**, et cette ADR recommande explicitly de ne
**pas** les fusionner dans un même champ `score_secondaire` : la commanditaire
elle-même met en garde contre la fusion de deux jugements hétérogènes dans un
seul score (c'est exactement l'erreur que l'étude dénonce pour besoin/capacité
— cf. §3.4 : « 40-70 = investit déjà mais mal » n'a de sens que si les deux
axes restent lisibles séparément). `score_capacite` (Lot 3 de l'étude, seuils
`[À CALIBRER]`, non implémenté) et `score_intention` (cette ADR) sont deux
extensions indépendantes de `Diagnostic`, qui pourront coexister sans jamais
se réduire l'une à l'autre.

## 1. Verdict sur l'hypothèse deux-axes

**L'hypothèse est retenue.** Besoin et intention ne sont pas interchangeables,
et les fusionner dégraderait la qualification, pour trois raisons vérifiables
dans le système actuel, pas seulement par argument théorique :

1. **Non-monotonie confirmée par construction du moteur actuel.** Le score de
   besoin est déjà pensé comme l'inverse d'une note de satisfaction
   (`knowledge/rubric_persona1.yaml:11-15` : « Un score BAS = un prospect
   CHAUD »). Ajouter un signal d'intention qui est, lui, positif par nature
   (sa présence est bonne) dans le **même** total reviendrait à additionner
   deux grandeurs dont le sens de variation par rapport à « bon prospect »
   n'est pas le même pour les deux axes au même moment : un besoin bas (site
   nickel) qui recrute un·e chargé·e de communication n'a pas le même sens
   commercial qu'un besoin haut (site à refaire) qui recrute la même
   personne. Un score composite écraserait cette différence en un seul
   nombre — exactement le défaut que la commanditaire anticipe.
2. **La classe de défaut est déjà connue et déjà corrigée une fois dans ce
   projet**, pour une raison structurellement identique. `scoring.py` (lignes
   11-36) documente comment fusionner « non observé » et « échec » a produit
   des scores fabriqués et des accroches fausses. Fusionner « pas de besoin
   pressant » et « pas d'intention détectée » dans un seul nombre reproduirait
   la même perte d'information pour une raison symétrique : deux états
   distincts (l'un temporel, l'un structurel) rendus indiscernables dans un
   seul chiffre.
3. **Le calendrier n'a pas de place dans le moteur actuel.** Aucun champ de
   `rubric_persona1.yaml` ni aucun test de `scoring.py` ne traite une notion de
   date ou de décroissance (vérifié par lecture complète des deux fichiers).
   Introduire un signal qui doit expirer dans le même total qu'un signal qui
   ne bouge qu'à la marge (un site refait ne change pas de nature tous les
   mois) créerait une alchimie de deux échelles de temps dans le même
   dénominateur — un artefact statistique, pas une mesure.

**Nuance à ne pas perdre** : séparer les axes n'implique pas de calculer une
« priorité » algorithmique à partir des deux. Cette ADR expose délibérément
**deux valeurs lisibles séparément** (`score_global`, `score_intention`) et,
au mieux, une **étiquette de cadran informative** (§Modèle), jamais un rang
de priorité imposé — cohérent avec l'invariant « l'orchestrateur ordonnance,
il ne décide rien », étendu par analogie au moteur de scoring : **le système
signale, il ne priorise pas à la place de l'opératrice.**

## 2. Le modèle d'intention

### Structure de données

Nouveau dataclass dans `diagnostic/models.py`, symétrique de `Gap` mais de
polarité opposée (positive, pas un problème) :

```python
@dataclass
class SignalIntention:
    """Un signal d'intention observé : la matière première d'une accroche
    orientée opportunité, pas orientée manque."""
    dimension: str
    intensite: str          # "haute" | "moyenne" | "basse" — jugement commercial,
                             # même vocabulaire que Gap.gravite mais nom distinct :
                             # l'intensité d'une opportunité n'est pas la gravité
                             # d'un problème.
    preuve: str              # phrase factuelle, DATE DÉJÀ INTERPOLÉE
    date_signal: date | None  # date de l'événement source (None si non datable)
```

`Diagnostic` gagne deux champs, en fin de dataclass, tous deux avec valeur par
défaut — ajout strictement additif, aucun champ existant retouché :

```python
scores_intention: dict[str, float | None] = field(default_factory=dict)
signaux_intention: list[SignalIntention] = field(default_factory=list)
```

Vérifié par lecture de `tests/test_j1_smoke.py` : aucune assertion n'exige une
égalité stricte sur `Diagnostic.to_dict()` ou ses clés — seulement des accès
ponctuels (`diag.scores["global"]`, `diag.meta["collecteurs"]`, etc.). L'ajout
ne casse aucune des six assertions de ce fichier.

### Où vit la datation

**Au niveau du collecteur, jamais du moteur.** Un collecteur est la seule
brique du système qui *observe* un fait ; la date d'un événement (une offre
d'emploi publiée, une page carrière modifiée) est elle-même un fait, au même
titre que le fait qu'il existe. `website.py` fait déjà cela pour un autre
signal : `derniere_maj` (ligne 90 de `collectors/website.py`) est calculé au
moment de la collecte, à partir de dates trouvées dans la page — c'est le
précédent direct, pas une invention de cette ADR.

### Comment la décroissance est paramétrée (donnée, pas code)

Nuance tranchée par lecture du code, pas supposée : **la décroissance n'est
ni dans le collecteur en dur, ni dans `scoring.py`.** Elle vit dans une
fonction utilitaire pure et partagée, **paramétrée par un YAML propre au
secteur**, injectée dans le collecteur exactement comme `vocabulaire_offre`
l'est déjà (`WebsiteCollector.__init__`, ADR 0003) :

```python
# diagnostic/collectors/_decay.py — nouveau, sur le modèle de _places.py
# (une fonction pure, aucun état, aucun réseau, aucune classe Collector).
def decroissance(date_evenement: date, config: dict, aujourdhui: date | None = None) -> float:
    """Retourne un facteur dans [plancher, 1.0], décroissant avec l'âge de
    l'événement. `config` = {"demi_vie_jours": int, "plancher": float}."""
```

`config` est lu depuis un nouveau bloc `decroissance:` dans
`knowledge/intent_{secteur_id}.yaml` (un fichier par secteur, exactement le
même schéma de nommage que `rubric_{secteur_id}.yaml` et
`vocabulaire_{secteur_id}.yaml`), chargé UNE FOIS par `vault_runner.py` (ou
`config.py`), puis **injecté** dans le collecteur — jamais lu par le
collecteur lui-même depuis le disque, jamais lu par `scoring.py`. Changer la
demi-vie d'un secteur à l'autre (un recrutement compte 45 jours en HVAC,
peut-être 90 jours ailleurs) = éditer ce YAML, zéro ligne de code.

Le collecteur produit alors deux signaux dans son dict de sortie, pas un
seul : la **valeur brute datée** (`recrutement.date_offre: date | None`,
utilisée pour écrire l'accroche) et la **valeur décroissante** utilisée pour
le scoring (`recrutement.intensite_decroissante: float | None`, dans
`[0, 1]`). Ce sont deux signaux distincts pour une seule et même raison :
le score doit décroître, l'accroche doit rester factuelle (« offre publiée
il y a 12 jours » ne devient pas fausse avec le temps — c'est la PONDÉRATION
qui doit baisser, pas le fait qui doit se déformer).

### Comment un signal d'intention devient une accroche

Symétrique et tout aussi déterministe que la dérivation actuelle de
`signal_chaud` (`serializers.py:30-36`, qui prend `hautes[0].preuve` sans
aucun LLM). Le gabarit de phrase vit dans la rubrique d'intention
(`opportunite: "Recrute un poste marketing/communication (offre du {jours} j)"`),
et l'interpolation (`.format()`, une ligne, zéro LLM) se fait dans le petit
module qui rejoue les checks (voir §3). Le texte produit ne remonte JAMAIS au
LLM : c'est une chaîne factuelle assemblée à partir de champs déjà connus, au
même régime que `signal_chaud` aujourd'hui — l'invariant « le LLM ne collecte
jamais » est donc tenu de la même manière qu'il l'est déjà pour le besoin, et
**il n'y a jamais de classificateur d'intention par LLM à aucun stade** : la
détection est un `is_true`/`gte` déterministe sur un fait déjà extrait par
regex/lien HTML.

## 3. Réutilisation ou non du `ScoringEngine` — démontré, pas supposé

Vérification faite en lisant `diagnostic/scoring.py` en entier (187 lignes).

**Ce qui se réutilise à l'identique, zéro ligne changée dans `scoring.py` :**
la classe `ScoringEngine`, sa méthode `score()`, la renormalisation sur les
dimensions observées, `_couverture`, et les deux fonctions utilitaires pures
`_resolve` et `_check_passes`. Une rubrique d'intention
(`knowledge/intent_persona1.yaml`, même schéma `dimensions/poids/checks/points`
que `rubric_persona1.yaml`) produit un score numérique par dimension et un
score global **par un appel `ScoringEngine(rubrique_intention).score(signaux)`
strictement identique à celui déjà fait pour le besoin.** C'est la partie
vraie de l'hypothèse, et elle est vraie sans réserve.

**Ce qui ne se réutilise PAS tel quel — trois frictions vérifiées par lecture,
pas supposées :**

1. **Le calendrier.** `_check_passes` (ligne 67) n'a aucune notion de date :
   il compare une valeur à un opérateur, point. La friction est résolue en
   amont du moteur, pas dedans (§2) : le signal fourni au moteur est déjà une
   valeur décroissante dans `[0, 1]`, comparée avec l'opérateur `gte` qui
   **existe déjà** (ligne 78-79) et qui accepte n'importe quel flottant sans
   modification. **Conclusion vérifiée : zéro nouvel opérateur nécessaire.**
2. **Le vocabulaire `gap`/`faille` est bien inversé, et c'est le point réel
   de friction.** `ScoringEngine.score()` (lignes 132-155) ne produit un objet
   que dans la branche `else` (`resultat` faux) — un `Gap`. Dans la branche
   `if resultat:` (ligne 140), rien n'est capturé au-delà du score : **le
   moteur jette aujourd'hui l'information « ce check est passé », qui est
   précisément celle dont l'intention a besoin.** Le vocabulaire `gap`/`gravite`
   n'a donc, littéralement, aucun sens pour l'intention : il faudrait afficher
   « Absence de recrutement marketing détecté » avec une `gravite`, ce qui est
   un non-sens commercial (l'absence d'intention n'est pas une faute du
   prospect) — cette friction est réelle, pas cosmétique.
3. **Le contrat `Diagnostic`/`serializers.py`/`export.py`/cockpit/575 tests.**
   Traité au §5 : tenable sans casse, par ajout strict.

**Décision : ne pas modifier `ScoringEngine`, écrire un petit module
supplémentaire qui l'enveloppe.** `diagnostic/intent.py` (nouveau, ~30 lignes) :

```python
from datetime import date
from diagnostic.models import SignalIntention
from diagnostic.scoring import ScoringEngine, GRAVITES, _resolve, _check_passes

def score_intent(
    rubrique_intention: dict, signaux: dict
) -> tuple[dict[str, float | None], list[SignalIntention]]:
    scores, _ = ScoringEngine(rubrique_intention).score(signaux)  # inchangé, réutilisé tel quel
    signaux_forts: list[SignalIntention] = []
    for dim_name, dim in rubrique_intention["dimensions"].items():
        for c in dim["checks"]:
            value = _resolve(signaux, c["signal"])
            resultat = _check_passes(value, c["op"], c.get("value"))
            if resultat is not True:
                continue  # False ou None : pas d'opportunité à afficher, jamais de "gap inversé"
            date_signal = _resolve(signaux, c["date_signal"]) if "date_signal" in c else None
            jours = (date.today() - date_signal).days if date_signal else None
            preuve = c["opportunite"].format(jours=jours) if jours is not None else c["opportunite"]
            signaux_forts.append(SignalIntention(
                dimension=dim_name, intensite=c.get("intensite", "moyenne"),
                preuve=preuve, date_signal=date_signal,
            ))
    signaux_forts.sort(key=lambda s: s.date_signal or date.min, reverse=True)
    return scores, signaux_forts
```

**`scoring.py` n'est pas modifié : zéro ligne.** `_resolve`/`_check_passes`
sont déjà des fonctions pures sans effet de bord, importées telles quelles
dans le même package — pas une nouvelle API publique, pas une nouvelle
dépendance. C'est une preuve exécutable, pas une promesse : `agent-revue` peut
vérifier par `git diff diagnostic/scoring.py` qu'il est vide après
implémentation.

## 4. Les collecteurs OSINT retenus (2, pas dix)

Rappel des décisions déjà actées dans `ETUDE-osint-api-architecture.md`
(§0, §3.3, §3.6) que cette ADR **ne rouvre pas** : `domaine.py` (RDAP/DNS/MX)
**supprimé du plan** ; `archive.py` (Wayback), `perf.py` (PageSpeed),
`emploi.py` (France Travail / Guichet-Emplois), `stack.py` payant
**écartés** (« quotas non sourcés, dépendances instables, rendement
marginal ») ; `registre.py` (REQ/Zefix/Sirene) **reporté hors périmètre 6
mois** (« effort élevé, point dur non résolu — rapprochement d'entités sans
faux positif »). Ces motifs restent valables ici : aucun ne devient plus
solide parce que la finalité est l'intention plutôt que le besoin. Ils sont
donc **maintenus rejetés**, pas ressuscités par cette porte.

### Retenu 1 — Extension de `website.py` : signal de recrutement marketing

| | |
|---|---|
| Palier | 0 (dérivé) en Lot 1, 0+1 en Lot 2 |
| Source | HTML déjà téléchargé (Lot 1) ; une page carrières du même domaine, un seul appel de plus, via le bus (Lot 2) |
| Apporte à | **Intention** (nouvelle dimension `recrutement_marketing` dans `intent_{secteur}.yaml`) |
| Mode dégradé | `None` si site injoignable ou vocabulaire non configuré pour le secteur (même discipline que `mentions_offre`, ADR 0003 anti-fuite B5) |
| Coût | 0 (Lot 1, zéro appel réseau supplémentaire) ; marginal (Lot 2, 1 appel/cible, mis en cache) |
| Conformité | Zéro donnée personnelle. Le signal est une caractéristique de poste (« un poste de marketing est ouvert »), jamais un nom, jamais un contact — même régime que `mentions_offre`. |

**Pourquoi lui plutôt qu'un `emploi.py` externe (rejeté) :** le candidat de la
commanditaire (« offres d'emploi ») est le signal d'intention le plus
directement pertinent — mais sa version « API externe » (France Travail /
Guichet-Emplois) a déjà été écartée pour asymétrie de couverture entre
marchés (excellente en France, quasi nulle en Suisse — `ETUDE §…` ligne 1694)
et dépendance à un fournisseur non maîtrisé. La version retenue ici lit le
site du **prospect lui-même** : symétrique sur les trois marchés (Québec,
Romandie, France), zéro nouvelle dépendance externe, zéro nouveau point du
bus au-delà de ce que `website.py` fait déjà. C'est un signal plus étroit
(seulement les postes que le prospect affiche lui-même) mais strictement
dans le périmètre déjà approuvé (extension de `website.py`, précédent direct
avec l'extension « joignabilité » déjà retenue par l'étude, §3.3).

### Retenu 2 — `legitimite.py` (nouveau module, palier 0)

| | |
|---|---|
| Palier | 0 |
| Source | HTML déjà en mémoire (regex : licence RBQ, mention RGE, suissetec, programme de subvention en vigueur) |
| Apporte à | **Besoin** (nouvelle dimension `legitimite_conformite`) — complète le socle avant scoring, comme demandé |
| Mode dégradé | `None` par check si le motif n'est pas configuré pour le secteur/marché (motifs dans `knowledge/certifications_{marche}.yaml`, donnée, pas code) |
| Coût | 0 |
| Conformité | Donnée publiée par l'entreprise sur elle-même (comme un badge), zéro donnée personnelle |

**Pourquoi lui** : déjà entièrement vetté par l'étude (§3.3, statut
« AJOUTER »), zéro nouveau risque d'invariant, répond directement au candidat
« certifications métier », et sert explicitement le besoin demandé par la
commanditaire de « parfaire le socle avant qualification et scoring » — sans
lui, une dimension de jugement métier réelle (licence professionnelle) reste
absente alors que le HTML qui la contient est déjà en mémoire.

### Exclus explicitement, et pourquoi (pas un report silencieux)

| Candidat | Décision | Motif |
|---|---|---|
| Registre légal (REQ/Zefix/Sirene) | **Exclu, aligné sur l'étude** | Reporté hors périmètre 6 mois par l'étude (rapprochement d'entités sans faux positif = point dur non résolu). Aurait pu nourrir « ancienneté d'entreprise » pour les deux axes, mais l'effort ne se justifie pas avant un run réel. |
| WHOIS/RDAP | **Exclu, aligné sur l'étude** (`domaine.py` supprimé du plan) | Signal statique (âge du domaine), n'est ni un événement daté au sens de l'intention, ni un signal manquant pour le besoin (déjà `derniere_maj`/`fraicheur_mois` via `website.py`, gratuit, sans dépendance externe). |
| Wayback Machine (fraîcheur réelle) | **Exclu, aligné sur l'étude** (`archive.py` écarté : « quotas non sourcés, rendement marginal ») | La fraîcheur DÉJÀ collectée (`derniere_maj` depuis Last-Modified/sitemap/copyright) est un proxy suffisant pour ce qu'elle sert (le besoin). Une meilleure précision de date n'aide pas l'intention : Wayback daterait une refonte de site (un événement lui aussi potentiellement pertinent pour l'intention), mais introduire une dépendance externe à quota non documenté pour un signal que l'étude a déjà jugé marginal n'est pas justifié tant qu'aucun pilote n'a mesuré le manque. |
| PageSpeed/Lighthouse | **Exclu, aligné sur l'étude** (`perf.py` écarté) | Signal de qualité technique, pas d'intention marketing ; l'étude l'a déjà classé rendement marginal pour le besoin. |
| Offres d'emploi (version API externe) | **Exclu** | Voir « Retenu 1 » : remplacé par une version dérivée du site du prospect, sans dépendance externe, symétrique par marché. |

## 5. Impact sur les contrats existants

| Contrat | Impact |
|---|---|
| `diagnostic/models.py::Diagnostic` | **Étendu** : + `SignalIntention` (nouveau dataclass), + 2 champs optionnels en fin de dataclass (`scores_intention`, `signaux_intention`). Aucun champ existant modifié. |
| `diagnostic/scoring.py` | **Non modifié.** Voir §3 — preuve par `git diff` vide attendue. |
| `diagnostic/pipeline.py` | **Étendu** : `DiagnosticPipeline.__init__` gagne un paramètre optionnel `rubrique_intention: dict \| None = None` (défaut `None` = comportement actuel inchangé à l'identique). `run()` gagne une branche conditionnelle de 4 lignes après le scoring de besoin. |
| `diagnostic/vault_schema.py::FicheProspect` | **Étendu**, deux nouveaux champs optionnels par défaut `None` : `score_intention: int \| None`, `signal_intention: str \| None` (Lot 1) ; `date_intention: date \| None` (Lot 2). Même régime que les champs J4/J5 déjà ajoutés (ADR 0003, `opt_out`, `signal_chaud`…) — fiches antérieures relues sans migration, `extra="allow"` inchangé. |
| `diagnostic/serializers.py` | **Étendu**, pas remplacé : `diagnostic_to_fiche` dérive `score_intention`/`signal_intention` depuis `diag.scores_intention`/`diag.signaux_intention`, au même endroit et selon le même principe que la dérivation actuelle de `signal_chaud`. `diagnostic_to_rapport_md` gagne une section optionnelle « Signaux d'intention », rendue seulement si `diag.signaux_intention` est non vide — **à vérifier contre `tests/test_serializers.py` avant merge : aucune assertion actuelle du dépôt ne fait d'égalité stricte sur le markdown complet (les dates/scores dynamiques l'interdiraient déjà), mais c'est une hypothèse à confirmer par exécution, pas à affirmer.** |
| `diagnostic/config.py` | **Étendu** : nouvelle fonction `load_rubrique_intention(secteur_id) -> dict \| None` (retourne `None`, pas `{}`, si le fichier `intent_{secteur_id}.yaml` est absent — distinction nécessaire entre « pas d'axe intention pour ce secteur » et « axe vide »). |
| `diagnostic/vault_runner.py::make_pipeline_for_secteur` | **Une ligne ajoutée** : `rubrique_intention=load_rubrique_intention(secteur_id)` passé au constructeur du pipeline. C'est le point d'intégration qui capitalise sur le mécanisme ADR 0003 déjà en place (résolution par fiche, pas par run) — zéro nouveau mécanisme de résolution de secteur. |
| `knowledge/export_kemana.yaml` | **Non modifié par cette ADR** — extension possible ultérieurement (colonne « Signal intention »), pure édition YAML, décision de contenu laissée à la consultante/`agent-produit` (le champ existera sur `FicheProspect`, donc `charger_schema_kemana` l'acceptera dès qu'il sera ajouté). |
| Cockpit (`webapp/backend/services.py`, frontend) | **Extension additive, hors scope de cette ADR** : `_fiche_to_list_item` pourrait exposer `score_intention`/`signal_intention` en lecture (GET seul, zéro écriture, zéro appel réseau, zéro transition — aucun invariant du cockpit n'est en jeu). Laissé à `agent-frontend`/`agent-dev-python` en Lot 3. |
| Suite de tests (575) | **Aucune régression attendue par construction** : tout ajout est un champ optionnel à défaut `None`/`[]`/`{}`, sur des contrats déjà conçus pour l'extension (ADR 0003 l'a déjà fait quatre fois : `secteur_id`, `contact_*`, `opt_out`, `signal_chaud`/`accroche`). À vérifier par exécution complète après implémentation, pas supposé. |

## 6. Lotissement

### Lot 1 — Intention minimale, sans réseau supplémentaire, résultat observable

- `models.py` : `SignalIntention`, 2 champs `Diagnostic`.
- `diagnostic/intent.py` (nouveau, ~30 lignes, décrit au §3).
- `collectors/website.py` : + `vocabulaire_intention: list[str] | None = None` (constructeur, même
  motif que `vocabulaire_offre`) ; + 1 champ dérivé `marketing_job_signal: bool | None` (scan lexical du
  texte déjà téléchargé — zéro fetch de plus). Pas de date en Lot 1 : le check
  d'intention est binaire (présent/absent), pas encore décroissant.
- `config.py` : `load_rubrique_intention`.
- `pipeline.py`, `vault_runner.py` : câblage (voir §5).
- `vault_schema.py` : `score_intention`, `signal_intention`.
- `serializers.py` : dérivation.
- `knowledge/intent_persona1.yaml` + `knowledge/vocabulaire_intention_persona1.yaml` : **donnée,
  rédigée par la consultante ou `agent-produit`, pas par cette ADR** (schéma
  fourni, contenu métier hors périmètre architecture — invariant #4).

**Effort** : moyen (un module de scoring en plus, câblage à 6 points
d'intégration déjà existants, aucun nouveau point de réseau). **Risque** :
faible — aucun changement à `scoring.py`, aucun nouveau chemin réseau, tout
est un ajout optionnel à défaut neutre. **Résultat observable** : deux
prospects de même score de besoin, l'un affichant un vocabulaire de
recrutement marketing sur sa page d'accueil, l'autre non, ressortent avec un
`score_intention` différent — visible en CLI (`run_diagnostic.py --json`) et
dans le rapport vault, sans qu'aucune touche de code métier n'ait bougé pour
un troisième secteur.

### Lot 2 — Datation réelle + décroissance + `legitimite.py`

- `collectors/_decay.py` (fonction pure `decroissance()`).
- `website.py` : escalade conditionnelle — si `marketing_job_signal` est vrai
  ET qu'un lien carrières a été détecté sur la page d'accueil, **un** appel de
  plus via `api_io.call()` (même convention que `_try_sitemap`, déjà présente
  dans le fichier) vers la page carrières, pour en extraire une date
  d'offre réelle.
- `legitimite.py` (nouveau collecteur, palier 0).
- `intent_{secteur}.yaml` : bloc `decroissance:` par secteur.
- `vault_schema.py` : `date_intention`.
- `intent.py` : interpolation `{jours}` dans le gabarit d'accroche.

**Effort** : moyen (un nouveau collecteur simple + une escalade réseau
disciplinée dans un fichier déjà familier). **Risque** : faible à moyen — le
point d'attention réel est la politesse (robots.txt, cache par hôte) sur le
fetch supplémentaire, déjà un chantier identifié par l'étude pour
`contact_site.py` ; à traiter avec la même rigueur ici plutôt que la
contourner.

### Lot 3 — Surface et présentation

- `export_kemana.yaml` : colonne(s) intention (donnée pure).
- Cockpit : exposition en lecture (`services.py`, types frontend).
- `vault_init.py::_dashboard_md()` : quatrième requête Dataview — une table
  croisant `score_global` et `signal_intention` (la « matrice » demandée),
  **dans Obsidian, pas dans le code** : c'est une chaîne de requête DQL
  ajoutée au générateur de tableau de bord, aucune nouvelle logique métier
  dans le système lui-même. Optionnellement, un champ dérivé
  `quadrant: str | None` sur `FicheProspect` (ex. `"chaud_intentionnel"`,
  `"chaud_dormant"`, `"froid_actif"`), calculé dans `serializers.py` à partir
  de seuils **marqués `[À CALIBRER]`, en donnée**, jamais utilisé pour trier
  ou disqualifier automatiquement — strictement informationnel, sur le
  modèle de prudence déjà posé par l'étude pour son propre Lot 3.

**Effort** : faible (édition YAML + extensions additives de surface).
**Risque** : faible — rien ici ne touche le bus, la machine à états, ou la
porte humaine.

### Ce qui n'est PAS un lot de cette ADR

Le hook GreenIT (router le modèle de synthèse en fonction de la présence d'un
signal d'intention) est mentionné comme extension naturelle possible, mais
**explicitement différé** (voir §8) : rien n'exige de le faire maintenant, et
il resterait de toute façon un routage YAML déterministe, jamais un
classificateur LLM.

## 7. Stratégie de test

1. **Non-régression** : `pytest tests/ -v` intégralement vert après chaque
   lot — condition d'acceptation dure, pas une aspiration.
2. **Preuve négative sur `scoring.py`** : `git diff --stat diagnostic/scoring.py`
   vide après le Lot 1. Si ce n'est pas le cas, l'implémentation a dévié de
   cette ADR et doit être justifiée par une ADR de remplacement, pas
   silencieusement.
3. **Preuve positive — l'intention discrimine réellement** (test à écrire,
   nom suggéré `test_intention_discrimine_a_besoin_egal`) : deux `Company`
   dont le HTML ne diffère QUE par la présence d'un vocabulaire de
   recrutement marketing sur la page d'accueil (même structure par ailleurs :
   même titre, mêmes signaux de besoin) → même `diag.scores["global"]`, mais
   `diag.scores_intention["global"]` et `diag.signaux_intention` diffèrent
   strictement entre les deux. Sans cette preuve, l'ADR n'a rien démontré de
   plus qu'un champ supplémentaire inerte.
4. **Décroissance (Lot 2)** : `decroissance(date_evenement, config)` testée
   en isolation — valeur ≈ 1.0 à J+0, ≈ 0.5 à la demi-vie déclarée, tend vers
   le plancher configuré au-delà, strictement décroissante, fonction pure
   (deux appels identiques → même résultat, aucune dépendance cachée à
   l'horloge système au-delà du paramètre explicite `aujourdhui`).
5. **Trois états préservés** : un test qui vérifie qu'un site injoignable
   produit `marketing_job_signal is None` (jamais `False`) et qu'aucun
   `SignalIntention` n'est fabriqué à partir d'un signal `None` — même
   discipline que `test_pipeline_stubs_ne_fabriquent_aucune_faille` existant,
   son miroir côté intention.
6. **Garde-fous bus inchangés** : aucun nouveau module (`intent.py`,
   `_decay.py`, `legitimite.py`) n'importe `requests`/`anthropic` au niveau
   module — déjà couvert par le test générique `rglob` de
   `tests/test_api_io.py` (pas besoin de toucher la liste explicite de
   `preflight.py`, bien que l'ajouter y reste recommandé pour la cohérence
   documentaire, dette déjà notée dans `CLAUDE.md`).
7. **Rétro-compatibilité** : une fiche vault écrite AVANT cette ADR (sans
   `score_intention`) se relit sans erreur de validation Pydantic — test
   direct sur un frontmatter fixe ne portant pas ces clés.

## 8. Ce que je refuse de faire maintenant

- **Je n'écris pas le contenu de `knowledge/intent_persona1.yaml` ni
  `vocabulaire_intention_persona1.yaml`.** C'est un jugement métier
  (quels intitulés de poste comptent, quelle demi-vie retenir), invariant #4 :
  donnée écrite par la consultante ou `agent-produit`, pas par l'architecte.
- **Je ne construis pas de score composite besoin×intention ni de tri de
  priorité automatique.** Voir §1 : c'est exactement l'erreur que l'hypothèse
  de la commanditaire met en garde contre, et l'étude a déjà posé la même
  prudence pour son propre second axe (Lot 3, seuils `[À CALIBRER]`,
  disqualification automatique explicitement annulée).
- **Je ne ressuscite pas `domaine.py` (RDAP), `archive.py` (Wayback),
  `perf.py` (PageSpeed), `emploi.py` (API externe) ni `registre.py`** — tous
  déjà tranchés par l'étude, motifs rappelés au §4, aucun argument nouveau ne
  les renverse ici.
- **Je n'introduis aucun classificateur d'intention par LLM**, à aucun stade,
  y compris pour la phrase d'accroche (interpolation déterministe, §2) — pas
  seulement « pour l'instant » : c'est une propriété durable de la conception,
  pas une limitation transitoire.
- **Je ne câble pas le hook GreenIT** (routage de modèle influencé par
  l'intention). Mentionné comme extension possible, non spécifié, non
  planifié dans un lot : ajouter une variable de routage sans usage réel
  serait de la complexité anticipée non payée par un besoin observé.
- **Je n'implémente rien.** Ce document est une conception ; le code
  ci-dessus est illustratif (signatures, pas des diffs prêts à appliquer) et
  sera vérifié puis ajusté par `agent-dev-python`/`agent-revue` en
  implémentation.

## Alternatives écartées

1. **Un seul score composite (besoin pondéré + bonus d'intention).** Rejeté :
   c'est précisément l'hypothèse que la commanditaire demandait de challenger,
   et le §1 en donne trois raisons vérifiées, pas une préférence de style.
2. **Faire porter la décroissance par `ScoringEngine` lui-même (nouvel
   opérateur `decays_since` dans `_check_passes`).** Rejeté : couplerait le
   moteur générique à une notion de calendrier dont aucune rubrique de besoin
   n'a besoin, et romprait la promesse « le moteur ne sait rien du secteur ni
   du temps » pour un seul axe. La solution retenue (décroissance pré-calculée
   par le collecteur, moteur inchangé) obtient le même résultat sans élargir
   la surface du moteur générique.
3. **Faire de `ScoringEngine.score()` un triplet `(scores, gaps, opportunites)`.**
   Rejeté : change l'arité de retour d'une fonction appelée directement par
   `pipeline.py` et probablement par plusieurs tests de `test_scoring.py` —
   un risque de casse mesurable contre un gain qu'un module séparé
   (`intent.py`) obtient sans aucune casse.
4. **Système de plugins par type de signal (registre de « détecteurs
   d'intention » découverts dynamiquement).** Rejeté pour la même raison que
   l'alternative équivalente déjà écartée par l'ADR 0003 : sur-ingénierie pour
   une consultante solo, bus factor 1 ; le mécanisme YAML + injection existant
   couvre le besoin.
5. **Recalcul de la décroissance à la lecture (cockpit/Obsidian), plutôt
   qu'au diagnostic.** Rejeté pour ce lot : dupliquerait la logique de score
   dans une seconde couche (webapp), exactement la dette déjà identifiée pour
   le coût GreenIT (`usage.py` vs `webapp/backend/greenit.py`). Limitation
   assumée et documentée : le score d'intention est un instantané figé à la
   date du diagnostic, pas une valeur qui continue de décroître pendant
   qu'une fiche attend en `valide`. Recalculer à la lecture reste une option
   pour un lot ultérieur si le délai de validation humaine s'avère long en
   pratique (métrique déjà identifiée par l'étude, §3.5 Lot 4) — pas construit
   par anticipation.

## Comment cette ADR sera vérifiée

- `pytest tests/ -v` intégralement vert après chaque lot.
- `git diff diagnostic/scoring.py` vide après le Lot 1 (preuve exécutable de
  la non-modification du moteur).
- Nouveau test de bout en bout (§7.3) : deux prospects de même besoin,
  intentions différentes, `scores_intention` et `signaux_intention`
  strictement différents.
- AST walk existant (`tests/test_api_io.py`, `rglob` sur `diagnostic/**`) :
  toujours vert, aucun nouveau module n'introduit d'import réseau de niveau
  module.
- Une fiche vault antérieure à cette ADR (sans les nouveaux champs) se relit
  sans erreur — test explicite de rétro-compatibilité.
