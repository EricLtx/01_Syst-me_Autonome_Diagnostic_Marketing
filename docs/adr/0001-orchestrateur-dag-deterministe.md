# ADR 0001 — Orchestrateur DAG déterministe « Kemana-Flow »

- **Statut** : acceptée — Palier 1 **implémenté** (commit `36380c8`, 2026-08-01)
- **Date** : 2026-08-01
- **Décideur** : chef de projet (autorité ultime), décision non rediscutée
- **Source** : `docs/strategie/STRATEGIE_agentique_B2B.md`, sections
  « Synthèse de la décision structurante » et « Matrice de décision »
- **Remplace** : —
- **Remplacée par** : —

---

## Contexte

Le socle J1-J5 existait, tournait hors ligne et passait sa suite de tests. Mais
il n'avait **pas de couche d'ordonnancement** : chaque étape se lançait par son
propre `run_*.py`, et l'enchaînement reposait sur l'opératrice.

Quatre défauts constatés dans le dépôt avant la décision :

1. **Chaque `run_*.py` fabriquait son propre `ApiIO`.** Conséquence : les
   budgets n'étaient pas partagés entre les étapes d'une même campagne, et le
   garde-fou budgétaire était inopérant à l'échelle de la chaîne.
2. **`run_diagnostic.py` n'avait pas d'`ApiIO`** injectable au même titre que
   les autres entrypoints.
3. **Aucune orchestration bout-en-bout** : ni `orchestrator.py`, ni
   `run_pipeline.py`, ni description du graphe.
4. **Préflight non branché comme porte** : le contrôle GO/NO-GO existait mais
   rien ne l'imposait avant un run.

Trois scénarios d'architecture ont été instruits et notés sur huit critères
pondérés. Les trois critères les plus lourds — time-to-market (18 %), OPEX
(15 %), complexité d'exploitation (14 %) — reflètent la contrainte cardinale du
projet : **une consultante solo, bus factor 1, qui doit industrialiser avant de
productiser**.

| Scénario | Total pondéré /5 |
|---|---|
| **A — Orchestrateur DAG déterministe (« Kemana-Flow »)** | **4,42** |
| B — SCOP-H, superviseur hiérarchique multi-agents | 3,56 |
| C — Nerf central événementiel, cloud-native multi-tenant | 2,52 |

---

## Décision

**Le Scénario A est retenu comme colonne vertébrale et livrable immédiat**,
hybridé selon une **trajectoire en trois paliers**. L'hybridation n'est pas un
compromis mou : c'est la lecture correcte de la matrice — B n'est pas un
concurrent frontal de A, c'est sa suite.

### Le socle (Palier 1 — livré)

1. **Trois artefacts, aucune réécriture métier.**
   `diagnostic/orchestrator.py` (ordonnanceur), `run_pipeline.py` (CLI unique),
   `dag_pipeline.yaml` (le graphe **est une donnée**). Chaque nœud est un
   adaptateur **mince** autour d'un entrypoint existant. Les `run_*.py`
   historiques continuent de fonctionner seuls : rétro-compatibilité préservée.

2. **Une instance `ApiIO` UNIQUE**, créée en tête de chaîne avec les budgets
   chargés depuis `api_pricing.yaml`, et **injectée** dans les nœuds découverte,
   diagnostic (et outreach, le jour où il existera). C'est le geste
   architectural qui corrige d'un coup les défauts 1 et 2 : un seul grand livre,
   un seul garde-fou budgétaire.

3. **Tri topologique déterministe** : algorithme de Kahn avec **départage
   alphabétique**. Deux exécutions du même DAG donnent exactement la même
   séquence, indépendamment de l'ordre d'écriture dans le YAML.

4. **Exécution strictement séquentielle.** La spécification initiale décrivait
   « export ∥ outreach » en parallèle tout en présentant l'orchestrateur comme
   séquentiel. **L'incohérence est tranchée en faveur du séquentiel strict** ;
   le symbole `∥` est retiré.

5. **Verrou de run exclusif** contre tout démarrage concurrent (cron + manuel
   sur le même vault). Création atomique par `os.open(..., O_CREAT|O_EXCL)` —
   délibérément **pas** `os.replace()`, qui reste l'exclusivité de `vault_io.py`.

