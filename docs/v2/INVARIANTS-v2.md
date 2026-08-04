# Invariants v2 — verdict sur les 24 invariants v1, et les invariants nouveaux

> Compagnon de `docs/v2/ARCHITECTURE-CIBLE.md`, qui argumente les choix ;
> ce document en tire le **verdict exécutable**. Statut : proposition, non
> actée. Les 24 invariants de référence sont ceux de
> `docs/architecture/invariants.md` (I1-I24) ; le coût d'apprentissage de
> chacun est détaillé dans `docs/v2/HERITAGE-v1-invariants-a-challenger.md`,
> non répété ici sauf nécessité.
>
> **Un invariant sans mécanisme de vérification exécutable n'est pas un
> invariant, c'est un vœu** — règle héritée de la v1
> (`docs/architecture/invariants.md`, ligne 3) et **durcie** ici : le
> mécanisme doit être un **balayage** (parcours exhaustif du code source ou
> des données), jamais une liste de fichiers tenue à la main. C'est la leçon
> de méthode n°5 de `HERITAGE-v1-…` (cinq modules absents d'une liste
> nominative de garde-fou), traitée comme une règle de conception à part
> entière, appliquée systématiquement ci-dessous.

---

## 0. Méta-invariant — comment on vérifie un invariant en v2

**Doctrine.** Deux sortes de listes existent dans un garde-fou par balayage :

- la liste de **ce qui est interdit** (primitives, imports, symboles) — courte,
  stable, change rarement (ex. : `os.replace`, `import requests`,
  `import anthropic`, un identifiant de fournisseur dans une Grille) ;
- la liste de **ce qui doit être vérifié** (modules, fichiers, nœuds) —
  longue, grossit à chaque ajout, se désynchronise silencieusement.

