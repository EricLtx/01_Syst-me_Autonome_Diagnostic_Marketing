# Paradigmes — les bascules structurantes du projet

> **Objet de ce document.** Pas un changelog de plus : un changelog dit *ce qui
> a changé*. Celui-ci dit **ce qui a changé dans la façon de penser le
> système** — les arbitrages qui reconfigurent la lecture de tout ce qui les
> entoure, pourquoi ils ont été pris, et ce qu'ils interdisent désormais.
>
> Public : la commanditaire (non-développeuse, exigeante sur la rigueur) et
> tout agent qui reprend le projet. Quinze minutes de lecture suffisent à
> obtenir la carte mentale du système.
>
> **Vérifié par exécution le 2026-08-03**, commit de tête `cc99302`, branche
> `claude/diagnostic-as-is-fonctionnalites-7kzdj4` (l'ADR 0004 a été révisée
> une première fois par `6ba11e2` avant toute implémentation, puis ses Lots
> 1-2 + volet export du Lot 3 ont été implémentés par `cc99302` — voir §P6,
> qui reflète l'état réel du code, pas seulement le design révisé). Chaque
> chiffre cité a été re-mesuré juste avant l'écriture de ce document (voir le
> rapport de l'itération qui l'a produit pour le détail des commandes).
>
> Règle de lecture : une bascule **implémentée** décrit du code vérifié par
> `Read`/`Grep`/exécution. Une bascule **`[PROPOSÉ — NON IMPLÉMENTÉ]**` décrit
> une conception actée dans une ADR, sans qu'une seule ligne de code n'en
> découle encore — le distinguo n'est pas cosmétique, c'est la règle n°1 du
> projet (ne jamais documenter une intention au présent).

---

## P1 — Du script enchaîné à l'ordonnancement déterministe

**Statut : implémenté**, ADR [0001](../adr/0001-orchestrateur-dag-deterministe.md),
commit `36380c8`.