6. **Machine à états intangible.** L'orchestrateur ne déclenche **que**
   `decouvert → diagnostique`. Les transitions `valide`, `contacte`, `rejete`
   restent **humaines**, dans Obsidian. Reprise idempotente entre les runs.

7. **Garde-fou AST étendu** à `orchestrator.py` et `run_pipeline.py` **avant**
   activation. Condition non négociable : nouveaux tests verts **en plus** de
   l'existant, aucun test supprimé ni affaibli.

8. **J6 livré comme ossature human-gated non activable** : `enabled: false` dans
   le DAG, runner qui refuse de s'exécuter même si l'on force le drapeau.
   Jamais présenté comme opérationnel.

9. **Préflight en première porte du DAG** : en mode réel un NO-GO refuse le
   démarrage ; en `--dry-run` il informe sans bloquer.

### La trajectoire

| Palier | Contenu | Condition de déclenchement |
|---|---|---|
| **1** | A intégral — orchestrateur, CLI, graphe en donnée, `ApiIO` unique, amorce J6 human-gated | maintenant — **fait** |
| **2** | Greffe sélective de B **sans son superviseur LLM** : (a) critique de grounding déterministe entre synthèse et transition ; (b) conformité-par-donnée — politiques `compliance/*.yaml` par marché (CASL-QC, nLPD + art. 3 LCD-CH, RGPD-FR, transparence AI Act) et nœud « Conformité » bloquant en amont d'export/outreach ; (c) routeur de modèle piloté par YAML | dès que le pilote tourne |
| **3** | Fragments de C, isolables uniquement : gateway `api_io` promue en service métré/budgété **par tenant**, isolation par tenant, reporting coût par tenant. Bus d'événements, event sourcing et RAG **reportés** | **gelé** jusqu'à un seuil de tenants payants défini à l'avance — pas sur une intuition |

---

## Conséquences

### Positives

- **Correction des quatre défauts AS-IS en un seul geste architectural**, sans
  réécrire aucune brique métier. A est le seul scénario dont la revendication
  « zéro réécriture métier » était crédible.
- **Déterminisme maximal** : hors les points de rédaction LLM, tout est
  reproductible. C'est la propriété qui rend le système auditable et qui
  différencie l'offre sur un marché saturé de superviseurs probabilistes.
- **OPEX plancher** : LLM marginal, cache réseau, budgets bloquants, repli
  déterministe hors ligne, aucune infrastructure permanente. Coût fixe ≈ 0.
- **Complexité d'exploitation minimale** : un seul point d'entrée
  (`run_pipeline.py`), reprise idempotente, manage-by-exception via Obsidian
  inchangé. Aucune compétence nouvelle exigée de l'opératrice.
- **Risque de régression minimal** : couche purement additive, aucune migration
  de données, invariants de bus préservés.
- **Traçabilité** : `run_id` + manifeste de run corrèlent `runs.log` et
  `api_usage.log` sans modifier leur schéma.

### Négatives — assumées

- **Scalabilité technique faible** (noté 2/5). Batch séquentiel, mono-vault,
  mono-opératrice. Aucun parallélisme, aucun multi-tenant. Un passage SaaS
  exigerait une refonte de la couche d'ordonnancement — c'est précisément
  l'objet du Palier 3, conditionné.
- **Faible différenciation produit en soi** (noté 2/5). Un orchestrateur DAG
  interne n'est pas un argument de vente ; la valeur est l'efficacité
  opérationnelle de la consultante.
- **Conformité solide mais non formalisée** (noté 4/5) : opt-out absolu, porte
  humaine, minimisation Apollo, zéro scraping LinkedIn — mais **pas de moteur de
  conformité par donnée**, et la transparence AI Act reste implicite. Suffisant
  pour un pilote, **à durcir avant toute activation réelle de J6** — c'est
  l'objet du Palier 2.
- **Observabilité basique** : journaux fichiers. Suffisant pour un pilote, à
  revoir si le volume croît.
- **Bus factor 1** assumé, mitigé par des procédures reprenables et par la
  documentation.

### Neutres, mais à savoir

- La décision **ne lève aucune des deux pré-conditions dures** :
  - **Phase D** — tant que `knowledge/api_pricing.yaml` est à `0` et que les
    clés API sont absentes, **le préflight est en NO-GO structurel** et aucun
    coût par fiche n'est engageant.
  - **Validation juridique** avant toute activation de J6.