**Règle.** Un invariant v2 ne maintient **jamais** la seconde liste. Il
parcourt **tout** l'arbre pertinent (`rglob`, AST walk, validation de schéma
appliquée à 100 % des enregistrements) et applique la première liste,
stable, à chaque élément trouvé. Une liste nominative peut subsister comme
**documentation** (elle aide à comprendre où regarder), mais **le test qui
fait foi est toujours le balayage générique**, jamais la liste — exactement
le renversement de priorité que la v1 a dû faire a posteriori pour I4
(`test_requests_pas_importe_niveau_module_hors_api_io`, filet générique qui a
sauvé l'invariant que la liste nominative avait laissé passer).

**Vérification de ce méta-invariant lui-même.** Chaque ligne des tables
ci-dessous porte une colonne « Mécanisme de vérification (balayage) ». Une
ligne dont le mécanisme décrit une liste à maintenir manuellement est, par
construction, non conforme à ce document — c'est un test de cohérence
applicable au document lui-même, pas seulement au code qu'il décrit.

---

## 1. Les 24 invariants v1 — verdict conservé / transformé / abandonné

| # | Invariant v1 (résumé) | Verdict | Motif (une ligne) |
|---|---|---|---|
| I1 | Un seul écrivain du vault (`os.replace()` exclusif à `vault_io.py`) | **TRANSFORMÉ** | Le magasin n'est plus garanti fichiers-plats en multi-tenant ; le principe devient « un seul module (`MagasinIO`) touche le pilote de stockage sous-jacent, quel qu'il soit », vérifié par balayage des primitives de pilote (§4.1 `ARCHITECTURE-CIBLE.md`), pas par la seule recherche d'`os.replace()` |
| I2 | Journal d'écritures append-only (`runs.log`, JSONL) | **TRANSFORMÉ** | Le principe (une trace immuable par écriture) est conservé ; le format JSONL local ne tient plus à l'échelle multi-tenant, remplacé par un journal partitionné par `tenant_id`, toujours append-only et toujours écrit par un seul point de passage |
| I3 | Schéma validé à l'écriture (`FicheProspect`, Pydantic v2) | **CONSERVÉ** | Aucune raison de l'affaiblir ; généralisé à un modèle par verticale, toujours validé avant persistance |
| I4 | Un seul chemin vers le réseau (`api_io.py`) | **CONSERVÉ, reclassé** | Reclassé explicitement **contrôle de sécurité** (R5 de `RECHERCHE-agentique.md`, §3.1 de `ARCHITECTURE-CIBLE.md`) plutôt que commodité de mesure — la raison de le garder est renforcée, pas seulement inchangée |
| I5 | Grand livre + registres recalculés depuis le fichier | **CONSERVÉ (partitionné)** | Cornerstone de la facturation à l'usage (D) ; recalcul désormais scopé par tenant, jamais un second état mémoire |
| I6 | Budget bloquant avant l'appel | **CONSERVÉ, étendu** | Devient une chaîne à deux garde-fous (budget tenant puis budget fournisseur), toujours avant l'appel, jamais après |
| I7 | Machine à états intangible (4 états fixes en Python) | **TRANSFORMÉ** | Les états et transitions deviennent une donnée par verticale (`knowledge/machines_etats/*.yaml`) ; le principe qui compte — aucune transition marquée `porte_humaine: true` n'est déclenchable par un agent — reste un interdit structurel du socle, jamais une convention |
| I8 | Le graphe du pipeline est une donnée (`dag_pipeline.yaml`) | **CONSERVÉ** | Cornerstone ; étendu par analogie à la machine à états (I7) et au manifeste d'agentivité bornée (§3.3) |
| I9 | Ordonnancement déterministe (Kahn, départage alphabétique) | **CONSERVÉ au niveau du DAG, complété** | Tranché en §3.2 d'`ARCHITECTURE-CIBLE.md` : le DAG reste intégralement déterministe ; une agentivité locale bornée est admise **à l'intérieur** d'un nœud déclaré, jamais au niveau de la séquence des nœuds |
| I10 | Verrou de run exclusif (`os.open(O_CREAT\|O_EXCL)`, global) | **TRANSFORMÉ** | Même primitive, scopée `(tenant_id, cible)` au lieu de globale — deux tenants s'exécutent en parallèle, un tenant reste séquentiel avec lui-même |
| I11 | Une seule instance `ApiIO` par run, injectée | **CONSERVÉ (scopé tenant)** | Le geste qui corrige le défaut AS-IS historique reste la référence ; « run » se scope désormais à un tenant, la règle d'unicité et d'injection ne bouge pas |
| I12 | Zéro logique métier dans l'orchestrateur | **CONSERVÉ** | Aucune raison de l'affaiblir — c'est ce qui garde le socle stable pendant que les verticales changent |
| I13 | Reprise idempotente | **CONSERVÉ, renforcé** | Encore plus critique multi-tenant (retries, files d'attente légères, §5.4) |
| I14 | Cockpit strictement lecture seule (Obsidian = porte humaine) | **CONSERVÉ dans le principe, découplé d'Obsidian** | La porte humaine ne dépend plus d'un outil particulier ; le principe — aucune écriture, aucune transition, aucun appel réseau depuis la console d'observation — reste absolu quel que soit l'outil qui la remplace ou la complète |
| I15 | Cache et exports hors du magasin versionné | **CONSERVÉ** | Cornerstone, reformulé « hors de la source de vérité », agnostique du backend de stockage |
| I16 | La connaissance métier est une donnée | **CONSERVÉ, pierre angulaire renforcée** | Devient le fondement de la séparation socle/verticale (§2.3 `ARCHITECTURE-CIBLE.md`) — c'est l'invariant qui rend le test « seconde verticale en configuration » possible |
| I17 | Le LLM rédige, il ne collecte jamais | **CONSERVÉ dans sa forme dure, exception étroite ajoutée** | Tranché en §3.1 d'`ARCHITECTURE-CIBLE.md` : reclassé contrôle de sécurité (R5) ; seule ouverture admise, l'agentivité bornée en lecture seule derrière le bus, jamais un accès réseau ou une écriture directs |
| I18 | J6/outreach non activable (double verrou) | **TRANSFORMÉ, généralisé** | Le patron (verrou déclaratif YAML + verrou de code qui refuse même si forcé) devient le mécanisme socle générique pour **toute** action à effet externe irréversible (`action_irreversible_sur_tiers: true`, §2.6), pas seulement l'envoi d'e-mails marketing |
| I19 | Aucun chiffre non mesuré présenté comme mesuré | **CONSERVÉ, cornerstone SaaS** | Devient plus, pas moins, exigeant : chaque tenant doit voir un coût réel, jamais un placeholder ; aucune facturation au résultat tant que le résultat n'est pas mesurable (R10, §5.5) |
| I20 | Routage de modèle déterministe piloté par YAML | **CONSERVÉ** | Aucune raison de l'affaiblir ; reste distinct et séparé de l'agentivité bornée (§3.3), qui ne choisit jamais le modèle, seulement l'ordre de lecture d'outils déjà déterminés |
| I21 | Frugalité : bornes appliquées avant l'émission | **CONSERVÉ, étendu** | S'applique désormais aussi aux bornes de l'agentivité bornée (`budget_tokens_max`, `iterations_max`, §3.3) — même discipline, un cas d'usage de plus |
| I22 | Trois états (ok/échec/inconnu), jamais un signal `None` traité comme un échec | **CONSERVÉ comme primitive, complété par une couche orthogonale** | La question de `HERITAGE-v1-…` (« trois états suffisent-ils ? ») est tranchée : **oui pour la valeur observée** (elle reste la primitive la moins chère et la plus testée du projet) ; la robustesse OSINT (fiabilité de source, contradiction entre fournisseurs) est ajoutée comme métadonnée **séparée** (`fiabilite` par Preuve, §2.2) plutôt que comme un quatrième état — la contradiction entre deux Sources devient deux Observations distinctes datées, arbitrées au niveau de la Règle, jamais fusionnée dans le signal lui-même |
| I23 | L'axe intention n'est jamais un score, ne touche jamais `scoring.py` | **CONSERVÉ, généralisé au-delà du marketing** | Devient le mécanisme socle pour toute règle `nature: evenement` dans n'importe quelle verticale (§2.2, Verdict de type Veille) — ce n'est plus un axe spécifique à l'intention marketing, c'est un type de Verdict de premier rang |
| I24 | `citable=True` obligatoire pour dériver `signal_intention` | **CONSERVÉ, généralisé** | Devient la politique de citation appliquée à **tout** Livrable marqué `communication_externe: true`, quelle que soit la verticale, pas seulement au champ `signal_intention` du marketing |

**Lecture d'ensemble.** Sur les 24 invariants v1 : **19 conservés**,
**5 transformés** (I1, I2, I7, I10, I18 — le principe tient, le mécanisme
change), **0 abandonné**. Les verdicts du tableau ci-dessus font foi ; ce
paragraphe les résume et ne doit jamais les contredire.

⚠️ **Zéro abandon est un résultat à regarder avec méfiance.** Le mandat
demandait de traiter les 24 invariants comme des hypothèses à réfuter ; n'en
éliminer aucun peut signaler un biais de préservation de l'existant. La
justification retenue est la suivante, et elle doit être contestable :
les invariants v1 ne sont pour l'essentiel pas des paris produit mais de la
**discipline** (un seul écrivain, un seul chemin réseau, grand livre, budget
bloquant, trois états, porte humaine) — et la discipline survit à une réécriture.
Les cinq invariants réellement liés au produit v1 (I7, I14, I18, I23, I24) sont
tous **transformés ou généralisés**, jamais reconduits tels quels : leur forme
marketing tombe, leur principe monte au socle. Si le donneur d'ordre juge cette
lecture complaisante, l'invariant à réexaminer en premier est **I17**, seul à
être en tension frontale avec une tendance technique documentée.
**Zéro invariant abandonné.** Ce n'est pas un satisfecit — c'est la
conséquence directe du fait que la v1, malgré n'avoir jamais vu d'entreprise
réelle (§1.1 `ARCHITECTURE-CIBLE.md`), a accumulé sa discipline de bus
(vault/réseau/budget/déterminisme) sur des bases indépendantes du domaine
marketing lui-même. Les invariants qui **portaient** une hypothèse produit
(machine à états à 4 noms fixes, cockpit lié à Obsidian, axe intention
spécifique) sont ceux qui bougent ; ceux qui portaient une discipline de
plateforme ne bougent pas.

---

## 2. Nouveaux invariants v2

Chacun porte son mécanisme de vérification, conformément à la doctrine du §0.
Traçabilité vers les recommandations de `RECHERCHE-agentique.md` (Rn) et les
constats de `FOURNISSEURS-DONNEES.md` (Cn) quand applicable.

### N1 — Aucun identifiant de fournisseur dans une Grille de verticale

**Invariant.** Un fichier sous `knowledge/grilles/**` ne référence jamais un
`adapter_id` déclaré dans `knowledge/fournisseurs.yaml` — seulement des
Capacités (`<famille>.<capacite>`).

**Pourquoi.** Corrige C1 (`FOURNISSEURS-DONNEES.md`) : le nom d'un fournisseur
figé dans une rubrique casse toutes les rubriques d'un secteur à chaque
substitution de fournisseur.

**Mécanisme de vérification (balayage).** Charger la liste courte et stable
des `adapter_id` depuis `fournisseurs.yaml` ; parcourir (`rglob`) tous les
fichiers sous `knowledge/grilles/**` ; échec si l'un des `adapter_id`
apparaît comme sous-chaîne d'un champ `signal`. Test cible :
`test_grilles_ne_referencent_aucun_fournisseur`.

### N2 — Aucun catalogue de fournisseurs en dur dans le bus réseau

**Invariant.** Le module bus (`ApiIO` généralisé) ne contient aucun dict
`{fournisseur: mesureur}` codé au niveau module. La table fournisseur →
mesureur d'unités est chargée depuis `knowledge/fournisseurs.yaml`.

**Pourquoi.** Corrige C2 : ajouter un fournisseur ne doit jamais exiger de
modifier le bus.

**Mécanisme de vérification (balayage).** AST walk du module bus : aucune
assignation de dict au niveau module dont les clés sont des littéraux chaîne
identifiables comme noms de fournisseur (heuristique : présence d'au moins
trois clés correspondant à des `adapter_id` connus de `fournisseurs.yaml`
déclenche un échec). Doublé par un test fonctionnel : ajouter un fournisseur
factice au seul YAML, sans toucher le bus, et vérifier qu'il est mesuré
correctement.

### N3 — Rétention par fournisseur lue et appliquée, jamais déclarée sans effet

**Invariant.** Tout champ `retention_max_jours` déclaré dans
`fournisseurs.yaml` est **lu** par le mécanisme de cache du bus lors de
chaque lecture de cache, pas seulement déclaré.

**Pourquoi.** Corrige C3 — `cache_ttl_jours` était déclaré deux fois en v1 et
lu par aucun code ; une réponse Google Places de janvier était encore servie
en août, en tension avec la clause de caching de 30 jours rapportée
(`FOURNISSEURS-DONNEES.md` §5.1, `[NON VÉRIFIÉ]` juridiquement mais le
mécanisme technique, lui, est vérifiable).

**Mécanisme de vérification (balayage).** Test de mutation : injecter dans
le cache une entrée horodatée au-delà de `retention_max_jours` pour **chaque**
fournisseur déclaré dans `fournisseurs.yaml` (boucle sur le fichier de
config, pas une liste de fournisseurs codée dans le test) et vérifier que la
lecture de cache la traite comme absente.

### N4 — `tenant_id` obligatoire sur tout objet traversant le socle

**Invariant.** Tout modèle Pydantic représentant une Entité, une Observation,
une Preuve, un Verdict, une `LedgerEntry`, une entrée de verrou, porte un
champ `tenant_id: str` non optionnel (ou explicitement `None` documenté
comme mode mono-tenant historique, jamais silencieux).

**Pourquoi.** §5.1 `ARCHITECTURE-CIBLE.md` — retrofiter cette clé après coup
est la migration la plus coûteuse, une fois des données réelles accumulées.

**Mécanisme de vérification (balayage).** Introspection de **tous** les
modèles Pydantic du socle (import dynamique de chaque module, itération sur
`model_fields`) ; échec si un modèle de la liste des types socle
(Entité, Observation, Preuve, Verdict, LedgerEntry) ne déclare pas
`tenant_id`. Pas de liste de modèles tenue à la main : la détection se fait
par héritage d'une classe de base socle commune, elle-même balayée.

### N5 — Aucune requête au magasin sans filtre `tenant_id`

**Invariant.** Toute méthode publique de `MagasinIO` qui lit ou écrit exige
`tenant_id` en premier paramètre positionnel.

**Pourquoi.** L'isolation par tenant n'a de valeur que si elle est
imposée par signature, pas par convention d'appel.

**Mécanisme de vérification (balayage).** Introspection de signature
(`inspect.signature`) sur **toutes** les méthodes publiques de `MagasinIO`
(balayage de `dir(MagasinIO)`, pas une liste de méthodes nommées) ; échec si
une méthode publique n'a pas `tenant_id` en première position après `self`.

### N6 — Aucune Règle de nature `evenement` n'entre dans un Verdict de type Audit

**Invariant.** Généralisation d'I23. Le moteur de Verdict (`VerdictEngine`)
lève une erreur de configuration si une Grille déclarée `type_verdict: audit`
contient une règle `nature: evenement`, et réciproquement si une Grille
`type_verdict: veille` contient une règle `nature: etat` agrégée dans un
score (les règles `etat` peuvent apparaître en contexte informatif dans une
Veille, jamais agrégées).

**Pourquoi.** C'est le socle qui interdit structurellement l'erreur relevée
par l'ADR 0004 (« un score n'a pas de date, or la date EST l'information »),
plutôt que de compter sur la discipline de chaque verticale à la refaire.

**Mécanisme de vérification (balayage).** Validation de schéma appliquée à
**toute** Grille au chargement (`rglob` sur `knowledge/grilles/**`), pas à un
sous-ensemble connu ; le test charge chaque fichier trouvé et vérifie la
cohérence `type_verdict` / `nature` de chacune de ses règles.

### N7 — Politique de citation généralisée sur tout Livrable externe

**Invariant.** Généralisation d'I24. Tout Livrable marqué
`communication_externe: true` ne peut dériver son contenu que d'Observations
dont la Preuve sous-jacente porte `citable: true` sur la Règle qui l'a
produite.

**Pourquoi.** Le principe « on ne cite que ce que l'entité a publié
délibérément pour être vue » ne doit pas être une règle propre au marketing —
c'est une règle de posture OSINT générale (§I24 v1, motif inchangé).

**Mécanisme de vérification (balayage).** Le sérialiseur socle qui produit un
Livrable `communication_externe: true` filtre programmatiquement sur
`citable` avant toute sélection de contenu — testé par injection d'un jeu
d'Observations mixtes (citable/non citable) et vérification qu'aucune
Observation non citable n'apparaît dans le rendu, pour **chaque** type de
Livrable du catalogue socle (balayage du catalogue, pas un seul type testé).

### N8 — Agentivité bornée : cinq bornes obligatoires, validées au chargement

**Invariant.** Tout nœud de DAG déclarant `agentivite.active: true` doit
fournir les cinq champs `outils_autorises`, `budget_tokens_max`,
`iterations_max`, `critere_arret`, `rejouable_depuis_cache` — validés par
schéma Pydantic (`AgentiviteConfig`) au chargement du DAG. Un nœud sans les
cinq n'est pas déployable (le chargement du DAG échoue explicitement,
`DagInvalide`).

**Pourquoi.** Tranché en §3.2-3.3 `ARCHITECTURE-CIBLE.md` : c'est le
mécanisme qui rend l'agentivité locale compatible avec le refus du
superviseur-planificateur (ADR 0001) — bornée, journalisée, rejouable.

**Mécanisme de vérification (balayage).** `charger_dag()` valide **chaque**
nœud portant `agentivite.active: true` contre `AgentiviteConfig`, pas une
liste de nœuds réputés agentiques — même mécanisme que la validation
existante de `DagInvalide`/`CycleDetecte` en v1, étendu.

### N9 — Aucun outil d'un nœud agentique ne fetch ni n'écrit hors bus

**Invariant.** Tout identifiant listé dans `outils_autorises` d'un nœud
agentique doit correspondre à une fonction enregistrée dans un registre
socle de « lectures pré-vetted », elles-mêmes implémentées en appelant
exclusivement `ApiIO`/`EvidenceStore` en mode lecture seule. Aucun outil
agentique ne peut être une fonction arbitraire.

**Pourquoi.** C'est le mécanisme concret qui tient la résolution de la
tension I17 (§3.1 `ARCHITECTURE-CIBLE.md`) — sans lui, « agentivité bornée »
ne serait qu'une déclaration d'intention.

**Mécanisme de vérification (balayage).** AST walk de **chaque** fonction du
registre de « lectures pré-vetted » (parcours du registre lui-même, pas
d'une liste externe) : aucun import `requests`/`anthropic` au niveau module
(réutilise le balayage d'I4), aucun appel à une méthode d'écriture de
`MagasinIO`. Un outil qui échoue ce balayage ne peut pas être enregistré —
le registre lui-même refuse l'ajout, échec à l'import plutôt qu'à l'usage.

### N10 — Régime de revue à deux vitesses (`pass^1` déterministe / `pass^k` non déterministe)

**Invariant.** Toute assertion de la porte de cohérence est classée
`déterministe` ou `non déterministe` (touche une sortie LLM). Les assertions
déterministes exigent une exécution, 100 %, zéro échec dur (régime inchangé
de la v1). Les assertions non déterministes exigent `pass^k` avec
`k ≥ 3` [À CALIBRER] contre des entrées gelées (issues de l'`EvidenceStore`,
N-non-numéroté ci-dessous — voir Preuve §2.2 `ARCHITECTURE-CIBLE.md`), et
leur seuil de passage est **déclaré et publié séparément**, jamais fondu
dans le pourcentage global de la porte.

**Pourquoi.** R3 de `RECHERCHE-agentique.md` : une exécution unique sur une
sortie LLM est un `pass^1` déguisé, et le billet Thinking Machines Lab
(§2.5) établit que la température 0 ne garantit pas la reproductibilité
derrière une API partagée — donc une assertion non rejouée plusieurs fois
sur la même entrée ne prouve rien de plus qu'un coup de chance.

**Mécanisme de vérification (balayage).** Chaque assertion déclarée dans le
protocole de revue porte un champ `regime: deterministe|non_deterministe` —
balayage du registre d'assertions au démarrage de la revue : toute assertion
qui invoque, directement ou transitivement, un appel LLM sans déclarer
`regime: non_deterministe` est rejetée avant exécution, pas après coup.

### N11 — Aucun rapport de qualité sans son coût attenant

**Invariant.** Un rapport d'évaluation (revue, benchmark, comparaison de
variantes) qui présente une mesure de qualité sans le coût qui l'a produite
(tokens, $, énergie estimée) est refusé par le garde-fou de publication.

**Pourquoi.** R4 de `RECHERCHE-agentique.md` (Kapoor et al., « AI Agents That
Matter ») : l'exactitude sans coût produit des agents inutilement complexes ;
l'infrastructure (`LedgerEntry`, 7 champs GreenIT) existe déjà, il ne
manquait que l'obligation de la coupler à toute publication.

**Mécanisme de vérification (balayage).** Le gabarit socle de rapport
d'évaluation exige structurellement un champ `cout` non vide ; un générateur
de rapport qui ne le remplit pas échoue à la validation de schéma du
gabarit, pas à une relecture humaine.

### N12 — Contrôle robots.txt / opt-out au niveau du bus, une seule fois

**Invariant.** Tout fetch HTTP passant par `ApiIO`/le crawl propre applique
un contrôle robots.txt **avant** la requête, journalisé (autorisé / refusé /
robots.txt injoignable) — au niveau du bus, jamais réimplémenté par
collecteur/adaptateur.

**Pourquoi.** R6 de `RECHERCHE-agentique.md` : robots.txt est le véhicule de
fait de l'opt-out TDM (art. 4, directive UE 2019/790) et un signal de bonne
foi retenu par les régulateurs (`[ÉTABLI]` tel que rapporté, §5.3) ; la dette
déjà identifiée en v1 (escalade « page carrières » sans contrôle) doit être
fermée **structurellement**, pas collecteur par collecteur — la même leçon
que le §4.2 (garde-fou par balayage) appliquée à un besoin juridique.

**Mécanisme de vérification (balayage).** Un seul point d'entrée de fetch
dans le bus (déjà vrai pour I4) ; test d'intégration qui vérifie qu'**aucun**
fetch HTTP du bus n'atteint le réseau sans qu'une décision robots.txt ait été
journalisée au préalable — vérifié en interceptant tous les appels sortants
du bus sur un run complet, pas en énumérant les collecteurs qui fetchent.

### N13 — Capture de Preuve horodatée pour toute Observation citable

**Invariant.** Toute Observation dont la Règle porte `citable: true` doit
référencer au moins une Preuve dans l'`EvidenceStore` (extrait, URL, date de
capture, hash) — pas seulement une valeur dérivée.

**Pourquoi.** R7 de `RECHERCHE-agentique.md` : un diagnostic contesté trois
mois plus tard est indéfendable si seule la conclusion est conservée, la page
source ayant pu changer entretemps (§5.2 de `FOURNISSEURS-DONNEES.md`,
absence de standard de chaîne de preuve OSINT faisant autorité — donc
l'horodatage de la capture, lui, est vérifiable même sans standard).

**Mécanisme de vérification (balayage).** Balayage de **toutes** les Règles
de **toutes** les Grilles (`rglob` sur `knowledge/grilles/**`) marquées
`citable: true` ; pour chacune, test d'intégration qui vérifie qu'une
Observation produite référence un identifiant de Preuve non vide dans
l'`EvidenceStore`.

### N14 — Le dénominateur commercial est instrumenté dès le socle

**Invariant.** Toute machine à états déclarant un état terminal de rejet
expose un champ `motif_rejet` (chaîne libre ou taxonomie fermée par
verticale) obligatoire à la transition, et le socle expose un **taux
d'approbation de la porte humaine** calculé et publié (jamais silencieux).

**Pourquoi.** R8 de `RECHERCHE-agentique.md`, généralisant le Lot 0 de
l'ADR 0004 (non fait en v1) : sans ce champ, aucune verticale ne peut jamais
mesurer si son Verdict améliore quoi que ce soit, et §3.5 de la recherche
établit qu'une porte humaine qui approuve massivement (> 95 % `[À
CALIBRER]`) cesse d'en être une, sans qu'on puisse le savoir sans le mesurer.

**Mécanisme de vérification (balayage).** Validation de schéma de **chaque**
machine à états déclarée (`knowledge/machines_etats/**`) : tout état marqué
`terminal: true` et `polarite: negative` exige un champ `motif_rejet` dans
son schéma de transition — refusé au chargement sinon. Le taux d'approbation
est un calcul systématique sur le journal de transitions, exposé par la
console d'observation pour **toute** verticale, jamais construit à la main
verticale par verticale.

### N15 — Aucune facturation au résultat sans mesure de lift préalable

**Invariant.** Un modèle de tarification `au_resultat` ne peut être activé
pour une verticale que si un rapport de lift incrémental (groupe témoin
apparié, R8) existe et est daté, référencé dans la configuration de
tarification de cette verticale.

**Pourquoi.** R10 de `RECHERCHE-agentique.md` : aucune source ne relie signal
observé et conversion (§7.1 de la recherche) — facturer un résultat non
mesuré transfère au client un risque que la plateforme elle-même ne sait pas
évaluer.

**Mécanisme de vérification (balayage).** Validation de schéma de
**chaque** configuration de tarification par verticale : le champ
`modele_facturation: au_resultat` exige un champ `rapport_lift_ref` non vide
pointant vers un rapport daté existant — refusé au chargement sinon, pas
laissé à la discrétion commerciale.

---

## 3. Ce qui reste `[À CALIBRER]` — pas décidé par ce document

| Paramètre | Où il apparaît | Ne peut être fixé que par |
|---|---|---|
| `k` du régime `pass^k` (N10) | Porte de cohérence, assertions non déterministes | Mesure de variance réelle sur des sorties LLM en production (aucune source lue ne fournit de valeur) |
| Seuil de taux d'approbation de la porte humaine au-delà duquel elle est jugée décorative (N14) | Console d'observation | Mesure réelle post-étape 2 (§1.3 `ARCHITECTURE-CIBLE.md`) ; aucune source ne fournit de seuil |
| Seuil de tenants payants déclenchant la bascule `MagasinIO` vers un backend transactionnel (§5.2, §5.5) | Infrastructure | Décision produit informée par le volume réel, pas par anticipation |
| `couverture_minimale_pour_classement` d'un Verdict Audit (§2.4 `ARCHITECTURE-CIBLE.md`) | `mode_comparabilite` d'une Grille | Décision par verticale, informée par la distribution réelle de couverture observée |
| Composition des cinq bornes d'agentivité (`budget_tokens_max`, `iterations_max` par défaut, §3.3) | `AgentiviteConfig` | Mesure de coût réel du premier nœud agentique déployé, pas une estimation a priori |

Chacune de ces lignes est délibérément laissée ouverte : les fixer sans
donnée réelle répéterait exactement l'erreur de méthode nommée en §1.1 de
`ARCHITECTURE-CIBLE.md`.