| | |
|---|---|
| **Avant** | Cinq briques (J1-J5) qui tournaient chacune par son propre `run_*.py`. L'enchaînement — et le partage du budget entre étapes — reposait sur la mémoire de l'opératrice. Chaque `run_*.py` fabriquait sa **propre** instance `ApiIO` : les budgets n'étaient jamais partagés entre les étapes d'une même campagne. |
| **Après** | `diagnostic/orchestrator.py` + `run_pipeline.py` + `dag_pipeline.yaml`. Le graphe (`preflight_gate → discovery → diagnostic → [porte humaine] → export → usage_snapshot`, `outreach` en `enabled: false`) est une **donnée YAML**. Tri topologique de Kahn avec départage **alphabétique** : deux exécutions du même DAG produisent exactement la même séquence de nœuds. Une instance `ApiIO` **unique**, créée en tête de chaîne avec les budgets de `api_pricing.yaml`, est **injectée** dans les nœuds réseau. Verrou de run exclusif (`os.open(..., O_CREAT|O_EXCL)`, délibérément distinct de `os.replace()` qui reste l'exclusivité de `vault_io.py`). |
| **Pourquoi** | Quatre défauts constatés dans le dépôt avant la décision (ADR 0001, §Contexte) : `ApiIO` multiple, `run_diagnostic.py` sans injection, aucune orchestration bout-en-bout, préflight non branché comme porte. Trois scénarios notés sur huit critères pondérés ; le scénario A (retenu) l'emporte à 4,42/5 contre 3,56 (superviseur hiérarchique) et 2,52 (nerf événementiel multi-tenant), sur les trois critères les plus lourds : time-to-market, OPEX, complexité d'exploitation — la contrainte cardinale d'une consultante solo, bus factor 1. |
| **Impact concret** | Un run peut être relancé après coupure sans double écriture ni double consommation de budget (reprise idempotente : le nœud `diagnostic` est sauté s'il ne reste aucune fiche `decouvert`). Le budget devient réellement bloquant à l'échelle d'une campagne complète, pas d'un seul `run_*.py`. |
| **Ce que ça interdit désormais** | Créer une seconde instance `ApiIO` dans un nœud du DAG. Réordonner les étapes en modifiant `orchestrator.py` plutôt que `dag_pipeline.yaml`. Le parallélisme entre nœuds (l'ambiguïté initiale « export ∥ outreach » a été tranchée en faveur du séquentiel strict). Le superviseur-planificateur LLM — explicitement refusé (coût, non-déterminisme, charge cognitive pour une opératrice solo) et une porte qu'aucune extension ultérieure ne doit rouvrir. |
| **Vérification** | `python -m pytest tests/test_orchestrator.py -q` (34 tests) et `python -m pytest tests/test_pipeline_cli.py -q` (4 tests). `python -c "from diagnostic.orchestrator import charger_dag, tri_topologique; n=charger_dag(); print([x.nom for x in tri_topologique(n)])"`. |

---

## P2 — Du coût subi au coût piloté

**Statut : implémenté** (mécanisme), ADR [0002](../adr/0002-greenit-efficience-et-observabilite.md),
commit `6055e14` (socle) + `d5b14d1` (observabilité cockpit).

| | |
|---|---|
| **Avant** | Le choix du modèle LLM était implicite dans `synthesis.py` : un choix codé en dur ne se pilote pas, ne se compare pas, ne se change pas sans toucher au code. Aucune notion de plafond d'entrée/sortie, aucune trace d'empreinte énergétique. |
| **Après** | `diagnostic/greenit.py` + `knowledge/greenit.yaml`. Routage de modèle **déterministe** (`choisir_modele(contexte, config)`) : profil `standard` par défaut (haiku, 600 tokens de sortie), escalade vers `qualite` (sonnet, 900) en mode `ou` sur trois règles explicites (`quality_check_echoue == true`, `nb_failles >= 6`, `score_global >= 75`). Bornes de frugalité appliquées **avant** l'appel : troncature du contexte (4 000 car.) et du prompt assemblé (8 000 car.), `max_tokens_sortie` qui écrase le profil s'il est plus permissif, TTL de cache 30 j. Sept champs ajoutés à `LedgerEntry` (`octets_entrants`, `octets_sortants`, `duree_ms`, `energie_wh`, `co2e_g`, `modele`, `profil`), tous optionnels — les lignes antérieures se relisent sans migration. |
| **Pourquoi** | Trois problèmes simultanés (ADR 0002, §Contexte) : économique (OPEX plancher, critère cardinal de l'ADR 0001), écologique (aucun fournisseur ne publie de consommation réelle par requête — rien à quoi se raccrocher sinon une estimation étiquetée), de pilotage (un choix codé en dur viole l'invariant « la connaissance métier est une donnée »). |
| **Impact concret** | Un cache-hit vaut **zéro absolu** : zéro coût, zéro énergie, zéro CO₂e — l'économie la plus facile à démontrer, donc la première mesurée. `tests/integration/test_e2e_bus.py::test_deux_appels_identiques_une_seule_requete_reseau` le prouve sur un vrai flux réseau (faux serveur HTTP local). |
| **Ce que ça interdit désormais** | Router le modèle par un LLM (« demander au modèle quel modèle utiliser ») — réintroduirait par la porte de service le superviseur-planificateur refusé en P1. Coder un nom de modèle en dur hors des deux constantes de repli explicites (`synthesis.py::MODELE_REPLI`, `greenit.py::CONFIG_DEFAUT`, qui pointent toutes deux vers le modèle le moins cher et n'entrent en jeu qu'en cas de configuration absente ou illisible). |
| ⚠️ **Réserve à maintenir** | **Aucune économie n'est chiffrable.** `knowledge/api_pricing.yaml` est intégralement à `0.0`, `releve_le: null` : tout coût affiché vaut 0,00. Les facteurs d'empreinte n'ont jamais été étalonnés (`releve_le: null` également) : ce sont des ordres de grandeur **comparatifs**, jamais un bilan carbone opposable. Toute affirmation de type « X % d'économie » serait une invention avant la Phase D. |
| **Vérification** | `python -m pytest tests/test_greenit.py --collect-only -q` → **78 tests collectés** (re-mesuré). `python run_usage.py` → tous les totaux à 0,00. |

---

## P3 — Du persona figé au secteur en donnée

**Statut : implémenté** (Lot 1 de l'ADR), ADR [0003](../adr/0003-icp-secteur-comme-cle-de-configuration-multi-industrie.md),
commit `356c361` (+ `675e85d` pour l'ADR, `db0af6e` pour le correctif cockpit
`persona: null`).

| | |
|---|---|
| **Avant** | `FicheProspect.persona: Literal[1, 2]` (`diagnostic/vault_schema.py`) plafonnait le système à deux personas **à jamais** — `persona=3` levait `ValidationError`. `Marche` était un enum fermé à cinq valeurs. **Le défaut le plus grave** : `run_vault_mode` construisait **un seul** `DiagnosticPipeline` avant la boucle et l'appliquait à **toutes** les fiches du lot, quel que soit leur persona — écrire une seconde rubrique n'aurait eu aucun effet, rien ne l'aurait chargée par fiche. Le vocabulaire métier HVAC (`OFFRE_KEYWORDS`) était codé en dur dans un collecteur générique. |
| **Après** | `secteur_id: str` devient la clé de sélection de rubrique, de vocabulaire et de fiche de connaissance (défaut si absent : `secteur_id = f"persona{persona}"`, donc `persona1-quebec` continue de se résoudre à l'identique — rétro-compatibilité vérifiée). `FicheProspect.persona` passe à `int | None` (borné `ge=1`), `FicheProspect.marche` passe de l'enum fermé à un `str` validé par un motif de slug. `secteur_id_for_fiche(fiche)` (`diagnostic/vault_runner.py`) résout la configuration **par fiche** ; `run_vault_mode` construit et met en cache **un pipeline par secteur rencontré dans le lot**. `WebsiteCollector` reçoit `vocabulaire_offre: list[str] | None` en paramètre injecté — vocabulaire absent → `mentions_offre = None` (inconnu), jamais `False`. |
| **Pourquoi** | Cinq blocages vérifiés par exécution (ADR 0003, §Contexte, B1 à B5) empêchaient de qualifier toute industrie hors HVAC. B5 est explicitement identifié comme la **troisième occurrence** du même défaut de fond en une itération (voir P4) : de la connaissance métier fuyant dans le code produit un faux négatif présenté comme un fait. |
| **Impact concret** | Ajouter un secteur/marché = écrire trois fichiers YAML (`icp/{secteur}-{marche}.yaml`, `knowledge/rubric_{secteur}.yaml`, `knowledge/vocabulaire_{secteur}.yaml`), **zéro ligne de code**. Un lot mixte (une fiche HVAC-Québec, une fiche d'un secteur fictif non-HVAC) est traité en un seul appel `run_vault_mode()`, chaque fiche recevant sa propre rubrique et son propre vocabulaire — démontré par `tests/test_multi_industrie.py` (15 tests). |
| **Ce que ça interdit désormais** | Construire un pipeline unique avant la boucle de traitement d'un lot vault. Instancier `WebsiteCollector` sans passer explicitement `vocabulaire_offre=` (y compris `None`) dès lors que l'appel est piloté par une configuration — sans quoi l'appelant hérite silencieusement du biais HVAC par défaut du constructeur (dette documentée, à surveiller en revue). Toute classification automatique du vocabulaire métier par LLM ou NLP — le vocabulaire reste écrit par un humain, en YAML. |
| **Ce qui reste un vestige assumé** | `persona` et l'enum `Marche` subsistent, partiellement redondants avec `secteur_id`/`icp_id`, pour ne pas casser le regroupement Dataview (`GROUP BY persona + marche`) ni les répertoires `10-Prospects/personaN-marche/` déjà écrits. |
| **Vérification** | `python -m pytest tests/test_multi_industrie.py -q` (15 tests) et `python -m pytest tests/test_icp_schema.py -q` (19 tests). |

---

## P4 — LE PLUS IMPORTANT : de deux états à trois

**Statut : implémenté**, commits `f77b4a6` (moteur) et `4827474` (collecteurs de production).

| | |
|---|---|
| **Avant** | Un check pouvait valoir `True` ou `False`. `None` (signal non observé) était compté comme un échec. |
| **Après** | Trois états : `ok` / `echec` / **`inconnu`**. `diagnostic/scoring.py::_check_passes` retourne `None` dès que `value is None` — **avant** toute évaluation de l'opérateur. `ScoringEngine.score()` : un check `inconnu` ne produit **ni point, ni dénominateur, ni faille** ; le score de chaque dimension est renormalisé sur le nombre de checks **réellement observés** (`max_points_connus`), et le score global sur les seules dimensions dont au moins un check a été observé. Le moteur publie `scores["_couverture"]` : la part du poids total réellement évaluée. |
| **Pourquoi** | Un signal ne vaut `False` que si un fait a été **positivement observé et jugé absent** ; sans observation possible, il vaut `None`. Le motif commun aux trois occurrences ci-dessous : **de la connaissance métier ou un échec technique qui produit un faux négatif présenté comme une observation.** |

### La classe de défaut, manifestée trois fois en une journée

| Occurrence | Où | Ce qui se passait | Conséquence mesurée |
|---|---|---|---|
| **(a) Le moteur lui-même** | `scoring.py`, avant `f77b4a6` | `_check_passes` comptait `None` comme un échec | Sans clé Google Places, `gbp` et `reviews` renvoient `None` : les dimensions `presence_locale` et `avis` valaient 0/100 pour **tous** les prospects — **45 % de la pondération fabriquée à zéro**. Mesuré sur trois entreprises radicalement différentes (site parfait / moyen / aucun site) : scores 27,5 / 15,0 / 0,0, et une **seule** accroche distincte pour les trois : « Fiche Google Business non vérifiée (à confirmer en J3) » — une affirmation jamais vérifiée envoyée à tout le monde. |
| **(b) Les collecteurs Google Places** | `gbp.py`/`reviews.py`, corrigé par `4827474` | `run_diagnostic._build_pipeline()` injectait **toujours** un `api_io`, même sans clé. Google Places répondait HTTP 200 avec `{"status":"REQUEST_DENIED","results":[]}`, et le code lisait ce `results: []` comme « aucune fiche trouvée » plutôt que « je n'ai pas pu vérifier » | Deux failles de gravité **haute** fabriquées pour toute entreprise diagnostiquée — dont celle qui alimentait l'accroche commerciale. C'était le défaut (a) réintroduit par une autre porte : non plus un stub `None`, mais une réponse d'API mal interprétée. Correction : `diagnostic/collectors/_places.py` — seuls `OK` et `ZERO_RESULTS` sont des observations ; `REQUEST_DENIED`, `OVER_QUERY_LIMIT`, `INVALID_REQUEST`, `UNKNOWN_ERROR` et toute réponse sans `status` produisent `None`. |
| **(c) Le vocabulaire métier** | `website.py::OFFRE_KEYWORDS`, corrigé par l'ADR 0003 (`356c361`) | Le vocabulaire HVAC était codé en dur dans un collecteur générique | Pour un secteur hors HVAC (ex. dentaire), absence de vocabulaire configuré → faux négatif de **25 points** en gravité haute sur `mentions_offre`, présenté comme un fait observé plutôt que comme une absence d'observation. |

**Ce que ça interdit désormais** : fusionner « non observé » et « échec » dans n'importe quel moteur ou collecteur du système, présent ou futur. Toute nouvelle source de signal doit distinguer explicitement un `None` (rien à en dire) d'un `False` (fait négatif constaté). C'est devenu un principe de conception vérifié en trois endroits distincts et cité comme précédent direct par l'ADR 0004 (§1.2) pour justifier la séparation besoin/intention.

**Vérification** :
```bash
python -m pytest tests/test_scoring.py -q                        # 19 tests
python -m pytest tests/test_collectors_phase_d.py -q              # 38 tests
python -m pytest tests/integration/test_e2e_diagnostic.py -q -k "repli"
```

---

## P5 — De la discipline au garde-fou exécutable

**Statut : implémenté**, commits `671ebeb` (création) et `7e41cb4` (durcissement).

| | |
|---|---|
| **Avant** | La cohérence entre ce que la documentation affirme (un nombre de tests, de routes, d'écrans, d'invariants, d'agents) et ce que le dépôt contient réellement n'était tenue **que par la bonne volonté** — une consigne « re-vérifie tes chiffres » dans le prompt de l'agent de documentation. |
| **Après** | `tests/test_doc_coherence.py` (**9 tests**, re-compté) compare ce que le Markdown du dépôt affirme à ce que la collecte `pytest --collect-only` et l'analyse statique du code produisent réellement. Portée volontairement large : tout le Markdown, pas seulement les fichiers qu'un agent vient d'éditer. Seuil « auto-calibrant » (F1 du commit `7e41cb4`) : ce n'est pas « au moins N lignes vérifiées », c'est **toute ligne qui se présente comme une ligne de tableau doit être exploitable** — ce qui interdit l'approximation (`~20`) qu'un plancher chiffré aurait laissée passer. |
| **Pourquoi** | La contre-mesure comportementale a échoué sur son **propre** terrain : sa checklist contenait la commande qui rend le bon chiffre, et un fichier affichait toujours l'ancien nombre — **dans le commit qui instituait la règle**. Le projet convertit sinon toute discipline en contrôle exécutable (garde-fou AST des imports réseau, 9 contrôles de préflight, rubrique = donnée) ; la cohérence documentaire était le seul invariant qui y échappait. |
| **Impact concret** | Il a trouvé, par exécution et non par relecture humaine, des erreurs qu'aucune des trois passes de revue précédentes n'avait vues : **six approximations `~20`/`~30`** dans un tableau de tests (repassées en dur pour échapper au contrôle avant le durcissement F1), **deux comptes faux** dans `.claude/agents/agent-documentation.md` (huit routes annoncées, alors que le réel était déjà de dix à ce moment-là). |
| **Ce que ça interdit désormais** | Écrire « ~N tests », « environ N routes » ou toute approximation chiffrée dans la documentation vivante du dépôt (`docs/strategie/**` et `docs/CHANGELOG.md` sont explicitement exclus du contrôle des totaux, car ce sont des journaux qui citent légitimement des chiffres révolus — voir le code du test pour la justification précise). |
| **Vérification (re-exécutée pour ce document)** :
```bash
python -m pytest tests/test_doc_coherence.py -q
```
→ **9 passed**, résultat ci-dessous. |

---

## P6 — De l'état à l'événement : le virage intent-based

**Statut : Lots 1-2 + volet export du Lot 3 IMPLÉMENTÉS** (commit `cc99302`).
ADR [0004](../adr/0004-axe-intention-et-collecteurs-osint-cibles.md),
commit `f36c276` (premier jet), **révisée le même jour par `6ba11e2`** avant
toute implémentation. Lot 0, Lot 0bis et le reste du Lot 3 restent
`[NON FAITS]` — voir en bas de section. L'en-tête de l'ADR elle-même dit
encore « proposée » : les ADR sont immuables une fois acceptées, l'écart entre
en-tête et implémentation réelle est documenté dans `docs/adr/README.md`, pas
corrigé dans le fichier de l'ADR (même traitement que l'écart déjà signalé
pour l'ADR 0003).

**Le premier jet lui-même a été corrigé avant d'être implémenté** — un fait à
documenter plutôt qu'à masquer, puisque c'est exactement le motif
d'hallucination que ce projet traque par ailleurs (P7) : le commit `f36c276`
décrivait dans son message un design déjà corrigé, alors que le *fichier*
contenait encore la version d'avant (`scores_intention: dict`, 5 occurrences).
`6ba11e2` répare l'écart entre message et fichier avant qu'une seule ligne de
code ne s'appuie dessus.

| | |
|---|---|
| **Ce qui est livré (design révisé, implémenté)** | Pas un second score. `Diagnostic` gagne un seul champ, `evenements_intention: list[EvenementIntention]` — une **liste de faits datés et périssables** (une offre d'emploi de production détectée, une certification affichée), chacun portant sa propre date d'observation et sa propre date de péremption calculée une fois (`diagnostic/models.py`). Le score de **besoin** reste un **état** permanent, inchangé, sans date. `scores_intention: dict[str, float]` — la version du premier jet — a été **explicitement retirée** du design implémenté : « un score n'a pas de date, or la date EST l'information » (note de cadrage retenue dans l'ADR, vérifiée par lecture de `diagnostic/intent.py`). |
| **Pourquoi séparer les deux axes, et pourquoi pas même un second score** | Trois raisons, vérifiées dans le code, pas une préférence de style (ADR 0004, §D1) : (1) le besoin est déjà l'inverse d'une note de satisfaction (`rubric_persona1.yaml` : « un score BAS = un prospect CHAUD ») — un événement d'intention, positif par nature, fusionné au même total ferait dépendre le sens du nombre final du hasard de la combinaison ; (2) **même classe de défaut que P4** — fusionner « pas de besoin pressant » et « pas d'événement détecté » dans un seul nombre, ou même les stocker comme deux scores comparables, reproduit la perte d'information déjà corrigée pour `inconnu`/`echec` ; (3) une date n'est pas une magnitude — un score /100 n'a pas de champ pour « ceci expire le [date] », et pré-décroître la valeur avant un test numérique **cacherait** l'information la plus importante (la date elle-même) dans un flottant. |
| **La table de correspondance, pas le calcul (D5)** | Besoin et intention se combinent en un **quadrant informationnel** (Q1 Fenêtre / Q2 Concurrence / Q3 Réservoir / Q4) par une **table de correspondance déterministe** sur deux libellés discrets (`fort`/`faible` de chaque côté) — jamais un produit, jamais une somme pondérée. Implémenté et mesuré côté banc d'essai (`scripts/benchmark_intention.py`, seuil `[À CALIBRER]`), mais `FicheProspect.quadrant` (Lot 3, champ persistant) **n'existe pas encore** : le quadrant reste, dans le dépôt à ce jour, un calcul d'illustration, jamais un champ écrit dans le vault ni utilisé pour trier ou disqualifier. |
| **Ce que ça capitalise sur P4, vérifié** | `scoring.py` reste inchangé — `git diff diagnostic/scoring.py` **re-exécuté et vide** au moment de la rédaction de cette section (commit de tête `cc99302`). La réutilisation n'est **pas** celle envisagée au premier jet : seules les deux primitives pures `_resolve`/`_check_passes` (`diagnostic/intent.py`) sont réutilisées, jamais l'agrégation de `ScoringEngine.score()` — l'agrégation renormalise et fait la moyenne, deux opérations qui n'ont pas de sens pour une liste d'événements datés. |
| **Ce que la conception interdit explicitement (ADR 0004 §D13), tenu** | Score composite besoin × intention ou tri de priorité automatique — rien de tel dans `intent.py`/`serializers.py`. `scoring.py` non modifié. Aucun classificateur d'intention par LLM (les deux collecteurs livrés sont déterministes : `is_true`/`exists` sur un fait déjà extrait). Aucun modèle appris. Aucun des cinq collecteurs déjà écartés par l'étude préalable n'a été ressuscité (registre légal, WHOIS/RDAP, Wayback, PageSpeed, offres d'emploi via API externe). Le quadrant n'est **exploité** nulle part en conditions réelles (pas de champ persistant, pas de tri) — cohérent avec le gate à deux vitesses de l'ADR tant que `motif_rejet` n'existe pas. |
| ⚠️ **Réserve de méthode, toujours vraie, jamais taire** | Les YAML livrés (`knowledge/intent_persona1.yaml`, `knowledge/vocabulaire_intention_persona1.yaml`) portent le même caveat que l'ADR : **« aucune source ne franchit le dernier pas entre signal ouvert observé et cette PME va acheter du conseil en branding. Cette hypothèse appartient à la consultante, pas à la recherche. »** Chaque référence citée dans l'ADR (Dawes 1979, D'Haen et al. 2016, Gutierrez et al. 2020, entre autres) reste marquée **`[NON LU]`** — vérifiée au seul niveau du résumé, jamais un texte intégral. Les trois YAML de l'axe intention sont eux-mêmes des **brouillons `[À CALIBRER]`** : aucun seuil (demi-vie, fenêtre de péremption, plancher, seuil de quadrant) n'a été validé par la consultante — le pilote doit trancher, pas le code. |
| **Ce qui reste `[NON FAIT]`** | **Lot 0** (`motif_rejet`, états `rdv`/`client` — sans eux, impossible de mesurer si Q1/Q2 convertissent mieux que Q3/Q4, l'hypothèse centrale reste une hypothèse). **Lot 0bis** (calibration graduée de `entretien.fraicheur_mois`, `diagnostic/collectors/_bareme.py` — n'existe pas, le check reste binaire `lte 18`). **Reste du Lot 3** (cockpit, 4ᵉ requête Dataview, `FicheProspect.quadrant` persistant). Limite connue et assumée : `diagnostic/collectors/legitimite.py` résout le marché en dur sur `"quebec"` (`MARCHE_CERTIFICATIONS_PAR_DEFAUT`), pas par fiche — symétrique de la limite déjà acceptée pour `vocabulaire_offre` (ADR 0003). Robots.txt non vérifié sur l'escalade page carrières. `VaultIO.append_historique()` posée, non exploitée. |
| **Vérification (re-exécutée pour cette section)** :
```bash
git diff diagnostic/scoring.py                      # vide — invariant dur tenu
python -m pytest tests/test_intent.py tests/test_decay.py tests/test_legitimite.py \
  tests/test_website_intention.py tests/test_config_intent.py \
  tests/test_serializers_intention.py tests/test_vault_io_historique.py -q   # 65 tests
python -m pytest tests/integration/test_e2e_intention.py -q                  # 10 tests
python scripts/benchmark_intention.py                                       # banc d'essai reproductible
```
|

---

## P7 — La gouvernance comme mécanisme, pas comme intention

**Statut : en fonctionnement**, protocole `docs/strategie/GOUVERNANCE-revue-iterative.md`
(propriété du chef de projet — lu, jamais réécrit ici).

| | |
|---|---|
| **Avant** | Un projet mené par des sessions d'agents dont la mémoire meurt à chaque fin de conversation. Rien n'obligeait à revérifier un chiffre, un test ou une affirmation d'un commit précédent. |
| **Après** | Chaque chantier (CORE, BACKEND, FRONTEND, GREENIT, INTÉGRATION, DOCUMENTATION…) est livré par itérations, avec 10 à 14 **assertions checkables par exécution** (tests, build, AST, `git diff`, conformité de contrat). `agent-revue` **ré-exécute** chaque contrôle — aucun rapport d'agent, aucun message de commit n'est pris pour argent comptant. `taux = assertions vérifiées / assertions totales` ; à cette granularité, **97 % impose zéro échec dur**. Sous le seuil, le **même** agent d'implémentation est relancé avec le backlog des assertions échouées comme contexte conservé — on ne re-spawne pas d'agent neuf. |
| **Pourquoi** | C'est un garde-fou anti-hallucination structurel : `agent-revue` n'a **aucun outil d'écriture** (`Read, Grep, Glob, Bash` uniquement) — un auditeur qui peut corriger ce qu'il audite n'en est plus un. |
| **Impact mesurable, avec les faits** | Itération 1 (`2ed8d93`) : CORE 12/12, BACKEND 7/7, FRONTEND 8/8 — 100 %, CLEARED, aucune hallucination détectée. Itération 2 (`04059f6`) : GREENIT 100 %, INTÉGRATION 100 %, WEBAPP 100 % → CLEARED ; **DOCUMENTATION 5/6 = 83,3 % → RELANCE** (assertion D4 : chiffres périmés dans `CLAUDE.md`/`README.md`, corrigés par `611eb74`). La revue a aussi recalé le chantier **multi-industrie** à **92,3 %** sur un défaut réel (`persona: null` faisait échouer le cockpit en 500 sur un vrai vault, reproduit par la revue elle-même, corrigé par `db0af6e`), et le chantier **scoring** à **78,6 %** en démontrant que la première correction (`f77b4a6`) avait été prouvée sur le **moteur**, pas sur le **système** — d'où la seconde correction `4827474` (occurrence (b) de P4). Le garde-fou documentaire lui-même (P5) est né d'une relance : la revue a signalé que la première contre-mesure comportementale échouait sur son propre terrain. |
| **Ce que ça interdit désormais** | Prendre pour acquis un message de commit — y compris celui du chef de projet, y compris celui qui institue une nouvelle règle — sans le ré-exécuter. Documenter un chiffre relevé en début de tâche sans le re-mesurer juste avant de rendre. |

---

## Ce que ces bascules ont en commun

Les sept convergent vers un seul principe : **remplacer une affirmation invérifiée par un mécanisme qui la falsifie ou la confirme, et refuser d'avancer un chiffre ou un fait tant qu'il n'y a pas de preuve d'exécution.**

- P1 remplace « l'opératrice se souvient de l'ordre » par un tri déterministe vérifiable.
- P2 remplace « le modèle est ce que le code choisit » par une règle explicite dans un YAML, testée.
- P3 remplace « le code sait que c'est du HVAC » par une résolution par fiche, vérifiée par un test qui traite un lot mixte.
- P4 est l'instance la plus fondamentale : **l'absence d'observation n'est pas une observation négative** — répétée trois fois parce que c'est le point où la tentation de fabriquer un fait est la plus forte (un moteur, une API qui répond mal, un vocabulaire absent).
- P5 convertit la dernière discipline purement humaine du projet (la cohérence documentaire) en contrôle exécutable, après avoir constaté que la consigne seule échouait sur son propre terrain.
- P6, **implémenté pour ses Lots 1-2 + volet export du Lot 3**, applique la leçon de P4 à un second axe : ne pas fusionner deux jugements de nature différente (un état permanent, un événement daté) même en les construisant l'un après l'autre.
- P7 est le mécanisme qui a *produit* les six autres : sans la ré-exécution systématique par un agent sans droit d'écriture, plusieurs de ces corrections n'auraient probablement pas eu lieu — la revue a recalé trois chantiers sur des défauts réels (documentation 83,3 %, multi-industrie 92,3 %, scoring 78,6 %) avant qu'ils ne soient acceptés.

Le fil conducteur : **ce projet ne se fie à rien qui n'ait été rejoué.** Ni un score, ni un compte de tests, ni un message de commit, ni même sa propre documentation.

---

## Ce qui n'a pas changé et ne doit pas changer

Ces invariants ont traversé les sept bascules sans être remis en cause — ce sont les fondations sur lesquelles les bascules ont pu être ajoutées sans réécriture :

| Invariant | Ce qu'il garantit | Détail |
|---|---|---|
| **La porte humaine** | Un agent ne peut déclencher que `decouvert → diagnostique`. `valide`, `contacte`, `rejete` restent des actes humains dans Obsidian. | `docs/architecture/invariants.md` I7 ; testé jusque dans l'exécution complète du DAG (`test_chaine_complete_ne_valide_aucune_fiche`). |
| **Les bus uniques** | `diagnostic/vault_io.py` seul écrivain du vault ; `diagnostic/api_io.py` seul point de contact réseau. | I1 et I4. Aucune des sept bascules n'a ajouté un second écrivain ou un second chemin réseau. |
| **La collecte est déterministe, le LLM rédige** | Les collecteurs observent des faits ; `synthesis.py` met en forme des faits déjà établis, jamais l'inverse. Repli déterministe sans clé Anthropic. | I17. P2 (GreenIT) et P6 (intention, Lots 1-2 livrés) réaffirment explicitement cette limite plutôt que de l'éroder — les deux collecteurs d'intention livrés (`website.py`, `legitimite.py`) sont déterministes, zéro LLM. |
| **Config = donnée** | Rubriques, ICP, tarifs, colonnes d'export, stratégie GreenIT, graphe du DAG : tous en YAML, zéro logique métier codée en dur. | I16. P1, P2 et P3 sont chacune l'application de ce principe à un nouveau domaine (ordonnancement, routage de modèle, secteur). |
| **Le vault est la source de vérité**, pas un read-model | Écarté explicitement du scénario C (nerf événementiel) par l'ADR 0001 : un event store qui projetterait le vault casserait l'auditabilité. | ADR 0001, alternatives écartées. |
| **Aucun chiffre non mesuré présenté comme mesuré** | Coûts et empreinte énergétique restent étiquetés « estimation » tant que `api_pricing.yaml` est à 0 et que les facteurs GreenIT n'ont pas été étalonnés. | I19. Directement hérité par P2 et par la réserve de P6. |

---

## Vérités inconfortables — état à la date de ce document

Elles ne disparaissent pas parce qu'une bascule de paradigme a eu lieu ; elles doivent rester visibles tant qu'elles sont vraies.

- **Aucune clé API dans l'environnement** (`SERP_API_KEY`, `APOLLO_API_KEY`, `GOOGLE_PLACES_API_KEY`, `ANTHROPIC_API_KEY`).
- **`knowledge/api_pricing.yaml` intégralement à `0.0`, `releve_le: null`** → `run_preflight.py` renvoie **NO-GO structurel** (code de sortie 1).
- **Le vault n'est pas initialisé** (`vault/` vide).
- **J6 / outreach non activable** : `enabled: false` dans `dag_pipeline.yaml` et double verrou côté code.
- **Aucune rubrique non-HVAC n'existe encore** : P3 rend l'ajout possible sans code, mais personne n'a encore écrit `rubric_dentaire.yaml` ou équivalent — c'est un travail de jugement métier, hors périmètre de cette passe.
- **Aucune économie GreenIT n'est chiffrable** : le mécanisme de P2 est livré, la démonstration de son gain ne l'est pas.
- **P6 n'a aucune ligne de code** : c'est une conception actée, rien de plus, et la validation empirique de son hypothèse centrale n'existe dans aucun document du projet.

---

## Commandes de re-vérification permanentes

```bash
# Le graphe et son déterminisme (P1)
python -c "from diagnostic.orchestrator import charger_dag, tri_topologique; \
n = charger_dag(); print([x.nom for x in tri_topologique(n)])"

# Le routage GreenIT et ses tests (P2)
python -m pytest tests/test_greenit.py --collect-only -q | tail -2

# La résolution par secteur (P3)
python -m pytest tests/test_multi_industrie.py -q

# Les trois états du moteur de scoring (P4)
python -m pytest tests/test_scoring.py tests/test_collectors_phase_d.py -q

# Le garde-fou documentaire lui-même (P5)
python -m pytest tests/test_doc_coherence.py -q

# Ce qui n'existe pas encore (P6) — doit renvoyer une liste vide
grep -rn "evenements_intention\|EvenementIntention" diagnostic/ 2>/dev/null

# Le préflight — pourquoi les vérités inconfortables restent vraies
python run_preflight.py; echo "code de sortie : $?"
```