- Tous les chiffres d'OPEX cités dans l'analyse stratégique sont des
  **estimations modélisées**. Aucun engagement de coût fixe ne doit être pris
  avant le relevé réel de la Phase D.

---

## Alternatives écartées

### B — SCOP-H, superviseur hiérarchique multi-agents (3,56/5)

**Rejeté comme architecture de remplacement, retenu comme greffe au Palier 2.**

Ce que B apporte et que A n'a pas : la revue croisée de grounding (agent
Critique) et la **conformité-par-donnée** — meilleure note du panel sur ce
critère (5/5), avec des politiques par marché en YAML versionné et testable.
Ces deux briques deviennent **nécessaires avant l'activation réelle de J6** :
elles sont importées comme **nœuds et données du DAG de A**.

Ce qui est **explicitement refusé** : le **superviseur-planificateur LLM**.
Motifs — c'est la principale source de coût (le LLM devient le poste dominant :
rédaction + critique + planification), de **non-déterminisme** (variance de
routage et de planification absente de A, alors que la reproductibilité est la
force cardinale de l'AS-IS), et de charge cognitive pour une opératrice solo.
B perd contre A précisément sur ces trois points. Le planificateur reste
**déterministe**.

### C — Nerf central événementiel, cloud-native multi-tenant (2,52/5)

**Disqualifié au stade actuel. Gelé, non enterré.**

- Dernier sur les trois critères les plus lourds : time-to-market (1/5), OPEX
  (2/5), complexité d'exploitation (1/5).
- **Coût fixe d'infrastructure** estimé entre ~200 et ~2 500 USD/mois selon le
  niveau de robustesse, contre ≈ 0 aujourd'hui — insoutenable sans dizaines de
  tenants payants. *(Estimation modélisée issue de la spécification du scénario,
  non un devis.)*
- **Compétences DevOps/SRE absentes en interne** (bus d'événements, event
  sourcing, RAG, observabilité distribuée, secrets par tenant).
- **Inversion d'un invariant fondateur** : C fait du vault un *read-model*
  projeté depuis un event store. Or **le vault EST la source de vérité
  versionnée**, écrite par le seul bus `vault_io`. Cette inversion casserait
  l'invariant I1 et la propriété d'auditabilité qui en découle.
- Recul sur le déterminisme : distribué asynchrone, ordre partiel,
  *at-least-once*, RAG non déterministe → la reproductibilité exacte devient
  plus difficile qu'en A ou B.

**Condition de réexamen** : un **seuil de tenants payants défini à l'avance**,
pas une intuition ni une opportunité. Ses bonnes idées isolables (gateway
métrée par tenant, isolation, coût par tenant temps réel) sont récupérables au
Palier 3 **sans** adopter le bus d'événements ni l'event sourcing.

### Statu quo — pas d'orchestrateur

Écarté sans hésitation : les quatre défauts constatés persistent, notamment
l'absence de budget partagé entre les étapes d'une même campagne — ce qui rend
le garde-fou financier illusoire au moment précis où il compte, c'est-à-dire
sur un run réel.

---

## Vérification

Décision implémentée et auditée à l'itération 1. Contrôles ré-exécutés
indépendamment (protocole `docs/strategie/GOUVERNANCE-revue-iterative.md`,
chantier CORE, 12 assertions, **100 %**, verdict CLEARED). Aucune hallucination
détectée.

Commandes de contrôle permanentes :

```bash
python -m pytest tests/ -q
python run_pipeline.py --help
python -c "from diagnostic.orchestrator import charger_dag, tri_topologique; \
n = charger_dag(); print([x.nom for x in tri_topologique(n)]); \
print({x.nom: x.enabled for x in n})"
python -c "from diagnostic.preflight import _check_garde_fous_bus; \
[print(c.ok, c.message) for c in _check_garde_fous_bus()]"
```

Les invariants issus de cette décision sont formalisés et tracés dans
`docs/architecture/invariants.md` : **I8** (graphe = donnée), **I9**
(déterminisme), **I10** (verrou de run), **I11** (`ApiIO` unique injectée),
**I12** (zéro logique métier), **I13** (reprise idempotente), **I18** (J6 non
activable).
