# Stratégie d'entreprise — Système Autonome de prospection B2B agentique
### Orchestration multi-agents · Chef de projet · Livrable consolidé
*Généré le 2026-07-30 — 14 sous-agents, 5 phases, 3 portes de revue anti-hallucination. Toutes les décisions structurantes ont reçu l'aval de l'agent de revue (verdict : approuvé avec réserves).*

---
## Sommaire
1. [Synthèse exécutive (chef de projet)](#1)
2. [Objectif 1 — Scénarios techniques & sélection](#2)
3. [Objectif 2 — Étude de marché (SWOT, PESTEL)](#3)
4. [Objectif 3 — Offre SaaS & chiffrage](#4)
5. [Objectif 4 — Plan d'implémentation](#5)
6. [Gouvernance & piste d'audit des revues](#6)

---
<a id="1"></a>
## 1. Synthèse exécutive — décision du chef de projet
# STRATÉGIE D'ENTREPRISE — COUCHE EXÉCUTIVE
## Système Autonome de Diagnostic Marketing / « Kemana-Flow »
### Décision de l'Agent Chef de Projet — 30 juillet 2026

---

## 1. EXECUTIVE SUMMARY

Nous industrialisons un actif déjà réel, pas une promesse. Le socle J1–J5 existe, tourne hors-ligne, et passe 365/365 tests. La décision structurante est prise et non rediscutée : **nous retenons le Scénario A (orchestrateur DAG déterministe « Kemana-Flow »)** comme colonne vertébrale et livrable immédiat, avec une **trajectoire en 3 paliers** qui greffe sélectivement le meilleur de B plus tard et gèle C jusqu'à preuve d'un besoin SaaS multi-tenant.

Trois vérités cadrent tout le reste :

1. **Le geste technique est mince et à faible risque.** Les 4 défauts AS-IS (budgets non câblés, `run_diagnostic` sans `api_io`, préflight NO-GO, orchestration absente) se corrigent par **un seul geste** — une instance `ApiIO` unique, budgets chargés depuis le YAML, injectée partout par l'orchestrateur — **sans réécrire aucune brique métier**. Les hooks d'injection existent déjà dans le code (`pipeline.py`, `api_io.py`). C'est du câblage, confirmé par lecture du dépôt.

2. **Deux pré-conditions dures encadrent TOUTE monétisation et tout run réel.** (a) **Phase D** : tant que `api_pricing.yaml = 0` et préflight NO-GO, aucun coût-par-fiche n'est engageant, aucune projection OPEX n'est ferme. (b) **Validation juridique + ESP conforme** avant toute activation de J6 (outreach), livré uniquement comme ossature human-gated non activable.

3. **Le marché valide l'angle, pas les chiffres.** L'étude confirme un quadrant vide et défendable — **haute conformité / débit modéré** — porté par l'échéance **AI Act art. 50 (transparence) au 2 août 2026**. Mais aucun chiffre de marché ne fonde la décision architecturale, et c'est voulu : la décision repose sur des faits AS-IS vérifiés, pas sur un TAM modélisé.

**Posture de gouvernance : les 3 revues ont rendu `approuvé_avec_réserves` (aval = true). Aucun aval bloquant (`aval=false`). Mais plusieurs réserves restent OUVERTES et sont des conditions de sortie, pas des acquis** (détail §4 et §5). Je les assume comme jalons, pas comme risques masqués.

---

## 2. LE FIL CONDUCTEUR : marché → scénario technique → offre SaaS → exécution

Ce projet tient parce que chaque maillon justifie le suivant sans rupture logique.

**Marché.** Le PESTEL et le SWOT situent une fenêtre réglementaire : durcissement de l'exécution RGPD sur l'outreach IA, entrée en vigueur AI Act art. 50 (transparence) au 2 août 2026, cadres CASL (QC) / nLPD + art. 3 LCD (CH) / RGPD (FR). Les concurrents (Apollo, Clay, AI SDR, Agentforce SDR, HubSpot) jouent le **contact-à-l'échelle**, cloud US, coût par siège, peu auditables ligne-à-ligne. Personne n'occupe le **diagnostic de marque conforme, frugal, auditable** pour micro-structures francophones. → *Le marché commande un produit à haute auditabilité et débit modéré assumé.*

**Scénario technique.** Ce positionnement exige déterminisme, traçabilité et OPEX plancher — exactement les propriétés natives de l'AS-IS (collecte déterministe, LLM confiné à la rédaction, bus vault source de vérité versionnée, bus `api_io` unique métré). Le Scénario A **prolonge** ces invariants au lieu de les casser. B ajouterait un superviseur-planificateur LLM (coût, non-déterminisme, charge cognitive) que je refuse à ce stade. C inverserait l'invariant J2 (vault → read-model) et imposerait 200–2 500 USD/mois d'infra pour une consultante solo. → *A est le seul dont « zéro réécriture métier » est crédible.*

**Offre SaaS.** Le produit se décline en deux visages : **Ligne A — Service** (revenu immédiat, auto-finançant, Palier 1) et **Ligne B — SaaS multi-tenant** (conditionnée au Palier 3). L'angle commercial dominant est le **compliance premium** : l'auditabilité ligne-à-ligne devient un argument réglementaire présent, pas un « nice-to-have ». Les trois promesses (« Zéro invention », « Facture prévisible », « Opposable en cas de contrôle ») sont chacune adossées à un mécanisme AS-IS vérifié, jamais à une aspiration. → *L'offre monétise une force existante, pas une roadmap.*

**Exécution.** Palier 1 = A intégral (orchestrateur + CLI + `dag_pipeline.yaml`, ~250–400 lignes, zéro logique métier). Palier 2 = greffe déterministe de B (nœud critique de grounding, nœud conformité-par-donnée, routage modèle YAML) SANS le superviseur LLM. Palier 3 = fragments de C (gateway par tenant, isolation, coût par tenant) conditionnés à un **seuil de tenants payants défini à l'avance**. → *La séquence protège le time-to-market sans hypothéquer l'avenir.*

Le fil est continu : **le marché exige la conformité auditable → l'architecture A la fournit nativement → l'offre la monétise en compliance premium → l'exécution la livre par paliers gouvernés par des seuils.**

---

## 3. SYNTHÈSE DE LA DÉCISION STRUCTURANTE ET DE SA JUSTIFICATION

**Décision retenue (autorité ultime, non rediscutée) :** Scénario A comme colonne vertébrale et livrable immédiat, hybridé en 3 paliers. Hybride assumé — ce n'est pas un compromis mou, c'est l'exploitation de la lecture correcte de la matrice.

**Pourquoi A, chiffré.** A domine la matrice (4,42/5) et gagne sur les 3 critères les plus lourds, qui sont précisément les contraintes cardinales d'une consultante solo devant industrialiser d'abord :
- Time-to-market (poids 18 %, note 5)
- OPEX (poids 15 %, note 5)
- Complexité d'exploitation (poids 14 %, note 5)

B arrive à 3,56/5, C à 2,52/5.

**Pourquoi hybride et pas A pur.** B n'est pas un concurrent frontal de A : c'est sa suite. Il apporte deux briques à forte valeur, nécessaires **avant** l'activation réelle de J6 : (a) la revue croisée de grounding, (b) la conformité-par-donnée (meilleure du panel, note 5 sur le critère conformité). Je les importe comme **nœuds/données du DAG A**, en **refusant explicitement le superviseur-planificateur LLM de B** — sa principale source de coût, de non-déterminisme et de charge cognitive, et le point exact où B perd contre A.

**Pourquoi C est écarté (au stade actuel).** Dernier sur les 3 critères majeurs ; coût fixe 200–2 500 USD/mois contre ~0 en AS-IS ; besoin DevOps/SRE absent en interne ; et surtout **inversion de l'invariant J2** (le vault n'est pas un read-model, il EST la source de vérité versionnée). Le rejet n'est pas une perte : les idées isolables (gateway par tenant, isolation, coût par tenant) sont récupérables au Palier 3 sans le bus d'événements ni l'event-sourcing.

**Décisions structurantes verrouillées :**
1. Créer `orchestrator.py` (tri topologique déterministe, zéro logique métier), `run_pipeline.py` (CLI unique), `dag_pipeline.yaml` (graphe = donnée). Chaque nœud enveloppe un `run_*.py` existant. Rétro-compat CLI préservée.
2. Instance `ApiIO` UNIQUE en tête de DAG, budgets chargés depuis `api_pricing.yaml`, injectée dans discovery, diagnostic ET outreach.
3. **Garde-fou AST étendu** à `orchestrator.py` + `run_pipeline.py` AVANT activation. Condition non négociable : nouveaux tests verts EN PLUS des 365.
4. Verrou de run (lockfile/run_id unique) contre tout démarrage concurrent (cron + manuel) sur le même vault.
5. Machine à états intangible : l'orchestrateur n'exécute QUE `decouvert → diagnostique`. Les transitions `valide/contacte/rejete` restent humaines via Obsidian. Reprise idempotente.
6. J6 livré comme **ossature human-gated non activable** — jamais présenté comme opérationnel.
7. Séquence topologique **strictement séquentielle** : le symbole ∥ (export ∥ outreach « en parallèle ») est retiré de la spécification retenue (incohérence de revue tranchée).

---

## 4. PISTE D'AUDIT DE LA GOUVERNANCE DE REVUE

Trois revues indépendantes ont été conduites. **Toutes ont rendu `approuvé_avec_réserves`, aval = true. Aucun `aval=false`.** Traçabilité :

| Revue | Verdict | Aval | Hallucinations détectées | Traitement dans la décision |
|---|---|---|---|---|
| **Revue Scénarios** | approuvé_avec_réserves | ✅ true | 3, **toutes concernant EXCLUSIVEMENT le Scénario C** (tarifs vendeurs pseudo-sourcés apiserpent/warmly ; inversion vault/event-store ; KPI grounding ≥98 % par LLM faillible) | **Neutralisées de facto par le rejet de C.** Aucun chiffre tarifaire fabriqué n'entre dans la décision. |
| **Revue Marché** | approuvé_avec_réserves | ✅ true | 5 (attribution Salesforce Piper/Hunter erronée ; « convergence » SAM surestimée ; TAM composite 5–8 Md non justifié ; « 67 % autorités UE » non sourçable ; « consensus 43–46 % » faux) | **Périphériques à la décision** — aucun chiffre de marché ne fonde l'architecture. Corrections exigées AVANT diffusion externe (voir §5). |
| **Revue Offre/Plan** | approuvé_avec_réserves | ✅ true | 4 incohérences chiffrées (marge 85–90 % vs COGS haut ; ARPU USD/EUR non réconcilié ; ARPU implicite variable ; coût-par-fiche vs COGS plafonné) | Chiffres **explicitement étiquetés ESTIMATION MODÉLISÉE, non-engageants avant Phase D.** Corrections exigées avant toute décision de tarification réelle. |

**Réserves LEVÉES par décision structurante :**
- *Réserve OPEX (projections non validées)* → LEVÉE : Phase D obligatoire avant toute décision budgétaire. Fourchettes étiquetées ESTIMATION MODÉLISÉE, aucun engagement de coût fixe.
- *Réserve « 365 tests = cible, pas état »* → LEVÉE et transformée en condition dure : garde-fou AST étendu + nouveaux tests verts exigés avant activation. Non-régression = critère de sortie.
- *Incohérence A (export ∥ outreach)* → TRANCHÉE : séquentiel strict, symbole ∥ retiré.
- *Réserve C (coût fixe + migration event-store)* → LEVÉE par le rejet de C et son conditionnement à un seuil de tenants payants.
- *Réserve conformité (grounding sur-promis)* → TRAITÉE au Palier 2 par contrôle DÉTERMINISTE (chaque affirmation du mini-audit doit référencer une faille de `diag.failles`) + échantillonnage humain, pas le seul verdict LLM.

**⚠️ RÉSERVES QUI RESTENT OUVERTES (non levées — jalons à franchir) :**
1. **Phase D non faite** — `api_pricing.yaml = 0`, préflight NO-GO structurel. **Blocage dur** de tout run réel ET de toute projection OPEX. Statut : OUVERT, dépend de l'opératrice.
2. **Validation juridique CASL/nLPD+art.3 LCD/RGPD/AI Act + ESP conforme** — condition d'activation J6. Statut : OUVERT, aucun envoi autorisé.
3. **Corrections chiffres offre/plan** (devise pivot unique, table de sensibilité marge, ARPU constant, réconciliation coût-par-fiche/COGS) — OUVERT, requis AVANT toute décision de tarification réelle.
4. **Correction attribution concurrentielle** (retirer Salesforce Piper/Hunter → Agentforce SDR uniquement ; réconcilier prix Apollo ; corriger « MRR annualisé » → ARR) — OUVERT, requis AVANT toute diffusion externe (investisseur/partenaire). Seule erreur factuelle dure et embarrassante.
5. **Non-régression 365 + nouveaux tests** — cible à atteindre, vérifiable seulement après écriture du code Palier 1.

**Point non-halluciné confirmé par les 3 revues :** la correction des 4 défauts AS-IS via l'unicité de l'instance `ApiIO` injectée est réelle et techniquement atteignable. Ce point est solide.

---

## 5. RISQUES MAJEURS ET ARBITRAGES

| # | Risque | Gravité | Arbitrage / mitigation (décision) |
|---|---|---|---|
| R1 | **Dérive de périmètre** : le câblage Palier 1 glisse vers de la logique métier → casse l'estimation ~40 sem. et la revendication « zéro réécriture » | Élevée | **Frontière dure** : orchestrateur = tri topologique + injection, zéro métier. Toute logique va dans un nœud existant. Revue de diff obligatoire. |
| R2 | **Bus factor 1** (1 dev temps partiel) sur toute la timeline | Élevée | Assumé. Mitigé par la minceur du geste et par le gel du Palier 3. Documentation + tests comme filet. |
| R3 | **Goulot humain non industrialisé** (porte `diagnostique → valide`) | Structurelle | **ASSUMÉ par conception** (manage-by-exception). On n'industrialise PAS la validation. Débit amont piloté par les budgets, jamais survendu au niveau système. |
| R4 | **Hallucination J1** via contenu scrapé injecté au LLM | Moyenne | Palier 2 : nœud critique déterministe (grounding sur `diag.failles`) + échantillonnage humain. Grounding reste étiqueté ESTIMATION MODÉLISÉE, jamais « ≥98 % ». |
| R5 | **Chiffres business incohérents** cités hors contexte comme engageants | Moyenne | Discipline ESTIMATION MODÉLISÉE maintenue. Aucun chiffre business exposé à un prospect avant Phase D preflight GO. Corrections §4 avant tarification. |
| R6 | **Activation J6 prématurée** sans cadre juridique | Élevée (légale) | J6 non activable par construction. Double verrou : validation juriste + ESP conforme. Jamais présenté comme opérationnel. |
| R7 | **Propagation d'erreur SAM/TAM** (facteur ≥10x) prise pour validation croisée | Faible (péri.) | Vocabulaire « convergence » abandonné → « cadrage à un ordre de grandeur ». Populations d'acheteurs = hypothèses de travail, jamais assises d'engagement. |
| R8 | **Run concurrent** (cron + manuel) corrompt le vault | Moyenne | Lockfile/run_id unique refusant le second démarrage. |

**Arbitrage cardinal :** je privilégie **time-to-market + déterminisme + OPEX plancher** sur le débit et l'échelle. C'est cohérent avec le marché (quadrant haute conformité / débit modéré) et avec la structure (solo). Toute pression future vers le volume passe par le Palier 3 gouverné par seuil, jamais par une entorse à l'invariant J2.

---

## 6. PROCHAINES ACTIONS — 30 / 60 / 90 JOURS

### J+30 — Fondation technique + déblocage Phase D (Palier 1 amont)
- **[Dev]** Créer `orchestrator.py`, `run_pipeline.py`, `dag_pipeline.yaml`. Instance `ApiIO` unique, budgets chargés depuis YAML, injectée partout. Fix 1-ligne `run_diagnostic.py`.
- **[Dev]** Étendre `_check_garde_fous_bus` (préflight) à `orchestrator.py` + `run_pipeline.py`. Écrire les nouveaux tests. **Cible : 365 + nouveaux, tous verts.**
- **[Dev]** Verrou de run (lockfile/run_id).
- **[Opératrice — Phase D]** Renseigner `SERP_API_KEY`, `APOLLO_API_KEY` ; relever les vrais tarifs → `prix_par_unite`, `releve_le`, `budgets > 0` dans `api_pricing.yaml`. Puis `python run_preflight.py` → **exiger GO**.
- **[Chef de projet]** Corriger l'attribution concurrentielle (retirer Piper/Hunter → Agentforce SDR) et « MRR annualisé » → ARR dans tout document sortant. *Lève réserve ouverte n°4.*

### J+60 — Premier run réel gouverné + hygiène business
- **[Run]** Après GO préflight : `python run_discovery.py --icp persona1-quebec --dry-run`, puis run réel borné par budgets. Vérifier corrélation `run_id` bout-en-bout (`runs.log` ↔ `api_usage.log`).
- **[Dev — Palier 2 amorce]** Nœud critique de grounding (déterministe) entre synthèse et transition ; `routing.yaml` (Haiku par défaut, modèle fort réservé aux cas signalés).
- **[Chef de projet]** Fixer devise pivot unique pour tout le chiffrage ; publier table de sensibilité marge (COGS bas/médian/haut → marge → LTV → LTV:CAC) ; ARPU constant. *Lève réserve ouverte n°3, débloque toute tarification réelle.*
- **[Juridique — amont J6]** Engager le juriste sur le cadre CASL/nLPD+art.3 LCD/RGPD/AI Act. Présélection ESP conforme. *Aucune activation.*

### J+90 — Pilote consolidé + conformité-par-donnée (Palier 2)
- **[Dev — Palier 2]** Nœud conformité bloquant en amont d'export/outreach, alimenté par `compliance/*.yaml` par marché. Ossature `OutreachAgent` human-gated (non activable).
- **[Run]** Pilote Québec consolidé : mesurer le débit amont réel vs budgets, instrumenter `taux_conversion_etats` (sinon toute la valeur économique du Palier 1 reste non mesurée — réserve honnête de l'étude).
- **[Chef de projet]** Porte de décision : OPEX réel (post-Phase D) remplace les estimations modélisées. Définir **à l'avance le seuil de tenants payants** déclenchant l'évaluation du Palier 3 (fragments de C). Ne pas ouvrir C avant ce seuil.
- **[Gouvernance]** Revue des 5 réserves ouvertes : n'en clore aucune sans preuve (préflight GO archivé, tests verts, avis juridique écrit, documents corrigés).

---

### Signalement final de gouvernance
**Aucun aval de revue n'est resté à `false`.** Les trois revues sont favorables sous réserves. **Cinq réserves restent explicitement NON LEVÉES** (§4) et sont traitées comme jalons de sortie, pas comme risques masqués : Phase D (blocage dur), validation juridique + ESP (J6), corrections chiffres offre/plan (avant tarification), correction attribution concurrentielle (avant diffusion externe), non-régression 365 + nouveaux tests (vérifiable après code). Tant que Phase D n'est pas GO, **aucune projection OPEX/coût-par-fiche n'est engageante et aucun run réel n'est autorisé.**

— *Agent Chef de Projet, autorité ultime sur les décisions structurantes.*

---
<a id="2"></a>
## 2. Objectif 1 — Scénarios techniques alternatifs & sélection
### 2.1 Critères de sélection pondérés
| Critère | Poids | Justification |
|---|---|---|
| Time-to-market vs existant (reutilisation AS-IS, effort de livraison) | 18% | Priorite n1 pour une micro-structure solo qui doit INDUSTRIALISER d'abord : chaque semaine passee a re-architecturer est une semaine sans prospection. Le socle J1-J5 (365 tests verts) est un actif ; le critere recompense la couche additionnelle la plus mince et le moindre risque de regression. |
| OPEX / cout LLM et cout d'infrastructure | 15% | Contrainte forte explicite (OPEX plancher). Couvre le cout variable par fiche (tokens Claude + SERP/Apollo/Places) ET le cout FIXE d'infrastructure, qui est le vrai discriminant entre un systeme batch hors-ligne (~0 fixe) et un cloud-native multi-tenant. |
| Complexite d'exploitation (charge pour une operatrice solo, bus factor) | 14% | Une consultante solo n'a ni SRE ni DevOps. Le systeme doit rester exploitable en manage-by-exception. Penalise l'ajout de bus d'evenements, RAG, observabilite distribuee, control plane que personne ne peut operer en interne. |
| Determinisme / auditabilite | 13% | Contrainte forte explicite et pilier de l'architecture (vault source de verite, runs.log + api_usage.log, regle d'or 'le LLM ne fetch jamais'). Condition de l'audit reglementaire et du debogage. Recompense la reproductibilite et la tracabilite bout-en-bout. |
| Conformite RGPD / CASL / nLPD / art.3 LCD / AI Act | 13% | Non negociable : la prospection B2B trans-juridictionnelle (QC->CH->FR) et l'outreach J6 exposent a sanction. Recompense l'opt-out absolu, la porte humaine, la minimisation (Apollo only, Contact 6 champs) et surtout la formalisation des politiques par marche et de la transparence AI Act. |
| Risque technique (regression, migration, modes de panne) | 12% | Le capital du projet est les 365 tests verts et les invariants de bus. Penalise toute approche a fort risque de casser ces contrats (ex. migration vault->event store) ou multipliant les modes de defaillance sans equipe pour les absorber. |
| Scalabilite / trajectoire SaaS multi-tenant | 10% | Objectif secondaire mais reel (productiser en SaaS). Pondere modestement car premature au stade actuel (mono-operatrice, aucun tenant payant) : recompense la capacite a evoluer sans refonte, sans exiger l'infrastructure tout de suite. |
| Differenciation marche / valeur produit | 5% | Pertinent seulement a la bascule produit. Faible poids car, pour une micro-structure, la valeur immediate vient de l'execution de la prospection, pas d'un differenciateur technique. Recompense les capacites vendables (qualite par revue, conformite multi-marche, temps quasi-reel). |

### 2.2 Matrice de décision (notes /5, total pondéré /5)
| Scénario | Total pondéré |
|---|---|
| Scenario A — Orchestrateur DAG deterministe (Kemana-Flow) | **4.42** |
| SCOP-H — Superviseur hierarchique multi-agents | **3.56** |
| Scenario C — Nerf central evenementiel, cloud-native multi-tenant | **2.52** |

**Recommandation analytique :** Recommandation : adopter le Scenario A (Orchestrateur DAG deterministe / Kemana-Flow) comme chemin par defaut immediat. Total pondere 4,42/5, en tete sur 6 des 8 criteres, dominant sur les 3 plus lourds (time-to-market 18%, OPEX 15%, complexite d'exploitation 14%). Il correspond exactement au mandat AS-IS : industrialiser d'abord, a risque et cout minimaux, en corrigeant d'un seul geste architectural les 3 defauts connus (ApiIO unique injecte -> budgets cables au runtime + run_diagnostic dote d'api_io + orchestration bout-en-bout), preflight en pre-condition resolvant le NO-GO une fois api_pricing.yaml renseigne (Phase D).\n\nSCOP-H (B, 3,56/5) n'est PAS un concurrent frontal de A mais sa suite logique : il apporte deux briques a forte valeur que A n'a pas — la revue croisee de grounding (agent Critique) et la conformite-par-donnee (politiques CASL/nLPD/RGPD/AI Act en YAML). A retenir comme increment de qualite/conformite, pas comme refonte.\n\nScenario C (2,52/5) est disqualifie AU STADE ACTUEL : dernier sur time-to-market, OPEX et complexite (les 3 criteres majeurs), a cause d'un cout fixe d'infrastructure (ESTIMATION MODELISEE ~200-2500 USD/mois selon la spec) et d'un besoin DevOps/SRE incompatibles avec une operatrice solo sans tenants payants. Il ne doit etre reconsidere que conditionnellement, a un seuil de tenants payants defini a l'avance (bascule produit avere), et ses bonnes idees (event store rejouable, isolation par tenant, cout par tenant temps-reel) restent des cibles futures, pas des choix presents.\n\nGarde-fou : tous les chiffres OPEX cites proviennent des payloads de scenarios et restent des ESTIMATIONS MODELISEES tant que api_pricing.yaml est a 0 ; aucune decision d'engagement de cout fixe ne doit etre prise avant le releve reel de la Phase D.

**Hybridation possible :** Oui — l'hybridation est nettement preferable a un choix pur, sous forme d'une trajectoire en 3 paliers plutot que d'un arbitrage unique.\n\nPALIER 1 (maintenant, base = Scenario A integral) : livrer l'orchestrateur DAG deterministe, la CLI unique, le dag_pipeline.yaml, l'ApiIO unique injecte, l'amorce J6 human-gated. Corrige les 4 defauts AS-IS, conserve 365/365 tests, OPEX plancher. C'est le socle non negociable.\n\nPALIER 2 (des que le pilote tourne, greffe selective de B sur le socle A — SANS le superviseur LLM) : importer les deux briques les plus rentables de SCOP-H comme noeuds/donnees du DAG existant : (a) l'agent Critique de grounding QA place entre le noeud synthese et la transition diagnostique, pour durcir 'aucune affirmation non adossee' avant J6 ; (b) la conformite-par-donnee : politiques compliance/*.yaml par marche (CASL-QC, nLPD+art.3 LCD-CH, RGPD-FR, transparence AI Act) et un noeud Conformite bloquant en amont d'export/outreach ; (c) le routeur de modele YAML (Haiku redaction/critique, modele fort reserve aux cas signales) pour piloter l'OPEX par la donnee. On garde le planificateur DETERMINISTE du DAG (on n'adopte PAS le superviseur-planificateur LLM de B, principale source de cout et de non-determinisme) — on ne prend de B que ce qui ajoute qualite et conformite sans rogner le determinisme ni le time-to-market.\n\nPALIER 3 (conditionnel, uniquement a la bascule SaaS averee avec tenants payants) : n'emprunter a C que ce qui est indispensable et isolable — d'abord la gateway api_io promue en service metre/budgete par tenant (extension naturelle du bus existant, faible risque), l'isolation par tenant et le reporting cout par tenant. Reporter le bus d'evenements, l'event sourcing et le RAG au moment ou le volume et le nombre de tenants les justifient economiquement. Declencher ce palier sur un seuil de tenants defini a l'avance, pas sur une intuition.\n\nEn resume : A comme colonne vertebrale, B en greffe qualite/conformite sur cette colonne, C reserve et fragmente pour la seule phase produit. Cette progression preserve a chaque etape le determinisme, l'auditabilite et les 365 tests, tout en payant la complexite seulement quand la valeur correspondante est avere.

#### Détail des notations par critère

**Scenario A — Orchestrateur DAG deterministe (Kemana-Flow)** — total 4.42/5

| Critère | Note /5 | Commentaire |
|---|---|---|
| Time-to-market vs existant (reutilisation AS-IS, effort de livraison) | 5 | Le plus proche de l'AS-IS : ~1 orchestrateur + 1 CLI + 1 YAML (~250-400 lignes estimees par la spec), zero reecriture des briques J1-J5, 365 tests preserves. Chaque noeud enveloppe un run_*.py existant. Livrable en jours, pas en semaines. Meilleur du panel. |
| OPEX / cout LLM et cout d'infrastructure | 5 | OPEX plancher : LLM marginal (2 points terminaux, synthese + brouillon J6), repli deterministe hors-ligne, cache api_io, budgets bloquants, infra quasi nulle (batch sur un poste/petite VM, aucun service permanent). Fixe ~0. Cout variable estime a quelques centimes/fiche (ESTIMATION MODELISEE, non confirmee tant que api_pricing.yaml=0). |
| Complexite d'exploitation (charge pour une operatrice solo, bus factor) | 5 | Un seul point d'entree (run_pipeline.py), reprise idempotente, manage-by-exception via Obsidian inchange. Aucune competence nouvelle requise. Observabilite basique (journaux fichiers) suffisante pour un pilote. Bus factor 1 assume mais procedures reprenables. |
| Determinisme / auditabilite | 5 | Determinisme maximal : hors les 2 noeuds de redaction, tout est reproductible. run_id correle runs.log et api_usage.log ; toute fiche exportee est tracable jusqu'a sa source. Garde-fous AST etendus aux 2 nouveaux modules. Reference du panel sur ce critere. |
| Conformite RGPD / CASL / nLPD / art.3 LCD / AI Act | 4 | Solide par construction : opt-out absolu, porte humaine avant tout envoi, minimisation Apollo, zero scraping LinkedIn. Limite : pas de moteur de conformite formalise ni de politique par marche en donnee ; la transparence AI Act (profilage) reste implicite/manuelle. Suffisant pilote, a durcir avant J6 reel. |
| Risque technique (regression, migration, modes de panne) | 5 | Risque minimal : couche additive, aucune migration de donnees, invariants de bus preserves. Reprise idempotente sur interruption. Seul point de vigilance (lockfile anti-concurrence cron+manuel) est trivial a mitiger. |
| Scalabilite / trajectoire SaaS multi-tenant | 2 | Batch sequentiel, mono-vault, mono-operatrice. Pas de parallelisme massif ni multi-tenant. Le passage SaaS exigerait une refonte de la couche d'ordonnancement. Convient a l'industrialisation, pas a la productisation a l'echelle. |
| Differenciation marche / valeur produit | 2 | Peu differenciant en tant que tel : orchestrateur DAG interne, pas de capacite vendable evidente (temps reel, multi-tenant). La valeur est l'efficacite operationnelle de la consultante, non un argument produit. |

**SCOP-H — Superviseur hierarchique multi-agents** — total 3.56/5

| Critère | Note /5 | Commentaire |
|---|---|---|
| Time-to-market vs existant (reutilisation AS-IS, effort de livraison) | 3 | Reutilise les bus mais ajoute plusieurs composants nouveaux (superviseur, BudgetGovernor, agent Critique, routeur de modele, bus TaskContract, agent Conformite). Plus de surface a ecrire et tester que A. La spec elle-meme recommande un deploiement incremental — signe d'un effort superieur. |
| OPEX / cout LLM et cout d'infrastructure | 3 | LLM devient le poste dominant (redaction Sonnet + critique Haiku + planification superviseur). ESTIMATION MODELISEE de la spec : ~0,015-0,05 USD LLM/fiche avec caching/batch, ~0,08-0,25 USD/prospect total. Leviers reels (routing YAML, prompt caching, batch, repli deterministe) mais risque de derive si le superviseur boucle. Infra fixe reste faible (batch/local). |
| Complexite d'exploitation (charge pour une operatrice solo, bus factor) | 3 | Plus d'agents et de contrats a superviser ; risque de sur-ingenierie pour une solo, reconnu par la spec. Reste local/batch (pas d'infra cloud), donc gerable si deploye par increments avec dashboards Obsidian synthetiques, mais charge cognitive superieure a A. |
| Determinisme / auditabilite | 4 | Auditabilite renforcee (contrats journalises, tokens LLM du superviseur/critique metres dans le meme ledger). Revue croisee durcit la QA de grounding. Mais le superviseur-planificateur LLM introduit une variance de routage/planification absente de A ; repli deterministe disponible mais le mode nominal est moins reproductible. |
| Conformite RGPD / CASL / nLPD / art.3 LCD / AI Act | 5 | Meilleur du panel : agent Conformite dedie et bloquant, politiques par marche en YAML (casl/nlpd/rgpd), exigences AI Act declarees, double garde sur J6, opt-out absolu. La conformite devient une donnee versionnee et testable, pas une pratique implicite. |
| Risque technique (regression, migration, modes de panne) | 4 | Reutilise les bus tel quel (contrats preserves, pas de migration de donnees) donc regression limitee. Risque residuel : boucle de revue/superviseur non bornee, injection de prompt via contenu scrape, plus de pieces mobiles que A. Mitigeable (plafonds, sandboxing faits/instructions). |
| Scalabilite / trajectoire SaaS multi-tenant | 3 | Meilleure separation des responsabilites (superviseur/workers/bus) qui prepare un futur SaaS, et montee multi-persona/marche par YAML. Mais toujours mono-vault et batch : pas de multi-tenant natif ni de scale horizontal. Trajectoire, pas destination. |
| Differenciation marche / valeur produit | 4 | Qualite par revue croisee (grounding QA institutionnalise) et conformite multi-marche en donnee sont deux arguments produit tangibles et vendables a des clients soumis a CASL/nLPD/RGPD/AI Act, sans exiger l'infrastructure cloud de C. |

**Scenario C — Nerf central evenementiel, cloud-native multi-tenant** — total 2.52/5

| Critère | Note /5 | Commentaire |
|---|---|---|
| Time-to-market vs existant (reutilisation AS-IS, effort de livraison) | 1 | Chantier lourd : migration du vault fichier source-de-verite vers un event store avec vault en projection, bus d'evenements, RAG, control plane. La spec elle-meme signale un risque de regression sur les 365 tests et une migration non triviale. Delai en mois. |
| OPEX / cout LLM et cout d'infrastructure | 2 | Rupture par le cout FIXE : ESTIMATION MODELISEE de la spec ~200-400 USD/mois (frugal) a ~1500-2500 USD/mois (robuste multi-AZ) contre ~0 en AS-IS. Le variable reste competitif (~0,04-0,15 USD/prospect) mais le fixe disqualifie l'usage solo tant qu'il n'y a pas des dizaines de tenants payants. Le scenario l'admet. |
| Complexite d'exploitation (charge pour une operatrice solo, bus factor) | 1 | Exige des competences DevOps/SRE absentes en interne (bus, event sourcing, RAG, observabilite distribuee, secrets par tenant). Ingerable par une consultante solo. Pire du panel sur ce critere structurant. |
| Determinisme / auditabilite | 3 | Event store rejouable + trace_id OTel bout-en-bout + grand livre en flux = auditabilite native forte. MAIS le distribue asynchrone (ordre partiel, at-least-once, RAG non deterministe) rend la reproductibilite exacte plus difficile que A/B — recul sur une force cle de l'AS-IS. |
| Conformite RGPD / CASL / nLPD / art.3 LCD / AI Act | 4 | Moteur de conformite bloquant, opt-out absolu, isolation par tenant (partition/RLS/secrets), preflight en gate CI/CD. Solide. Mais la couche RAG/memoire vectorielle et le profilage a l'echelle AUGMENTENT la surface reglementaire (fuite inter-tenant, contenu obsolete injecte comme 'fait', profilage AI Act) — d'ou 4 et non 5. |
| Risque technique (regression, migration, modes de panne) | 2 | Migration a fort risque de regression sur les 365 tests ; multiplication des modes de panne (bus, DLQ, RAG, cache distribue) sans equipe pour les operer. Risque de derive OPEX sur boucle d'evenements mal maitrisee. Le plus expose du panel. |
| Scalabilite / trajectoire SaaS multi-tenant | 5 | Vraie scalabilite horizontale, multi-tenant de premiere classe, cout par tenant en quasi temps-reel, temps quasi-reel pour demandes a la volee. Seul scenario nativement pret pour un SaaS a l'echelle. Reference du panel sur ce critere. |
| Differenciation marche / valeur produit | 5 | Multi-tenant, temps quasi-reel, isolation et facturation par tenant, API tenant : c'est un produit SaaS, pas un outil interne. Differenciation maximale — mais seulement pertinente apres bascule produit avec tenants payants. |

### 2.3 Les trois scénarios en détail

#### Scénario 1 — Scénario A — Orchestrateur DAG déterministe (évolution incrémentale J1→J6, nom de travail « Kemana-Flow »)
**Paradigme.** Orchestration centralisée déterministe (DAG / pipeline). Un orchestrateur unique et explicite ordonnance des étapes déterministes enfichables (les agents J1/J4/J5 existants deviennent des nœuds du graphe). Le LLM (Claude) est strictement cantonné à la synthèse rédactionnelle (mini-audit J1, brouillon d'email J6) : il ne fetch jamais, ne décide jamais du routage. Le vault Obsidian et sa machine à états servent de « tableau noir » (blackboard) unique — il n'y a pas de bus de messages inter-agents supplémentaire, ce qui préserve l'architecture micro-ordinateur existante. C'est le scénario le plus proche de l'AS-IS : addition d'une fine couche d'ordonnancement au-dessus des cinq livrables, zéro réécriture des briques métier.

**Résumé.** Le système J1-J5 possède déjà toutes les briques déterministes (collecteurs, scoring, buses vault_io/api_io, export, préflight) mais aucune couche qui les enchaîne de bout en bout : chaque run_*.py est lancé à la main et run_diagnostic n'injecte même pas api_io. Ce scénario ajoute un unique module orchestrateur (DAG déterministe, ~1 nœud par run_*.py existant) qui exécute, dans un ordre topologique figé et journalisé, la chaîne préflight → découverte → diagnostic → [validation humaine] → export → outreach → snapshot usage. Le graphe est une DONNÉE (YAML), les nœuds sont des adaptateurs autour du code existant, et une seule instance ApiIO est créée en tête de DAG puis injectée partout — ce qui corrige d'un coup trois défauts AS-IS (budgets non câblés, run_diagnostic sans api_io, absence d'orchestration). La progression est pilotée par la machine à états du vault : chaque nœud est idempotent et reprend là où le précédent s'est arrêté, ce qui rend l'ensemble reprenable, auditable ligne à ligne (runs.log + api_usage.log) et compatible avec le cron J7. Le LLM reste marginal (synthèse + brouillon email), garantissant un OPEX plancher et un déterminisme quasi total. J6 (outreach) est ajouté comme dernier nœud, avec porte humaine obligatoire avant tout envoi (CASL/nLPD/RGPD).

**Architecture.**

COUCHES (de bas en haut, alignées sur l'analogie micro-ordinateur existante) :

1. Couche DONNÉES / ROM — inchangée : rubric_*.yaml, icp/*.yaml, api_pricing.yaml, export_kemana.yaml, + NOUVEAU dag_pipeline.yaml (définition déclarative du graphe : nœuds, dépendances, filtres d'état, budgets par nœud). Le DAG est une donnée, jamais du code — même principe que « la rubrique est une donnée ».

2. Couche BUS (contrôleurs uniques) — inchangée mais mieux exploitée : vault_io.py (bus stockage, écriture atomique, journal runs.log, machine à états) et api_io.py (bus réseau unique, cache, budgets, grand livre api_usage.log). NOUVEAUTÉ : une seule instance ApiIO est instanciée par l'orchestrateur au démarrage du DAG, avec les budgets chargés depuis api_pricing.yaml, puis passée par injection de dépendance à chaque nœud (découverte, diagnostic, outreach). Fin des instances ApiIO éparpillées et des budgets non appliqués.

3. Couche AGENTS / CPU (nœuds du DAG) — code existant réemballé : DiscoveryCollector+PersonEnrichment (J4), DiagnosticPipeline (J1), export (J5), usage (J5), + NOUVEAU OutreachAgent (J6). Chaque nœud expose un contrat uniforme : run(ctx) -> NodeResult, lit son état d'entrée dans le vault, écrit son état de sortie via vault_io, ne dépasse jamais sa transition autorisée.

4. Couche ORCHESTRATION — NOUVELLE, mince (~250-400 lignes) : orchestrator.py (chargement du DAG YAML, tri topologique déterministe, exécution séquentielle, gestion BudgetExceeded, reprise idempotente, journalisation d'un run_id corrélant runs.log ⇄ api_usage.log) + run_pipeline.py (CLI unique). L'orchestrateur ne contient AUCUNE logique métier : il branche, ordonne, journalise, s'arrête proprement. Exactement l'esprit de pipeline.py, hissé au niveau inter-agents.

5. Couche CONSOLE / porte humaine — Obsidian, inchangé : l'opératrice valide diagnostique→valide (manage-by-exception) et diagnostique→contacte n'est jamais automatique. L'orchestrateur s'arrête à la frontière humaine et reprend au run suivant.

FLUX DE DONNÉES (DAG, ordre topologique figé) :
preflight_gate (GO/NO-GO bloquant) → discovery [SERP→Apollo→fiches 'decouvert'] → diagnostic [fiches 'decouvert' → collecteurs+scoring+synthèse LLM → 'diagnostique' + rapport] → [PORTE HUMAINE Obsidian : 'diagnostique'→'valide'] → export [fiches 'valide' non opt_out → CSV/JSONL Kemana, lecture seule] ∥ outreach [J6 : 'valide' → brouillon email LLM → validation humaine → 'contacte'] → usage_snapshot [agrégat api_usage.log → vault/90-Systeme]. Les nœuds export et usage_snapshot sont sans effet de bord réseau ; discovery/diagnostic/outreach passent exclusivement par api_io.

OÙ VIT LE LLM : deux points, tous deux terminaux et non décisionnels. (a) synthesis.py — rédaction du mini-audit et de l'accroche à partir de faits DÉJÀ collectés (règle d'or J1 préservée). (b) OutreachAgent J6 — rédaction d'un brouillon d'email personnalisé à partir de la fiche 'valide' et de son diagnostic ; jamais envoyé sans revue humaine. Partout ailleurs : déterministe pur. Sans ANTHROPIC_API_KEY, repli déterministe → le DAG tourne hors-ligne (sauf collecte réseau).

INTERFACES : entrée = ICP YAML + déclencheur (CLI manuel ou cron J7) ; sortie = vault (source de vérité auditable), exports/ (livrables Kemana hors vault), api_usage.log (grand livre coûts), runs.log (journal opérations). Aucune API exposée : système batch, pas de service temps réel.

**Composants.**

- **orchestrator.py (NOUVEAU)** — Cœur du scénario. Charge le DAG depuis dag_pipeline.yaml, effectue un tri topologique déterministe, exécute les nœuds en séquence, instancie l'unique ApiIO (budgets depuis api_pricing.yaml) et l'injecte partout, attribue un run_id corrélant runs.log et api_usage.log, capture BudgetExceeded pour un arrêt propre, assure la reprise idempotente. Aucune logique métier.
- **run_pipeline.py (NOUVEAU)** — Point d'entrée CLI unique remplaçant l'enchaînement manuel des run_*.py. Ex. : python run_pipeline.py --icp persona1-quebec [--dry-run] [--depuis-etat decouvert] [--jusqu-a export]. Refuse de démarrer si le préflight est NO-GO (pré-condition cron J7).
- **dag_pipeline.yaml (NOUVEAU, DONNÉE)** — Définition déclarative du graphe : liste des nœuds, dépendances, filtre d'état d'entrée/sortie, plafond budgétaire par nœud, nœud humain (barrière). Ajouter/réordonner une étape = éditer le YAML, jamais le code — cohérent avec 'la rubrique/l'ICP est une donnée'.
- **preflight_gate (nœud, réutilise preflight.py J5)** — Premier nœud bloquant. Rejoue les 9 contrôles GO/NO-GO ; NO-GO ⇒ le DAG ne démarre pas. Garantit tarifs relevés, budgets > 0, clés présentes, vault initialisé, tests verts, garde-fous bus AST.
- **discovery (nœud, réutilise DiscoveryCollector + PersonEnrichment J4)** — SERP → candidates filtrées/dédupliquées → enrichissement Apollo → fiches 'decouvert' via vault_io. Reçoit l'ApiIO injecté (budgets serp/apollo appliqués). Dédup inter-runs via vault_io.exists(). Zéro LLM, zéro scraping LinkedIn.
- **diagnostic (nœud, réutilise DiagnosticPipeline J1)** — Traite les fiches 'decouvert' : collecteurs (website/seo/social/gbp/reviews) → scoring rubrique → synthèse LLM → transition 'decouvert'→'diagnostique' + rapport. CORRIGE le défaut AS-IS : reçoit l'ApiIO injecté (collecteurs palier 1 réellement câblés, tokens Claude métrés).
- **OutreachAgent + run logic (NOUVEAU, J6)** — Dernier nœud métier. Fiches 'valide' non opt_out → brouillon d'email personnalisé (LLM, à partir du diagnostic) → dépôt du brouillon dans le vault pour revue → après validation humaine, transition 'valide'→'contacte'. Séquence, cadence et gabarits = données YAML. Envoi réel derrière une porte humaine obligatoire (conformité).
- **export + usage (nœuds, réutilisent export.py / usage.py J5)** — export : fiches 'valide' non opt_out → CSV/JSONL Kemana hors vault, lecture seule, aucune transition. usage : agrège api_usage.log → snapshot vault/90-Systeme via write_system_note. Ferment le DAG par la couche d'audit.
- **vault_io.py (INCHANGÉ, bus stockage)** — Seul module écrivant le vault. Écriture atomique os.replace, journal append-only runs.log, validation Pydantic FicheProspect, machine à états gardée. L'orchestrateur ne contourne jamais ce bus : c'est le tableau noir partagé entre nœuds.
- **api_io.py (INCHANGÉ, bus réseau)** — Seul module réseau. Cache disque idempotent, budgets bloquants (BudgetExceeded avant l'appel), grand livre api_usage.log, registres recalculés depuis le ledger. Désormais instancié une seule fois par l'orchestrateur et injecté — élimine les états dupliqués.
- **cron J7 (planificateur, config)** — Déclenche run_pipeline.py sur une cadence bornée (ex. quotidienne/hebdomadaire), avec préflight en pré-condition dure. Traitement batch planifié : aucune boucle temps réel, OPEX prévisible.

**Interfaçage / intégrations.**

- SERP (fournisseur managé à retenir : SerpAPI / Bright Data / équiv.) — via api_io uniquement, endpoints search/maps/reviews, budget en requêtes.
- Apollo API (people_enrichment) — via api_io, budget en crédits, minimisation RGPD (Contact = 6 champs, contact_email_source obligatoire, zéro scraping LinkedIn).
- Google Places (text_search / place_details) — via api_io, collecteurs palier 1 gbp/reviews ; stub si GOOGLE_PLACES_API_KEY absente.
- Anthropic / Claude (messages) — via api_io, tokens métrés au grand livre ; synthèse J1 + brouillon email J6 ; repli déterministe hors-ligne si clé absente.
- Obsidian (console opérateur) — lecture/écriture du vault Markdown+frontmatter ; validation manage-by-exception des transitions humaines ; Dashboard Dataview (pipeline, top gaps, relances).
- Kemana (outil de campagne aval) — via fichiers d'export CSV utf-8-sig / JSONL déposés dans exports/ (hors vault) ; interface fichier, pas d'API.
- Fournisseur d'envoi email J6 (à choisir : ESP transactionnel/SMTP conforme) — derrière porte humaine ; branché sur api_io comme tout appel réseau ; NON activé tant que le cadre CASL/nLPD/RGPD n'est pas validé par un juriste.
- Vault (interface interne / tableau noir) — contrat FicheProspect Pydantic v2 ; frontmatter YAML ; runs.log JSONL comme journal inter-nœuds.
- api_usage.log + runs.log — interfaces d'audit machine (grand livre coûts, journal opérations) corrélés par run_id.
- Cron / planificateur système — interface de déclenchement du DAG, préflight en pré-condition.

**Exigences fonctionnelles.**

- EF1 — Orchestration déclarative : le DAG (nœuds + dépendances + filtres d'état + budgets) est défini dans dag_pipeline.yaml ; ajouter/réordonner une étape ne modifie aucun code.
- EF2 — Unicité de l'ApiIO : une seule instance ApiIO par exécution, budgets chargés depuis api_pricing.yaml, injectée dans discovery, diagnostic et outreach (corrige budgets non câblés + run_diagnostic sans api_io).
- EF3 — Idempotence & reprise : chaque nœud est reprenable ; relancer le DAG après interruption ne duplique ni fiche ni appel réseau (dédup vault + cache api_io).
- EF4 — Arrêt propre sur budget : BudgetExceeded interrompt le DAG sans corrompre l'état ; les fiches déjà écrites restent valides ; la ré-exécution reprend sous plafond.
- EF5 — Respect strict de la machine à états : l'agent n'exécute que decouvert→diagnostique et valide→contacte (après revue) ; toute autre transition est humaine ou lève ValueError.
- EF6 — Porte humaine explicite : le DAG s'interrompt à la frontière diagnostique→valide (validation Obsidian) et n'envoie jamais d'email sans revue humaine.
- EF7 — LLM cantonné : le LLM n'intervient que pour rédiger (mini-audit, accroche, brouillon email) à partir de faits établis ; il ne fetch pas, ne route pas, ne décide pas d'un score.
- EF8 — Mode dry-run global : run_pipeline --dry-run exécute et mètre les SERP (cache utile) sans aucune écriture vault ni envoi.
- EF9 — Traçabilité totale : chaque run possède un run_id corrélant runs.log (opérations) et api_usage.log (coûts) ; tout export est reproductible depuis le vault.
- EF10 — Pré-condition préflight : run_pipeline refuse de démarrer si le préflight est NO-GO ; --strict rend les tests bloquants.
- EF11 — Opt-out absolu : les fiches opt_out=true sont exclues de l'export ET de l'outreach, sans exception (RGPD/CASL/nLPD).
- EF12 — Planification cron : le DAG s'exécute en batch planifié, borné par les budgets, sans intervention manuelle une fois GO.
- EF13 — Sélection d'ICP et de bornes : run_pipeline --icp <id> [--jusqu-a <noeud>] [--depuis-etat <statut>] pilote la portée d'un run sans toucher au code.

**Spécifications atteintes.**

- S1 (J1 préservé) : la règle d'or 'le LLM ne fetch jamais' est renforcée — le LLM ne vit qu'aux nœuds synthesis et outreach ; test_j1_smoke et le contrat JSON Diagnostic restent intacts (aucune modification de pipeline.py ni des collecteurs).
- S2 (J2 respecté) : toute écriture passe par vault_io (os.replace atomique, runs.log append-only, FicheProspect validée) ; l'orchestrateur n'appelle jamais os.replace ni open() sur le vault — le garde-fou AST J2 reste vert.
- S3 (J3 exploité pleinement) : l'unicité de l'ApiIO honore enfin l'injection de dépendance prévue par la spec J3 ; budgets réellement appliqués ; api_usage.log devient la source de vérité coûts de tout le pipeline, pas seulement de la découverte.
- S4 (J4 réutilisé tel quel) : discovery reste zéro-LLM, dédup intra-lot par domaine normalisé, dédup inter-runs via exists(), Contact minimisé 6 champs — le nœud enveloppe run_discovery sans le réécrire.
- S5 (J5 réutilisé tel quel) : export lecture seule, opt_out absolu, exports hors vault ; usage --snapshot via write_system_note ; préflight 9 contrôles hissé au rang de premier nœud du DAG — garde-fous bus AST étendus aux 2 nouveaux modules (orchestrator, run_pipeline).
- S6 (défauts AS-IS corrigés) : (a) budgets injectés au runtime dans ApiIO ; (b) run_diagnostic/diagnostic reçoit api_io ; (c) préflight NO-GO résolu une fois tarifs relevés + budgets > 0 dans api_pricing.yaml ; (d) orchestration de bout en bout ajoutée.
- S7 (J6 amorcé) : l'ossature outreach est posée (nœud + états valide→contacte + brouillon LLM + porte humaine), prête à être activée après validation juridique — sans dette d'architecture.

**KPIs.**

| KPI | Cible |
|---|---|
| Taux de complétion du DAG (runs terminés sans erreur bloquante) | >= 95% des runs planifiés (ESTIMATION MODELISEE ; hypothèse : erreurs résiduelles = quotas API/timeouts, absorbées par reprise idempotente) |
| Verdict préflight GO avant chaque run réel | 100% (pré-condition dure ; un NO-GO bloque le run par conception) |
| Taux de réutilisation cache api_io (cache_hits / total appels) | >= 40-60% en régime établi (ESTIMATION MODELISEE ; hypothèse : re-diagnostics et rejeux fréquents sur un même ICP borné) |
| Fiches diagnostiquées par run (persona1-quebec, pilote borné) | 50-200 / run selon budgets (ESTIMATION MODELISEE ; hypothèse budgets pilote : serp ~500 requêtes, apollo ~50 crédits) |
| Couverture d'audit (fiches exportées traçables jusqu'au run_id source) | 100% (garanti par corrélation runs.log ⇄ api_usage.log ⇄ vault) |
| Déterminisme de la couche non-LLM (mêmes entrées → mêmes sorties, hors rédaction) | 100% des étapes collecte/scoring/export (le LLM est la seule source de variance, isolée aux 2 nœuds de rédaction) |
| Part d'appels LLM dans le total réseau | <= 15-25% des appels (ESTIMATION MODELISEE ; hypothèse : 1 appel synthèse / fiche, SERP+Apollo+Places dominant le volume) |
| Délai découverte→export d'une cohorte (hors latence humaine) | minutes à heures selon volume et quotas (ESTIMATION MODELISEE ; batch, non temps réel) |
| Taux de fiches bloquées par opt_out correctement exclues | 100% (invariant conformité, testé) |
| Régression tests | 365/365 conservés + nouveaux tests orchestrateur/J6 verts avant activation |

**Métriques opérationnelles.**

| Métrique | Définition |
|---|---|
| cout_par_fiche_diagnostiquee | Somme des coûts api_usage.log (SERP + Apollo + Places + tokens Claude) rapportée au nombre de fiches passées en 'diagnostique' sur le run. Sourcé du grand livre par run_id. |
| taux_cache_par_fournisseur | cache_hits / (cache_hits + appels) par fournisseur, issu de usage.agreger(). Indicateur direct de l'efficacité OPEX du bus api_io. |
| budget_consomme_vs_plafond | Pour serp/apollo/anthropic : unités consommées / unites_max configuré dans api_pricing.yaml. Déclenche l'alerte avant BudgetExceeded. |
| nb_appels_reseau_par_noeud | Décompte des LedgerEntry par nœud du DAG (via un champ contexte/run_id), pour localiser les postes de coût. |
| taux_conversion_etats | Ratios decouvert→diagnostique→valide→contacte, calculés depuis les transitions runs.log. Mesure le rendement du pipeline et le goulot humain. |
| duree_par_noeud | Temps mur de chaque nœud (journalisé par l'orchestrateur), pour repérer les étapes lentes (souvent I/O réseau/timeouts collecteurs). |
| nb_lignes_ledger_illisibles | usage.nb_erreurs_lecture — intégrité du grand livre append-only ; toute dérive signale une corruption à investiguer. |
| nb_reprises_idempotentes | Nombre de nœuds re-exécutés sans nouvel effet de bord (dédup/cache actifs). Valide la robustesse du redémarrage. |
| tokens_in_out_par_synthese | Moyenne input/output tokens par appel Claude (mesurer_anthropic), pilote le levier prompt caching / choix de modèle. |
| delta_preflight | Nombre et nature des checks échoués entre deux préflights — santé de la configuration (tarifs, budgets, clés, tests). |

**OPEX & leviers de réduction.** "POSTES DE COÛT (par ordre de contribution attendu, ESTIMATION MODELISEE) : 1) API de découverte/données — SERP (requêtes) + Apollo (crédits d'enrichissement) : poste dominant en volume, car 1 à N appels par candidate. 2) Google Places (palier 1, text_search/place_details) : quelques requêtes par fiche diagnostiquée. 3) Tokens Claude — synthèse J1 (~1 appel/fiche) + brouillon email J6 (~1 appel/fiche 'valide') : poste modeste en nombre d'appels mais sensible au modèle choisi. 4) Infra — quasi nul : le système tourne en batch sur un poste/petite VM, sans service permanent (pas de coût temps réel). 5) Exploitation humaine — temps de l'opératrice (validation manage-by-exception) : hors budget API mais réel.\n\nORDRE DE GRANDEUR MODELISÉ (à confirmer via le relevé api_pricing.yaml — AUCUN prix vendeur n'est inventé ici) : Hypothèses = 1 appel synthèse/fiche (quelques milliers de tokens in, ~1k out), 1-3 requêtes SERP/candidate, 1 crédit Apollo/contact, 2 requêtes Places/fiche. Sous ces hypothèses, le coût API par fiche diagnostiquée se situe vraisemblablement dans une fourchette basse de l'ordre de quelques centimes à quelques dizaines de centimes USD, dominé par Apollo/SERP, la part LLM restant minoritaire si l'on utilise un petit modèle pour la synthèse. Un pilote borné (budgets ~500 requêtes SERP + ~50 crédits Apollo) plafonne mécaniquement la dépense d'un run — c'est l'objet même des budgets bloquants. Les vrais chiffres ne seront connus qu'après saisie de prix_par_unite réels et releve_le dans api_pricing.yaml (Phase D).\n\nLEVIERS DE RÉDUCTION (par impact) : (a) CACHE api_io déjà en place — maximiser sa réutilisation (rejeux, re-diagnostics) est le levier n°1 ; viser 40-60% de cache_hits. (b) REPLI DÉTERMINISTE hors-ligne — sans ANTHROPIC_API_KEY, la synthèse retombe sur un rendu déterministe : coût LLM nul quand la qualité rédactionnelle n'est pas requise (ex. runs de test/volume). (c) CHOIX DE MODÈLE — cantonner la synthèse à un petit modèle (Haiku-classe) et réserver un modèle plus fort aux seuls brouillons outreach : réduit fortement le poste tokens ; à valider via claude-api. (d) PROMPT CACHING — la rubrique et les gabarits sont stables : mettre en cache la partie invariante du prompt réduit les input_tokens facturés (métré via cache_read_input_tokens déjà supporté par mesurer_anthropic). (e) BUDGETS BLOQUANTS — plafonds serp/apollo par run : garantissent qu'aucun run ne dérape, OPEX prévisible par conception. (f) DRY-RUN — valider une portée d'ICP sans écriture ni sur-consommation. (g) DÉDUP inter-runs — ne jamais re-payer un enrichissement déjà en vault (exists()). (h) CADENCE CRON BORNÉE — batch planifié plutôt que polling continu : pas de coût d'attente. (i) PALIERS DE COLLECTE — n'activer les collecteurs palier 1 (Places) que sur les fiches franchissant un seuil de score au palier 0, pour ne pas payer d'appels réseau sur des prospects non qualifiés."

**Forces.** Proximité maximale à l'AS-IS : la couche ajoutée est mince (~1 orchestrateur + 1 CLI + 1 YAML) ; les 365 tests et toute la logique métier restent intacts — risque d'intégration minimal, mise en œuvre rapide. ; Déterminisme fort : hors les 2 nœuds de rédaction LLM, tout le pipeline est reproductible ; les mêmes entrées produisent les mêmes sorties, ce qui facilite le débogage et l'audit. ; Auditabilité totale : run_id corrélant runs.log (opérations) et api_usage.log (coûts) ; toute fiche exportée est traçable jusqu'à sa source ; le vault est la source de vérité versionnée. ; OPEX plancher et prévisible : LLM marginal, cache réutilisé, budgets bloquants, repli hors-ligne — la dépense d'un run est plafonnée par conception. ; Conformité par construction : opt-out absolu, porte humaine avant tout envoi, minimisation RGPD (Apollo only, Contact 6 champs), aucun scraping LinkedIn — le cadre CASL/nLPD/RGPD est respectable sans réécriture. ; Correction naturelle des défauts AS-IS : l'unicité de l'ApiIO résout budgets non câblés + run_diagnostic sans api_io en un seul geste architectural. ; Reprise idempotente : un run interrompu (budget, quota, panne) redémarre sans duplication grâce à la dédup vault et au cache api_io. ; Séparation des préoccupations préservée : la rubrique/l'ICP/le DAG sont des données ; ajouter un persona, un marché ou une étape ne touche pas le code. ; Compatibilité cron J7 immédiate : préflight en pré-condition, batch borné — l'industrialisation planifiée est un simple branchement.

**Limites.** Rigidité du DAG : le graphe est figé par exécution ; aucun routage adaptatif ni décision dynamique (par choix — c'est le prix du déterminisme). Un cas nécessitant une branche conditionnelle riche devra l'exprimer en données, ce qui peut devenir verbeux. ; Débit borné par le séquencement : exécution essentiellement séquentielle et batch ; pas de parallélisme massif natif ni de traitement temps réel. Le passage à l'échelle SaaS multi-tenant demanderait une refonte de la couche d'ordonnancement. ; Goulot humain structurel : la porte diagnostique→valide (et la revue outreach) dépend de la disponibilité de l'opératrice ; le taux de conversion aval est plafonné par ce maillon manuel. ; Dépendance au vault comme unique tableau noir : convient à une micro-structure mono-opératrice ; l'accès concurrent multi-agents/multi-utilisateurs sur des fichiers Markdown n'est pas prévu (verrouillage limité). ; Qualité LLM non déterministe sur les 2 nœuds de rédaction : la synthèse et les brouillons email varient d'un run à l'autre ; la QA J1 limite le risque mais ne l'annule pas. ; J6 non finalisé : l'outreach est une ossature, pas un produit ; l'envoi réel exige un ESP conforme et une validation juridique préalable — non livrable en l'état. ; OPEX chiffré incertain tant que api_pricing.yaml n'est pas renseigné : toutes les projections restent des estimations modélisées jusqu'au relevé réel des tarifs. ; Observabilité basique : journaux fichiers (runs.log/api_usage.log) sans dashboard temps réel ni alerting proactif — suffisant pour un pilote, limite pour un run 24/7.

**Risques.** Conformité outreach (CASL au Québec, nLPD + art. 3 LCD en Suisse, RGPD + AI Act en France) : tout envoi J6 sans validation juridique préalable expose à des sanctions ; MITIGATION = porte humaine obligatoire, opt-out absolu, J6 désactivé tant que le cadre n'est pas validé par un juriste. ; Tarifs/budgets non renseignés (défaut AS-IS) : préflight NO-GO tant que api_pricing.yaml reste à 0 ; risque de blocage opérationnel ; MITIGATION = Phase D (relevé tarifs + releve_le + budgets > 0) avant premier run réel. ; Dérive de coût si le cache est peu efficace ou les budgets mal calibrés : un ICP trop large peut consommer vite ; MITIGATION = budgets bloquants par fournisseur, dry-run préalable, seuil de score avant palier 1. ; Qualité des données Apollo/SERP variable (emails obsolètes, faux positifs ICP) : dégrade le taux de conversion et le respect RGPD ; MITIGATION = contact_email_source tracé, filtres ICP, revue humaine. ; Fragilité des collecteurs face aux changements de sites/API tiers (structure HTML, quotas, SKU Places) : casse silencieuse ; MITIGATION = safe_collect isole les échecs, mode dégradé par collecteur, journalisation. ; Corruption/troncature du grand livre append-only sous interruption : fausse les coûts ; MITIGATION = nb_erreurs_lecture surveillé, écriture ligne par ligne, registres recalculés depuis le fichier. ; Introduction d'un import réseau/écriture directe dans les nouveaux modules (orchestrator, run_pipeline) : violerait les buses uniques ; MITIGATION = étendre le garde-fou AST J5 à ces 2 modules (test bloquant). ; Concurrence de deux runs simultanés sur le même vault (ex. cron + manuel) : écritures entrelacées ; MITIGATION = verrou de run (lockfile/run_id unique) refusant un second démarrage. ; Sur-confiance dans la synthèse LLM (affirmations non adossées aux faits) : risque réputationnel pour la consultante ; MITIGATION = QA J1 (aucune affirmation hors failles réelles) appliquée aussi aux brouillons J6. ; Dépendance à une opératrice unique (bus factor 1) : la porte humaine et l'exploitation reposent sur une personne ; MITIGATION = manage-by-exception via Obsidian, documentation CLAUDE.md, procédures reprenables.

#### Scénario 2 — SCOP-H — Superviseur Chef-de-Projet, Orchestration Hiérarchique B2B
**Paradigme.** Orchestration multi-agents hiérarchique : un agent superviseur "chef de projet" décompose la mission en contrats de tâche structurés (Pydantic/JSON), les route vers des sous-agents spécialisés semi-autonomes, et intègre une boucle de revue croisée (agent critique). Tout tool-use (réseau + LLM) transite par le bus api_io ; toute persistance par le bus vault_io. Le LLM est confiné aux tâches de rédaction et de revue ; la collecte reste déterministe (règle d'or J1 préservée).

**Résumé.** Scénario d'industrialisation qui coiffe l'existant J1-J5 d'une couche d'orchestration hiérarchique, sans réécrire les bus. Un superviseur (planificateur, LLM léger avec repli déterministe) alloue des budgets et des contrats de tâche descendants à des sous-agents qui encapsulent chacun un livrable existant : Découverte (J4), Collecte-Diagnostic (J1), Enrichissement (J4/Apollo), Rédaction (synthèse J1 LLM), Critique/QA (grounding), Conformité (CASL/nLPD/RGPD/AI Act), Export (J5), et Outreach (J6, planifié, human-gated). La communication passe par des messages contractuels validés et journalisés ; la revue croisée garantit qu'aucune affirmation n'échappe aux failles réelles. Le scénario corrige au passage les quatre défauts AS-IS : preflight en pré-condition de tout batch, budgets injectés au runtime dans ApiIO via un BudgetGovernor, api_io réellement injecté dans le pipeline diagnostic, et amorce J6 sous double garde conformité. Les priorités sont la montée en périmètre multi-persona/multi-marché (par ajout de YAML, zéro code) et la qualité par revue, avec un équilibre coût/capacité obtenu par routage de modèle (Haiku pour la revue/planification, Sonnet pour la rédaction, Opus réservé aux cas difficiles), prompt caching et mode batch.

**Architecture.**

Cinq couches, du bas (données) vers le haut (console), fidèles à l'analogie micro-ordinateur du projet.

COUCHE 0 — ROM / DONNÉES (lecture seule pour les agents) : rubrics YAML (knowledge/rubric_*.yaml), ICP YAML (icp/*.yaml), grille tarifaire (knowledge/api_pricing.yaml), config export (knowledge/export_kemana.yaml). AJOUTS planifiés, tous en YAML : (a) schémas de contrat de tâche, (b) politique de conformité par marché (compliance/casl-quebec.yaml, nlpd-ch.yaml, rgpd-fr.yaml) déclarant base légale, mentions obligatoires, fenêtres de contact, exigences de transparence AI Act, (c) matrice de routage de modèle (routing.yaml : tâche→modèle→budget). Principe existant préservé : "la rubrique/l'ICP est une donnée, jamais du code" — un nouveau persona/marché = un nouveau fichier.

COUCHE 1 — BUS (inchangée dans son contrat, durcie) : vault_io.py = seul module d'écriture stockage (écriture atomique os.replace, journal append-only runs.log, machine à états, schéma FicheProspect). api_io.py = seul module réseau (cache disque, budgets, grand livre api_usage.log). NOUVEAU : api_io devient l'unique "tool gateway" — les appels LLM du superviseur, de la rédaction ET de la critique passent tous par api_io.call(fournisseur="anthropic", ...), donc métrés au token dans le même ledger que SERP/Places/Apollo. Aucun sous-agent n'ouvre de socket ni n'appelle anthropic directement (garde-fou AST walk §9.6 étendu aux nouveaux modules d'agents).

COUCHE 2 — SOUS-AGENTS SPÉCIALISÉS (les "CPU workers") : chacun est un wrapper mince autour d'un livrable existant, exposant une interface uniforme execute(TaskContract)->TaskResult. Découverte, Collecte-Diagnostic, Enrichissement, Export et Conformité(volet déterministe) sont ZÉRO-LLM (respecte J4/J5). Rédaction et Critique sont les seuls consommateurs LLM. Chaque sous-agent reçoit api_io et vault_io par injection de dépendance (patron déjà en place dans DiagnosticPipeline.__init__(api_io=...)), et un sous-budget alloué par le superviseur.

COUCHE 3 — ORCHESTRATION (le superviseur "chef de projet") : reçoit une mission (ex. "traiter persona1-quebec, 200 prospects, plafond X USD"), exécute d'abord run_preflight (gate GO/NO-GO, pré-condition dure), puis planifie un DAG de contrats de tâche, alloue les budgets descendants via le BudgetGovernor, dispatche, collecte les TaskResult, pilote la boucle de revue (Rédaction→Critique→re-Rédaction, ≤1 itération par défaut), et escalade à l'humain les cas hors tolérance (manage-by-exception). Le superviseur est LLM-léger (Haiku) pour la planification en langage naturel, mais dégrade en planificateur déterministe (règles fixes du DAG) si ANTHROPIC_API_KEY absente — le système reste hors-ligne, comme aujourd'hui.

COUCHE 4 — CONSOLE (opérateur humain) : Obsidian reste la source de vérité et le poste de validation (Dataview : pipeline, top gaps, files d'escalade, budget consommé). Le superviseur n'exécute JAMAIS de transition réservée à l'humain (valide, contacte, rejete) sans validation console explicite.

FLUX DE DONNÉES (batch nominal) : preflight GO → Découverte (SERP via api_io → fiches 'decouvert' via vault_io) → pour chaque fiche : Collecte-Diagnostic (collecteurs déterministes, api_io injecté ; faits établis) → Rédaction (LLM rédige mini-audit+accroche à partir des faits, NE FETCH JAMAIS) → Critique (LLM vérifie le grounding : chaque affirmation adossée à diag.failles) → si rejet, renvoi avec feedback structuré ; sinon transition decouvert→diagnostique (seule transition agent autorisée) → Enrichissement (Apollo via api_io, Contact 6 champs, minimisation RGPD) → [console : humain valide diagnostique→valide] → Conformité (contrôle opt_out absolu + politique marché) → Export J5 (lecture seule → liste Kemana). J6 Outreach (valide→contacte) reste derrière double garde : feu vert Conformité + validation humaine.

OÙ VIT LE LLM : uniquement dans (1) le superviseur-planificateur (Haiku, repli déterministe), (2) l'agent Rédaction (Sonnet par défaut, Opus si cas signalé difficile), (3) l'agent Critique (Haiku). Zéro LLM dans Découverte, Collecte, Enrichissement, Export, et le noyau déterministe de Conformité. La règle d'or "le LLM ne fetch jamais" est structurellement garantie : le LLM n'a pas accès aux collecteurs, seulement aux faits déjà sérialisés (signaux + failles).

**Composants.**

- **Agent Superviseur (Chef de projet)** — Planifie la mission en DAG de contrats de tâche, alloue les budgets descendants, dispatche vers les sous-agents, pilote la boucle de revue et l'escalade humaine. LLM Haiku pour la planification NL, repli déterministe (DAG fixe) si pas de clé. Exécute run_preflight comme gate d'entrée.
- **BudgetGovernor** — Charge la section budgets: de api_pricing.yaml, la traduit en plafonds par fournisseur ET par contrat, et les injecte au runtime dans ApiIO(budgets=...). Corrige le défaut AS-IS 'budgets non injectés'. Allocation hiérarchique : un contrat ne peut dépenser au-delà de son sous-budget ; BudgetExceeded remonte proprement au superviseur.
- **Agent Découverte** — Wrapper de run_discovery.py (J4). SERP→candidates→fiches 'decouvert'. Zéro LLM, zéro scraping LinkedIn. Dédup intra-lot (domaine normalisé) et inter-runs (vault_io.exists). Honore --dry-run et BudgetExceeded (idempotent).
- **Agent Collecte-Diagnostic** — Wrapper de DiagnosticPipeline (J1) construit AVEC api_io injecté (corrige le défaut 'run_diagnostic sans api_io'). Lance les collecteurs déterministes (website/seo/social/gbp/reviews), applique la rubrique, produit un Diagnostic (faits + scores + failles). N'appelle pas le LLM lui-même.
- **Agent Rédaction** — Encapsule synthesis.synthesize() via api_io. Rédige mini-audit + accroche à partir des faits établis uniquement. LLM Sonnet par défaut, Opus si le contrat porte un flag 'difficulté'. Ne fetch jamais ; repli déterministe si pas de clé.
- **Agent Critique / QA** — Revue croisée LLM légère (Haiku) : vérifie que chaque affirmation du mini-audit est adossée à une faille réelle (diag.failles), détecte les sur-affirmations et hallucinations, renvoie un verdict {accepte|rejete, feedback}. Boucle ≤1 re-rédaction. Applique la règle J1 'aucune affirmation non adossée'.
- **Agent Enrichissement** — Wrapper de PersonEnrichment (J4/Apollo) via api_io. Contact = 6 champs (extra=forbid), contact_email_source toujours renseigné (audit RGPD). Zéro LLM, zéro scraping. Respecte max_enrichissements de l'ICP et le budget crédits.
- **Agent Conformité** — Noyau déterministe + LLM léger optionnel. Charge la politique du marché (casl/nlpd/rgpd YAML), impose l'exclusion opt_out absolue, vérifie mentions/base légale/fenêtres de contact et exigences de transparence AI Act avant tout export ou outreach. Bloquant : produit un feu rouge/vert horodaté.
- **Agent Export** — Wrapper de run_export.py (J5). Lecture seule, aucune transition, aucun réseau. Fiches 'valide' non opt_out → Kemana CSV/JSONL hors vault. Rapport d'anomalies. Garde-fou : refus si --out sous vault/.
- **Agent Outreach (J6, planifié)** — NON présent dans l'AS-IS — amorce du scénario. Séquence d'emails valide→contacte, strictement human-gated + feu vert Conformité. Utilise api_io pour l'envoi (nouveau fournisseur email métré), respecte la machine à états (transition contrôlée, double validation). Ne s'exécute pas sans validation juridique préalable.
- **Bus TaskContract / MessageBus** — Canal de communication inter-agents : contrats et résultats en Pydantic validés, échangés en mémoire et journalisés (append-only). Porte task_id, type, cible, inputs, budget_alloue, deadline, statut ; résultats : status, artefacts (refs fiches), cout, incidents. Aucune donnée métier n'échappe au schéma.
- **Routeur de modèle** — Lit routing.yaml (tâche→modèle→budget) et sélectionne Haiku/Sonnet/Opus + options (batch, prompt caching) par tâche. Découple le choix de modèle du code : rééquilibrer coût/capacité = éditer un YAML.

**Interfaçage / intégrations.**

- api_io.py comme unique tool gateway : Anthropic Messages (superviseur/rédaction/critique), SERP, Google Places (text_search/place_details), Apollo (people_enrichment), http (fetch statique). Cache, budget et ledger appliqués uniformément.
- vault_io.py : persistance Obsidian (Markdown + frontmatter YAML), écriture atomique, journal runs.log, machine à états, schéma FicheProspect.
- Console opérateur Obsidian : Dashboard Dataview étendu (pipeline, top gaps, file d'escalade, budget consommé temps réel, feux Conformité) ; validation manage-by-exception des transitions humaines.
- Export Kemana : CSV utf-8-sig (Excel FR) / JSONL, dossier exports/ hors vault, .gitignore, + rapport d'anomalies (J5).
- Grand livre api_usage.log (JSONL append-only) : source de vérité unique des coûts, désormais alimentée aussi par les tokens LLM du superviseur et de la critique (auditabilité complète).
- Secrets par variables d'environnement (ANTHROPIC_API_KEY, GOOGLE_PLACES_API_KEY, SERP_API_KEY, APOLLO_API_KEY) ; recommandation planifiée : coffre de secrets (vault applicatif / gestionnaire OS) plutôt que .env en clair.
- Orchestrateur planifié (cron J7) : déclenche un batch après run_preflight GO ; le superviseur est le point d'entrée du cron.
- Connecteurs SaaS optionnels pour la console (Airtable / Google Drive via MCP) en LECTURE/miroir uniquement — le vault Obsidian reste la source de vérité, jamais contourné pour l'écriture d'état.

**Exigences fonctionnelles.**

- Le superviseur DOIT exécuter run_preflight et obtenir GO avant tout batch réseau ; NO-GO = arrêt, aucune dépense.
- Tout appel réseau ou LLM DOIT passer par api_io.call() (budget + cache + ledger) ; aucun import requests/anthropic hors api_io (garde-fou AST étendu aux modules d'agents).
- Chaque tâche DOIT être portée par un TaskContract validé (Pydantic) et son résultat par un TaskResult validé ; échanges journalisés.
- Les budgets DOIVENT être injectés au runtime dans ApiIO depuis api_pricing.yaml, et alloués de façon hiérarchique (mission→contrat) ; BudgetExceeded remonte proprement, les fiches déjà écrites restent valides (idempotence).
- L'agent Rédaction NE DOIT jamais déclencher de collecte ; il ne consomme que des faits déjà établis (règle d'or J1).
- L'agent Critique DOIT valider le grounding de chaque affirmation contre diag.failles ; un rejet renvoie un feedback structuré et déclenche ≤1 re-rédaction.
- Les seules transitions d'état exécutées par un agent SONT decouvert→diagnostique ; valide, contacte, rejete restent réservées à la console humaine.
- L'agent Conformité DOIT exclure sans exception les fiches opt_out et bloquer l'export/outreach non conforme (CASL/nLPD/RGPD/AI Act).
- L'ajout d'un persona ou d'un marché NE DOIT nécessiter aucun changement de code : nouveaux fichiers YAML (ICP, rubric, politique conformité, routage) uniquement.
- Le système DOIT tourner hors-ligne sans clé LLM : superviseur déterministe + repli déterministe de la synthèse ; aucune régression sur les 365 tests existants.
- Le routage de modèle (Haiku/Sonnet/Opus, batch, caching) DOIT être piloté par YAML, sans toucher au code des agents.
- Toute exécution DOIT être auditable de bout en bout : journal vault (runs.log) + grand livre coûts (api_usage.log) + log des contrats/décisions du superviseur.

**Spécifications atteintes.**

- J1 préservé : le pipeline diagnostic reste la chaîne déterministe entrée→collecteurs→signaux→scoring→synthèse+QA ; le LLM ne fetch jamais. Le contrat JSON Diagnostic est inchangé (test_j1_smoke intact), la rubrique reste une donnée.
- J1 renforcé : la revue croisée (agent Critique) formalise et durcit la QA 'aucune affirmation non adossée aux failles réelles', avec boucle de correction traçable.
- J2 préservé : toute persistance passe par vault_io (écriture atomique, journal append-only, schéma FicheProspect) ; la machine à états est respectée, l'agent limité à decouvert→diagnostique, l'humain garde valide/contacte/rejete via Obsidian.
- J3 étendu proprement : api_io reste le bus réseau unique et devient le tool gateway des appels LLM eux-mêmes — les tokens du superviseur et de la critique sont métrés dans api_usage.log ; grille tarifaire et budgets restent des données YAML.
- J3 défaut corrigé : le BudgetGovernor injecte réellement les budgets au runtime dans ApiIO (plus seulement lus par preflight), avec allocation hiérarchique par contrat.
- J1/J3 défaut corrigé : l'agent Collecte-Diagnostic construit DiagnosticPipeline avec api_io injecté — le diagnostic est désormais métré et budgété (fin du 'run_diagnostic sans api_io').
- J4 préservé : Découverte et Enrichissement restent zéro-LLM, ICP en YAML, dédup intra/inter-runs, Contact 6 champs minimisé, dry-run métré, aucun scraping LinkedIn/Facebook.
- J5 préservé : Export lecture seule, opt_out absolu, exports hors vault, preflight GO/NO-GO comme pré-condition du cron ; signal_chaud reste dérivé dans les serializers.
- J5 défaut adressé : les prix/budgets à 0 (NO-GO) sont traités par la Phase D de paramétrage que le scénario impose comme étape 0, avec le superviseur qui refuse de démarrer tant que preflight n'est pas GO.
- J6 amorcé : l'agent Outreach fournit le squelette valide→contacte manquant, mais sous double garde (Conformité + humain) et sans envoi avant validation juridique — conforme à la trajectoire prévue dans CLAUDE.md.

**KPIs.**

| KPI | Cible |
|---|---|
| Taux de grounding QA (affirmations adossées à une faille réelle) | >= 98% après revue croisée (ESTIMATION MODELISEE ; mesuré par l'agent Critique, vérifiable par échantillonnage humain) |
| Débit de traitement (fiches diagnostiquées de bout en bout) | 30 à 80 fiches/heure en batch, dominé par la latence LLM et les quotas API (ESTIMATION MODELISEE ; dépend du fournisseur SERP/Places et du mode batch) |
| Taux d'escalade humaine (manage-by-exception) | < 15% des fiches (ESTIMATION MODELISEE ; cible de charge soutenable pour une consultante solo) |
| Taux de rejet par l'agent Critique (1re passe) | 10 à 25% initial, en baisse à mesure que rubriques/prompts se stabilisent (ESTIMATION MODELISEE) |
| Taux de succès du preflight avant batch | 100% des batchs lancés passent GO (contrainte dure, pas une moyenne) |
| Cache hit rate api_io (SERP/Places/Apollo) | > 40% en régime établi grâce à la dédup et aux ré-exécutions (ESTIMATION MODELISEE) |
| Coût API par prospect entièrement traité (découverte+diagnostic+rédaction+enrichissement) | 0,08 à 0,25 USD/prospect (ESTIMATION MODELISEE ; voir hypothèses OPEX) |
| Délai d'onboarding d'un nouveau marché (ex. Romandie, France) | < 1 jour-personne, zéro code (ajout de YAML ICP/rubric/conformité/routage) |
| Respect budgétaire (dépassements non contrôlés) | 0 dépassement silencieux — tout arrêt est un BudgetExceeded journalisé (contrainte dure) |

**Métriques opérationnelles.**

| Métrique | Définition |
|---|---|
| cout_par_fiche | Somme des coûts ledger (api_usage.log) attribués à une fiche via le champ 'fiche', tous fournisseurs confondus (LLM + SERP + Places + Apollo). |
| tokens_par_fiche | input_tokens + output_tokens (et cache_read/creation) agrégés pour la rédaction, la critique et la part superviseur imputable à la fiche. |
| cache_hit_rate | Part des appels api_io résolus par le cache disque (cache_hit=True) sur le total des appels, par fournisseur. |
| iterations_revue_moyennes | Nombre moyen de cycles Rédaction→Critique par fiche (cible <= 1,3). |
| taux_rejet_critique | Part des mini-audits rejetés au moins une fois par l'agent Critique. |
| budget_utilisation | Coût consommé / plafond alloué, par fournisseur et par contrat, calculé en continu par le BudgetGovernor. |
| latence_bout_en_bout | Temps entre l'entrée d'une fiche 'decouvert' et sa transition 'diagnostique', décomposé par étape (collecte, rédaction, revue). |
| taux_erreur_collecteur | Part des safe_collect en échec par collecteur (website/gbp/reviews/seo/social), révélant les paliers dégradés. |
| taux_escalade_humaine | Part des fiches routées vers la file de validation console au lieu d'un flux automatique. |
| opt_out_exclus | Nombre de fiches écartées à l'export pour opt_out=true (contrôle RGPD/CASL/nLPD, doit toujours être traçable). |
| transitions_par_etat | Compte des transitions par arc de la machine à états (via runs.log), pour surveiller que seul decouvert→diagnostique est automatisé. |
| preflight_resultat | Historique GO/NO-GO horodaté avec le détail des 9 contrôles, en amont de chaque batch. |

**OPEX & leviers de réduction.** STRUCTURE DES COÛTS. Le poste dominant est le LLM (rédaction + critique + planification superviseur) ; le réseau de collecte (SERP/Places/Apollo) est secondaire et fortement caché. Le socle J1-J5 tourne déjà hors-ligne, donc l'OPEX incrémental du scénario est essentiellement le coût des trois agents LLM plus les crédits API de découverte/enrichissement.

CHIFFRAGE LLM (SOURCE : tarifs Anthropic 2026 — Opus 4.8 5$/25$, Sonnet 4.6 3$/15$, Haiku 4.5 1$/5$ par million de tokens input/output ; batch -50%, prompt caching -90% sur l'input caché). ESTIMATION MODELISEE par fiche, hypothèses : rédaction Sonnet ~5k tokens input de faits + ~1,2k output ≈ 0,015$ + 0,018$ ≈ 0,033$ ; critique Haiku ~2k input + ~0,4k output ≈ 0,004$ ; planification superviseur amortie ≈ 0,002$/fiche. Soit ~0,03 à 0,05 USD LLM/fiche sans optimisation. Avec prompt caching de la partie stable (system + rubrique + templates, ~3k tokens à -90%) et mode batch pour les runs cron : fourchette abaissée à ~0,015 à 0,03 USD/fiche.

CHIFFRAGE COLLECTE (ESTIMATION MODELISEE — tarifs réels À RENSEIGNER en Phase D, actuellement à 0 dans api_pricing.yaml). Ordres de grandeur usuels : Google Places text_search + place_details ~2 requêtes/fiche, de l'ordre de 0,03 à 0,08$ ; SERP amorti sur le lot (0,001 à 0,015$/recherche selon fournisseur) ; Apollo enrichissement ~1 crédit/fiche, ~0,02 à 0,10$ selon plan. Total collecte ~0,05 à 0,20 USD/prospect. TOTAL bout-en-bout : ~0,08 à 0,25 USD/prospect (cohérent avec le KPI). Pour un pilote de 500 prospects/mois : ESTIMATION ~40 à 125 USD/mois d'API. À confirmer une fois les tarifs relevés.

LEVIERS DE RÉDUCTION. (1) Routage de modèle par YAML : Haiku pour critique/superviseur, Sonnet pour la rédaction, Opus réservé aux cas signalés difficiles — évite de payer Opus par défaut. (2) Prompt caching : mettre en cache system+rubrique+templates (constants) coupe ~90% du coût input récurrent. (3) Mode batch (-50%) pour tout ce qui n'est pas temps réel, c.-à-d. les runs planifiés du cron J7. (4) LLM à la demande : conserver le repli déterministe J1 pour les fiches simples/non ambiguës et n'invoquer la rédaction LLM que si les signaux le justifient. (5) Cache api_io déjà en place : la dédup SERP/Places/Apollo et l'idempotence des ré-exécutions évitent de repayer. (6) Budgets hiérarchiques stricts : plafond par contrat + BudgetExceeded = zéro dérive. (7) Limiter la boucle de revue à 1 itération (le coût croît linéairement avec les tours). (8) Choisir un fournisseur SERP économique (ex. Serper-like) et n'appeler place_details que si text_search laisse une ambiguïté. Levier structurel : puisque tout est métré dans un ledger unique, l'optimisation est pilotée par la donnée (run_usage) plutôt qu'à l'aveugle.

**Forces.** S'appuie sur l'existant sans le réécrire : les bus vault_io/api_io et les livrables J1-J5 sont réutilisés tels quels, les 365 tests restent verts, le risque de régression est faible. ; Auditabilité totale : chaque décision (contrat superviseur), écriture (runs.log) et dépense (api_usage.log, y compris tokens LLM) est journalisée — atout majeur pour une prospection soumise à CASL/nLPD/RGPD/AI Act. ; Déterminisme préservé : la collecte reste factuelle, le LLM confiné à la rédaction/revue, avec repli déterministe complet — le système tourne hors-ligne et le comportement est reproductible. ; Qualité par revue croisée : l'agent Critique institutionnalise le contrôle de grounding, réduisant hallucinations et sur-affirmations avant toute sortie client. ; Montée en périmètre par la donnée : nouveau persona/marché = fichiers YAML (ICP, rubric, conformité, routage), zéro code — répond directement à la priorité flexibilité/multi-persona. ; Coût maîtrisé et pilotable : routage de modèle, caching, batch, budgets hiérarchiques et repli déterministe donnent des leviers OPEX concrets, adaptés à une micro-structure. ; Corrige quatre défauts AS-IS (preflight en gate, budgets injectés au runtime, api_io dans le diagnostic, amorce J6) sans casser les contrats existants. ; Séparation nette des responsabilités (superviseur/planif vs sous-agents/exécution vs bus/I-O) : lisible, testable, et évolutif vers un futur SaaS multi-tenant.

**Limites.** Sur-ingénierie potentielle pour une consultante solo : une orchestration hiérarchique complète peut dépasser le besoin réel ; à déployer par incréments (d'abord superviseur déterministe + revue, LLM ensuite). ; Latence accrue par la boucle de revue et le passage superviseur→sous-agents : le mode batch/asynchrone est adapté, le temps réel l'est moins. ; Coût du superviseur LLM : mal cadré (planification bavarde, itérations non bornées), il peut éroder le gain — d'où le plafonnement strict et le repli déterministe. ; Couverture 'personnes' bornée : l'exclusion volontaire de LinkedIn/Facebook (minimisation RGPD) limite l'enrichissement à Apollo et laisse des trous de contact. ; Outreach (J6) reste non opérationnel : l'agent est un squelette human-gated ; aucun envoi possible avant validation juridique CASL/nLPD/art.3 LCD/RGPD. ; Tarifs réels non renseignés (api_pricing.yaml à 0) : tout le chiffrage OPEX reste une estimation modélisée tant que la Phase D n'a pas relevé les prix ; preflight restera NO-GO jusque-là. ; Dépendance fournisseurs (SERP, Apollo, Places) : risque de lock-in, de changements de tarif/quotas et de politiques d'usage hors du contrôle du projet. ; La qualité de la revue dépend de la qualité des failles produites en amont : si le scoring/rubrique est pauvre, la critique n'a rien de solide contre quoi vérifier (garbage-in).

**Risques.** Injection de prompt via contenu scrapé : le texte de site web collecté est transmis à l'agent Rédaction (LLM) ; un contenu malveillant pourrait tenter de détourner la synthèse. Mitigation : séparation faits/instructions, sandboxing du contenu comme donnée non exécutable, contrôle de grounding par la critique. ; Dérive budgétaire du superviseur LLM (boucles non bornées, planification coûteuse). Mitigation : budgets hiérarchiques, itérations plafonnées, BudgetExceeded journalisé, repli déterministe. ; Hallucination résiduelle malgré la revue : la critique elle-même est un LLM faillible. Mitigation : contrôle déterministe complémentaire (chaque affirmation doit référencer une faille existante), échantillonnage humain, seuil d'escalade. ; Non-conformité réglementaire (CASL/nLPD/art.3 LCD/RGPD/AI Act) : envoi non consenti, base légale absente, défaut de transparence sur l'automatisation. Mitigation : agent Conformité bloquant, opt_out absolu, J6 human-gated, validation juridique préalable obligatoire. ; Violation de la machine à états si un agent tente une transition réservée. Mitigation : ValueError durci dans vault_io, seule decouvert→diagnostique autorisée, tests de garde. ; Fuite de secrets (.env en clair, clés dans les logs). Mitigation : coffre de secrets, aucun secret journalisé, revue des logs. ; Complexité opérationnelle dépassant la capacité d'une opératrice solo : trop d'agents/contrats à superviser. Mitigation : déploiement incrémental, manage-by-exception, dashboards Obsidian synthétiques. ; Contamination du cache / faux positifs de dédup : un cache api_io ou une dédup de domaine trop agressive peut masquer des données fraîches ou fusionner des prospects distincts. Mitigation : clés de cache datées/TTL, normalisation de domaine testée, journal de dédup auditable. ; Effet 'garbage-in' sur les données de marché : tarifs, quotas ou taux estimés faux faussent l'OPEX et les décisions. Mitigation : étiquetage explicite estimation vs vérifié, relevé Phase D, recalcul depuis le ledger réel.

#### Scénario 3 — Scenario C — "Nerf central evenementiel" : orchestration d'agents B2B event-driven, cloud-native et multi-tenant
**Paradigme.** Architecture evenementielle d'agents autonomes cloud-native : bus d'evenements central, agents reactifs decouples (consommateurs), RAG + memoire vectorielle par tenant, tool-use large mais borne, scaling horizontal, multi-tenant SaaS. Scenario "le plus ambitieux/scalable", explicitement mis en regard de son OPEX et de sa complexite pour une micro-structure solo.

**Résumé.** Le systeme AS-IS (5 livrables J1-J5, 365 tests verts, deterministe, hors-ligne, mono-utilisateur) est reprojete sur un plan evenementiel. Chaque etape de la chaine actuelle (decouverte -> collecte -> scoring -> synthese -> validation -> export -> outreach) devient un agent reactif independant qui consomme et emet des evenements sur un bus. Les deux "bus" logiques deja presents dans le code (vault_io = bus stockage, api_io = bus reseau) sont promus en services partages : api_io devient une passerelle reseau centrale metree et budgetee par tenant (ce qui corrige d'un coup trois defauts AS-IS : run_diagnostic sans api_io, budgets non injectes au runtime, et la fuite potentielle d'appels reseau hors bus), et le vault Obsidian devient une projection en lecture (read-model) d'un magasin evenementiel source-de-verite. Une couche RAG + memoire vectorielle par tenant alimente la synthese en contexte (diagnostics anterieurs, rubriques, connaissance de marque du client) sans jamais laisser le LLM aller chercher lui-meme sur le reseau : la regle d'or J1 ("le LLM ne fetch jamais") est preservee en exposant les collecteurs et api_io comme des outils (tool-use) au schema strict. L'ambition (temps quasi-reel, scaling horizontal, SaaS multi-tenant) est reelle mais son cout fixe d'infrastructure et sa complexite operationnelle sont dis-proportionnes pour une consultante solo : ce scenario n'a de sens economique qu'a partir d'une bascule productisee (dizaines de tenants payants). C'est donc le scenario "borne haute" a comparer a des options plus frugales.

**Architecture.**

Sept couches, du declencheur a la console.

1) COUCHE DECLENCHEUR / INGESTION. Sources d'evenements : (a) schedulers (cron manage / EventBridge Scheduler) qui emettent `discovery.requested` par ICP ; (b) API tenant (REST/gRPC) pour une demande a la volee ("diagnostique cette entreprise") ; (c) webhooks entrants (formulaire site, CRM du client). Chaque message est normalise en enveloppe CloudEvents (id, source, type, tenant_id, trace_id, payload) et publie sur le bus.

2) COUCHE BUS D'EVENEMENTS (colonne vertebrale). Un log de commit partitionne par tenant. Topics : `discovery.requested`, `candidate.found`, `fiche.decouvert`, `diagnostic.requested`, `diagnostic.done`, `fiche.diagnostique`, `validation.requested`, `fiche.valide`, `outreach.requested`, `outreach.sent`, `api.usage` (grand livre en flux), `dead.letter`. Choix techno = variable de decision explicite : NATS JetStream ou Redpanda serverless (frugal, scale-to-zero) versus Kafka manage type Confluent/MSK (robuste mais cout fixe eleve). Le partitionnement par `tenant_id` garantit l'ordre par prospect et l'isolation multi-tenant. Cle d'idempotence = hash(domaine_normalise + tenant) pour rejouer sans doublon (reprend la dedup J4 : domaine minuscule sans www ni trailing slash).

3) COUCHE AGENTS REACTIFS (le CPU, decouple). Chaque agent est un consommateur autonome, sans etat, scalable horizontalement (N replicas par groupe de consommation) : DiscoveryAgent (enveloppe run_discovery.py / DiscoveryCollector), EnrichmentAgent (PersonEnrichment / Apollo), DiagnosticAgent (DiagnosticPipeline : website/seo/social/gbp/reviews -> scoring), SynthesisAgent (le SEUL a heberger le LLM), ValidationGateAgent (n'auto-transitionne jamais valide : il prepare et notifie l'operateur, la transition diagnostique->valide reste humaine), OutreachAgent (J6, nouveau), UsageAgent (agrege le flux `api.usage`). Les agents communiquent uniquement par evenements : aucun appel direct agent-a-agent, aucun etat partage en memoire.

4) COUCHE SERVICES PARTAGES (les deux bus promus). (a) NETWORK GATEWAY = api_io hisse en micro-service : point de passage UNIQUE et obligatoire pour tout appel externe (SERP, Places, Apollo, Anthropic), avec cache distribue (Redis), budgets charges PAR TENANT au demarrage de l'instance et re-verifies a chaque appel (BudgetExceeded -> arret propre + evenement `budget.exceeded`), et emission systematique d'une ligne `api.usage`. C'est la generalisation cloud de la regle J3 "bus unique reseau". (b) EVENT STORE = magasin source-de-verite (log append-only + Postgres pour les projections). Le vault Obsidian Markdown+frontmatter devient une PROJECTION read-only reconstruite depuis l'event store, pour conserver la console operateur J2 sans en faire le systeme de verite.

5) COUCHE MEMOIRE / RAG. Base vectorielle (pgvector ou managed) segmentee par tenant (Row-Level Security). Contenu indexe : rubriques (rubric_persona*.yaml), diagnostics anterieurs, notes de marque fournies par le client, gabarits d'accroche valides. Le SynthesisAgent recupere le contexte pertinent (retrieval) et le passe au LLM comme faits deja etablis. La memoire vectorielle sert la personnalisation et la coherence inter-runs, PAS la collecte de faits nouveaux.

6) OU VIT LE LLM. Exclusivement dans le SynthesisAgent (et un mini "routeur" de personnalisation d'accroche). Le LLM redige a partir (i) des signaux collectes de facon deterministe en amont, (ii) du contexte RAG. Le "tool-use large" est encadre : les seuls outils exposes au LLM sont des wrappers a schema strict des collecteurs et de la passerelle api_io ; le LLM ne recoit jamais de socket ni d'URL brute a fetch. La regle d'or J1 est ainsi structurellement preservee malgre l'elargissement du tool-use.

7) COUCHE OBSERVABILITE / CONTROL PLANE. Tracing distribue OpenTelemetry (trace_id porte de bout en bout dans l'enveloppe), metriques Prometheus, flux `api.usage` sinke vers un entrepot pour le reporting cout par tenant. Control plane multi-tenant : provisioning des cles (Vault/Secrets Manager), quotas et budgets par tenant, feature flags, et une passe preflight J5 promue en GATE de deploiement (GO/NO-GO en CI/CD : refuse de deployer un tenant dont les prix/budgets sont a 0 -> corrige le defaut AS-IS de preflight NO-GO structurel).

FLUX DE DONNEES NOMINAL (un prospect, de bout en bout) : scheduler -> `discovery.requested(tenant, icp)` -> DiscoveryAgent (SERP via gateway, dedup, filtres ICP) -> `candidate.found` -> mapping FicheProspect -> `fiche.decouvert` (ecrit event store, projete vault) -> EnrichmentAgent (Apollo via gateway, Contact 6 champs minimises) -> DiagnosticAgent (collecteurs paliers 0/1 via gateway, scoring rubrique) -> `diagnostic.done` -> SynthesisAgent (RAG + LLM, accroche + mini-audit) -> `fiche.diagnostique` -> ValidationGateAgent notifie l'operateur (Obsidian) -> [HUMAIN valide] -> `fiche.valide` -> ExportAgent (liste Kemana) et/ou OutreachAgent (J6, apres feu vert conformite). A chaque saut reseau, une ligne `api.usage` est emise.

**Composants.**

- **Event Bus (NATS JetStream / Redpanda / Kafka manage)** — Colonne vertebrale : log partitionne par tenant, topics par etape du cycle de vie, ordre par prospect, idempotence par hash(domaine+tenant), dead-letter queue. Decouple totalement les agents.
- **Network Gateway (api_io promu en service)** — Point de passage UNIQUE de tout appel externe (SERP/Places/Apollo/Anthropic). Cache distribue Redis, budgets PAR TENANT injectes au runtime et re-verifies a chaque appel, emission de la ligne api.usage. Corrige : run_diagnostic sans api_io, budgets non injectes, fuite reseau hors bus.
- **DiscoveryAgent** — Consommateur de discovery.requested. Enveloppe DiscoveryCollector/run_discovery : SERP via gateway, dedup intra-lot par domaine normalise, filtres ICP YAML, emet candidate.found puis fiche.decouvert. Zero LLM (regle J4 preservee).
- **EnrichmentAgent** — Enrichissement personnes via Apollo (gateway). Contact a 6 champs (minimisation RGPD), contact_email_source toujours renseigne. Zero scraping LinkedIn/Facebook.
- **DiagnosticAgent** — Enveloppe DiagnosticPipeline : collecteurs enfichables paliers 0/1 (website/seo/social/gbp/reviews) via gateway, scoring pilote par rubrique YAML. Emet diagnostic.done avec signaux + scores + failles. Aucun LLM.
- **SynthesisAgent (heberge le LLM)** — Seul composant appelant Claude (via gateway, metre). RAG : recupere rubrique + diagnostics anterieurs + memoire de marque, redige accroche + mini-audit a partir de faits etablis. Repli deterministe si pas de cle (comportement J1 conserve). QA avant emission.
- **ValidationGateAgent** — Prepare la fiche diagnostique pour revue humaine, notifie l'operateur (Obsidian/console). N'execute JAMAIS diagnostique->valide : la transition reste humaine (machine a etats J2 respectee, manage-by-exception).
- **OutreachAgent (J6, nouveau)** — Consomme fiche.valide approuvee. Sequence email declenchee (valide->contacte). Moteur de conformite integre (CASL/nLPD+LCD/RGPD) bloquant, opt_out absolu herite de J5, journal des envois. Livrable absent en AS-IS, ajoute par ce scenario.
- **UsageAgent + entrepot cout** — Agrege le flux api.usage (grand livre en streaming) : cout par tenant, par fournisseur, taux de cache, budgets consommes. Generalisation de run_usage.py.
- **Event Store + projection Vault** — Log append-only source-de-verite (+ Postgres pour projections). Le vault Obsidian Markdown devient un read-model reconstruit, preservant la console operateur J2 sans etre le systeme de verite. Ecriture atomique conservee cote projection.
- **Memoire vectorielle / RAG (pgvector, RLS par tenant)** — Indexe rubriques, diagnostics passes, notes de marque client, accroches validees. Alimente la synthese en contexte. Isolation stricte par tenant. Ne collecte aucun fait nouveau.
- **Control Plane multi-tenant** — Provisioning cles (Vault/Secrets Manager), quotas et budgets par tenant, feature flags, preflight J5 promu en GATE de deploiement CI/CD (refuse prix/budgets a 0).
- **Observabilite (OpenTelemetry + Prometheus)** — Trace_id de bout en bout dans l'enveloppe CloudEvents, metriques par agent et par topic, alerting sur DLQ, latence, budget.

**Interfaçage / intégrations.**

- APIs externes via la SEULE passerelle api_io : SERP (SerpAPI/Serper/Bright Data au choix), Google Places (text_search/place_details), Apollo (people_enrichment), Anthropic Messages API (synthese, avec prompt caching et Batch API).
- Enveloppe d'evenements CloudEvents (JSON) sur le bus ; contrat de topics versionne (schema registry recommande pour l'evolutivite SaaS).
- Secrets et cles par tenant via HashiCorp Vault ou cloud Secrets Manager (fin du 'pas de secret en dur', cles par tenant et non globales).
- Console operateur = vault Obsidian (projection read-model) : validation manage-by-exception, journal-decisions.md editable ; alternative web front SaaS pour les tenants non-Obsidian.
- Sortie commerciale : export liste Kemana (CSV utf-8-sig / JSONL) via ExportAgent, lecture seule, opt_out absolu ; connecteurs CRM sortants optionnels (HubSpot/Pipedrive) cote OutreachAgent.
- Entrepot analytique (BigQuery/Snowflake/Postgres) sinke depuis le flux api.usage pour le reporting cout et KPI par tenant.
- Observabilite : export OTLP vers Grafana/Tempo/Prometheus ; DLQ monitoree.
- Moteur de conformite J6 : interface avec un registre d'opt-out et un journal d'envois horodate (preuve CASL/nLPD/RGPD).

**Exigences fonctionnelles.**

- Traiter un evenement discovery.requested de bout en bout jusqu'a fiche.diagnostique sans intervention humaine, en preservant la separation collecte deterministe / redaction LLM.
- Garantir l'idempotence : rejouer un evenement (crash, redemarrage, at-least-once) ne cree ni doublon de fiche ni double facturation (cache + cle d'idempotence + dedup inter-runs J4).
- Isoler strictement les tenants : donnees, memoire vectorielle, cles, budgets et cout separes ; aucune fuite inter-tenant.
- Imposer que TOUT appel reseau passe par la gateway metree et budgetee ; tout appel hors gateway est un echec de conformite d'architecture (teste par AST walk, comme en J3, etendu aux nouveaux agents).
- Preserver la machine a etats : les agents ne font que decouvert->diagnostique ; valide, contacte et rejete restent des transitions humaines ou humaines-approuvees.
- Appliquer l'opt_out de facon absolue a l'export ET a l'outreach (RGPD/CASL/nLPD), sans exception.
- Bloquer tout deploiement de tenant dont les prix/budgets sont a 0 (preflight promu en gate CI/CD).
- Fournir un cout consolide par tenant en quasi temps-reel depuis le flux api.usage.
- Degrader proprement : sans cle Anthropic -> repli deterministe ; sans cle Places -> collecteurs palier 1 en stub ; budget atteint -> arret propre, fiches deja ecrites valides.
- Assurer la tracabilite complete : chaque fiche reconstructible depuis l'event store ; chaque euro depense adosse a une ligne du grand livre.

**Spécifications atteintes.**

- EXISTANT preserve — J1 : chaine collecte->scoring->synthese conservee ; collecteurs enfichables (Collector/safe_collect) deviennent la boite a outils du DiagnosticAgent ; rubrique reste une donnee YAML ; 'le LLM ne fetch jamais' garanti structurellement par le tool-use borne.
- EXISTANT preserve — J2 : machine a etats decouvert->diagnostique->valide->contacte respectee ; ecriture atomique et journal append-only conserves cote projection vault ; validation humaine manage-by-exception maintenue (ValidationGateAgent).
- EXISTANT generalise — J3 : le 'bus unique reseau' api_io devient un service partage obligatoire ; grand livre api_usage.log devient un topic api.usage streame ; tarifs et budgets restent des donnees (YAML/config par tenant) ; garde-fou AST 'aucun import requests/anthropic hors gateway' etendu a tous les nouveaux agents.
- EXISTANT preserve — J4 : ICP en YAML, dedup domaine normalise (intra-lot + inter-runs), Contact 6 champs, BudgetExceeded arret propre, dry-run, zero LLM, zero scraping LinkedIn.
- EXISTANT preserve — J5 : export Kemana lecture seule, opt_out absolu, exports hors vault, agregat usage, preflight GO/NO-GO — le preflight est en plus promu en gate de deploiement.
- DEFAUT AS-IS corrige : budgets desormais injectes au runtime dans la gateway (ApiIO) par tenant, re-verifies a chaque appel.
- DEFAUT AS-IS corrige : run_diagnostic passe obligatoirement par la gateway — plus aucun chemin de diagnostic non metre.
- DEFAUT AS-IS corrige : prix/budgets a 0 bloquent le deploiement via le gate preflight (fin du NO-GO structurel silencieux).
- PLANIFIE — J6 : OutreachAgent avec moteur de conformite bloquant (CASL/nLPD+art.3 LCD/RGPD), opt_out absolu, journal d'envois — comble l'absence totale de code outreach en AS-IS.
- PLANIFIE — extension multi-persona/multi-marche : nouveau rubric_persona2.yaml et nouveaux ICP YAML sans changement de code, deployes par tenant.

**KPIs.**

| KPI | Cible |
|---|---|
| Latence bout-en-bout discovery.requested -> fiche.diagnostique (p95) | < 90 s par prospect en charge nominale (ESTIMATION MODELISEE : ~2-4 appels reseau serialises de 2-8 s + 1 appel LLM Haiku ~3-6 s ; hypothese cache SERP tiede) |
| Debit soutenu | 200-1000 prospects/heure par tenant en scale horizontal (ESTIMATION MODELISEE : borne par quotas fournisseurs SERP/Apollo/Places, pas par le compute ; horizon a valider en charge) |
| Taux de cache gateway (SERP+Places) | > 40 % en regime etabli sur ICP recurrents (herite du cache api_io J3 ; reduit d'autant l'OPEX variable) |
| Cout variable par prospect entierement traite | 0,04-0,15 USD (ESTIMATION MODELISEE, detail en OPEX ; borne basse Haiku+cache+batch, borne haute Sonnet+Places complet) |
| Taux d'auto-completion sans intervention humaine (jusqu'a diagnostique) | > 95 % des fiches ; < 5 % en dead-letter/revue (hypothese : sites accessibles, ICP bien cadre) |
| Isolation multi-tenant (incidents de fuite) | 0 (exigence dure, non negociable) |
| Precision du grand livre cout (ecart facture reelle vs api.usage) | < 2 % (reconciliation mensuelle ; depend de tarifs YAML a jour) |
| Disponibilite du bus + gateway | 99,5 % (ESTIMATION MODELISEE realiste pour un SaaS early-stage mono-region ; 99,9 % exige multi-AZ et augmente l'OPEX fixe) |
| Conformite outreach (envois hors cadre / opt_out ignore) | 0 (bloquant J6 ; garanti par opt_out absolu + moteur de conformite) |

**Métriques opérationnelles.**

| Métrique | Définition |
|---|---|
| consumer_lag par topic et par tenant | Nombre d'evenements en attente par groupe de consommation ; signal d'alerte de saturation et de besoin de scale-out. |
| dead_letter_rate | Part des evenements routes en DLQ (echec collecte, site inaccessible, schema invalide) sur total traite ; qualite de la pipeline. |
| cost_per_tenant_per_day | Somme des lignes api.usage par tenant/jour, ventilee par fournisseur (SERP/Places/Apollo/Anthropic) ; pilotage OPEX et facturation SaaS. |
| budget_utilisation_pct | Consommation vs plafond par tenant et par fournisseur ; declenche throttling ou BudgetExceeded avant depassement. |
| cache_hit_ratio gateway | Hits / (hits+miss) sur le cache reseau distribue ; principal levier de reduction du cout variable. |
| llm_tokens_in/out et cache_read_ratio | Volume de tokens par synthese et part servie par prompt caching ; suit l'efficacite du levier caching (10 % du prix input). |
| human_validation_backlog | Fiches diagnostique en attente de validation humaine ; le goulot reel du systeme (l'operateur solo est le facteur limitant, pas le compute). |
| idempotency_replay_count | Nombre d'evenements rejoues sans effet de bord ; verifie l'absence de double facturation/doublon. |
| trace_completeness | Part des fiches disposant d'une trace OTel complete bout-en-bout ; auditabilite. |
| time_to_valide (humain) | Delai fiche.diagnostique -> fiche.valide ; mesure la charge de la console operateur. |

**OPEX & leviers de réduction.** Deux blocs : cout VARIABLE (par prospect, domine par les fournisseurs) et cout FIXE d'infrastructure (la vraie rupture par rapport a l'AS-IS qui tourne a ~0 fixe, hors-ligne).

COUT VARIABLE PAR PROSPECT (ESTIMATION MODELISEE, hypotheses ci-dessous ; sources tarifaires citees). Hypotheses : 1 fiche = ~0,1-0,3 requete SERP amortie (une recherche renvoie ~10 resultats), 1 credit Apollo (unlock email), 2-3 requetes Google Places (text_search + place_details), 1 synthese LLM (~4-6k tokens input, ~1-1,5k output). Tarifs releves (juillet 2026) : SerpAPI ~0,025 USD/recherche en entree de gamme, ~0,009 a l'echelle [apiserpent.com/costbench] ; Apollo ~0,025 USD/credit (25 USD/1000 credits, 1 credit/email) [warmly.ai/salesmotion.io] ; Google Places ~0,017-0,032 USD/requete selon SKU (ordre de grandeur connu, a reconfirmer sur developers.google.com/maps/billing) ; Claude Haiku 4.5 = 1 USD input / 5 USD output par million de tokens, Sonnet 5 = 2-3 USD input / 10-15 USD output, cache-read a 10 % du prix input, Batch API -50 % [cloudzero.com/finout.io/benchlm.ai]. Calcul : SERP ~0,003-0,01 + Apollo ~0,025 + Places ~0,04-0,10 + LLM ~0,01 (Haiku+cache+batch) a ~0,035 (Sonnet plein) => FOURCHETTE ~0,04-0,15 USD par prospect entierement traite. A 5 000 prospects/mois : ~200-750 USD/mois de variable.

COUT FIXE D'INFRASTRUCTURE (ESTIMATION MODELISEE, borne haute du scenario, c'est le point de friction). Bus manage (Confluent/MSK) ~100-500+ USD/mois, OU option frugale NATS/Redpanda serverless ~0-100 USD/mois ; base vectorielle managee ~70-300 USD/mois (ou pgvector auto-heberge quasi-gratuit) ; runtime conteneurs scale-to-zero (Cloud Run/Fargate) ~50-300 USD/mois ; Redis cache ~30-100 USD ; observabilite (Grafana Cloud/Datadog) ~0-300 USD ; Postgres event store ~30-150 USD. TOTAL FIXE : ~200-400 USD/mois en configuration frugale (serverless, auto-heberge) jusqu'a ~1 500-2 500 USD/mois en configuration robuste multi-AZ managee. Pour une consultante solo, ce cout fixe est le probleme central : il n'a de sens qu'amorti sur plusieurs tenants payants.

LEVIERS DE REDUCTION (par ordre de rendement) : (1) Prompt caching Anthropic sur rubrique + system prompt = input a 10 % => la synthese devient quasi gratuite en input. (2) Batch API -50 % pour la synthese non temps-reel (la plupart des diagnostics ne sont pas urgents) — attention, cela contredit partiellement l'exigence 'quasi temps-reel', arbitrage a assumer. (3) Router Haiku par defaut, Sonnet seulement sur les fiches a fort signal_chaud (routing par score). (4) Cache reseau distribue deja present en J3 : >40 % de hits attendus sur ICP recurrents. (5) Scale-to-zero des consumers (serverless) : payer le compute seulement pendant les pics. (6) Choix NATS/Redpanda + pgvector auto-heberge plutot que Kafka manage + vector DB managee => divise le cout fixe par ~3-5. (7) Budgets par tenant re-verifies au runtime (defaut AS-IS corrige) : plafonne mecaniquement la derive. (8) Deduplication et idempotence : zero double facturation sur rejeu. Conclusion OPEX : le variable est maitrise et competitif ; c'est le FIXE cloud-native qui disqualifie ce scenario pour un usage solo et ne se justifie qu'en mode SaaS multi-tenant a l'echelle.

**Forces.** Scalabilite horizontale reelle : chaque agent scale independamment ; le compute n'est jamais le goulot (les quotas fournisseurs et l'operateur humain le sont). ; Decouplage fort : ajouter un agent (nouveau collecteur, nouveau canal outreach) = ajouter un consommateur, sans toucher aux autres — prolonge la philosophie 'collecteurs enfichables' J1 a l'echelle systeme. ; Auditabilite native renforcee : event store source-de-verite + trace_id bout-en-bout + grand livre en flux => chaque fiche et chaque euro reconstructibles (repond a la contrainte forte de tracabilite). ; Multi-tenant SaaS de premiere classe : isolation par partition/RLS/secrets par tenant, cout par tenant en temps quasi-reel — base d'un modele de facturation. ; Corrige plusieurs defauts AS-IS d'un seul mouvement architectural : gateway obligatoire (run_diagnostic metre, budgets injectes, aucune fuite reseau), preflight en gate de deploiement. ; Regle d'or J1 preservee malgre le tool-use large : le LLM redige, ne fetch jamais, grace au bornage strict des outils. ; Resilience : at-least-once + idempotence + DLQ => tolerance aux pannes et rejeu sans effet de bord. ; Quasi temps-reel possible pour les demandes a la volee (API tenant), la ou l'AS-IS est batch.

**Limites.** Cout fixe d'infrastructure disproportionne pour une consultante solo : ~200-2 500 USD/mois de fixe contre ~0 en AS-IS hors-ligne — ne se rentabilise qu'en SaaS multi-tenant a l'echelle. ; Complexite operationnelle elevee : bus, event sourcing, RAG, observabilite distribuee, control plane => competences DevOps/SRE qu'une micro-structure n'a pas en interne. ; Le determinisme et la reproductibilite exacte, forces de l'AS-IS, sont plus difficiles a garantir en systeme distribue asynchrone (ordre partiel, at-least-once, RAG non deterministe). ; Le goulot reel reste HUMAIN : la validation manage-by-exception (diagnostique->valide) ne scale pas avec le compute — industrialiser la decouverte sans industrialiser la validation deplace juste l'embouteillage. ; Contradiction interne 'quasi temps-reel' vs 'OPEX minimal' : Batch API -50 % et scale-to-zero, principaux leviers de cout, degradent la latence. ; La memoire vectorielle/RAG ajoute une surface de risque (fuite inter-tenant, contenu obsolete injecte comme 'fait') sans apport decisif tant que le volume de diagnostics anterieurs est faible. ; Over-engineering probable au stade actuel : l'AS-IS mono-utilisateur ne genere pas le volume qui justifierait un bus d'evenements ; le ROI n'apparait qu'apres bascule produit. ; Migration non triviale : passer d'un vault fichier source-de-verite a un event store avec vault en projection est un chantier a risque de regression sur 365 tests.

**Risques.** Conformite / juridique (eleve) : l'OutreachAgent J6 automatise l'envoi ; sans validation juriste prealable du cadre CASL (QC) / nLPD + art.3 LCD (CH) / RGPD (UE) et sans respect de l'AI Act (systeme de profilage B2B), risque de sanction. Mitigation : moteur de conformite bloquant, opt_out absolu, feu vert juriste avant tout envoi (deja exige en J6). ; Derive OPEX (eleve) : un bug de boucle d'evenements ou un rejeu mal maitrise peut multiplier les appels factures. Mitigation : budgets par tenant re-verifies au runtime, idempotence, alerting budget_utilisation_pct. ; Fuite inter-tenant (eleve en SaaS) : mauvaise isolation partition/RLS/secrets = fuite de donnees prospects entre clients. Mitigation : cle de partition = tenant_id, RLS, secrets par tenant, tests d'isolation. ; Dependance fournisseurs (moyen) : changement de tarif ou de quota SERP/Apollo/Places/Anthropic casse le modele economique. Mitigation : tarifs en donnee (YAML), abstraction fournisseur SERP, releve date des tarifs. ; Complexite -> indisponibilite (moyen) : plus de pieces mobiles = plus de modes de panne pour une equipe sans SRE. Mitigation : commencer frugal (NATS + pgvector + scale-to-zero), DLQ, observabilite des le depart. ; Qualite RAG (moyen) : contexte obsolete ou hors-sujet injecte comme 'fait etabli' degrade la synthese et viole l'esprit de la regle J1. Mitigation : retrieval strictement borne aux faits collectes du run + memoire versionnee, QA avant sortie conservee. ; Non-determinisme d'audit (moyen) : en distribue asynchrone, reproduire a l'identique un diagnostic pour un audit est plus dur qu'en AS-IS. Mitigation : event store rejouable + snapshots de contexte LLM. ; Sur-investissement premature (strategique, eleve) : engager le cout fixe cloud avant d'avoir des tenants payants peut assecher une micro-structure. Mitigation : conditionner ce scenario a un seuil de tenants ; garder l'AS-IS frugal comme chemin par defaut jusque-la.

### 2.4 Décision structurante #1 — sélection (autorité chef de projet)
**Scénario retenu :** Scénario A (Orchestrateur DAG déterministe « Kemana-Flow ») comme colonne vertébrale et livrable immédiat, hybridé selon une trajectoire en 3 paliers : Palier 1 = A intégral maintenant ; Palier 2 = greffe sélective de B (revue de grounding + conformité-par-donnée + routage modèle YAML) SANS le superviseur-planificateur LLM ; Palier 3 = fragments de C réservés et conditionnés à une bascule SaaS multi-tenant avérée.

**Hybride :** oui — **Autorité :** Agent Chef de Projet — autorité ultime sur les décisions structurantes

**Justification.** La matrice place A en tête (4,42/5) et dominant sur les 3 critères les plus lourds — time-to-market (18%, note 5), OPEX (15%, note 5), complexité d'exploitation (14%, note 5) — qui sont précisément les contraintes cardinales d'une consultante solo dont le mandat est d'INDUSTRIALISER d'abord. A corrige les 4 défauts AS-IS (vérifiés sur le dépôt : api_pricing.yaml à 0.0, releve_le=null, aucun orchestrator.py/run_pipeline.py) par un seul geste architectural — l'instance ApiIO unique injectée — sans réécrire aucune brique J1-J5. C'est le seul scénario dont la revendication « zéro réécriture métier » est crédible selon la revue.

L'hybridation n'est pas un compromis mou mais l'exploitation de la lecture correcte de la revue et de la matrice : B (3,56/5) n'est pas un concurrent frontal de A, c'est sa suite. B apporte deux briques à forte valeur que A n'a pas et qui deviennent nécessaires AVANT l'activation réelle de J6 : (a) la revue croisée de grounding, (b) la conformité-par-donnée (politiques CASL/nLPD+art.3 LCD/RGPD/AI Act en YAML), meilleure du panel sur le critère conformité (note 5). On importe ces briques comme NŒUDS/DONNÉES du DAG A, mais on REFUSE explicitement le superviseur-planificateur LLM de B — principale source de coût, de non-déterminisme et de charge cognitive, et point sur lequel B perd contre A (déterminisme, OPEX, exploitation).

C (2,52/5) est écarté au stade actuel : dernier sur les 3 critères majeurs, coût fixe d'infrastructure de 200 à 2500 USD/mois contre ~0 en AS-IS, besoin DevOps/SRE absent en interne, et surtout inversion de l'invariant J2 (le vault N'EST PAS un read-model, il EST la source de vérité versionnée écrite par le seul bus vault_io). Le rejeter n'est pas une perte : ses bonnes idées isolables (gateway par tenant, isolation, coût par tenant) sont récupérables au Palier 3 sans le bus d'événements ni l'event-sourcing.

**Décisions structurantes qui en découlent :**

- Palier 1 (livrable immédiat) : créer orchestrator.py (tri topologique déterministe, ~250-400 lignes, ZÉRO logique métier), run_pipeline.py (CLI unique), dag_pipeline.yaml (graphe = donnée). Chaque nœud enveloppe un run_*.py existant. Aucune modification de pipeline.py ni des collecteurs.
- Instance ApiIO UNIQUE créée en tête de DAG avec budgets chargés depuis api_pricing.yaml, injectée dans discovery, diagnostic ET outreach — corrige d'un coup : budgets non câblés, run_diagnostic sans api_io, orchestration absente.
- Garde-fou AST (interdiction import requests/anthropic hors bus) ÉTENDU à orchestrator.py et run_pipeline.py AVANT toute activation. Condition non négociable : les nouveaux tests verts EN PLUS des 365 existants — la non-régression est une CIBLE À ATTEINDRE, pas un acquis.
- Verrou de run (lockfile/run_id unique) refusant un second démarrage concurrent (cron + manuel) sur le même vault.
- Machine à états intangible : l'orchestrateur n'exécute QUE decouvert->diagnostique ; les transitions valide/contacte/rejete restent humaines via Obsidian. Le DAG s'arrête à la frontière humaine et reprend au run suivant (reprise idempotente).
- J6 (outreach) livré comme OSSATURE human-gated uniquement, NON activable : aucun envoi avant (a) validation juridique CASL/nLPD+art.3 LCD/RGPD/AI Act par un juriste, (b) ESP conforme retenu. À ne jamais présenter comme opérationnel à la porte de décision.
- Palier 2 (dès que le pilote tourne) : greffer un nœud Critique de grounding entre synthèse et transition, un nœud Conformité bloquant en amont d'export/outreach alimenté par compliance/*.yaml par marché, et un routing.yaml (Haiku par défaut, modèle fort réservé aux cas signalés). On conserve le planificateur DÉTERMINISTE du DAG.
- Palier 3 (conditionnel, déclenché sur un SEUIL de tenants payants défini à l'avance — pas sur une intuition) : n'emprunter à C que la gateway api_io métrée/budgétée par tenant + isolation + reporting par tenant. Bus d'événements, event-sourcing et RAG différés jusqu'à justification économique.
- Phase D obligatoire AVANT toute porte de décision budgétaire ET avant le premier run réel : relever les vrais tarifs, renseigner prix_par_unite + releve_le + budgets>0 dans api_pricing.yaml, puis python run_preflight.py => exiger GO.

**Conditions & réserves de revue traitées :**

- Aval de revue = approuve_avec_reserves (aval=true) : aucun aval=false à traiter. Les 3 hallucinations détectées concernent EXCLUSIVEMENT le Scénario C (tarifs vendeurs pseudo-sourcés apiserpent/warmly ; inversion vault/event-store ; KPI grounding >=98% par un LLM faillible). En écartant C au stade actuel, ces hallucinations sont neutralisées de facto : aucun chiffre tarifaire fabriqué n'entre dans la décision.
- Reserve OPEX (projections non validées tant que api_pricing.yaml=0) : LEVÉE par la décision structurante Phase D obligatoire avant toute décision budgétaire. Toutes les fourchettes citées restent étiquetées ESTIMATION MODELISEE ; aucun engagement de coût fixe autorisé avant le relevé réel.
- Reserve « 365/365 tests conservés est une cible, pas un état » : ACCEPTÉE et transformée en condition dure — extension du garde-fou AST aux nouveaux modules + nouveaux tests verts exigés avant activation. La non-régression devient un critère de sortie, non une hypothèse.
- Incohérence relevée sur A (export ∥ outreach « en parallèle » alors que l'exécution est séquentielle) : TRANCHÉE — dag_pipeline.yaml décrit un ordre topologique séquentiel strict ; aucun parallélisme massif n'est revendiqué ni requis pour un pilote solo. Le symbole ∥ est retiré de la spécification retenue.
- Reserve conformité (J1 hallucination via contenu scrapé, KPI grounding sur-promis) : traitée au Palier 2 par un contrôle DÉTERMINISTE complémentaire — chaque affirmation du mini-audit DOIT référencer une faille existante dans diag.failles — adossé à un échantillonnage humain, plutôt qu'au seul verdict d'un LLM critique. Le grounding reste étiqueté ESTIMATION MODELISEE.
- Reserve « goulot humain non industrialisé » : ASSUMÉE explicitement — la porte diagnostique->valide reste le facteur limitant par conception (manage-by-exception). On n'industrialise pas la découverte en prétendant industrialiser la validation ; le débit amont est piloté par les budgets, pas survendu au niveau système.
- Reserve C (coût fixe + migration event-store à risque) : LEVÉE par le rejet de C au stade actuel et son conditionnement à un seuil de tenants payants ; toute reprise future de C exige au préalable la résolution de l'inversion vault/event-store et le retrait des citations tarifaires non sourcées.

---
<a id="3"></a>
## 3. Objectif 2 — Étude de marché
### Dimensionnement (TAM/SAM/SOM) & SWOT
# Étude de marché — Système Autonome de Diagnostic Marketing (agentique marketing & sales)

## Note de cadrage et garde-fous

Ce document distingue systématiquement trois registres :
- **[VÉRIFIÉ]** = donnée sourcée (WebSearch, citée) ou fait établi de l'AS-IS du dépôt.
- **[PLANIFIÉ]** = brique décidée mais non encore codée (J6, Phase D, Paliers 2-3).
- **[ESTIMATION MODÉLISÉE]** = chiffre reconstruit par hypothèses explicites, faute de source directe ; toujours donné en fourchette.

Les marchés « globaux » sont sourcés ; les découpages géographiques fins (Québec, Romandie) et les prix unitaires ne le sont pas directement et sont donc modélisés. Aucun tarif fournisseur (SERP/Apollo/Places/Anthropic) n'est chiffré ici comme « réel » : `api_pricing.yaml` est à 0 dans le dépôt et la **Phase D** reste la pré-condition dure à tout engagement budgétaire.

---

## PARTIE 1 — DIMENSIONNEMENT DU MARCHÉ (TAM / SAM / SOM)

### 1.1 Définition des trois marchés emboîtés (le produit a deux visages)

Le projet est à la fois un **outil d'usage interne** (la consultante industrialise SA prospection) et un **produit potentiel** (SaaS/licence vendu à d'autres consultants/agences — trajectoire Palier 3). Le dimensionnement doit donc traiter deux « adressables » distincts :

- **Marché A — « outil de production »** : valeur = le chiffre d'affaires de conseil que la prospection industrialisée permet de générer/capter. Pertinent dès aujourd'hui (Palier 1).
- **Marché B — « produit agentique »** : valeur = ce qu'on peut vendre en licence/abonnement à la population des consultants et micro-agences marketing. Pertinent au Palier 3 (bascule SaaS avérée).

Le TAM ci-dessous est ancré sur le **segment agentique marketing & sales** (marché B, le plus « scalable »), puis rapporté au marché A par le bottom-up.

### 1.2 TAM — top-down (marché mondial de référence)

Trois marchés-cadres se chevauchent ; je les donne pour borner, pas pour additionner (le double-comptage serait une erreur méthodologique) :

| Marché de référence (mondial) | Taille ~2025 | CAGR | Horizon |
|---|---|---|---|
| **Agentic AI** (toutes verticales) | ~7,3 Md USD (fourchette 7,0–7,8) | 30–47 % (consensus 43–46 %) | 24–52 Md USD d'ici 2030 |
| **AI in Marketing** | ~20–47 Md USD selon définition | 22–27 % | ~82 Md USD d'ici 2030 (Grand View, 25 %) |
| **AI SDR / sales development** | ~4,4 Md USD | ~29–32 % | ~15 Md USD d'ici 2030 |

*Sources : Precedence/Fortune/MarketsandMarkets (agentic AI) ; Grand View/Precedence (AI marketing) ; MarketsandMarkets/CMI (AI SDR).* **[VÉRIFIÉ, fourchettes larges — méthodologies analystes hétérogènes.]**

**TAM retenu pour ce projet.** Le produit n'est ni « toute l'IA marketing » ni « tout l'agentique » : c'est l'**intersection agentique × prospection/diagnostic B2B**, la plus proche de l'AI SDR. On prend donc l'**AI SDR (~4,4 Md USD 2025 → ~15 Md USD 2030)** comme TAM primaire, en notant qu'il capte mal la partie « diagnostic/audit de marque » (adjacente à l'AI marketing). **TAM composite retenu : ordre de 5–8 Md USD (2025)** pour « agentique de prospection + diagnostic B2B ». **[ESTIMATION MODÉLISÉE — bornage par recoupement des trois marchés sourcés.]**

### 1.3 SAM — segment servable (géographies + segment cible)

Le SAM restreint le TAM aux **géographies de la séquence** (Québec/Canada → Romandie → France/UE) et au **segment SMB/micro-structure** (persona 1 HVAC et assimilés, plus la population des consultants francophones pour le marché B).

**Top-down (part géographique du TAM).** L'Amérique du Nord représente typiquement ~35–40 % du marché IA mondial et l'Europe ~20–25 % **[ESTIMATION MODÉLISÉE d'après répartitions usuelles des rapports cités]**. La cible francophone (Québec + Romandie + France) est une **sous-fraction** :

| Zone | Poids dans TAM mondial (modélisé) | SAM agentique prospection ~2025 |
|---|---|---|
| Canada (dont Québec ~22 % du privé CA) | ~3–4 % | ~150–320 M USD (Québec : ~35–70 M USD) |
| France / UE francophone | ~2–3 % | ~120–240 M USD |
| Suisse (Romandie ~25 % de l'éco suisse) | ~0,5–0,8 % | ~30–60 M USD (Romandie : ~8–15 M USD) |
| **SAM francophone cumulé** | | **~0,3–0,6 Md USD** |

**[ESTIMATION MODÉLISÉE — application de parts géographiques au TAM composite ; à traiter comme ordre de grandeur, pas comme mesure.]**

### 1.4 SAM/SOM — bottom-up (le contrôle de cohérence)

Le bottom-up part des **populations de comptes réels** et d'un ARPU modélisé. C'est la méthode la plus fiable ici car les découpages fins ne sont pas sourçables top-down.

**Assises démographiques [VÉRIFIÉ] :**
- Québec : **228 622** petites entreprises employeuses (déc. 2024, ISED). Canada : **1,10 M** entreprises employeuses, dont 98,2 % petites.
- Suisse : **99,7 %** des entreprises sont des PME (OFS) ; base communément citée ~**600 k** PME **[VÉRIFIÉ pour le ratio ; total ~600k = ordre de grandeur usuel]**. Romandie ≈ un quart de l'économie suisse.
- France : ~**4 M** entreprises (INSEE, dont ~3 M micro) ; ~**164 k** PME non-micro.
- Adoption IA PME : **54–57 %** utilisent déjà des outils marketing IA, **>70 %** en vente/lead-gen (2024-25) ; 76 % marketing en 2026. **[VÉRIFIÉ]**

**Marché B (vendre le produit agentique aux consultants/micro-agences francophones) :**

Hypothèses de population de **buyers** (consultants marketing indépendants + micro-agences ≤5 personnes) **[ESTIMATION MODÉLISÉE]** :
- Québec : ~2 000–5 000 ; Romandie : ~1 000–3 000 ; France : ~25 000–60 000. Total francophone : **~28 000–68 000 buyers potentiels.**
- ARPU SaaS outil de prospection déterministe/conforme : **~600–3 600 USD/an** (50–300 USD/mois) **[ESTIMATION MODÉLISÉE ; cohérente avec le positionnement micro-structure vs suites AI SDR à plusieurs milliers USD/mois].**

→ **SAM bottom-up marché B = 28 000–68 000 × 600–3 600 USD ≈ 17 M – 245 M USD/an.** Fourchette large ; point médian modélisé **~50–90 M USD**. Cohérent (même ordre de grandeur) avec le SAM top-down de 0,3–0,6 Md — le bottom-up est plus conservateur car il exclut les grandes agences et les usages non-francophones. **[ESTIMATION MODÉLISÉE — convergence des deux méthodes à un facteur ~5, acceptable pour un cadrage.]**

**SOM marché B (capture réaliste d'une micro-structure solo, horizon 3 ans, si bascule SaaS Palier 3) :**
- Pénétration atteignable en solo : **0,05–0,3 %** des buyers du SAM **[ESTIMATION MODÉLISÉE ; un éditeur solo sans force de vente].**
- Soit **~15–200 clients payants**, ARPU ~1 200 USD/an → **SOM ≈ 18 k – 240 k USD/an de MRR annualisé.**
- Seuil de bascule Palier 3 (« tenants payants avérés ») : la décision chef de projet le conditionne — cohérent avec un **point mort d'infra** que le Scénario C chiffrait à ~200–2 500 USD/mois de coût fixe. Il faut donc **au moins ~20–40 tenants** à l'ARPU médian pour amortir une infra multi-tenant frugale. **[ESTIMATION MODÉLISÉE.]**

**Marché A (usage interne — le SOM réellement actif au Palier 1) :**

C'est le marché qui compte maintenant. Bottom-up par le débit du pipeline :
- Capacité de diagnostic : **50–200 fiches/run** sous budgets pilote (KPI Scénario A) **[PLANIFIÉ, borné par budgets].**
- Goulot réel = **validation humaine** (porte `diagnostique→valide`), assumée comme facteur limitant par conception (manage-by-exception). Débit soutenable solo : **quelques dizaines de prospects qualifiés/semaine** **[ESTIMATION MODÉLISÉE].**
- Valeur : ce n'est pas un revenu produit mais un **levier de CA de conseil** — chaque prospect qualifié/converti alimente des mandats de branding/marketing. Le SOM marché A = **la fraction de mandats gagnés attribuable à la prospection industrialisée**, non chiffrable sans données de conversion propres à la consultante. **[HYPOTHÈSE — à instrumenter via `taux_conversion_etats` du vault.]**

### 1.5 Aperçu Amérique du Nord (borne haute d'expansion)

L'Amérique du Nord est le **plus gros pôle** du marché AI SDR/agentique (~35–40 % mondial **[ESTIMATION MODÉLISÉE]**), avec l'écosystème d'incumbents le plus dense (Clay, Apollo.io, Outreach, 11x, Artisan…). Pour une micro-structure francophone, elle représente une **borne haute théorique** (marché B anglophone = 10–20× le SAM francophone) mais **hors de portée sans refonte multi-tenant + go-to-market**, donc pertinente seulement en scénario Palier 3 avancé. Le différenciateur exportable y serait la **conformité-par-donnée** (utile aussi pour CASL côté Canada anglophone et pour les États US à législation stricte type CCPA).

### 1.6 Synthèse chiffrée

| Niveau | Marché B (produit agentique, francophone) | Base |
|---|---|---|
| **TAM** (mondial, agentique prospection+diagnostic) | ~5–8 Md USD (2025) → forte croissance (AI SDR ~29-32 %/an) | Top-down sourcé |
| **SAM** (francophone QC+CH-Romandie+FR, SMB) | ~0,3–0,6 Md (top-down) / ~17–245 M (bottom-up) | 2 méthodes convergentes |
| **SOM** (solo, 3 ans, si Palier 3) | ~18 k–240 k USD/an | Bottom-up pénétration 0,05–0,3 % |
| **SOM marché A** (usage interne, Palier 1) | Levier de CA conseil, non chiffré | Débit borné par validation humaine |

---

## PARTIE 2 — SWOT DE L'OFFRE (corrélée au Scénario A hybride retenu)

Rappel du scénario retenu : **Orchestrateur DAG déterministe « Kemana-Flow »**, Palier 1 = A intégral (orchestrator.py + run_pipeline.py + dag_pipeline.yaml, instance ApiIO unique injectée, zéro réécriture métier) ; Palier 2 = greffe sélective de B (critique de grounding déterministe, conformité-par-donnée YAML, routage modèle) **sans** superviseur-planificateur LLM ; Palier 3 = fragments de C **conditionnés** à une bascule SaaS avérée.

### FORCES (internes)

- **F1 — Déterminisme comme produit, pas comme contrainte [VÉRIFIÉ AS-IS].** Collecte déterministe / LLM cantonné à la rédaction (« le LLM ne fetch jamais »). 365/365 tests verts. Sur un marché où le reproche n°1 fait aux agents est le non-déterminisme et l'hallucination, c'est un **argument de vente**, pas une limite technique.
- **F2 — Auditabilité native [VÉRIFIÉ].** `runs.log` + `api_usage.log` corrélés par `run_id`, vault versionné source de vérité. Réponse directe à l'exigence de traçabilité de l'AI Act et des audits RGPD/CASL.
- **F3 — OPEX plancher et prévisible [VÉRIFIÉ (mécanisme) / ESTIMATION (montant)].** LLM marginal (~15-25 % des appels), cache api_io, budgets bloquants, repli hors-ligne. Le socle tourne à **~0 coût fixe** — l'anti-thèse du Scénario C (200–2 500 USD/mois). Décisif pour une micro-structure.
- **F4 — Conformité-par-construction [VÉRIFIÉ].** opt_out absolu, porte humaine avant tout envoi, minimisation RGPD (Apollo only, Contact 6 champs, zéro scraping LinkedIn). Le Palier 2 ajoute la conformité-par-donnée (`compliance/*.yaml` par marché).
- **F5 — Coût d'implémentation quasi nul [VÉRIFIÉ].** « Zéro réécriture métier » crédible : la couche ajoutée est ~250-400 lignes. Time-to-market = semaines, pas mois.
- **F6 — Séparation données/code [VÉRIFIÉ].** Rubrics, ICP, DAG = YAML. Nouveau persona/marché = nouveau fichier. Onboarding d'un marché < 1 j-personne.

### FAIBLESSES (internes)

- **W1 — J6 outreach = ossature non activable [PLANIFIÉ].** Le maillon qui « ferme la boucle » commerciale (envoi email) n'existe pas en produit ; aucun envoi avant validation juridique + ESP conforme. L'offre s'arrête à la génération de listes Kemana.
- **W2 — Tarifs/budgets à 0 → préflight NO-GO [VÉRIFIÉ].** Aucun run réel possible ni aucun OPEX chiffrable tant que la Phase D n'est pas faite. Bloqueur opérationnel dur.
- **W3 — Goulot humain structurel [VÉRIFIÉ, assumé].** La porte `diagnostique→valide` plafonne le débit aval. On industrialise la découverte, pas la validation — le débit système est piloté par les budgets, pas survendu.
- **W4 — Bus factor 1 [VÉRIFIÉ].** Exploitation, validation et développement reposent sur une personne. Risque de continuité.
- **W5 — Pas de temps réel ni multi-tenant natif [VÉRIFIÉ].** Batch mono-vault. Le passage SaaS exige une refonte de l'ordonnancement (précisément ce que le Palier 3 diffère).
- **W6 — Observabilité basique [VÉRIFIÉ].** Journaux fichiers sans dashboard temps réel/alerting — suffisant pilote, limite pour un run 24/7.

### OPPORTUNITÉS (externes)

- **O1 — Adoption IA PME en rampe raide [VÉRIFIÉ].** 54-57 % des PME utilisent déjà l'IA marketing, >70 % en vente ; investissement IA PME +58 % en 2 ans. Le marché-cible s'équipe **maintenant**.
- **O2 — L'AI Act crée une demande d'agents auditables/déterministes [VÉRIFIÉ macro].** La prospection B2B = profilage → obligations de transparence/traçabilité. Le déterminisme + l'auditabilité (F1-F2) deviennent un **avantage réglementaire différenciant**, pas un simple « nice-to-have ».
- **O3 — Niche francophone conforme sous-servie [ESTIMATION MODÉLISÉE].** Les incumbents AI SDR sont anglophones et « growth-first » (peu outillés CASL/nLPD+art.3 LCD/RGPD). Un outil francophone conforme-par-donnée occupe un espace peu disputé.
- **O4 — Croissance du marché sous-jacent [VÉRIFIÉ].** AI SDR ~29-32 %/an → un SAM qui double en ~2,5-3 ans. La fenêtre de productisation (Palier 3) s'élargit mécaniquement.
- **O5 — « Compliance premium ».** Sur QC/CH/FR, la conformité justifie un tarif supérieur et réduit le risque client — argument de rétention pour le marché B.

### MENACES (externes)

- **T1 — Incumbents AI SDR bien financés [VÉRIFIÉ].** Clay, Apollo, 11x, Artisan… débit et intégrations largement supérieurs. Risque de commoditisation de la découverte.
- **T2 — Dépendance fournisseurs [VÉRIFIÉ AS-IS].** SERP/Apollo/Places/Anthropic : changements de tarif/quota/politique hors contrôle. Mitigé par « tarifs = donnée YAML » et abstraction fournisseur, pas éliminé.
- **T3 — Durcissement réglementaire.** L'AI Act et les régimes anti-spam peuvent alourdir les obligations d'outreach au-delà de ce qu'un solo peut suivre juridiquement (d'où W1 assumé).
- **T4 — Qualité des données tierces [VÉRIFIÉ risque].** Emails obsolètes/faux positifs ICP dégradent conversion et exposition RGPD.
- **T5 — Course à la capacité vs positionnement frugal.** Si le marché valorise le débit brut plus que la conformité/déterminisme, le positionnement (frugal, auditable, solo) devient un marché de niche plutôt qu'un marché de masse.

---

## PARTIE 3 — CORRÉLATION SCÉNARIO RETENU ↔ BESOIN RÉEL DU MARCHÉ

### 3.1 Le besoin réel n'est pas « plus d'agents », c'est « des agents qu'on peut assumer »

Les données de marché convergent sur un point que le Scénario A adresse mieux que B ou C : l'adoption IA PME explose (**O1**), mais le frein dominant reste la **confiance** — hallucination, coût imprévisible, exposition réglementaire. Le besoin réel du segment SMB/consultant francophone se décompose en trois exigences, et **chacune mappe une force du Scénario A** :

| Besoin réel du marché (sourcé/inféré) | Réponse structurelle du Scénario A | Registre |
|---|---|---|
| **Coût maîtrisé** (PME sensibles à l'OPEX, budgets serrés) | LLM marginal + cache + budgets bloquants + repli hors-ligne → OPEX plancher (**F3**) | VÉRIFIÉ (mécanisme) |
| **Fiabilité/non-hallucination** (frein n°1 à l'adoption agentique) | Collecte déterministe, LLM cantonné à la rédaction, QA grounding au Palier 2 (**F1**) | VÉRIFIÉ + PLANIFIÉ |
| **Conformité opposable** (CASL/nLPD/RGPD/AI Act) | opt_out absolu, porte humaine, minimisation, conformité-par-donnée (**F2, F4**) | VÉRIFIÉ + PLANIFIÉ |

Autrement dit : **le marché ne récompense pas la sophistication architecturale (C) ni l'autonomie du planificateur LLM (B), il récompense la maîtrise.** La décision d'écarter le superviseur-planificateur LLM de B et de conditionner C n'est pas un compromis défensif : c'est l'alignement le plus serré sur la structure de coût et de risque du segment cible.

### 3.2 Évolutivité portée par la valeur opérationnelle

L'évolutivité du Scénario A ne vient pas d'une capacité technique à scaler horizontalement (elle est faible — W5), mais de sa **valeur opérationnelle**, qui suit exactement la trajectoire en 3 paliers :

1. **Réduction OPEX comme moteur de marge (Palier 1).** Sur le marché A (usage interne), l'OPEX plancher signifie que **chaque prospect qualifié coûte quelques centimes à quelques dizaines de centimes** **[ESTIMATION MODÉLISÉE, à confirmer Phase D]** contre le temps-homme qu'il remplace. La valeur est immédiate et ne dépend d'aucun financement d'infra. C'est ce qui rend le Palier 1 **auto-finançable**.

2. **Déterminisme comme actif de confiance revendable (Palier 2).** La greffe conformité-par-donnée + critique de grounding déterministe transforme une qualité technique en **argument commercial vérifiable** (F1→O2). C'est le palier qui rend l'offre *productisable* : on peut promettre par contrat « aucune affirmation non adossée à une faille réelle » et le prouver par échantillonnage.

3. **Conformité comme barrière à l'entrée sur la niche (Palier 3).** La bascule SaaS n'emprunte à C que la gateway métrée/budgétée par tenant — soit précisément l'infrastructure de **facturation et d'isolation** qui monétise la conformité déjà acquise. L'évolutivité économique (SOM marché B, §1.4) est **déclenchée par un seuil de tenants**, pas par une intuition — cohérent avec le point mort d'infra modélisé (~20-40 tenants).

**Conclusion de corrélation.** Le Scénario A est le seul des trois dont la valeur opérationnelle (OPEX bas, déterminisme, conformité) est **immédiatement alignée sur les contraintes cardinales d'une micro-structure** ET **cumulable** vers le marché produit sans dette d'architecture. Sa faiblesse d'évolutivité *technique* (W5) est neutralisée par une évolutivité *économique* pilotée par paliers conditionnels : on ne paie l'infrastructure de scale (C) qu'après avoir prouvé la demande (tenants payants). Le risque principal n'est donc pas architectural — il est **exogène** : W2 (Phase D non faite → NO-GO) et W1/T3 (J6 non activable sans cadre juridique). Les deux sont des pré-conditions déjà inscrites dans la décision, pas des angles morts.

### 3.3 Recommandations d'instrumentation (pour dé-risquer les estimations)

Toutes les fourchettes ci-dessus resteront **ESTIMATION MODÉLISÉE** jusqu'à ce que le projet produise ses propres données. Deux gestes suffisent à convertir la moitié de ce rapport en VÉRIFIÉ :
1. **Exécuter la Phase D** (relever tarifs réels, `prix_par_unite` + `releve_le` + budgets>0, `run_preflight` → GO) : débloque le coût réel par fiche → valide/invalide F3 et le SOM marché A.
2. **Instrumenter `taux_conversion_etats`** sur 1-2 cohortes réelles : convertit le SOM marché A (levier de CA conseil) d'hypothèse en mesure, et calibre l'ARPU du marché B.

---

## Sources

- [Precedence Research — Agentic AI Market](https://www.precedenceresearch.com/agentic-ai-market)
- [Fortune Business Insights — Agentic AI Market](https://www.fortunebusinessinsights.com/agentic-ai-market-114233)
- [MarketsandMarkets — Enterprise Agentic AI / AI Agents](https://www.marketsandmarkets.com/Market-Reports/enterprise-agentic-ai-market-219711254.html)
- [Grand View Research — AI in Marketing Market](https://www.grandviewresearch.com/industry-analysis/artificial-intelligence-marketing-market-report)
- [Precedence Research — AI in Marketing Market](https://www.precedenceresearch.com/artificial-intelligence-in-marketing-market)
- [MarketsandMarkets — AI SDR Market](https://www.marketsandmarkets.com/Market-Reports/ai-sdr-market-83561460.html)
- [Custom Market Insights — AI SDR Market](https://www.custommarketinsights.com/report/ai-sdr-market/)
- [ISED Canada — Key Small Business Statistics 2024](https://ised-isde.canada.ca/site/sme-research-statistics/en/key-small-business-statistics/key-small-business-statistics-2024)
- [OFS/kmu.admin.ch — Faits et chiffres PME Suisse](https://www.kmu.admin.ch/kmu/fr/home/savoir-pratique/politique-pme-faits-et-chiffres/chiffres-sur-les-pme/entreprises-et-emplois.html)
- [INSEE — Catégories d'entreprises en France](https://www.insee.fr/en/statistiques/1379706)
- [Capsule CRM — Small business AI adoption statistics 2026](https://capsulecrm.com/blog/small-business-ai-adoption-statistics/)
- [Business.com — 2026 Small Business AI Outlook](https://www.business.com/articles/ai-usage-smb-workplace-study/)

*Réserve méthodologique : les tailles de marché « globales » sont sourcées mais présentent une forte dispersion inter-analystes (définitions hétérogènes). Les découpages géographiques francophones, les ARPU et le coût par fiche sont des ESTIMATIONS MODÉLISÉES explicitées, non des mesures. Aucun tarif fournisseur n'est présenté comme réel : la Phase D reste la pré-condition à tout chiffrage d'OPEX engageant.*

### PESTEL macro concurrentiel
I have enough grounding. Let me write the analysis directly as my final response.

---

# PESTEL MACRO-CONCURRENTIELLE — Secteur agentique marketing & commerce

**Cadre:** forces macro structurant le marché des agents IA appliqués au marketing/prospection B2B, avec panorama concurrentiel et localisation du différenciateur pour l'offre retenue (Scénario A « Kemana-Flow », orchestrateur DAG déterministe).

**Convention de fiabilité utilisée partout ci-dessous:** `[SOURCÉ]` = chiffre issu d'une recherche web citée · `[ESTIMATION MODÉLISÉE]` = calcul avec hypothèses explicites · `[EXISTANT]` / `[PLANIFIÉ]` / `[HYPOTHÈSE]` = statut vis-à-vis de l'AS-IS du dépôt.

---

## 1. PESTEL

### P — Politique

- **Souveraineté numérique et fragmentation des régimes.** La séquence géographique du projet (Québec → Suisse → France) traverse trois régimes de données non alignés: un cadre nord-américain (Canada/CASL), un cadre suisse autonome (nLPD, hors UE mais reconnu adéquat), et le cadre UE. Force macro: il n'existe pas de « marché unique » réglementaire de la prospection agentique — chaque expansion géographique est un coût de conformité discret, pas marginal. **Différenciateur A:** la conformité-par-donnée (`compliance/*.yaml` par marché, Palier 2) transforme cette fragmentation politique en un simple ajout de fichier YAML plutôt qu'en refonte — cohérent avec l'invariant « la rubrique est une donnée » `[EXISTANT: principe; PLANIFIÉ: fichiers compliance]`.
- **Pression politique sur l'automatisation du travail commercial.** Le discours public 2025-2026 sur le remplacement des SDR (Sales Development Reps) par des agents crée un risque réputationnel et un futur risque réglementaire (transparence de l'automatisation). L'EU AI Act impose déjà des obligations de transparence sur les communications générées par IA `[SOURCÉ]`.
- **Autonomie stratégique européenne / hébergement.** Tendance politique de fond favorisant les solutions self-hosted / on-premise. **Différenciateur A:** un système qui « tourne hors-ligne sur un poste/petite VM » `[EXISTANT]` répond nativement à une demande de souveraineté que les plateformes SaaS cloud US ne satisfont pas sans effort.

### E — Économique

- **Marché en hypercroissance mais aux chiffrages dispersés.** Les estimations du marché agentique IA global 2026 vont de **~5,3 à ~10,9 Md USD selon les cabinets**, avec des **CAGR annoncés de ~40 à 49 %** `[SOURCÉ — coherentmarketinsights, grandviewresearch, precedenceresearch, mordorintelligence]`. La dispersion elle-même est un signal: le marché n'est pas stabilisé, les définitions varient. **Prudence:** ces chiffres agrègent tout l'agentique enterprise, pas le sous-segment marketing/prospection — les extrapoler à ce niche serait une sur-précision fallacieuse.
- **Adoption martech massive.** Une source rapporte **90,3 % d'organisations marketing utilisant des agents IA quelque part dans leur stack**, agents de production de contenu (68,9 %) et de découverte d'audience (40,8 %) en tête `[SOURCÉ — martech.org / emarketer, chiffre à traiter comme déclaratif d'éditeur, non audité]`. Implication: l'agentique marketing n'est plus un avantage précoce, c'est une table stakes — le différenciateur se déplace du « faire de l'IA » vers « auditabilité, coût, conformité ».
- **Économie unitaire favorable au frugal.** Structure de coût du Scénario A: LLM marginal (2 nœuds de rédaction), cache réseau, budgets bloquants, repli déterministe hors-ligne. **Coût API par fiche diagnostiquée: quelques centimes à quelques dizaines de centimes USD** `[ESTIMATION MODÉLISÉE — hypothèses: 1 appel synthèse/fiche (~qq milliers tokens in, ~1k out), 1-3 requêtes SERP/candidate, 1 crédit Apollo/contact, 2 requêtes Places/fiche; dominé par Apollo/SERP; À CONFIRMER en Phase D car api_pricing.yaml=0]`. Point d'ancrage externe: Apollo ~99 USD/siège de base, budget réel 150-400 USD/user/mois avec overages; Clay en crédits, paliers 149/349/800 USD/mois `[SOURCÉ — salesmotion.io]`. L'offre A ne vend pas une place de plateforme mais un coût variable plafonné par budget — proposition économiquement distincte pour une micro-structure.
- **Coût fixe = barrière macro pour le solo.** L'AS-IS tourne à **~0 USD de coût fixe** (hors-ligne, batch). Le contre-modèle événementiel/cloud (Scénario C écarté) impliquerait **~200 à 2500 USD/mois de fixe** `[ESTIMATION MODÉLISÉE, cf. scénario C]`. Force macro: pour une consultante solo, l'OPEX fixe est le discriminant économique n°1 — ce qui valide économiquement le choix A au Palier 1.
- **Compression des marges agences.** 62 % des leaders marketing B2B tech déclarent manquer de compétences/budget/stratégie face aux firmes AI-native `[SOURCÉ — coseom/martech]`. Ouverture économique pour un prestataire outillé qui vend le diagnostic industrialisé plutôt que l'heure.

### S — Socioculturel

- **Fatigue du cold outreach et « AI slop ».** La saturation des boîtes mail par des séquences génériques générées par IA dégrade les taux de réponse et provoque un rejet culturel. Contre-tendance: la personnalisation véritablement adossée à des faits. **Différenciateur A:** la règle d'or « le LLM ne fetch jamais, il rédige à partir de faits établis » + QA de grounding (chaque affirmation adossée à `diag.failles`) `[EXISTANT: J1; PLANIFIÉ: nœud critique Palier 2]` produit un audit factuel, à l'opposé du slop.
- **Défiance envers l'automatisation opaque.** Attente sociétale croissante de traçabilité (« pourquoi ai-je été contacté? »). L'auditabilité totale (run_id corrélant `runs.log` ⇄ `api_usage.log` ⇄ vault) `[EXISTANT]` est un actif socioculturel autant que technique.
- **Human-in-the-loop comme norme émergente.** La pratique gagnante 2026 décrite par le marché est « AI-does-research-then-human-sends » `[SOURCÉ — digitalapplied/salesmotion]`. C'est exactement le design du Scénario A: porte humaine obligatoire `diagnostique→valide`, envoi J6 human-gated. L'offre est alignée avec la norme socioculturelle plutôt qu'en avance risquée dessus.

### T — Technologique

- **Standardisation de l'orchestration agentique.** 2025-2026 voit l'émergence de patterns (DAG déterministe vs superviseur LLM vs event-driven) et de protocoles d'interopérabilité (MCP, tool-use à schéma strict). Le Scénario A parie sur le pôle **déterministe** de ce spectre — choix technologique conservateur assumé, à contre-courant de la mode du « superviseur-planificateur LLM » (rejeté explicitement dans la décision).
- **Commoditisation du LLM + leviers de coût.** Prompt caching (-90 % input caché), Batch API (-50 %), routage multi-modèle (petit modèle par défaut). Force macro: le coût du LLM baisse et devient pilotable par YAML. **Différenciateur A (Palier 2):** `routing.yaml` (Haiku par défaut, modèle fort réservé aux cas signalés) capture ce levier sans réécrire le code.
- **Buyer-side AI / GEO.** Montée des assistants IA côté acheteur qui rebattent la découverte de marque (Generative Engine Optimization) `[SOURCÉ — emarketer]`. Signal faible pertinent: le diagnostic de marque J1 pourrait à terme intégrer une dimension « visibilité dans les moteurs génératifs » — piste d'évolution de rubrique, `[HYPOTHÈSE]`.
- **Risque technologique — dépendance fournisseurs.** SERP/Apollo/Places/Anthropic hors du contrôle du projet (tarifs, quotas, SKU). Mitigation architecturale: tarifs en donnée YAML, bus api_io unique abstrayant les fournisseurs `[EXISTANT]`.

### E — Écologique

- **Coût énergétique/carbone de l'inférence LLM sous surveillance.** Pression montante pour un reporting environnemental de l'IA. Force macro faible aujourd'hui mais croissante. **Différenciateur A involontaire mais réel:** un système qui minimise les appels LLM (déterminisme dominant, repli hors-ligne, cache, batch) a une empreinte inférence structurellement basse — argument ESG opportuniste, non chiffré `[HYPOTHÈSE — aucune mesure carbone dans l'AS-IS]`.
- **Frugalité = alignement écologique.** Le choix « pas de service permanent, batch sur petite VM » vs infrastructure cloud always-on multi-AZ a un corollaire écologique (moins de compute au repos). À ne pas survendre: non mesuré.

### L — Legal

- **EU AI Act — calendrier d'exécution serré.** Obligations pour systèmes à haut risque (évaluation de conformité, documentation technique, marquage CE, enregistrement) **applicables au 2 août 2026** `[SOURCÉ — legalnodes, gdprlocal]`. La prospection IA relève typiquement du « risque limité » (obligations de transparence) mais peut basculer en « haut risque » selon l'usage `[SOURCÉ]`. Sanctions: **jusqu'à 35 M€ ou 7 % du CA mondial** (usages prohibés), **15 M€ ou 3 %** (haut risque sans garde-fous) `[SOURCÉ — legalnodes]`.
- **Durcissement de l'exécution GDPR sur l'outreach IA.** Une source rapporte **67 % des autorités de protection UE ayant accru leurs actions** contre l'outreach IA sur 12 mois `[SOURCÉ — growthspreeofficial; chiffre d'éditeur, non primaire — à traiter avec réserve]`. Violations types: absence de disclosure IA, liens de désinscription manquants dans les séquences rédigées par IA, capture de consentement absente `[SOURCÉ]`.
- **Empilement CASL / nLPD + art. 3 LCD / RGPD + AI Act.** Chaque marché du projet ajoute une couche. **Différenciateur A décisif:** opt-out absolu testé, minimisation RGPD (Apollo-only, Contact 6 champs, `contact_email_source` obligatoire, zéro scraping LinkedIn), porte humaine avant tout envoi, J6 non activable sans validation juridique `[EXISTANT pour J1-J5; PLANIFIÉ/OSSATURE pour J6]`. La conformité est un invariant d'architecture, pas une fonctionnalité — position légale défendable là où les plateformes SaaS externalisent le risque sur l'utilisateur.
- **Réserve honnête:** aucune de ces briques ne dispense de la validation juriste exigée avant tout envoi réel (CASL/nLPD/LCD/RGPD/AI Act). Le legal est le facteur bloquant explicite de J6.

---

## 2. Panorama concurrentiel

Cinq catégories d'acteurs, leur logique économique, et l'espace laissé libre.

### (a) Plateformes martech/adtech intégrées
**Acteurs réels:** Salesforce (Agentforce, agents **Piper** SDR et **Hunter** de prospection), HubSpot (agents IA embarqués dans le CRM), Demandbase (orchestration ABM par agents) `[SOURCÉ — futurumgroup, martech.org]`.
**Logique:** vendre l'agent comme extension d'une suite déjà installée; capture par la donnée CRM existante; ROI « verticalisé embarqué ».
**Faiblesse exploitable:** lourdeur, coût par siège, opacité de l'auditabilité, dépendance à l'écosystème. Inadaptées à une consultante solo cherchant déterminisme et souveraineté.

### (b) Agents IA verticalisés (AI SDR / prospection)
**Acteurs réels:** Apollo.io (base de contacts + séquençage + IA, ~99 USD/siège base), Clay (enrichissement + workflow, crédits 149-800 USD/mois), Instantly, Lemlist, Outreach, AiSDR `[SOURCÉ — salesmotion, digitalapplied, topo.io]`.
**Logique:** « research-then-send », volume outbound, credits d'enrichissement. Le marché converge vers « AI fait la recherche, humain envoie » `[SOURCÉ]`.
**Faiblesse exploitable:** produisent du contact-à-grande-échelle, **pas un audit de marque diagnostique**. Peu déterministes, peu auditables ligne à ligne, cloud US (frictions nLPD/souveraineté). Coût fixe mensuel par siège vs coût variable plafonné.

### (c) Orchestrateurs généralistes / automation
**Acteurs réels:** n8n, Make, Activepieces (open-source, 640+ intégrations), Tray, Lyzr, Gumloop `[SOURCÉ — activepieces, marketbetter]`.
**Logique:** tuyauterie générique connectant des briques; flexibilité maximale, aucune connaissance métier.
**Faiblesse exploitable:** aucune rubrique de diagnostic marketing, aucune machine à états métier, aucun garde-fou conformité intégré. Le Scénario A est précisément un orchestrateur DAG **spécialisé** (préflight → découverte → diagnostic → export) — même paradigme technique, mais chargé de sens métier + conformité que les généralistes n'ont pas.

### (d) Agences augmentées
**Acteurs:** agences marketing/branding intégrant l'IA à leur delivery (catégorie diffuse, pas de leader unique cité).
**Logique:** vendre l'expertise humaine + IA en coulisse; facturation au projet/à l'heure.
**Faiblesse exploitable:** 62 % des leaders B2B tech se disent sous-outillés face aux AI-native `[SOURCÉ]`. **C'est le positionnement natif de la consultante** — mais l'offre A lui donne l'outillage industriel qui manque à la catégorie, potentiellement productisable.

### (e) DIY / open-source
**Acteurs réels:** n8n, SendPortal (email open-source), Yalc (« operator OS » en markdown, tourne sur la machine locale), stacks maison `[SOURCÉ — thecmo, yalc.ai]`.
**Logique:** contrôle total, coût logiciel nul, charge d'intégration sur l'utilisateur.
**Faiblesse exploitable:** effort d'assemblage, pas de conformité prête, pas de QA de grounding. Le Scénario A **est** une solution DIY aboutie et testée (365 tests) — il occupe cette case mais avec la rigueur d'un produit.

---

## 3. Où se loge le différenciateur de l'offre retenue (Scénario A)

Le marché est saturé sur « générer du contact à l'échelle » et sur « agent IA embarqué ». Il est **peu couvert** sur l'intersection suivante, qui définit l'espace défendable de Kemana-Flow:

1. **Diagnostic de marque déterministe et auditable** (pas de la génération de contacts) — collecte de faits séparée de la rédaction LLM, traçable au run_id. Les acteurs (b)/(c) ne font pas d'audit de marque; les acteurs (a) le font sans auditabilité ligne à ligne.
2. **Conformité-par-donnée multi-juridiction** (CASL/nLPD/LCD/RGPD/AI Act en YAML) — invariant d'architecture, pas option. Aucun concurrent frugal ne l'offre nativement; c'est le levier legal + politique le plus fort face à la fragmentation réglementaire.
3. **OPEX plancher + souveraineté hors-ligne** — ~0 coût fixe, batch, repli déterministe. Répond à la contrainte économique du solo ET à la tendance politique/écologique de souveraineté/frugalité, là où (a) et le SaaS cloud imposent un coût fixe et un hébergement US.
4. **Alignement avec la norme socioculturelle human-in-the-loop** — « research then human sends » est déjà le pattern gagnant du marché; l'offre est conforme, pas en pari risqué.

**Ligne de crête stratégique (honnête):** ces différenciateurs sont des forces sur les axes *auditabilité / conformité / coût / souveraineté*, PAS sur *débit / échelle / temps réel* — où les plateformes intégrées et l'événementiel (C) dominent. Le positionnement défendable est donc « diagnostic de marque conforme, frugal et auditable pour micro-structures et marchés réglementés », **pas** « machine à outbound de masse ». Tenter le second terrain reviendrait à affronter Apollo/Clay/Salesforce sur leurs forces.

**Réserves anti-hallucination récapitulées:** les tailles de marché et CAGR (§E) sont des agrégats de cabinets aux définitions divergentes, non spécifiques au niche marketing/prospection; les chiffres « 90,3 % », « 67 % », « 62 % » sont déclaratifs d'éditeurs martech, non des données primaires auditées; tous les coûts unitaires de l'offre restent des ESTIMATIONS MODÉLISÉES tant que la Phase D n'a pas renseigné `api_pricing.yaml` (préflight NO-GO jusque-là). Aucun tarif fournisseur n'a été inventé: Apollo/Clay proviennent de salesmotion.io.

**Sources:**
- https://www.emarketer.com/content/faq-on-martech--how-ai-agents-composable-stacks-reshaping-marketing-technology-2026
- https://futurumgroup.com/insights/salesforce-bets-on-agentic-marketing-will-unified-ai-agents-redefine-martech-roi/
- https://martech.org/how-ai-agents-will-reshape-every-part-of-marketing-in-2026/
- https://www.coseom.com/ai-agents-b2b-marketing/
- https://www.coherentmarketinsights.com/industry-reports/agentic-ai-market
- https://www.grandviewresearch.com/industry-analysis/enterprise-agentic-ai-market-report
- https://www.precedenceresearch.com/agentic-ai-market
- https://www.mordorintelligence.com/industry-reports/agentic-ai-market
- https://www.legalnodes.com/article/eu-ai-act-2026-updates-compliance-requirements-and-business-risks
- https://gdprlocal.com/eu-ai-act-summary/
- https://www.law.berkeley.edu/research/bclt/bclt-legal-analysis/eu-ai-act/
- https://www.growthspreeofficial.com/blogs/ai-compliance-b2b-saas-b2b-marketing-2026-gdpr-ccpa-eu-ai-act-brand-safety-framework
- https://www.smartlead.ai/blog/ai-and-data-privacy-concerns
- https://salesmotion.io/blog/apollo-pricing
- https://salesmotion.io/clay-vs-apollo
- https://www.digitalapplied.com/blog/ai-sdr-platforms-apollo-outreach-clay-lemlist-2026
- https://www.topo.io/blog/best-ai-outbound-prospecting
- https://www.activepieces.com/blog/outbound-email-automation
- https://www.yalc.ai/blog/best-ai-sdr-platforms-2026/
- https://thecmo.com/tools/best-open-source-email-marketing-software/

### PESTEL axe digital
PESTEL — AXE DIGITAL / TECHNOLOGIQUE
Secteur : agents de prospection B2B (martech/adtech agentique)
Scénario technique de référence : **Scénario A « Kemana-Flow »** (orchestrateur DAG déterministe, Palier 1 immédiat ; greffes B au Palier 2 ; fragments C conditionnés au Palier 3).

Convention de preuve utilisée partout : **[VÉRIFIÉ]** = attesté dans le dépôt AS-IS ou sourcé web ; **[PLANIFIÉ]** = décidé mais pas encore codé ; **[HYPOTHÈSE / ESTIMATION MODÉLISÉE]** = projection avec hypothèses explicites, non engageante.

---

## P — POLITIQUE (souveraineté numérique, dépendance fournisseurs, géographie réglementaire)

**Facteur 1 — Séquence géographique Québec → Suisse → France = 3 régimes politiques de la donnée non alignés.** Le projet cible trois juridictions dont les cadres divergent : CASL (Canada/QC), nLPD + art. 3 LCD (Suisse, hors UE, décision d'adéquation UE en vigueur), RGPD + AI Act (UE/France). Aucune surcouche « conformité » ne peut être codée en dur.
→ **Implication A** : conforte la décision structurante « conformité-par-donnée » du Palier 2 (`compliance/casl-quebec.yaml`, `nlpd-ch.yaml`, `rgpd-fr.yaml`) comme **nœuds/données du DAG**, pas comme code. Cohérent avec l'invariant existant « la rubrique est une donnée » [VÉRIFIÉ dans CLAUDE.md]. Le nœud Conformité bloquant est **[PLANIFIÉ]**, aujourd'hui absent du dépôt.

**Facteur 2 — Dépendance à des fournisseurs sous juridiction étrangère (US pour SERP/Apollo/Anthropic).** Risque politique de lock-in, de changement unilatéral de tarif/quota/politique d'usage.
→ **Implication A** : le bus unique `api_io.py` [VÉRIFIÉ] est précisément le point d'abstraction qui permet de substituer un fournisseur SERP sans toucher au métier. La grille tarifaire en YAML (`api_pricing.yaml`) [VÉRIFIÉ] rend un changement de fournisseur = édition de donnée. Le Scénario A n'ajoute aucune dépendance politique nouvelle par rapport à l'AS-IS (contrairement à C, qui ajoute un cloud managé).

**Facteur 3 — Souveraineté/hébergement.** Le SaaS multi-tenant (Scénario C) impliquerait un choix de région cloud et une exposition à des exigences de localisation des données (surtout pour des prospects UE).
→ **Implication A** : l'AS-IS tourne **hors-ligne, sans coût fixe d'infrastructure** [VÉRIFIÉ : aucun service permanent dans le dépôt]. Le rejet de C au stade actuel neutralise la question de souveraineté d'hébergement tant qu'il n'y a pas de bascule SaaS. C'est un **avantage politique** de A : la donnée reste sur le poste de l'opératrice.

---

## E — ÉCONOMIQUE (OPEX, structure de coûts API, marché martech)

**Facteur 4 — Coût variable dominé par les API tierces, pas par le compute.** Ordres de grandeur de **prix de liste publics** (à traiter comme externes, NON injectés dans la décision — voir garde-fou) :
- SerpApi : ~25 USD / 1 000 recherches en entrée de gamme, jusqu'à ~9 USD / 1 000 à l'échelle ([SerpApi pricing 2026, apiserpent](https://apiserpent.com/blog/serpapi-pricing-explained) ; [searchcans](https://www.searchcans.com/blog/serpapi-pricing-alternatives-comparison-2026/)).
- Apollo : email finder ~10 crédits / contact, plans ~49–119 USD/user/mois ([Apollo pricing 2026, prospeo](https://prospeo.io/s/apolloio-pricing) ; [enrich.so](https://www.enrich.so/blog/apollo-pricing-breakdown)).

⚠️ **Ces chiffres sont des prix de liste vendeurs, cités pour ordre de grandeur uniquement.** Ils correspondent exactement aux sources que la revue a signalées comme risque d'hallucination (apiserpent/warmly). Ils NE remplacent PAS le relevé réel. Le dépôt a `prix_par_unite = 0.0` et `releve_le = null` [VÉRIFIÉ].
→ **Implication A** : impose la **Phase D obligatoire AVANT tout run réel et toute porte budgétaire** (décision structurante) : renseigner `prix_par_unite`, `releve_le`, `budgets > 0`, puis `run_preflight.py` → exiger GO. Toute projection OPEX reste **[ESTIMATION MODÉLISÉE]** jusque-là.

**Facteur 5 — Coût LLM en baisse structurelle et pilotable.** Le poste tokens est le plus compressible du panel : prompt caching, mode batch, et routage de modèle (petit modèle par défaut).
→ **Implication A** : le LLM est déjà **marginal par conception** — cantonné à 2 nœuds terminaux (synthèse J1, brouillon J6) [VÉRIFIÉ : `synthesis.py` seul point LLM ; repli déterministe hors-ligne]. Le `routing.yaml` (Haiku par défaut, modèle fort réservé aux cas signalés) est **[PLANIFIÉ Palier 2]**. **[ESTIMATION MODÉLISÉE]** : sous hypothèses ~1 appel synthèse/fiche + petit modèle + cache, le LLM reste minoritaire dans le coût réseau total (SERP+Apollo+Places dominent le volume). Hypothèses à valider par `run_usage.py` sur données réelles.

**Facteur 6 — Rupture de coût fixe entre frugal (A) et cloud-native (C).** L'AS-IS = ~0 fixe. Un SaaS événementiel = coût fixe mensuel non nul (bus, base vectorielle, runtime, observabilité), qui n'a de sens qu'amorti sur plusieurs tenants payants.
→ **Implication A** : la contrainte cardinale « micro-structure solo, OPEX plancher » disqualifie C au stade actuel et valide A comme colonne vertébrale. Les fragments C (gateway par tenant, isolation, coût par tenant) sont **[PLANIFIÉ Palier 3, conditionné à un seuil de tenants payants défini à l'avance]**.

**Facteur 7 — Marché martech en adoption agressive de l'agentique.** Signaux 2026 : ~90 % des organisations marketing déclarent utiliser des agents IA quelque part dans leur stack (recherche Martech de S. Brinker citée), mais seulement ~17 % des organisations ont réellement *déployé* des agents et ~23 % en ont *industrialisé* un en production ([Gartner CIO Survey / McKinsey, via joget](https://joget.com/ai-agent-adoption-in-2026-what-the-analysts-data-shows/)) ; Gartner projette 40 % des applications d'entreprise intégrant des agents « task-specific » fin 2026 ([Gartner press release](https://www.gartner.com/en/newsroom/press-releases/2025-08-26-gartner-predicts-40-percent-of-enterprise-apps-will-feature-task-specific-ai-agents-by-2026-up-from-less-than-5-percent-in-2025)). Contrepoint : Gartner estime que >40 % des projets agentiques risquent l'abandon d'ici 2027 faute de gouvernance/observabilité/ROI ([onereach/joget](https://joget.com/ai-agent-adoption-in-2026-what-the-analysts-data-shows/)).
→ **Implication A** : l'écart « déclaré vs industrialisé » et le risque d'abandon valident le pari du chef de projet : **industrialiser du déterministe auditable** (A) plutôt qu'un superviseur-planificateur LLM (rejeté de B). La différenciation commerciale de la consultante est précisément la **gouvernance-par-conception** (run_id, ledger, préflight) que 40 % des projets n'ont pas.

---

## S — SOCIAL / SOCIÉTAL (acceptabilité, goulot humain, confiance)

**Facteur 8 — Défiance croissante envers la prospection automatisée et le contenu « IA ».** Le B2B froid est saturé ; l'acceptabilité repose sur la pertinence et la transparence.
→ **Implication A** : la **porte humaine `diagnostique → valide`** [VÉRIFIÉ : machine à états, agent limité à `decouvert → diagnostique`] et la revue de brouillon J6 sont un atout social, pas seulement conformité. Le mini-audit adossé à des failles réelles (QA J1) [VÉRIFIÉ] positionne l'approche comme « diagnostic à valeur » plutôt que spam.

**Facteur 9 — Goulot humain structurel (bus factor 1).** L'opératrice solo est le facteur limitant réel du débit (validation manage-by-exception).
→ **Implication A** : réserve **assumée explicitement** par la décision. Le débit amont est piloté par les budgets, pas survendu au niveau système. A n'industrialise pas la validation — et ne le prétend pas. C'est une limite honnête à porter en porte de décision, pas un défaut à masquer.

**Facteur 10 — Attente sociétale de traçabilité/explicabilité de l'automatisation.**
→ **Implication A** : l'auditabilité ligne-à-ligne (`runs.log` + `api_usage.log` corrélés par `run_id`) [VÉRIFIÉ en partie : buses présents ; corrélation `run_id` bout-en-bout = **[PLANIFIÉ]** via `orchestrator.py` à créer] répond directement à cette attente.

---

## T — TECHNOLOGIQUE (maturité IA/agents, martech, canaux, plateformes)

**Facteur 11 — Maturité de l'IA générative et des agents.** L'agentique est en phase de « désillusion » chez Gartner (Hype Cycle Agentic AI 2026) : le déterminisme et l'observabilité redeviennent des critères de sélection.
→ **Implication A** : le choix d'un **orchestrateur DAG déterministe** (tri topologique, ~250–400 lignes, zéro logique métier) [PLANIFIÉ] plutôt qu'un superviseur LLM est aligné sur la maturité réelle du marché. Le LLM ne **route jamais**, ne **fetch jamais** [VÉRIFIÉ comme règle d'or J1] — c'est structurellement anti-hallucination-au-niveau-orchestration.

**Facteur 12 — Écosystème martech/adtech fragmenté (SERP, CRM, Places, ESP).** Chaque canal a son API, son quota, sa structure de coût.
→ **Implication A** : les **collecteurs enfichables** (héritent de `Collector`, `safe_collect`) [VÉRIFIÉ] et le bus `api_io` unique absorbent la fragmentation. Ajouter un canal = ajouter un collecteur, sans toucher aux autres. Interface Kemana = **fichier CSV/JSONL hors vault** [VÉRIFIÉ], pas d'API — découplage volontaire de l'aval.

**Facteur 13 — Déliverabilité email / anti-spam (canal outreach J6).** Depuis fév. 2024, Gmail/Yahoo imposent aux expéditeurs de masse (>5 000 msg/jour vers Gmail) : SPF **et** DKIM, DMARC (min. `p=none`), désabonnement en un clic (RFC 8058), taux de plainte < 0,3 % (viser < 0,1 %) ([Gmail sender guidelines](https://support.google.com/mail/answer/81126) ; [Mailgun](https://www.mailgun.com/state-of-email-deliverability/chapter/yahoogle-bulk-senders/)).
→ **Implication A** : contrainte **technique dure** sur J6, distincte du juridique. Elle impose le choix d'un **ESP conforme** (authentification, list-unsubscribe, suppression list) comme pré-condition d'activation, en plus du feu vert juridique. J6 est **[PLANIFIÉ, OSSATURE human-gated NON activable]** — cohérent : aucun code outreach en AS-IS [VÉRIFIÉ]. Le seuil de 5 000/jour rend d'ailleurs improbable qu'un pilote solo déclenche le régime « bulk » à court terme **[HYPOTHÈSE : volumes pilote < seuil]** — mais les règles d'authentification et d'opt-out s'appliquent quel que soit le volume.

**Facteur 14 — Plateformes « personnes » (LinkedIn/Facebook) hostiles au scraping.**
→ **Implication A** : décision existante « zéro scraping LinkedIn, données personnes via Apollo uniquement » [VÉRIFIÉ], à la fois choix technique (robustesse) et minimisation RGPD. A la conserve telle quelle.

**Facteur 15 — Volatilité des collecteurs (changements HTML/SKU/quota).**
→ **Implication A** : `safe_collect` isole les échecs, mode dégradé par collecteur [VÉRIFIÉ]. Le DAG s'arrête proprement sur `BudgetExceeded` et reprend idempotent [VÉRIFIÉ pour J4 ; extension à l'orchestrateur = **[PLANIFIÉ]**].

---

## E — ENVIRONNEMENTAL / OPÉRATIONNEL (empreinte, résilience, exploitation)

**Facteur 16 — Empreinte de calcul.** Batch frugal sur un poste vs service cloud permanent 24/7.
→ **Implication A** : le batch planifié (cron J7, préflight en pré-condition) [VÉRIFIÉ : préflight existe ; cron = **[PLANIFIÉ]**] et le repli déterministe hors-ligne minimisent l'empreinte. A a l'empreinte la plus faible du panel ; C (scale-to-zero) atténue mais réintroduit un socle permanent.

**Facteur 17 — Résilience/reprise sans SRE en interne.** Une micro-structure n'a pas d'astreinte.
→ **Implication A** : l'**idempotence + cache `api_io` + dédup vault** [VÉRIFIÉ] permettent une reprise sans intervention experte. Le **verrou de run (lockfile/run_id)** refusant un second démarrage concurrent (cron + manuel) est une décision structurante **[PLANIFIÉE]**, aujourd'hui absente — risque réel d'écritures entrelacées sur le vault fichier.

**Facteur 18 — Observabilité basique (journaux fichiers, pas de dashboard temps réel).**
→ **Implication A** : suffisant pour un pilote [assumé comme limite de A]. `run_usage.py` + snapshot vault [VÉRIFIÉ] donnent l'agrégat coût. Pas d'alerting proactif — acceptable tant que le débit est borné par l'humain.

---

## L — LÉGAL (AI Act, data privacy, impact opérationnel)

**Facteur 19 — AI Act : calendrier et qualification du système.** Entrée en application échelonnée : pratiques interdites + littératie IA depuis fév. 2025 ; obligations GPAI depuis août 2025 ; **transparence (art. 50) + systèmes à haut risque Annexe III + application au 2 août 2026** ([Commission européenne / digital-strategy](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai) ; [artificialintelligenceact.eu timeline](https://artificialintelligenceact.eu/implementation-timeline/) ; [DLA Piper](https://www.dlapiper.com/en-us/insights/publications/2025/08/latest-wave-of-obligations-under-the-eu-ai-act-take-effect)).
- **Qualification [HYPOTHÈSE à faire trancher par un juriste]** : un système qui *rédige un mini-audit* et *personnalise un email* à partir de faits déterministes est vraisemblablement **hors « haut risque » Annexe III** (pas de scoring de personnes physiques à finalité protégée type crédit/emploi). Mais l'**obligation de transparence art. 50** (informer que le contenu / l'interaction est généré par IA) est plausiblement applicable au brouillon d'email et devra être tranchée.
→ **Implication A** : renforce que J6 reste **NON activable** avant validation juridique CASL/nLPD+art.3 LCD/RGPD **et AI Act** [décision structurante VÉRIFIÉE dans le mandat]. Le nœud Conformité (Palier 2) doit porter la **mention de transparence IA** comme donnée YAML par marché **[PLANIFIÉ]**. L'échéance opérationnelle **2 août 2026** est déjà passée à la date du run (30 juillet 2026 → août imminent) : la transparence art. 50 est donc un impératif présent, pas futur, dès l'activation de tout envoi UE.

**Facteur 20 — Data privacy / minimisation.** RGPD (minimisation, base légale, source de la donnée), CASL (consentement plus strict), nLPD (registre, information).
→ **Implication A** : minimisation **native** — `Contact = 6 champs` (extra="forbid"), `contact_email_source` toujours renseigné [VÉRIFIÉ]. `opt_out: true` = exclusion absolue à l'export ET à l'outreach [VÉRIFIÉ pour export ; outreach = **[PLANIFIÉ]**]. Aucune réécriture nécessaire pour A.

**Facteur 21 — Auditabilité comme preuve légale.** Face à une plainte, il faut reconstruire *pourquoi* un prospect a été contacté.
→ **Implication A** : event store non requis — le **vault versionné + `runs.log` append-only** est déjà la source de vérité auditable [VÉRIFIÉ]. C'est l'argument central du **rejet de C** (qui inverserait l'invariant J2 en faisant du vault un simple read-model). La reproductibilité déterministe (hors 2 nœuds LLM) est une **force légale** de A.

**Facteur 22 — Marquage des contenus synthétiques (art. 50 AI Act).** Obligation émergente de marquer/rendre détectable le contenu généré.
→ **Implication A [PLANIFIÉ / à préciser]** : le brouillon d'email J6 devra porter une mention/traçabilité IA. Faible coût d'implémentation (donnée de template), mais à ne pas oublier avant activation.

---

## Synthèse — priorités d'implication pour le Scénario A

| # | Facteur digital le plus structurant | Statut | Action A directe |
|---|---|---|---|
| 1 | AI Act art. 50 (transparence) échéance août 2026 **présente** | [PLANIFIÉ] | Nœud Conformité + mention IA par marché (Palier 2) avant tout envoi |
| 2 | Déliverabilité Gmail/Yahoo 2024 (SPF/DKIM/DMARC/opt-out 1-clic) | [VÉRIFIÉ sourcé] | ESP conforme = 2ᵉ pré-condition d'activation J6, en sus du juridique |
| 3 | Tarifs API réels inconnus (`pricing.yaml = 0`, préflight NO-GO) | [VÉRIFIÉ défaut] | **Phase D obligatoire** → GO avant 1ᵉʳ run réel |
| 4 | Budgets non injectés au runtime dans ApiIO | [VÉRIFIÉ défaut] | Instance ApiIO **unique** en tête de DAG, budgets depuis YAML (Palier 1) |
| 5 | `run_diagnostic` sans api_io | [VÉRIFIÉ défaut] | Injection api_io dans le nœud diagnostic (Palier 1) |
| 6 | Concurrence cron + manuel sur vault fichier | [PLANIFIÉ] | Verrou de run (lockfile/run_id) |
| 7 | Maturité agentique : déterminisme > superviseur LLM | [VÉRIFIÉ marché] | DAG déterministe ; refus du planificateur LLM de B |
| 8 | Coût fixe cloud disproportionné (souveraineté/OPEX) | [VÉRIFIÉ] | C écarté ; fragments réservés Palier 3 sous seuil tenants |

**Garde-fou respecté** : aucun chiffre de marché n'est présenté comme fondement de la décision. Les prix SerpApi/Apollo sont des **prix de liste vendeurs cités pour ordre de grandeur**, explicitement à revérifier en Phase D — ce sont les mêmes sources signalées comme risque d'hallucination dans la revue, donc neutralisées ici par étiquetage et exclusion du calcul décisionnel. Les seuils réglementaires (dates AI Act, règles Gmail/Yahoo) sont **sourcés**. Toute projection OPEX ou de débit est **[ESTIMATION MODÉLISÉE]** avec hypothèses explicites, jamais engageante.

Sources : [Commission européenne — AI Act](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai) · [artificialintelligenceact.eu — timeline](https://artificialintelligenceact.eu/implementation-timeline/) · [DLA Piper — AI Act obligations](https://www.dlapiper.com/en-us/insights/publications/2025/08/latest-wave-of-obligations-under-the-eu-ai-act-take-effect) · [Gmail sender guidelines](https://support.google.com/mail/answer/81126) · [Mailgun — Yahoogle bulk senders](https://www.mailgun.com/state-of-email-deliverability/chapter/yahoogle-bulk-senders/) · [Gartner — 40% enterprise apps agents 2026](https://www.gartner.com/en/newsroom/press-releases/2025-08-26-gartner-predicts-40-percent-of-enterprise-apps-will-feature-task-specific-ai-agents-by-2026-up-from-less-than-5-percent-in-2025) · [joget — Gartner/McKinsey adoption](https://joget.com/ai-agent-adoption-in-2026-what-the-analysts-data-shows/) · [SerpApi pricing 2026](https://apiserpent.com/blog/serpapi-pricing-explained) · [Apollo pricing 2026](https://prospeo.io/s/apolloio-pricing)

---
<a id="4"></a>
## 4. Objectif 3 — Offre de service SaaS & chiffrage
# OFFRE DE SERVICE SaaS — « Kemana-Flow » : diagnostic de marque déterministe, conforme et auditable pour micro-structures francophones

> **Périmètre & garde-fous.** Cette offre productise le **Scénario A retenu** (orchestrateur DAG déterministe, OPEX plancher). Conventions : **[VÉRIFIÉ]** = AS-IS du dépôt ou source web citée · **[PLANIFIÉ]** = décidé, non codé (J6, Phase D, Paliers 2-3) · **[ESTIMATION MODÉLISÉE]** = calcul à hypothèses explicites, en fourchette. **Deux pré-conditions dures encadrent TOUTE monétisation** : (1) **Phase D** — tant que `api_pricing.yaml = 0` et préflight NO-GO [VÉRIFIÉ], aucun coût-par-fiche n'est engageant ; (2) **validation juridique + ESP conforme** avant activation J6 [PLANIFIÉ]. Aucun tarif fournisseur n'est présenté comme réel.

---

## 1. PROPOSITION DE VALEUR

**Phrase-noyau :** *« Le seul système de prospection B2B qui vous livre un mini-audit de marque factuel, traçable ligne à ligne, et conforme par conception (CASL / nLPD / RGPD / AI Act) — à coût variable plafonné, sans infrastructure cloud à payer. »*

Trois promesses différenciantes, chacune adossée à une force AS-IS (et non à une aspiration) :

| Promesse client | Mécanisme AS-IS | Registre |
|---|---|---|
| **« Zéro invention »** — chaque affirmation du diagnostic est adossée à une faille réelle | Collecte déterministe séparée de la rédaction LLM ; « le LLM ne fetch jamais » ; QA de grounding | [VÉRIFIÉ J1] + [PLANIFIÉ nœud critique P2] |
| **« Facture prévisible »** — vous ne pouvez pas dépasser votre budget | Budgets bloquants `api_io`, cache, repli déterministe hors-ligne, LLM marginal (~15-25 % des appels) | [VÉRIFIÉ mécanisme] / [ESTIMATION montant] |
| **« Opposable en cas de contrôle »** — reconstruire *pourquoi* un prospect a été contacté | `runs.log` + `api_usage.log` corrélés par `run_id`, vault versionné = source de vérité ; opt-out absolu ; minimisation (Apollo-only, Contact 6 champs) | [VÉRIFIÉ export] / [PLANIFIÉ corrélation run_id bout-en-bout] |

**Ce que l'offre N'EST PAS** (honnêteté du positionnement) : pas une machine à outbound de masse, pas de débit temps réel, pas de scraping LinkedIn. Le débit est **borné par la validation humaine** [VÉRIFIÉ, assumé] — c'est un choix de conformité, pas un défaut masqué.

---

## 2. POSITIONNEMENT

**Énoncé :** *« Diagnostic de marque conforme, frugal et auditable — pour consultants marketing et micro-agences opérant sur des marchés réglementés francophones. »*

Carte de positionnement (2 axes issus du PESTEL) : **auditabilité/conformité** (élevée) × **débit/échelle** (volontairement modéré). Kemana-Flow occupe le quadrant *haute conformité / débit modéré* — vide chez les concurrents :

- **vs Apollo / Clay / AI SDR** [SOURCÉ, salesmotion/digitalapplied] : eux = contact-à-l'échelle, cloud US, coût par siège, peu auditables ligne-à-ligne. Nous = **audit de marque** (pas de la liste de contacts) + souveraineté hors-ligne.
- **vs Salesforce Agentforce SDR / HubSpot** : eux = agent embarqué dans une suite lourde. Nous = frugal, sans lock-in de suite.
- **vs n8n / Make / DIY** : eux = tuyauterie générique sans métier ni conformité. Nous = orchestrateur DAG **spécialisé** métier + conformité-par-donnée.

> ⚠️ Correction de revue intégrée : je ne reprends PAS l'attribution erronée « Salesforce Piper/Hunter » (Piper = Qualified.ai). Concurrents Salesforce cités : **Agentforce SDR** uniquement.

**Angle commercial dominant :** le *compliance premium*. L'échéance **AI Act art. 50 (transparence) au 2 août 2026** [SOURCÉ, legalnodes / artificialintelligenceact.eu] transforme l'auditabilité d'un « nice-to-have » en argument réglementaire présent. Sur QC/CH/FR, la conformité justifie un tarif supérieur et réduit le risque client [O2/O5 de l'étude].

---

## 3. PACKAGING / TIERS

Deux « visages » du produit → deux lignes d'offre. **La ligne Service (Marché A) est le revenu immédiat et auto-finançant [Palier 1] ; la ligne SaaS (Marché B) est conditionnée au Palier 3.**

### Ligne A — SERVICE (revenu immédiat, Palier 1, pas de code SaaS requis)
- **« Diagnostic à la demande »** : la consultante exploite le système en interne et **vend le mini-audit + liste qualifiée Kemana** à ses propres clients (done-for-you). Facturation au mandat / à la cohorte. C'est le SOM Marché A [levier de CA conseil, non chiffré — étude §1.4].

### Ligne B — SaaS (Marché B, productisation, Palier 3 conditionné à un seuil de tenants)

| Tier | Cible | Inclus | Quota indicatif [ESTIMATION] |
|---|---|---|---|
| **Solo** | Consultant indépendant, 1 marché | Découverte + diagnostic déterministe, export Kemana CSV/JSONL, 1 ICP, vault Obsidian | ~150-300 fiches diagnostiquées/mois |
| **Cabinet** ★ *(cœur de gamme)* | Micro-agence ≤5 pers., multi-ICP | Solo + **conformité-par-donnée multi-marché** (`compliance/*.yaml`), routage modèle YAML, QA grounding, multi-persona | ~500-1 000 fiches/mois |
| **Agence** | Agence multi-clients/marchés | Cabinet + isolation par client (gateway métrée par tenant), reporting coût par client, support prioritaire | ~2 000+ fiches/mois, budgets par client |
| **Interne / Licence** | Usage propre consultante | Auto-hébergé, hors-ligne, zéro coût fixe | Borné par budgets |

**Barrières de tier = données, pas code** [cohérent invariant « la rubrique/l'ICP/le DAG est une donnée »] : nombre d'ICP, nombre de marchés conformité, budgets, isolation tenant. Le J6 outreach n'est **dans aucun tier tant qu'il n'est pas activé** (ESP conforme + feu vert juriste) [PLANIFIÉ, W1].

---

## 4. MODÈLE DE TARIFICATION & NIVEAUX DE PRIX

**Modèle retenu : abonnement mensuel par tier + plafond d'usage inclus, dépassement en pré-paiement de crédits** (jamais d'overage silencieux — cohérent avec les budgets bloquants `api_io`). Ce modèle « base + crédits plafonnés » reflète l'architecture : le coût variable est réel (API tierces) mais borné.

**Ancrage concurrentiel [SOURCÉ, étude]** : Apollo ~99 USD/siège base (budget réel 150-400 USD/user/mois) ; Clay 149-800 USD/mois. Positionnement micro-structure de l'étude : **50-300 USD/mois** [ESTIMATION MODÉLISÉE cohérente, étude §1.4].

### Niveaux proposés [ESTIMATION MODÉLISÉE — à valider après Phase D]

| Tier | Prix mensuel | Prix annuel (−17 %) | ARPU annuel |
|---|---|---|---|
| **Solo** | 49 € / mois | 490 € / an | ~490-590 € |
| **Cabinet** ★ | 149 € / mois | 1 490 € / an | ~1 500-1 800 € |
| **Agence** | 349 € / mois | 3 490 € / an | ~3 500-4 200 € |

**ARPU mix pondéré cible : ~1 200-1 500 €/an** [ESTIMATION] — placé au **point médian modélisé de l'étude (600-3 600 USD/an)**, dominé par le tier Cabinet.

**Justification des niveaux :**
1. **Plancher 49 € (Solo)** : sous le seuil de friction d'un consultant solo (< 1 h de facturation de conseil/mois), au-dessus du coût variable modélisé pour préserver la marge. Positionne franchement *sous* Apollo/Clay → « conformité incluse, sans le coût plateforme ».
2. **Cœur 149 € (Cabinet)** : aligné sur le palier d'entrée Clay [SOURCÉ] mais avec la **conformité-par-donnée** que Clay n'a pas → même prix, valeur réglementaire supérieure = *compliance premium* capturé sans prime nominale (réduit la friction d'adoption).
3. **349 € (Agence)** : capture la valeur d'isolation multi-clients ; reste très en-dessous du « budget réel Apollo 150-400 USD/*user*/mois » dès 2-3 utilisateurs.
4. **Remise annuelle 17 %** (~2 mois offerts) : standard SaaS, améliore le cash et **réduit le churn** (engagement annuel).

**Ce que la tarification NE fait PAS** : pas de facturation à l'email envoyé (J6 non activable) ; pas de tarif à la performance (pas de données de conversion instrumentées — `taux_conversion_etats` [PLANIFIÉ]).

---

## 5. ICP DÉTAILLÉ

### ICP primaire — « Le consultant marketing conforme » (Marché B, acheteur du SaaS)

**Firmographie [ESTIMATION MODÉLISÉE, populations infalsifiables à instrumenter — réserve de revue respectée] :**
- Taille : 1-5 personnes (consultant solo ou micro-agence branding/marketing).
- Géo : Québec → Romandie → France (séquence AS-IS). Population buyers francophone estimée **28 000-68 000** [étude §1.4, *hypothèse de travail, non assise sourcée*].
- Stack : déjà équipé d'un CRM léger + 1 outil IA marketing (adoption PME 54-57 % en marketing, >70 % en vente [SOURCÉ, étude O1]).
- Maturité : sait vendre du conseil, **n'a pas d'équipe technique/DevOps** (bus factor 1 côté client aussi → valorise le hors-ligne clé-en-main).

**Pains (classés par intensité) :**
1. **Peur du risque réglementaire** — prospecte à froid sur des marchés à 3 régimes empilés, sans savoir prouver sa conformité. *(Réponse : opt-out absolu + minimisation + auditabilité [VÉRIFIÉ].)*
2. **Défiance client envers l'« AI slop »** — ses emails génériques ne convertissent plus. *(Réponse : mini-audit factuel adossé aux failles réelles.)*
3. **OPEX imprévisible** — refuse un abonnement plateforme à 150-400 USD/mois par siège pour un usage irrégulier. *(Réponse : coût variable plafonné, ~0 coût fixe.)*
4. **Sous-outillage vs AI-native** — 62 % des leaders B2B tech se déclarent sous-outillés [SOURCÉ, étude]. *(Réponse : industrialisation clé-en-main.)*

**Déclencheurs d'achat (triggers) :**
- Échéance **AI Act art. 50 (2 août 2026, imminente)** [SOURCÉ] → besoin urgent de transparence/traçabilité.
- Un client final exige une preuve de conformité RGPD/CASL.
- Un incident de délivrabilité (Gmail/Yahoo SPF/DKIM/DMARC depuis 2024 [SOURCÉ]) qui l'a fait blacklister.
- Croissance : passe de 1 à plusieurs marchés → besoin de conformité-par-marché sans réécrire.

### ICP secondaire — « L'installateur/détaillant HVAC » (Marché A, cible du diagnostic, persona 1 AS-IS)
Firmographie : PME de service local (Québec puis Romandie), site web faible, présence Google/avis lacunaire → **matériau riche pour le mini-audit**. C'est la cible *du diagnostic vendu*, pas l'acheteur du SaaS. Assise démographique réelle [VÉRIFIÉ, étude] : Québec 228 622 petites entreprises employeuses.

---

## 6. CHIFFRAGE

### 6.1 Rappel marché (depuis l'étude, non re-dérivé)

| Niveau | Valeur | Registre |
|---|---|---|
| **TAM** (agentique prospection+diagnostic B2B) | Ancrage nommé : **AI SDR ~4,4 Md USD 2025 → ~15 Md 2030** ; « composite » 5-8 Md = fourchette d'encadrement **non additive, sans médiane** | [SOURCÉ borne basse] / [ESTIMATION encadrement] |
| **SAM** francophone | Plage **~50 M – 600 M USD** (bottom-up 17-245 M ↔ top-down 0,3-0,6 Md) — **écart d'environ un ordre de grandeur, cadrage grossier, PAS une validation croisée** | [ESTIMATION MODÉLISÉE] |
| **SOM** solo 3 ans (si Palier 3) | **~18 k – 240 k USD/an** de revenu récurrent annualisé (ARR), soit ~15-200 clients à ARPU ~1 200 USD | [ESTIMATION MODÉLISÉE] |
| **Seuil de bascule Palier 3** | **~20-40 tenants payants** pour amortir une infra multi-tenant frugale (~200-2 500 USD/mois de fixe) | [ESTIMATION MODÉLISÉE] |

> Corrections de revue intégrées : pas de « convergence » (j'écris *encadrement à un ordre de grandeur*) ; pas de médiane TAM implicite ; « ARR » et non « MRR annualisé ».

### 6.2 Unit economics du SaaS lui-même [ESTIMATION MODÉLISÉE — Phase D requise pour verrouiller la marge]

**Hypothèses de base :** ARPU mix **~1 400 €/an** (~117 €/mois) ; churn mensuel logo **3-5 %** (SMB/micro-SaaS [SOURCÉ, culta.ai/optif.ai : 3-5 % SMB, <500 $/an churn élevé]) → durée de vie **~20-33 mois**.

**Marge brute :**
- COGS/tenant = coût API variable (SERP+Apollo+Places+LLM, **budget-plafonné**) + quote-part infra (Palier 3 uniquement).
- Coût-par-fiche modélisé : *quelques centimes à quelques dizaines de centimes* [ESTIMATION, dominé Apollo/SERP, LLM minoritaire]. Un tenant Cabinet (~700 fiches/mo) → **~15-70 €/mois de COGS variable** [ESTIMATION large ; **À CONFIRMER Phase D**].
- Palier 1-2 (hors-ligne, ~0 fixe) → **marge brute logicielle ~85-90 %**. Palier 3 (infra frugale amortie) → **~78-85 %**. [ESTIMATION MODÉLISÉE]

**CAC :** solo sans force de vente, acquisition *content-led + dogfooding* (la consultante utilise son propre outil pour se prospecter) + niche francophone conforme peu disputée [O3]. **CAC estimé 150-500 €** [ESTIMATION MODÉLISÉE ; le dogfooding tire le CAC vers le bas].

**LTV & ratios [ESTIMATION MODÉLISÉE] :**
- LTV = ARPU × marge brute × durée de vie ≈ 1 400 € × 0,85 × ~2 ans ≈ **~2 400 €** (fourchette ~1 600-3 100 €).
- **LTV:CAC ≈ 3:1 à 8:1** — sain à excellent (benchmark : SMB SaaS sain ≥ 3:1, top quartile 4-6:1 [SOURCÉ, growthspreeofficial/foundrycro]).
- **CAC payback ≈ 2-5 mois** (= CAC / (ARPU_mensuel × marge)) — sous le seuil sain de 12 mois [SOURCÉ].

> Ces ratios sont *structurellement* favorables car la marge brute est haute (LLM marginal) et le CAC bas (niche + dogfooding). **Ils s'effondrent si Phase D révèle des tarifs API élevés OU si le churn dépasse 6-7 %/mois** (voir sensibilité §7).

---

## 7. TROIS SCÉNARIOS DE CROISSANCE — 12 MOIS

**Point de départ (T0) :** Palier 1 livré (orchestrateur DAG, ApiIO unique, Phase D faite → **préflight GO**), Marché A actif (revenu conseil). Productisation SaaS (Palier 2) = pré-requis de tout client payant. Premiers tenants payants réalistes à **M6-M9**. Tous chiffres **[ESTIMATION MODÉLISÉE]**, ARPU ~1 400 €/an, churn 4 %/mo médian.

### Scénario CONSERVATEUR — « Auto-financé, sous le seuil »
- **Hypothèses :** Phase D confirme OPEX bas ; J6 reste inactivé ; acquisition purement organique (bouche-à-oreille, dogfooding) ; productisation lente (temps partiel, bus factor 1).
- **Jalons :** M0-M6 Palier 1+2 en prod, usage interne ; M6 premier tenant beta ; M9 offre payante ouverte.
- **Trajectoire clients :** M12 = **5-10 tenants payants**.
- **MRR/ARR :** MRR ~**600-1 200 €** → **ARR ~7-15 k€**.
- **Position vs seuil :** **sous** le seuil Palier 3 (20-40 tenants) → **on NE déclenche PAS l'infra cloud** ; l'activité reste frugale et financée par le conseil (Marché A). *C'est un résultat sain, pas un échec.*

### Scénario BASE — « Traction de niche, approche du seuil »
- **Hypothèses :** *compliance premium* résonne (échéance AI Act) ; 1-2 canaux de contenu francophone ; J6 activé pour early adopters après validation juriste + ESP conforme [PLANIFIÉ] ; ajout marché Romandie.
- **Jalons :** M3 productisation ; M6 lancement public 3 tiers ; M9 nœud conformité multi-marché ; M12 préparation gateway par tenant.
- **Trajectoire clients :** M12 = **15-25 tenants** (mix Cabinet dominant).
- **MRR/ARR :** MRR ~**2 000-3 500 €** → **ARR ~24-42 k€**.
- **Position vs seuil :** **atteint le bas de la fourchette de bascule (20-40)** → décision Palier 3 *déclenchée par la donnée*, infra frugale (NATS/pgvector auto-hébergé) amorcée en fin d'année.

### Scénario AGRESSIF — « Franchit le seuil, entre en Palier 3 »
- **Hypothèses :** l'échéance réglementaire crée un pic de demande ; partenariats (ordres professionnels, réseaux de consultants QC/CH/FR) ; J6 activé et différenciant ; embauche d'un renfort (lève partiellement le bus factor 1).
- **Jalons :** M6 public + premiers partenariats ; M9 franchissement 30 tenants → infra multi-tenant frugale ; M12 isolation + reporting coût par tenant en prod.
- **Trajectoire clients :** M12 = **35-60 tenants**.
- **MRR/ARR :** MRR ~**5 000-8 500 €** → **ARR ~60-100 k€**.
- **Position vs seuil :** **franchit** le seuil → Palier 3 justifié économiquement. Cohérent avec la trajectoire 3 ans du SOM (→ 200 clients / 240 k€).

| Scénario | Tenants M12 | MRR M12 | ARR M12 | Palier 3 infra ? |
|---|---|---|---|---|
| Conservateur | 5-10 | ~0,6-1,2 k€ | ~7-15 k€ | Non (frugal maintenu) |
| Base | 15-25 | ~2-3,5 k€ | ~24-42 k€ | Amorcé fin d'année |
| Agressif | 35-60 | ~5-8,5 k€ | ~60-100 k€ | Oui (seuil franchi) |

### Sensibilité à l'OPEX (le facteur décisif)

1. **Coût variable API (Phase D)** — *risque de marge.* Si les tarifs relevés sont 2-3× le modèle, COGS/tenant Cabinet passe de ~15-70 € à ~40-150 €/mois → marge brute chute de ~85 % à **~65-75 %**. **Levier :** paliers de collecte (Places seulement au-dessus d'un seuil de score), cache ≥40-60 %, repli déterministe, routage Haiku. La marge reste positive tant que le budget bloquant tient — *aucune dérive silencieuse possible par conception.*

2. **Coût fixe Palier 3 (200-2 500 USD/mois)** — *risque de point mort.* Déclencher l'infra **avant** ~20-40 tenants détruit la marge. **Règle absolue de la décision :** Palier 3 conditionné à un **seuil de tenants payants défini à l'avance**, jamais à une intuition. En conservateur/base précoce → rester frugal auto-hébergé (÷3-5 le fixe : NATS + pgvector + scale-to-zero).

3. **Churn** — *risque de LTV.* À 4 %/mo, LTV:CAC ~4-8:1. À **7 %/mo** (haut de fourchette SMB [SOURCÉ]), durée de vie ~14 mois → LTV:CAC tombe vers **~2-3:1** (limite basse acceptable). **Levier :** engagement annuel (−17 %), switching cost du vault versionné, compliance premium (rétention O5).

**Conclusion de sensibilité :** l'offre est **robuste par construction** — coût variable plafonné (budgets bloquants), coût fixe différé (seuil de tenants), marge haute (LLM marginal). Le seul risque non maîtrisable en interne est **exogène** : Phase D non faite (préflight NO-GO, W2) et J6 non validable juridiquement (W1/T3). Les deux sont des **pré-conditions explicites déjà inscrites dans la décision**, pas des angles morts.

---

## Réserves finales (garde-fou respecté)
- Aucun tarif fournisseur inventé : Apollo/Clay proviennent de l'étude sourcée ; benchmarks LTV:CAC/churn cités ci-dessous.
- **Tout coût-par-fiche, marge, CAC, LTV et toute trajectoire MRR/ARR sont [ESTIMATION MODÉLISÉE]** — non engageants tant que la **Phase D** n'a pas renseigné `api_pricing.yaml` et obtenu **préflight GO**.
- Populations de buyers (28-68 k) = *hypothèses de travail à instrumenter*, pas assises sourcées.
- SOM Marché A (levier CA conseil) reste **non chiffré** tant que `taux_conversion_etats` n'est pas instrumenté [PLANIFIÉ].
- J6 outreach : **aucune monétisation à l'envoi** avant validation juriste (CASL/nLPD+art.3 LCD/RGPD/AI Act art. 50) ET ESP conforme (SPF/DKIM/DMARC, opt-out 1-clic).

**Sources (benchmarks unit economics) :** [growthspreeofficial — LTV:CAC B2B SaaS 2026](https://www.growthspreeofficial.com/blogs/ltv-cac-ratio-b2b-saas-benchmarks-2026) · [Foundry CRO — LTV:CAC 2026](https://foundrycro.com/blog/ltv-cac-ratio-benchmarks-2026/) · [culta.ai — SaaS churn benchmarks 2026](https://culta.ai/blog/saas-churn-rate-guide-benchmarks) · [Optifai — B2B SaaS churn par segment](https://optif.ai/learn/questions/b2b-saas-churn-rate-benchmark/). Tarifs concurrents et données marché : voir sources de l'étude fournie (salesmotion.io, digitalapplied, legalnodes, ISED, INSEE).

---
<a id="5"></a>
## 5. Objectif 4 — Plan d'implémentation détaillé
J'ai vérifié l'AS-IS dans le dépôt. Voici le plan d'implémentation. (Je n'ai créé aucun fichier — le plan est ci-dessous.)

---

# PLAN D'IMPLÉMENTATION — Scénario A hybride « Kemana-Flow »
## Orchestrateur DAG déterministe sur socle J1–J5, trajectoire 3 paliers

### Légende de fiabilité (garde-fou anti-hallucination)
- **[VÉRIFIÉ]** = constaté dans le dépôt à l'instant (fichier/ligne lus).
- **[PLANIFIÉ]** = à construire, contrat défini ici, non encore codé.
- **[HYP]** = hypothèse de cadrage / estimation modélisée (méthode + hypothèses données).
- Aucun tarif fournisseur n'est chiffré ici : tous restent des placeholders `api_pricing.yaml` à renseigner en **Phase D**. Les durées sont des **ESTIMATION MODELISEE** (méthode en §5).

---

## 0. Ancrage AS-IS vérifié (point de départ réel)

| Constat | Preuve dans le dépôt | Conséquence plan |
|---|---|---|
| `DiagnosticPipeline.__init__` accepte **déjà** `api_io=None` et l'injecte dans les collecteurs (`_api_io`) + dans `synthesize(..., api_io=...)` | `diagnostic/pipeline.py` l.25-40 | **Le hook d'injection existe.** Le correctif est du *câblage*, pas de la réécriture. [VÉRIFIÉ] |
| `run_diagnostic.py._build_pipeline()` construit le pipeline **sans** `api_io` (mode standard ET mode `--out vault` via `vault_runner`) | `run_diagnostic.py` l.42-49 | Locus exact du défaut « run_diagnostic sans api_io ». [VÉRIFIÉ] |
| `ApiIO.__init__(pricing, ledger_path, cache_dir, budgets=None, vault_path=None)` | `diagnostic/api_io.py` l.77-84 | **Le paramètre `budgets` existe** ; rien ne le charge depuis le YAML au runtime. Défaut = câblage manquant, pas API absente. [VÉRIFIÉ] |
| `api_pricing.yaml` : `releve_le: null`, tous `prix_par_unite: 0.0`, `budgets.serp/apollo = 0` | `knowledge/api_pricing.yaml` | Préflight **NO-GO structurel** tant que Phase D non faite. [VÉRIFIÉ] |
| `_check_garde_fous_bus` scanne une **liste figée** de 6 modules (export, usage, preflight, run_export, run_usage, run_preflight) ; les modules absents → `warn`+ok | `diagnostic/preflight.py` l.250-277 | Il faut **étendre la liste** à `orchestrator.py` + `run_pipeline.py`, sinon garde-fou aveugle. [VÉRIFIÉ] |
| Aucun `orchestrator.py` / `run_pipeline.py` / `dag_pipeline.yaml` ; aucun code J6/J7 | `ls` racine + `diagnostic/` | Ce sont les seuls nouveaux modules du Palier 1. [VÉRIFIÉ] |
| 17 fichiers de tests (365 tests annoncés) | `tests/` | Cible de non-régression = 365 **+** nouveaux tests verts. [VÉRIFIÉ liste ; 365 = annoncé CLAUDE.md] |

**Lecture clé** : les 4 défauts AS-IS se corrigent par **un seul geste** (instance `ApiIO` unique, budgets chargés, injectée partout via l'orchestrateur) + **Phase D** (renseigner le YAML). Zéro réécriture métier — revendication crédible confirmée par lecture du code.

---

## 1. Correctifs AS-IS → geste technique (fondation, non négociable avant tout run réel)

| Défaut AS-IS | Geste | Fichier(s) touché(s) | Effort [HYP] |
|---|---|---|---|
| Budgets non injectés au runtime | Charger `pricing['budgets']` et le passer à `ApiIO(budgets=...)` dans le point d'entrée unique | `orchestrator.py` [PLANIFIÉ] | S |
| `run_diagnostic` sans api_io | L'orchestrateur passe l'`ApiIO` unique au nœud diagnostic → `DiagnosticPipeline(..., api_io=io)` | câblage nœud [PLANIFIÉ] ; `run_diagnostic.py` reçoit aussi le fix (1 ligne) | S |
| Prix/budgets à 0 (NO-GO) | **Phase D** : `releve_le`, `prix_par_unite`, `budgets>0` | `knowledge/api_pricing.yaml` (donnée) | S (relevé) — bloqué sur opératrice |
| J6 outreach absent | Ossature `OutreachAgent` **human-gated, non activable** | `diagnostic/outreach.py` + nœud [PLANIFIÉ] | M |

> Principe : `run_diagnostic.py`, `run_discovery.py`, etc. **restent utilisables seuls** ; l'orchestrateur les enveloppe sans les remplacer (rétro-compat CLI préservée).

---

## 2. Architecture cible & contrats d'interface

### 2.1 Couches (inchangées sauf couche Orchestration ajoutée)
ROM/DONNÉES (rubrics, ICP, `api_pricing.yaml`, `export_kemana.yaml`, **+ `dag_pipeline.yaml`**) → BUS (`vault_io`, `api_io` — inchangés, mieux exploités) → AGENTS/CPU (nœuds enveloppant le code J1/J4/J5 **+ J6**) → **ORCHESTRATION** (`orchestrator.py` + `run_pipeline.py`) → CONSOLE (Obsidian).

### 2.2 Contrat de nœud [PLANIFIÉ]
Contrat uniforme, minimal, **zéro logique métier dans l'orchestrateur** :

```
NodeContext:
  run_id: str                 # corrèle runs.log ⇄ api_usage.log
  icp_id: str | None
  vault_io: VaultIO           # injecté (bus stockage unique)
  api_io: ApiIO               # instance UNIQUE injectée (bus réseau unique)
  dry_run: bool
  params: dict                # bornes: depuis_etat, jusqu_a, plafonds nœud
  logger: RunLogger

NodeResult:
  node: str
  status: Literal["ok","skipped","budget_exceeded","error","human_gate"]
  fiches_touchees: list[str]  # refs, pas d'objets métier
  cout_estime: float | None   # lu depuis le ledger, jamais recalculé
  incidents: list[str]

Node protocol:  run(ctx: NodeContext) -> NodeResult
```

Règle dure : un nœud **lit son état d'entrée via `vault_io`**, écrit via `vault_io`, ne dépasse jamais sa transition autorisée (`decouvert→diagnostique` uniquement pour l'agent), ne touche le réseau que via `ctx.api_io`.

### 2.3 `dag_pipeline.yaml` — le graphe est une donnée [PLANIFIÉ]
```yaml
run:
  lock: true                      # verrou de run (cf. §8)
  api_io: { budgets_from: knowledge/api_pricing.yaml }
nodes:
  - id: preflight_gate            # bloquant: NO-GO => DAG ne démarre pas
  - id: discovery                 # J4, needs: [preflight_gate]
    etat_entree: null  etat_sortie: decouvert
    budget: { serp: <plafond>, apollo: <plafond> }
  - id: diagnostic                # J1, needs: [discovery]
    etat_entree: decouvert  etat_sortie: diagnostique
  - id: human_gate_valide         # BARRIÈRE humaine (Obsidian), needs: [diagnostic]
    type: human_barrier           # le DAG s'arrête ici, reprend au run suivant
  - id: export                    # J5, needs: [human_gate_valide]
    etat_entree: valide
  - id: outreach                  # J6 OSSATURE, needs: [human_gate_valide]
    active: false                 # jamais activable sans feu vert juridique + ESP
  - id: usage_snapshot            # J5, needs: [export]
```
> Ordre **topologique séquentiel strict** (le symbole ∥ export/outreach est retiré, cf. réserve tranchée par le chef de projet). Ajouter/réordonner une étape = éditer le YAML, jamais le code.

### 2.4 Responsabilités `orchestrator.py` (~250-400 lignes, [HYP] cohérent avec la décision)
Charger le DAG → tri topologique déterministe → instancier **une** `ApiIO` (budgets du YAML) → attribuer `run_id` → exécuter les nœuds en séquence → capter `BudgetExceeded` (arrêt propre, fiches déjà écrites valides) → s'arrêter aux barrières humaines → journaliser. **Aucun `os.replace`, aucun `open()` sur le vault, aucun import `requests`/`anthropic`.**

### 2.5 Interfaces externes (toutes via `api_io`)
SERP, Apollo, Google Places, Anthropic (tokens métrés), + ESP email J6 (branché mais **non activé**). Sorties : vault (vérité), `exports/` (hors vault), `api_usage.log`, `runs.log`, corrélés par `run_id`.

---

## 3. Lotissement en phases & backlog

### PALIER 1 — Orchestrateur A intégral (livrable immédiat)

**Lot L0 — Phase D (pré-requis dur, bloque tout run réel)**
- L0.1 Renseigner `SERP_API_KEY`, `APOLLO_API_KEY` (env) — opératrice.
- L0.2 Relever vrais tarifs → `prix_par_unite` + `releve_le` (`api_pricing.yaml`).
- L0.3 Budgets pilote `>0` (`budgets.serp.unites_max.requetes`, `budgets.apollo.unites_max.credits`) — valeurs pilote à décider (ex. bornes basses), **[HYP]**.
- L0.4 `python run_preflight.py` → exiger **GO**.
- DoD L0 : préflight GO reproductible ; aucun placeholder à 0 restant.

**Lot L1 — Contrats & squelette orchestrateur**
- L1.1 `NodeContext`/`NodeResult` (Pydantic v2, `extra="forbid"`).
- L1.2 `orchestrator.py` : chargement DAG, tri topo, run_id, journalisation, arrêt propre `BudgetExceeded`.
- L1.3 `dag_pipeline.yaml` v1.
- L1.4 `run_pipeline.py` (CLI : `--icp`, `--dry-run`, `--depuis-etat`, `--jusqu-a`, refus si préflight NO-GO).
- L1.5 **Étendre `_check_garde_fous_bus`** aux 2 nouveaux modules + tests AST.
- L1.6 Instance `ApiIO` unique + chargement budgets → **corrige défauts #1 et #2**.

**Lot L2 — Enveloppes de nœuds (réutilisation, zéro réécriture)**
- L2.1 `preflight_gate` (enveloppe `preflight.py`).
- L2.2 `discovery` (enveloppe `run_discovery`/`DiscoveryCollector`+`PersonEnrichment`).
- L2.3 `diagnostic` (enveloppe `DiagnosticPipeline` **avec api_io injecté**).
- L2.4 `export` + `usage_snapshot` (enveloppes J5).
- L2.5 `human_gate_valide` (barrière : le DAG s'arrête, reprise idempotente au run suivant).

**Lot L3 — Robustesse d'exécution**
- L3.1 **Verrou de run** (lockfile/`run_id` unique) refusant un 2ᵉ démarrage concurrent sur le même vault (cron + manuel).
- L3.2 Reprise idempotente prouvée (dédup vault + cache api_io) — test de rejeu.
- L3.3 `--dry-run` global (SERP métrée, cache utile, **aucune** écriture vault).

**Lot L4 — J6 ossature (human-gated, NON activable)**
- L4.1 `diagnostic/outreach.py` : `OutreachAgent`, transition `valide→contacte` derrière double garde (humain + conformité), brouillon LLM déposé dans le vault pour revue.
- L4.2 Nœud `outreach` avec `active: false` par défaut ; opt_out absolu hérité de J5.
- L4.3 Gabarits/cadence = données YAML.
- DoD L4 : **aucun chemin d'envoi réel** ; impossible d'activer sans flag + validation juridique + ESP retenu.

**Lot L5 — J7 cron (planification bornée)**
- L5.1 Déclencheur cron → `run_pipeline.py`, **préflight en pré-condition dure**.
- L5.2 Batch borné par budgets ; pas de boucle temps réel.

### PALIER 2 — Greffe sélective de B (dès que le pilote tourne)
*(NŒUDS/DONNÉES du DAG A ; **refus explicite** du superviseur-planificateur LLM de B.)*
- **L6 — Nœud Critique de grounding DÉTERMINISTE** entre synthèse et transition : chaque affirmation du mini-audit **DOIT référencer une faille existante dans `diag.failles`** (contrôle par correspondance, **pas** un LLM juge). Échantillonnage humain complémentaire. → cf. §9.
- **L7 — Nœud Conformité bloquant** en amont d'export/outreach, alimenté par `compliance/*.yaml` par marché (`casl-quebec.yaml`, `nlpd-ch.yaml`, `rgpd-fr.yaml`). Feu rouge/vert horodaté. → cf. §10.
- **L8 — `routing.yaml`** (modèle par tâche : petit modèle par défaut, modèle fort réservé aux cas signalés). Planificateur **reste déterministe**.

### PALIER 3 — Fragments de C (conditionnel, **gelé** jusqu'à seuil de tenants payants défini à l'avance)
- Uniquement : gateway `api_io` métrée/budgétée **par tenant** + isolation + reporting par tenant. **Bus d'événements, event-sourcing, RAG différés.** Ne pas engager de coût fixe cloud avant justification économique. Reprise conditionnée à la résolution de l'inversion vault/event-store et au retrait de toute citation tarifaire non sourcée (hallucinations neutralisées par le rejet de C au stade actuel).

---

## 4. Stack technique
- **Langage** : Python 3.10+, type hints, `from __future__ import annotations` (inchangé). [VÉRIFIÉ conventions]
- **Validation** : Pydantic v2 (`model_dump(mode="json")`) — réutilisé pour `NodeContext/Result`, `dag_pipeline.yaml`.
- **Orchestration** : maison, ~250-400 lignes, **pas de dépendance externe** (Airflow/Prefect exclus au Palier 1 — surdimensionnés, contre l'OPEX plancher et le déterminisme). Tri topologique = `graphlib.TopologicalSorter` (stdlib).
- **Persistance** : vault Markdown+YAML via `vault_io` (os.replace atomique, `runs.log`). Inchangé.
- **Réseau/LLM** : `api_io` unique (cache disque, `api_usage.log`). Modèle Claude via `ANTHROPIC_API_KEY` (repli déterministe hors-ligne). *Choix de modèle et tarifs → à confirmer via la doc officielle en Phase D ; non chiffré ici.*
- **Cron** : cron système / planificateur, préflight en pré-condition.
- **Tests** : pytest (365 existants + nouveaux).
- **Palier 3 uniquement (gelé)** : gateway multi-tenant. Aucune infra cloud engagée avant seuil.

---

## 5. Jalons & timeline indicative ~12 mois

**Méthode d'estimation [ESTIMATION MODELISEE]** : hypothèses = **1 dev principal** (temps partiel, la consultante ou un dev sous-traité) + interventions ponctuelles (juriste, opératrice) ; vélocité modeste car socle mature et bien testé (peu de découverte, surtout du câblage) ; unités en **semaines-calendaires**, non en jours-homme pleins. À recalibrer après L1.

| Jalon | Contenu | Fenêtre [HYP] |
|---|---|---|
| **J-A0** | L0 Phase D — préflight GO | Semaines 1-2 (dépend du relevé tarifs, hors code) |
| **J-A1** | L1+L2 — orchestrateur + nœuds, DAG bout-en-bout en dry-run | Semaines 3-8 |
| **J-A2** | L3 — verrou, idempotence, dry-run global ; **1er run réel borné persona1-quebec** | Semaines 9-12 |
| **J-A3** | L4 — J6 ossature human-gated (non activable) | Semaines 13-16 |
| **J-A4** | L5 — cron J7 borné en production pilote | Semaines 17-20 |
| **J-B1** | L6 nœud Critique grounding déterministe + échantillonnage humain | Semaines 21-26 |
| **J-B2** | L7 nœud Conformité + `compliance/*.yaml` (CASL/nLPD/RGPD/AI Act) — **pré-requis à toute activation J6** | Semaines 27-34 |
| **J-B3** | L8 `routing.yaml` + extension marchés (Romandie) par YAML | Semaines 35-40 |
| **Réserve / durcissement** | Buffer, dette, doc, éventuel 2ᵉ persona | Semaines 41-52 |
| **Palier 3** | **Gelé** — déclenché seulement sur seuil de tenants payants | Hors fenêtre 12 mois |

> Activation réelle de J6 (envois) : **jalon conditionnel indépendant de la timeline technique** — subordonné à (a) validation juridique, (b) ESP conforme retenu.

---

## 6. Rôles / équipe (micro-structure solo)
- **Tech lead / dev (1)** : orchestrateur, nœuds, tests, garde-fous. (Bus factor 1 — risque assumé, cf. §8.)
- **Opératrice (la consultante)** : Phase D, validation `diagnostique→valide` en Obsidian (manage-by-exception), console.
- **Juriste (ponctuel, externe)** : validation CASL/nLPD+art.3 LCD/RGPD/AI Act **avant** toute activation J6. Bloquant.
- **Relecteur/QA (peut être le tech lead + échantillonnage humain)** : gouvernance de revue §9.
- **DevOps/SRE** : **non requis** aux Paliers 1-2 (batch, pas de service permanent). Requis seulement si Palier 3 débloqué.

---

## 7. Dépendances
- **Bloquantes amont** : Phase D (clés + tarifs + budgets) → sinon préflight NO-GO → `run_pipeline` refuse de démarrer. Choix du fournisseur SERP et du plan Apollo.
- **Inter-lots** : L1→L2→L3 séquentiel ; L4/L5 après L3 ; L6/L7/L8 après pilote stable (J-A2) ; L7 (Conformité) **pré-requis dur** à toute activation J6.
- **Externes** : disponibilité juriste (J6), stabilité API tierces (SERP/Apollo/Places/Anthropic — tarifs/quotas hors contrôle).
- **Palier 3** : seuil de tenants payants défini à l'avance (déclencheur économique, non technique).

---

## 8. Risques & mitigations
| Risque | Gravité | Mitigation |
|---|---|---|
| Import réseau/écriture directe dans `orchestrator.py`/`run_pipeline.py` (viole les bus uniques) | Élevé | **Étendre le garde-fou AST** (L1.5) + tests bloquants **avant** activation. [VÉRIFIÉ : liste actuellement figée sans ces modules] |
| Deux runs concurrents (cron + manuel) → écritures entrelacées | Élevé | Verrou de run L3.1 (lockfile/run_id), refus du 2ᵉ démarrage. |
| Envoi J6 sans cadre juridique | Élevé (sanctions) | J6 `active:false`, double garde, validation juriste + ESP obligatoires ; opt_out absolu. |
| Régression sur 365 tests | Moyen | Non-régression = **critère de sortie** (DoD), pas hypothèse : 365 + nouveaux tests verts avant chaque activation. |
| Dérive de coût (cache inefficace / budgets mal calibrés) | Moyen | Budgets bloquants par fournisseur, `--dry-run` préalable, paliers de collecte (Places seulement au-dessus d'un seuil de score palier 0). |
| OPEX chiffré incertain | Moyen | **Réserve levée par Phase D** ; toute fourchette = ESTIMATION MODELISEE, aucun engagement de coût fixe avant relevé réel. |
| Corruption ledger append-only sous interruption | Moyen | `nb_erreurs_lecture` surveillé, écriture ligne à ligne, registres recalculés depuis le fichier. |
| Sur-confiance synthèse LLM (affirmation hors faits) | Moyen (réputation) | QA J1 + **nœud Critique déterministe L6** (référence obligatoire à `diag.failles`) + échantillonnage humain. |
| Bus factor 1 (opératrice/dev unique) | Moyen | Manage-by-exception, `CLAUDE.md` à jour, procédures reprenables, reprise idempotente. |
| Fragilité collecteurs (sites/API tierces) | Moyen | `safe_collect` isole les échecs, mode dégradé par collecteur, journalisation. |

---

## 9. Gouvernance de revue (dont agent anti-hallucination)
1. **Revue de code par lot** : chaque lot merge derrière PR ; check obligatoire = 365 tests + nouveaux tests verts + préflight `garde_fous_bus` vert (AST étendu).
2. **Nœud Critique de grounding (L6, Palier 2) — DÉTERMINISTE, pas un LLM juge** : contrôle par correspondance que **chaque affirmation du mini-audit renvoie à une faille présente dans `diag.failles`**. C'est la traduction de la règle J1 « aucune affirmation non adossée aux failles réelles » en garde bloquant. Le grounding reste étiqueté **ESTIMATION MODELISEE** (pas de KPI type « ≥98 % » promis par un LLM faillible — hallucination écartée du panel C).
3. **Échantillonnage humain** : l'opératrice contrôle un échantillon des mini-audits/brouillons à chaque run (manage-by-exception).
4. **Porte de décision budgétaire** : interdite avant Phase D ; toute projection présentée comme ESTIMATION MODELISEE.
5. **J6 jamais présenté comme opérationnel** avant feu vert juridique + ESP.

---

## 10. Conformité (RGPD / CASL / nLPD+art.3 LCD / AI Act)
- **Par-donnée (L7)** : `compliance/casl-quebec.yaml`, `nlpd-ch.yaml`, `rgpd-fr.yaml` déclarent base légale, mentions obligatoires, fenêtres de contact, exigences de transparence AI Act. Nœud Conformité **bloquant** en amont d'export/outreach.
- **Opt-out absolu** : `opt_out=true` exclu de l'export **et** de l'outreach, sans exception (hérité J5). Testé.
- **Minimisation RGPD** : Apollo uniquement, `Contact` 6 champs, `contact_email_source` renseigné, **zéro scraping LinkedIn/Facebook** (hérité J4).
- **Séquence géographique** : Québec (CASL) → Romandie (nLPD + art.3 LCD) → France (RGPD + AI Act) — un marché = un YAML conformité, zéro code.
- **Blocage dur J6** : aucun envoi avant validation juridique documentée par un juriste + ESP conforme retenu.

---

## 11. Definition of Done
**Par lot** : code + tests verts (365 + nouveaux) ; préflight GO ; `garde_fous_bus` (AST) vert incluant `orchestrator.py`+`run_pipeline.py` ; aucun `os.replace`/`open()` vault hors `vault_io` ; aucun `import requests`/`anthropic` hors `api_io` ; doc `CLAUDE.md` à jour.
**Palier 1 (global)** : `run_pipeline.py --icp persona1-quebec` exécute le DAG bout-en-bout ; ApiIO unique avec budgets chargés ; run reprenable/idempotent ; verrou de run actif ; `--dry-run` sans écriture ; run_id corrèle `runs.log`⇄`api_usage.log` ; J6 présent mais non activable ; cron branché avec préflight pré-condition.
**Palier 2** : nœud Critique déterministe + nœud Conformité bloquant + `routing.yaml` opérationnels, tous testés.
**Activation J6 (jalon conditionnel séparé)** : validation juridique écrite + ESP conforme + conformité `*.yaml` verte pour le marché ciblé.

---

## 12. Métriques de suivi
- **Livraison** : lots livrés DoD-complets ; **365 + N tests verts** (dur) ; préflight GO avant chaque run réel (100 %, dur).
- **Exécution** : taux de complétion du DAG **[cible ≥95 %, ESTIMATION MODELISEE — hyp. : erreurs résiduelles = quotas/timeouts absorbés par reprise idempotente]** ; nb reprises idempotentes sans effet de bord ; durée par nœud.
- **Coût/OPEX** (renseignés **après** Phase D, jamais avant) : `cout_par_fiche_diagnostiquee` (depuis ledger, par run_id) ; `taux_cache_par_fournisseur` **[cible 40-60 %, ESTIMATION MODELISEE — hyp. : rejeux/re-diagnostics fréquents sur ICP borné]** ; `budget_consomme_vs_plafond` ; part LLM du total réseau **[≤15-25 %, ESTIMATION MODELISEE]**.
- **Conformité** : fiches opt_out correctement exclues (100 %, dur, testé) ; couverture d'audit (fiche→run_id) 100 %.
- **Qualité** : taux de grounding **échantillonné humainement** (étiqueté ESTIMATION MODELISEE, jamais un chiffre LLM-juge) ; `nb_lignes_ledger_illisibles` = 0.
- **Rendement pipeline** : `taux_conversion_etats` (decouvert→diagnostique→valide→contacte) — le goulot `diagnostique→valide` reste **humain par conception** (assumé, non survendu).

---

**Séquence de démarrage immédiate** : L0 (Phase D) → préflight GO → L1 (contrats + orchestrateur + AST étendu) → L2 (nœuds) → L3 (verrou + idempotence) → 1er run réel borné. J6 en ossature gelée ; Conformité (L7) obligatoire avant toute velléité d'activation.

*Fichiers pertinents à créer (chemins absolus) : `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/orchestrator.py`, `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/run_pipeline.py`, `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/dag_pipeline.yaml`, `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/diagnostic/outreach.py`, `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/compliance/{casl-quebec,nlpd-ch,rgpd-fr}.yaml`, `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/knowledge/routing.yaml`. À modifier : `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/diagnostic/preflight.py` (étendre `_check_garde_fous_bus`), `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/knowledge/api_pricing.yaml` (Phase D), `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/run_diagnostic.py` (injection api_io).*

---
<a id="6"></a>
## 6. Gouvernance & piste d'audit des revues anti-hallucination
L'agent de revue est intervenu à trois portes de décision structurante. Synthèse des avals :

| Porte de revue | Verdict | Aval | Hallucinations relevées | Réserves |
|---|---|---|---|---|
| Scénarios techniques | approuve_avec_reserves | ✅ | 3 | 5 |
| Étude de marché | approuve_avec_reserves | ✅ | 5 | 5 |
| Offre SaaS + plan | approuve_avec_reserves | ✅ | 4 | 5 |

### Scénarios techniques — approuve_avec_reserves

**Hallucinations / affirmations à corriger détectées :**

- ⚠️ *Scenario C: 'Tarifs releves (juillet 2026) : SerpAPI ~0,025 USD/recherche ... Apollo ~0,025 USD/credit ... Google Places ~0,017-0,032 USD/requete' avec URLs sources (apiserpent.com/costbench, warmly.ai, salesmotion.io).* → Prix vendeurs specifiques presentes comme un releve source, avec des URLs invraisemblables/non verifiables (apiserpent.com, warmly.ai/salesmotion.io comme sources tarifaires Apollo). Cela CONTREDIT directement la discipline AS-IS de api_pricing.yaml (valeurs a 0, releve_le=null, 'AUCUN prix vendeur n'est invente') que les scenarios A et B respectent explicitement. Citations a haut risque de fabrication. — **Correction :** Ne pas presenter ces chiffres comme un releve. Les traiter comme des ordres de grandeur non sources, ou renvoyer la fixation reelle a la Phase D (saisie prix_par_unite + releve_le dans api_pricing.yaml), comme le font A et B.
- ⚠️ *Scenario C: 'le vault Obsidian Markdown+frontmatter devient une PROJECTION read-only reconstruite depuis l event store' (event store = source-de-verite).* → Inversion d un invariant structurant de l AS-IS J2: le vault EST la source de verite versionnee, vault_io est le SEUL bus d ecriture (os.replace atomique, journal append-only, machine a etats). Demoter le vault en read-model deplace la source de verite hors du bus teste par AST walk. Le scenario admet lui-meme 'chantier a risque de regression sur 365 tests', ce qui contredit sa propre affirmation de preservation de J2. — **Correction :** Reconnaitre que cette bascule n est pas une 'preservation de J2' mais une reecriture de la couche de persistance ; conditionner explicitement le maintien des 365 tests a cette migration non triviale.
- ⚠️ *Scenario B & C: KPI 'Taux de grounding QA >= 98%' / 'Auto-completion sans intervention humaine > 95%' obtenus par un agent Critique lui-meme LLM.* → Sur-promesse metrologique: un controle de grounding execute par un LLM faillible ne peut garantir un chiffre >=98% ; c est une estimation modelisee presentee comme cible dure. Le scenario B le reconnait partiellement en risques mais l affiche en KPI. — **Correction :** Conserver l etiquette ESTIMATION MODELISEE et adosser la cible a un controle DETERMINISTE complementaire (chaque affirmation doit referencer une faille existante dans diag.failles) + echantillonnage humain, plutot qu au seul verdict du LLM critique.

**Incohérences d'artefacts :**

- Scenario C — contradiction interne assumee 'quasi temps-reel' vs 'OPEX minimal': les deux principaux leviers de cout (Batch API -50%, scale-to-zero) degradent la latence, invalidant partiellement l argument temps-reel. Le scenario la signale mais la maintient comme force ('Quasi temps-reel possible').
- Scenario C — le debit annonce (200-1000 prospects/h/tenant) coexiste avec l aveu repete que 'le goulot reel reste HUMAIN' (validation diagnostique->valide). Industrialiser la decouverte sans industrialiser la porte humaine ne fait que deplacer l embouteillage: le KPI de debit amont est donc trompeur au niveau systeme.
- Scenario A — le flux decrit export et outreach 'en parallele' (∥) alors que l orchestrateur est presente comme 'execution sequentielle' en 'ordre topologique fige' ; le parallelisme reel des noeuds n est pas etaye (limite reconnue: 'pas de parallelisme massif natif').
- Tous scenarios — l affirmation '365/365 tests conserves' est presentee comme acquise, mais chaque scenario ajoute des modules (orchestrator, agents, gateway) soumis au garde-fou AST (interdiction import requests/anthropic hors bus). C n est vrai qu APRES ecriture des nouveaux tests ; c est une cible, pas un etat preserve.

**Réserves :**

- La correction des 4 defauts AS-IS (budgets non cables, run_diagnostic sans api_io, preflight NO-GO, orchestration absente) est verifiee comme reelle et techniquement atteignable par les 3 scenarios via l unicite de l instance ApiIO injectee — ce point est solide et non hallucine.
- Scenario C ne doit PAS passer la porte comme option d adoption immediate: son cout fixe (~200-2500 USD/mois) et sa complexite SRE sont disproportionnes pour une consultante solo, et il repose sur une migration event-store a risque de regression. Ne le retenir que conditionne a une bascule SaaS multi-tenant a l echelle (dizaines de tenants payants), comme le scenario le concede lui-meme.
- Toute projection OPEX chiffree des 3 scenarios reste non validee tant que api_pricing.yaml n est pas renseigne (Phase D). Aucune decision budgetaire ferme ne doit s appuyer sur les fourchettes citees, en particulier celles de C.
- J6 (outreach) est un squelette dans les 3 cas ; l activation exige validation juridique CASL/nLPD+art.3 LCD/RGPD/AI Act ET un ESP conforme avant tout envoi. Aucun scenario ne livre J6 operationnel — a ne pas presenter comme tel a la porte de decision.
- La preservation de la regle d or J1 ('le LLM ne fetch jamais') est correctement raisonnee dans les 3 scenarios (LLM confine a synthese+outreach, tool-use borne en C) — pas de reserve sur ce point.

**Recommandations :**

- Retenir le Scenario A (DAG deterministe Kemana-Flow) comme chemin par defaut: proximite maximale a l AS-IS, couche mince (~1 orchestrateur + 1 CLI + 1 YAML), correction des 4 defauts en un geste, risque de regression minimal. C est le seul dont l affirmation 'zero reecriture des briques metier' est credible.
- Traiter les elements du Scenario B (revue croisee Critique, BudgetGovernor hierarchique, routage de modele par YAML) comme des increments OPTIONNELS a superposer sur A si le besoin qualite/multi-persona se materialise — pas comme une architecture a deployer d emblee (sur-ingenierie reconnue pour une structure solo).
- Rejeter le Scenario C pour le stade actuel ; le conserver uniquement comme reference 'borne haute' conditionnee a un seuil de tenants payants. Exiger, s il est jamais repris, la resolution prealable de l inversion vault/event-store et le retrait des citations tarifaires non sourcees.
- Avant toute porte de decision budgetaire: executer la Phase D (releve reel des tarifs + releve_le + budgets>0 dans api_pricing.yaml) puis 'python run_preflight.py' pour obtenir GO, afin de remplacer les estimations modelisees par des chiffres reels.
- Imposer que tout nouveau module (orchestrator, run_pipeline, agents) soit ajoute au garde-fou AST (interdiction import requests/anthropic hors bus) AVANT activation, et que les nouveaux tests soient verts en plus des 365 existants — condition non negociable pour valider la revendication de non-regression.

### Étude de marché — approuve_avec_reserves

**Hallucinations / affirmations à corriger détectées :**

- ⚠️ *Salesforce (Agentforce, agents Piper SDR et Hunter de prospection)* → Attribution concurrentielle vraisemblablement erronee. 'Piper the AI SDR' est le produit de Qualified.ai, PAS un agent Salesforce Agentforce (dont l'agent de prospection s'appelle 'Agentforce SDR', ex-Einstein SDR Agent). Aucun agent Salesforce nomme 'Hunter' n'est etabli. La source citee (futurumgroup/martech) ne suffit pas a valider ces noms de produits, qui melangent des vendeurs distincts. — **Correction :** Remplacer par : 'Salesforce (Agentforce SDR), HubSpot, Demandbase' et retirer 'Piper' et 'Hunter' — ou verifier nommement chaque agent avant publication. Piper releve d'un autre concurrent (Qualified.ai) a lister separement s'il est pertinent.
- ⚠️ *SAM top-down 0,3-0,6 Md et bottom-up median 50-90 M USD : 'convergence des deux methodes a un facteur ~5, acceptable'* → Le mot 'convergence' surestime l'accord. 0,3-0,6 Md vs 50-90 M represente un ecart de 5x a 10x selon les bornes retenues ; deux estimations distantes d'un ordre de grandeur ne 'convergent' pas, elles s'encadrent au mieux. La formulation donne une fausse impression de validation croisee. — **Correction :** Reformuler : 'les deux methodes situent le SAM dans une plage 50 M - 600 M USD, soit un ecart d'environ un ordre de grandeur — cadrage grossier, non une validation mutuelle'. Ne pas presenter le facteur 5-10 comme un controle de coherence reussi.
- ⚠️ *TAM composite retenu : ordre de 5-8 Md USD (2025) pour 'agentique de prospection + diagnostic B2B'* → Chiffre construit par recoupement de trois marches aux definitions heterogenes (agentic AI, AI marketing, AI SDR), dont l'intersection 'agentique x prospection/diagnostic B2B' n'a aucune source directe. Partir d'un AI SDR a ~4,4 Md et remonter a 5-8 Md pour ajouter le 'diagnostic' est une inflation non justifiee methodologiquement. Bien qu'etiquete [ESTIMATION MODELISEE], le chiffre risque d'etre cite hors contexte comme un TAM etabli. — **Correction :** Conserver l'AI SDR sourcé (~4,4 Md, borne basse) comme unique ancrage nomme et presenter le 'composite' uniquement comme fourchette d'encadrement explicitement non additive, sans point median implicite.
- ⚠️ *67 % des autorites de protection UE ont accru leurs actions contre l'outreach IA sur 12 mois (source growthspreeofficial)* → Statistique d'editeur martketing (blog commercial), sans base primaire identifiable ; un chiffre '67 % des autorites UE' n'a aucune source institutionnelle plausible (EDPB/CNIL/etc. ne publient pas cet agregat). L'etude le signale comme 'non primaire — a traiter avec reserve', mais un chiffre vraisemblablement fabrique ne devrait pas figurer meme etiquete. — **Correction :** Supprimer le chiffre '67 %' et le remplacer par l'observation qualitative sourcable (durcissement de l'execution RGPD sur l'outreach IA) sans quantification.
- ⚠️ *CAGR agentic AI '30-47 % (consensus 43-46 %)'* → Presenter '43-46 %' comme un 'consensus' au sein d'une fourchette de 30-47 % est une fausse precision : si les analystes vont de 30 a 47 %, il n'y a precisement pas de consensus resserre. Le terme 'consensus' contredit la dispersion affichee. — **Correction :** Retirer '(consensus 43-46 %)' ; ecrire 'CAGR annonces 30-47 % selon cabinet, forte dispersion inter-analystes, pas de valeur consensuelle'.

**Incohérences d'artefacts :**

- Prix Apollo divergents entre les deux PESTEL : le doc concurrentiel cite '~99 USD/siege de base, 150-400 USD/user/mois' (source salesmotion) tandis que le doc digital cite '~49-119 USD/user/mois' (sources prospeo/enrich.so). Deux fourchettes incompatibles pour le meme fournisseur, non reconciliees.
- 'SOM ~18 k-240 k USD/an de MRR annualise' : confusion terminologique. Le MRR est mensuel ; 'MRR annualise' = ARR. La formulation melange MRR et montant annuel et brouille la lecture financiere.
- Tension inter-documents sur l'adoption : le doc concurrentiel affirme '90,3 % des organisations marketing utilisent des agents IA' (table stakes) alors que le doc digital cite '~17 % ont reellement deploye / ~23 % industrialise'. Les deux sont etiquetes mais la juxtaposition 'quasi-universel' vs 'quasi-inexistant en production' merite d'etre explicitement reconciliee (usage declaratif ponctuel != deploiement industrialise), sinon elle affaiblit la credibilite globale.
- AS-IS verifie coherent : 365 tests, api_pricing a 0.0, J6 absent, synthesis.py seul point LLM, orchestrator.py/run_pipeline.py/dag_pipeline.yaml inexistants — tous correctement etiquetes [PLANIFIE]. Aucune incoherence AS-IS detectee sur ce front.

**Réserves :**

- Chaine multiplicative d'incertitude non soulignee : le SAM geographique = (part geo modelisee) x (TAM composite modelise) — deux estimations non sourcees multipliees. L'intervalle affiche (ex. Quebec 35-70 M USD) porte une fausse precision : la vraie incertitude est d'au moins un ordre de grandeur. Ajouter un avertissement explicite sur la propagation d'erreur.
- Les populations de 'buyers' (France 25 000-60 000, Quebec 2 000-5 000, Romandie 1 000-3 000) sont des estimations sans aucune assise sourcee et essentiellement infalsifiables ; elles fondent pourtant tout le SAM bottom-up marche B. A qualifier comme hypotheses de travail a instrumenter, pas comme assises.
- Le SOM marche A (levier de CA conseil) est honnêtement declare non chiffrable — c'est la bonne posture. Mais l'etude devrait rappeler que sans donnees de conversion propres (taux_conversion_etats non encore instrumente), TOUTE la valeur economique du Palier 1 reste une promesse non mesuree.
- Les statistiques d'editeurs martech (90,3 %, 62 %, 67 %) devraient etre regroupees et signalees en bloc comme 'declaratif vendeur non audite', voire retirees des tableaux de synthese, pour eviter qu'elles ne soient recitees comme faits.
- L'AI SDR a ~4,4 Md USD 2025 est une categorie tres jeune : la precision a une decimale ('4,4') est excessive pour un segment aussi recent et mono-analyste (MarketsandMarkets/CMI). A donner en fourchette large uniquement.

**Recommandations :**

- Aval accorde pour la porte de decision car le garde-fou central est respecte : aucun chiffre de marche ne fonde la decision architecturale (Scenario A), qui repose sur des faits AS-IS verifies + la Phase D comme pre-condition dure. Les hallucinations detectees sont peripheriques a la decision.
- Avant toute diffusion externe (investisseur, partenaire), corriger l'attribution concurrentielle Salesforce/Piper/Hunter — c'est la seule erreur factuelle dure et elle est verifiable/embarrassante.
- Reconcilier les deux fourchettes de prix Apollo entre les documents et harmoniser en un seul ordre de grandeur etiquete 'prix de liste vendeur, a revalider Phase D'.
- Corriger 'MRR annualise' en 'ARR' ou 'revenu annuel recurrent'.
- Remplacer le vocabulaire de 'convergence' des methodes SAM par un cadrage honnete a un ordre de grandeur pres.
- Maintenir la Phase D comme pre-condition explicite : tant que api_pricing.yaml=0 et preflight NO-GO, aucune projection OPEX/coût-par-fiche ne doit etre presentee comme engageante — l'etude le fait deja correctement.

### Offre SaaS + plan — approuve_avec_reserves

**Hallucinations / affirmations à corriger détectées :**

- ⚠️ *Palier 1-2 (hors-ligne, ~0 fixe) -> marge brute logicielle ~85-90 %* → Incoherent avec la borne haute de COGS du meme document (15-70 euros/mois pour un tenant Cabinet). A 70 euros de COGS contre un prix Cabinet de 149 euros/mois (ou ARPU melange 117 euros/mois), la marge tombe a ~53 % (voire ~40 % vs ARPU melange), pas 85-90 %. Le 85-90 % ne tient qu'a la borne basse du COGS (~10-15 euros). Comme la LTV utilise marge=0,85, le ratio LTV:CAC 3-8:1 herite de cette hypothese optimiste. — **Correction :** Presenter la marge comme une fourchette dependant du COGS : ~85-90 % SEULEMENT si COGS <= ~15 euros/mois ; ~50-60 % au bord haut de la fourchette COGS actuelle (avant meme toute surprise Phase D). Recalculer LTV et LTV:CAC avec la borne basse de marge pour montrer la sensibilite reelle.
- ⚠️ *SOM : ~15-200 clients a ARPU ~1 200 USD ; ailleurs ARPU mix ~1 400 euros/an ; cible ~1 200-1 500 euros/an* → Melange de devises non reconcilie sur l'ARPU. 1 200 USD ~= 1 100 euros, soit SOUS le plancher annonce de 1 200-1 500 euros. Le socle ARPU differe selon la section (1 200 USD vs 1 400 euros vs 1 200-1 500 euros). — **Correction :** Fixer une devise pivot unique (USD ou EUR) pour tout le chiffrage business et convertir explicitement. Aligner l'ARPU du SOM sur l'ARPU des unit economics (1 400 euros ~= 1 500 USD).
- ⚠️ *Trajectoires MRR : Base 15-25 tenants -> MRR ~2 000-3 500 euros ; Agressif 35-60 -> 5 000-8 500 euros* → L'ARPU implicite n'est pas constant : ~117 euros/mois (conservateur), ~133-140 euros/mois (base), ~142 euros/mois (agressif), alors que le document annonce un ARPU fixe ~1 400 euros/an (117 euros/mois). En appliquant l'ARPU annonce, le scenario Base donnerait 1 755-2 925 euros de MRR, pas 2 000-3 500 euros (derive a la hausse de ~15-20 %). — **Correction :** Soit expliciter le glissement de mix (part Cabinet croissante) qui justifie un ARPU plus eleve dans Base/Agressif, soit recalculer les MRR avec l'ARPU annonce. Ne pas laisser deux ARPU implicites contradictoires.
- ⚠️ *Cout-par-fiche : quelques centimes a quelques dizaines de centimes ; tenant Cabinet (~700 fiches/mo) -> ~15-70 euros/mois de COGS* → Les deux fourchettes ne se reconcilient pas a leur borne haute : 'dizaines de centimes' (jusqu'a ~0,30 euros) x 700 fiches = ~210 euros/mois, alors que le COGS est plafonne a 70 euros/mois (soit <= ~0,10 euros/fiche). — **Correction :** Rendre les deux bornes coherentes : soit limiter le cout-par-fiche a 'quelques centimes' (<= 0,10 euros), soit relever la borne haute du COGS Cabinet a ~150-210 euros/mois.

**Incohérences d'artefacts :**

- Marge brute 85-90 % vs borne haute COGS 70 euros/mois (incoherence interne majeure)
- ARPU en USD (SOM ~1 200) vs EUR (unit econ 1 400 ; cible 1 200-1 500) - devises non reconciliees
- ARPU implicite variable (117 vs 133-140 vs 142 euros/mois) a travers les trajectoires MRR malgre un ARPU annonce fixe de 1 400 euros/an
- Cout-par-fiche 'quelques dizaines de centimes' vs COGS plafonne a 70 euros/mois pour 700 fiches (borne haute non reconciliee)
- Plancher SAM 50M vs plancher bottom-up 17M

**Réserves :**

- Les ratios structurellement favorables (LTV:CAC 3-8:1, payback 2-5 mois, marge 85-90 %) reposent sur la branche COGS basse ; ils se compriment vers ~2-4:1 et marge ~50-60 % si le COGS reel est au haut de la fourchette DEJA modelisee, avant meme un ecart Phase D. A afficher comme conditionnels, pas comme acquis.
- Timeline : Palier 1+2 boucle en ~40 semaines par 1 dev a temps partiel avec bus factor 1 assume, plus ossature J6, noeuds conformite et coordination juriste. Realiste UNIQUEMENT si le perimetre reste du cablage (comme le code le confirme) et si Palier 3 reste gele. Toute derive vers de la logique metier casse l'estimation.
- Populations d'acheteurs (28-68 k) : hypothese de travail non sourcee, deja signalee par l'auteur ; ne doit jamais servir de base a un TAM/SOM engageant.
- Borne haute SAM (plage 50M-600M) : le plancher 50M ne correspond pas au plancher bottom-up 17M qu'elle pretend encadrer ; deja etiquete 'cadrage grossier', mais l'ecart d'un ordre de grandeur interdit toute lecture comme validation croisee.
- L'aval est donne parce que la decision structurante (Scenario A, orchestrateur, Phase D en pre-condition dure de TOUTE monetisation) est saine et verifiee au niveau code ; les incoherences ci-dessus portent sur des chiffres explicitement etiquetes ESTIMATION MODELISEE et non-engageants avant Phase D. Elles doivent etre corrigees AVANT que ces chiffres servent de base a une decision de tarification reelle.

**Recommandations :**

- Fixer une devise pivot unique pour tout le chiffrage et convertir explicitement partout (USD ou EUR).
- Publier une petite table de sensibilite marge : COGS bas/median/haut -> marge brute -> LTV -> LTV:CAC, pour montrer que 3-8:1 est conditionnel a COGS bas et que la vraie inconnue est le COGS Phase D.
- Tenir l'ARPU constant (ou documenter explicitement le glissement de mix Cabinet) et recalculer les MRR des scenarios Base/Agressif en consequence.
- Reconcilier les deux fourchettes de cout unitaire (cout-par-fiche vs COGS mensuel) sur leurs bornes hautes ET basses.
- Conserver la discipline actuelle (ESTIMATION MODELISEE, non-engageant avant Phase D preflight GO) et n'exposer aucun chiffre business a un prospect avant relevé tarifaire reel.
