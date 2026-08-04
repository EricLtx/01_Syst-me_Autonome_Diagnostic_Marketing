# Note de recherche — socle SaaS agentique (refonte V2)

- **Statut** : **note de recherche**. Aucune décision d'architecture n'est prise
  ici. Ce document est le **matériau d'entrée** d'une future ADR de refonte ;
  il n'en tient pas lieu.
- **Date** : 2026-08-04.
- **Portée** : littérature et tendances sur les systèmes agentiques, leurs modes
  d'échec, leur évaluation ; littérature sur la détection de signaux faibles et
  sur l'OSINT ; état de l'industrie 2025-2026. Le domaine actuel (diagnostic
  marketing / image de marque pour PME) est traité comme **première verticale**
  d'un socle destiné à en accueillir d'autres.
- **Ne se substitue pas à** : `docs/adr/0001` (orchestrateur DAG déterministe),
  `0002` (GreenIT), `0003` (multi-industrie), `0004` (axe intention),
  `0005` (audit comme produit). Plusieurs conclusions ci-dessous **confortent**
  des choix déjà faits dans le système V1 ; d'autres les **remettent en cause**.
  Les deux sont signalées.

---

## 0. Méthode — et ce qu'elle vaut exactement

### 0.1 Contrainte d'accès subie dans cette session

**Aucun texte intégral n'a été lu.** C'est une limite dure, mesurée, pas une
formule de prudence :

| Canal tenté | Résultat observé |
|---|---|
| `WebFetch` sur `arxiv.org/abs/…` | **HTTP 403** |
| `WebFetch` sur `arxiv.org/pdf/…` | **HTTP 403** |
| `WebFetch` sur `openreview.net/forum…` | **HTTP 403** |
| `WebFetch` sur `anthropic.com/engineering/…` | **HTTP 403** |
| `curl` direct (`https://arxiv.org`, `https://example.com`) | **CONNECT tunnel failed, 403** (code de sortie 56) |

Le proxy d'agent est actif (`enabled: true`) et l'egress HTTP arbitraire est
fermé. **Seul `WebSearch` a fonctionné.** Or `WebSearch` ne renvoie pas des
textes : il renvoie des titres, des URL, et **un résumé synthétisé par un
modèle tiers** à partir de ces pages. Toute donnée chiffrée figurant dans ce
document a donc transité par **deux couches de résumé** avant d'arriver ici.

C'est **exactement le précédent** de l'ADR 0004 (`docs/adr/0004-…`, §Note de
révision) : « `WebFetch` était bloqué par la politique d'egress — 403
systématique sur toutes les sources. Aucun texte intégral n'a été lu. » La
présente note applique la même règle, en plus strict, parce que la contrainte
est ici plus sévère : en 2026-08 je n'ai même pas eu les résumés d'auteurs, mais
des résumés de résumés.

### 0.2 Convention de marquage — deux axes indépendants

**Axe A — ce que j'ai pu lire de la source :**

- `[NON LU]` — référence **identifiée** (titre, et selon les cas auteurs / année /
  URL / identifiant arXiv), **texte intégral jamais ouvert**. C'est le statut de
  **100 % des références de ce document**. Sans exception.
- `[RÉSUMÉ-OUTIL]` — s'ajoute à `[NON LU]` quand je rapporte un **chiffre** ou un
  **résultat précis** : ce chiffre provient du résumé produit par `WebSearch`,
  pas d'une lecture. **Il doit être revérifié en source avant tout usage
  engageant** (devis, promesse client, argument commercial, spécification).
- `[MÉMOIRE]` — élément (identifiant arXiv, venue, année) que je restitue depuis
  ma connaissance pré-entraînée et qui **n'est pas apparu littéralement** dans
  les résultats de recherche de cette session. À revérifier. Ma date de coupure
  de connaissances est **mai 2026** : tout ce qui est postérieur ne peut pas
  venir de `[MÉMOIRE]`, et je ne le prétends nulle part.

**Axe B — le statut épistémique de l'affirmation :**

- **[ÉTABLI]** — résultat issu d'un travail évalué (revue par les pairs, ou
  benchmark public reproductible avec protocole publié), **et** cohérent avec
  plusieurs sources indépendantes. Le plus fort niveau que ce document atteint.
- **[PRATIQUE]** — pratique d'ingénierie répandue, décrite dans des guides
  techniques sérieux, mais **sans évaluation comparative publiée** qui en isole
  l'effet. Ce n'est pas faux ; ce n'est pas démontré.
- **[COMMERCIAL]** — affirmation issue d'un éditeur, d'un cabinet d'analystes ou
  d'un fonds d'investissement, dont le chiffre sert un intérêt. Peut être vrai.
  N'est jamais une preuve.

Toute affirmation structurante de ce document porte les deux marques.

### 0.3 Prudence particulière sur les publications 2026

Plusieurs résultats renvoyés par `WebSearch` portent des identifiants arXiv de
2026 (`2601.*`, `2604.*`, `2605.*`, `2606.*`, `2607.*`). Ils sont **postérieurs
à ma coupure de connaissances**. Je peux rapporter que *le moteur de recherche a
renvoyé un document portant ce titre à cette URL* ; je ne peux **rien** attester
de leur contenu, de leur sérieux, de leur statut (prépublication non relue ?
atelier ? revue ?), ni même de leur existence effective. Ils sont cités
**comme pistes à ouvrir**, jamais comme appui. Marqués `[2026 — NON VÉRIFIABLE
ICI]`.

### 0.4 Ce que cette note ne peut pas être

Elle ne peut pas être une revue systématique. Il n'y a eu ni protocole de
sélection, ni critère d'inclusion, ni comptage de la littérature écartée. C'est
une **cartographie orientée décision**, faite par requêtes ciblées. Un biais de
confirmation est structurellement possible : j'ai cherché ce que je savais
chercher.

---

## 1. Architectures agentiques — état de la recherche

### 1.1 La distinction fondatrice : *workflow* vs *agent*

La formulation la plus citée de la distinction est celle d'Anthropic dans
« Building Effective Agents » (décembre 2024) `[NON LU]` : un **workflow**
orchestre des appels LLM et outils selon un **flux de contrôle écrit en code**
(le concepteur possède le branchement) ; un **agent** laisse le modèle **choisir
sa prochaine action** à partir des retours de l'environnement (le concepteur ne
possède que l'objectif et les garde-fous). La recommandation explicite y est
« trouver la solution la plus simple possible, et n'augmenter la complexité que
si nécessaire » `[NON LU] [RÉSUMÉ-OUTIL]`.

> **Statut : [PRATIQUE].** C'est un guide d'ingénierie remarquablement lucide,
> largement repris, mais ce n'est **pas** une évaluation comparative. La
> distinction est conceptuellement utile ; sa supériorité n'est pas mesurée
> *dans ce document*. Elle l'est ailleurs — voir §1.4.

**Lecture pour la refonte** : l'ADR 0001 du système V1 a tranché pour un DAG
déterministe et a **explicitement refusé** un superviseur-planificateur LLM. La
littérature examinée ci-dessous ne contredit pas ce choix. Elle le renforce.

### 1.2 Le catalogue des patterns d'orchestration

Les quatre patterns nommés dans la demande sont bien tous attestés dans la
littérature d'ingénierie et dans au moins une revue :

| Pattern | Description | Attestation |
|---|---|---|
| **Superviseur / orchestrateur-ouvrier** | un agent coordinateur décompose et délègue à des ouvriers spécialisés | revue *LLM-Based Multi-Agent Orchestration: A Survey of Frameworks, Communication Protocols, and Emerging Patterns*, *Future Internet* 18(6):326 `[NON LU] [2026 — NON VÉRIFIABLE ICI]` |
| **Pipeline / séquentiel** | étapes ordonnées, sortie de l'une = entrée de la suivante | idem |
| **Blackboard** | mémoire partagée en lecture/écriture pour tous les agents ; pas de contrôleur central du flux | idem `[RÉSUMÉ-OUTIL]` |
| **Marché d'agents** | allocation de tâches par enchère / négociation | idem, cité mais **je n'ai trouvé aucune évaluation empirique en contexte LLM** |

La revue citée propose une taxonomie en **trois topologies** — centralisée,
décentralisée, hiérarchique — avec un axe optionnel de contrôle
dynamique-adaptatif, et compare six cadres (LangGraph, CrewAI,
AutoGen / Microsoft Agent Framework, OpenAI Agents SDK, MetaGPT, DSPy) sur la
granularité de gestion d'état, la structure de coût en tokens, les options de
reprise sur échec `[NON LU] [RÉSUMÉ-OUTIL] [2026 — NON VÉRIFIABLE ICI]`.

Un chiffre circule — « le pattern superviseur représenterait ~70 % des
déploiements multi-agents en production en 2026 » — attribué à des « enquêtes
industrie » sans source primaire nommée dans les résultats.
**Statut : [COMMERCIAL] `[RÉSUMÉ-OUTIL]`. Ne pas réutiliser.**

> **Ce qui manque cruellement** : je n'ai trouvé **aucune comparaison contrôlée
> des quatre patterns entre eux**, toutes choses égales par ailleurs, sur une
> tâche commune. Le catalogue est un vocabulaire, pas un classement.

### 1.3 Décomposition de tâches

Le socle académique est ancien et solide :

- **Least-to-Most Prompting** (Zhou et al., ICLR 2023, arXiv 2205.10625) `[NON LU]` :
  décomposer un problème complexe en sous-problèmes résolus en séquence, chacun
  bénéficiant des réponses précédentes. Le gain rapporté sur SCAN est
  spectaculaire — de 6 % (prompting standard) à 76 %, et jusqu'à 99,7 % avec
  `code-davinci-002` `[RÉSUMÉ-OUTIL]`.
  **[ÉTABLI]** pour l'existence de l'effet ; **mais SCAN est une tâche
  compositionnelle synthétique**, très éloignée d'un diagnostic OSINT sur une
  PME réelle. La généralisation n'est pas acquise.
- **ReAct** (Yao et al., ICLR 2023) `[NON LU]` `[MÉMOIRE : arXiv 2210.03629]` :
  entrelacement raisonnement / action / observation.
- **Reflexion** (Shinn et al., NeurIPS 2023) `[NON LU]` `[MÉMOIRE : arXiv 2303.11366]` :
  l'agent critique sa propre sortie et rejoue avec la critique en mémoire.

Les limites de ces deux derniers sont **documentées et convergentes** :

- ReAct paie un appel de modèle par boucle — latence et coût croissent
  linéairement avec la longueur de chaîne ; **et si un outil renvoie une donnée
  fausse, l'erreur se propage dans tout le raisonnement aval**
  `[NON LU] [RÉSUMÉ-OUTIL]`.
- Reflexion dépend entièrement de la capacité d'auto-évaluation du modèle. Le
  mode d'échec le mieux documenté est la **« dégénérescence de la pensée »** :
  l'agent qui réfléchit sur son propre raisonnement **renforce la logique
  erronée** au lieu d'en changer `[NON LU] [RÉSUMÉ-OUTIL]`.

Ce dernier point n'est pas anecdotique : il rejoint un résultat central.

### 1.4 Le résultat le plus important pour la refonte : l'auto-correction ne marche pas seule

**Huang et al., « Large Language Models Cannot Self-Correct Reasoning Yet »,
ICLR 2024 (arXiv 2310.01798)** `[NON LU]`.

Le titre dit le résultat. **Sans signal externe** (test qui s'exécute, oracle,
vérité terrain, outil qui échoue franchement), demander à un LLM de se corriger
**dégrade** en moyenne les performances de raisonnement plutôt qu'elle ne les
améliore.

> **Statut : [ÉTABLI]** — publié à ICLR, très largement cité, et cohérent avec
> la « dégénérescence de la pensée » observée sur Reflexion, avec les résultats
> sur le débat multi-agents (§1.5) et avec le constat MAST sur les agents
> vérificateurs superficiels (§2.1).

**Conséquence directe et non négociable pour la V2** : un agent « QA », un agent
« critique », un agent « relecteur » **n'apporte rien s'il n'a pas accès à un
signal externe vérifiable**. Le garde-fou du système V1 — `agent-revue` qui
**ré-exécute** les contrôles au lieu de croire le rapport — est précisément la
forme que la recherche valide. Ce n'est pas une coquetterie de méthode : c'est
la seule variante qui fonctionne.

### 1.5 Multi-agents : ce qui est revendiqué vs ce qui est démontré

C'est le point où l'écart entre discours et preuve est le plus large.

**Revendiqué [COMMERCIAL] / [PRATIQUE] :**

- Anthropic rapporte qu'un système avec Claude Opus 4 comme agent principal et
  Claude Sonnet 4 en sous-agents a dépassé une configuration mono-agent de
  **plus de 90 %** sur ses évaluations **internes**
  `[NON LU] [RÉSUMÉ-OUTIL]`. Évaluation interne, tâche de recherche
  documentaire, protocole non public : informatif, **pas une preuve
  généralisable**.
- Une prépublication rapporte « 100 % de qualité de recommandation actionnable
  contre 1,7 % pour un système mono-agent », avec « variance de qualité nulle »
  en réponse à incident `[NON LU] [RÉSUMÉ-OUTIL] [2026 — NON VÉRIFIABLE ICI]`.
  **Un écart 1,7 % → 100 % avec variance nulle est extraordinaire.** Une
  affirmation extraordinaire non lue, non revue, ne s'utilise pas. **À écarter
  jusqu'à lecture.**

**Démontré, et dans l'autre sens [ÉTABLI] :**

- Anthropic mesure que les systèmes multi-agents consomment **~15× plus de
  tokens** qu'une interaction de chat, les agents simples ~4×
  `[NON LU] [RÉSUMÉ-OUTIL]`. Le multi-agents n'est justifié que quand la valeur
  du résultat dépasse ce coût — c'est la formulation d'Anthropic elle-même.
- **Smit et al., « Should we be going MAD? A look at multi-agent debate
  strategies for LLMs », ICML 2024** `[NON LU]` : les systèmes de débat
  multi-agents, dans leur forme actuelle, **ne surpassent pas de façon fiable**
  des stratégies de prompting plus simples comme l'auto-cohérence ou l'ensemble
  de chemins de raisonnement `[RÉSUMÉ-OUTIL]`.
- **Wang et al., « Rethinking the Bounds of LLM Reasoning: Are Multi-Agent
  Discussions the Key? » (arXiv 2402.18272)** `[NON LU]` : même famille de
  conclusion.
- Un travail plus récent conclut que **les systèmes mono-agent égalent ou
  dépassent les multi-agents quand le budget de calcul est normalisé**, sur deux
  jeux (FRAMES, MuSiQue), trois familles de modèles (Qwen3, DeepSeek, Gemini) et
  cinq architectures multi-agents (séquentielle, débat, ensemble, rôles
  parallèles, sous-tâches parallèles)
  `[NON LU] [RÉSUMÉ-OUTIL] [2026 — NON VÉRIFIABLE ICI]`.
  Sa thèse : **« beaucoup de gains multi-agents rapportés s'expliquent mieux par
  des effets de calcul et de contexte que par une supériorité architecturale
  intrinsèque. »**

> **Synthèse §1.5 — à retenir mot pour mot.**
> **La supériorité du multi-agents sur le mono-agent, à budget de calcul égal,
> n'est pas établie.** Elle est *revendiquée* par les éditeurs et *contredite*
> par plusieurs évaluations indépendantes. Le multi-agents a des justifications
> réelles — **parallélisme, isolation des permissions, séparation des contextes,
> spécialisation des outils** — mais « plusieurs agents raisonnent mieux qu'un »
> **n'en fait pas partie**.

### 1.6 Planificateur LLM vs orchestration déterministe

Les résultats convergent sur le **mécanisme** du problème, indépendamment de
toute prise de position :

- **Coupler planification et exécution introduit une variabilité importante du
  comportement d'exécution : de petites variations de sortie du modèle
  produisent des chemins d'exécution divergents, ce qui complique la
  reproductibilité, la stabilité et la prévisibilité du coût**
  `[NON LU] [RÉSUMÉ-OUTIL] [2026 — NON VÉRIFIABLE ICI]`.
- Les sorties stochastiques imposent un multi-échantillonnage coûteux pour
  atteindre la fiabilité ; des coûts d'orchestrateur de **1 à 5 $ par tâche
  complexe** avec des modèles de raisonnement de pointe sont rapportés
  `[NON LU] [RÉSUMÉ-OUTIL] [2026 — NON VÉRIFIABLE ICI]`.
- Une étude contrôlée compare orchestration déterministe et orchestration
  pilotée par LLM sur une modernisation COBOL→Python en tenant constants
  modèles, prompts, outils et configuration, **ne faisant varier que la
  stratégie de contrôle d'exécution**
  `[NON LU] [2026 — NON VÉRIFIABLE ICI]`. **Le protocole est exactement le
  bon** ; je n'ai pas pu en lire le résultat, et je ne l'invente pas.

> **Statut : [ÉTABLI] pour le mécanisme** (le couplage planification/exécution
> dégrade reproductibilité et prévisibilité du coût — c'est une conséquence
> directe de la non-déterminisme d'inférence, §2.5, pas une opinion).
> **[NON ÉTABLI] pour le verdict quantitatif** : je n'ai lu **aucune** mesure
> chiffrée et lisible de l'écart de taux d'échec entre planificateur LLM et
> orchestration déterministe. **C'est une question ouverte, à trancher, pas un
> acquis.**

### 1.7 Mémoire et état des agents

Le vocabulaire est stabilisé, importé des architectures cognitives classiques
(Soar, ACT-R) : **mémoire de travail**, **épisodique** (traces d'expériences),
**sémantique** (connaissances générales), **procédurale** (compétences)
`[NON LU] [RÉSUMÉ-OUTIL]`.

Deux références fondatrices en contexte LLM :

- **Park et al., « Generative Agents », UIST 2023** `[NON LU]`
  `[MÉMOIRE : arXiv 2304.03442]` — hiérarchie à trois niveaux : observation
  brute, réflexion (abstraction de plus haut niveau), récupération par recherche
  sémantique pondérée par l'importance `[RÉSUMÉ-OUTIL]`.
- **MemGPT (Packer et al., 2023)** `[NON LU]` `[MÉMOIRE : arXiv 2310.08560]` —
  le LLM traité comme un système d'exploitation : contexte principal (≈ RAM) +
  stockage externe illimité (≈ disque), avec pagination
  `[RÉSUMÉ-OUTIL]`.

> **Résonance forte avec l'existant.** L'architecture « micro-ordinateur » du
> système V1 (vault = RAM/stockage, `vault_io.py` = contrôleur de bus,
> `api_io.py` = bus I/O, rubriques YAML = ROM) est **la même métaphore que
> MemGPT**, arrivée indépendamment. Ce n'est pas une preuve que c'est juste,
> mais ce n'est pas une bizarrerie locale : c'est un pattern reconnu.

**Ce qui n'est pas établi** : quelle architecture de mémoire est *meilleure*, et
pour quoi. Les benchmarks existent et se multiplient (Episodic Memory Benchmark,
PerLTQA, StreamBench cités `[NON LU] [RÉSUMÉ-OUTIL]`), mais je n'ai vu **aucune
comparaison croisée faisant autorité**. Le constat le plus utile trouvé est
qualitatif : **les domaines sollicitent des mémoires différentes** — assistants
personnels → sémantique ; agents de génie logiciel → procédurale ; agents
scientifiques → sémantique avec suivi explicite de l'incertitude
`[NON LU] [RÉSUMÉ-OUTIL]`. Pour un diagnostic OSINT daté et périssable, la
mémoire dominante est **épisodique et horodatée** — ce qui recoupe exactement la
décision de l'ADR 0004 (un `EvenementIntention` daté, jamais un score).

---

## 2. Modes d'échec documentés

### 2.1 MAST — la taxonomie empirique de référence

**Cemri, Pan, Yang et al., « Why Do Multi-Agent LLM Systems Fail? »
(arXiv 2503.13657, 2025 ; atelier Building Trust, ICLR 2025)** `[NON LU]`.

C'est la source la plus solide de cette section. Éléments rapportés :

| Élément | Valeur rapportée | Statut |
|---|---|---|
| Cadres multi-agents analysés | 7 | `[RÉSUMÉ-OUTIL]` |
| Tâches | > 200 | `[RÉSUMÉ-OUTIL]` |
| Annotateurs experts humains | 6 | `[RÉSUMÉ-OUTIL]` |
| Traces d'exécution annotées (MAST-Data) | 1 642 | `[RÉSUMÉ-OUTIL]` |
| Modes d'échec identifiés | **14** | `[RÉSUMÉ-OUTIL]` |
| Catégories | **3** : (i) problèmes de spécification, (ii) désalignement inter-agents, (iii) vérification de la tâche | `[RÉSUMÉ-OUTIL]` |
| Accord inter-annotateurs (Cohen κ) | 0,88 | `[RÉSUMÉ-OUTIL]` |
| Pipeline LLM-as-judge validé | 94 % d'exactitude, κ = 0,77 vs experts humains | `[RÉSUMÉ-OUTIL]` |

> **Statut : [ÉTABLI]** pour l'existence et la structure de la taxonomie
> (méthodologie explicite, κ rapporté, validation croisée). **Tous les chiffres
> ci-dessus restent `[RÉSUMÉ-OUTIL]` et doivent être revérifiés en source.**

**Le résultat le plus actionnable, et le plus inconfortable** : les interventions
testées pour corriger les échecs identifiés **n'ont pas suffi**. Un gain de
**+15,6 % pour ChatDev** est rapporté, mais « les interventions simples n'ont
pas résolu les problèmes sous-jacents » `[RÉSUMÉ-OUTIL]`. Et surtout :

> **« Les implémentations multi-agents actuelles incluent souvent un agent
> vérificateur, mais ses contrôles sont superficiels — le code est accepté s'il
> compile, les programmes sont supposés corrects si les commentaires paraissent
> cohérents. Ajouter des couches de vérification exige des changements
> architecturaux et l'intégration de contrôles symboliques, pas seulement des
> instructions de prompt supplémentaires. »** `[NON LU] [RÉSUMÉ-OUTIL]`

C'est la même conclusion que Huang et al. (§1.4), par un autre chemin. **Un
vérificateur qui n'exécute rien ne vérifie rien.**

### 2.2 Cascade d'erreurs et horizon long

- **Compoundage exponentiel** : pour un taux d'erreur par étape ε et N étapes
  indépendantes, la probabilité de succès décroît en (1−ε)^N. **Mais les erreurs
  ne sont pas indépendantes** : elles sont **positivement corrélées** entre
  étapes, ce qui rend le compoundage *pire* que le cas indépendant
  `[NON LU] [RÉSUMÉ-OUTIL] [2026 — NON VÉRIFIABLE ICI]`.
  **[PRATIQUE / partiellement ÉTABLI]** — le calcul (1−ε)^N est arithmétique et
  incontestable ; la **corrélation positive** est une affirmation empirique dont
  je n'ai pas lu la démonstration.
- **METR, « Measuring AI Ability to Complete Long (Software) Tasks »
  (arXiv 2503.14499, mars 2025)** `[NON LU]` : introduit l'**horizon temporel à
  50 %** — la durée humaine des tâches qu'un modèle réussit une fois sur deux.
  Rapporté : **doublement environ tous les 7 mois sur 6 ans** ; suite de **170
  tâches** ; Claude 3.7 Sonnet autour de **50 minutes** d'horizon à 50 %
  `[RÉSUMÉ-OUTIL]`.
  **[ÉTABLI] comme mesure**, **[NON ÉTABLI] comme extrapolation** — la
  projection « en moins de cinq ans, des tâches de plusieurs jours » est une
  extrapolation des auteurs, pas un résultat.
  ⚠️ **Périmètre** : tâches de génie logiciel, cybersécurité et raisonnement
  général. **Rien n'autorise à transposer cet horizon à un diagnostic OSINT
  commercial.**

> **Conséquence de conception, indépendante des chiffres** : la fiabilité
> s'effondre avec la longueur de chaîne. La parade n'est pas un meilleur modèle,
> c'est **la brièveté des chaînes autonomes** et **des points de contrôle
> vérifiables entre les segments**. Le DAG de l'ADR 0001, avec sa porte humaine
> au milieu (`diagnostique → valide`), fait déjà exactement cela.

### 2.3 Dérive de contexte

Deux mécanismes **distincts** — les confondre est une erreur d'ingénierie
courante :

1. **Dégradation positionnelle — « lost in the middle »** (Liu et al., TACL
   2024) `[NON LU]` `[MÉMOIRE : arXiv 2307.03172]` : la performance suit une
   courbe en U selon la position de l'information pertinente ; l'exactitude
   chute **de plus de 30 %** quand elle est au milieu du contexte. Répliqué sur
   six familles de modèles (GPT-3.5-Turbo, GPT-4, Claude 1.3, LongChat-13B,
   MPT-30B, Cohere Command) `[RÉSUMÉ-OUTIL]`. **[ÉTABLI]** — TACL, réplication
   multi-modèles.
2. **Dégradation par longueur — « context rot »** : la performance décline à
   mesure que l'entrée grandit, **indépendamment de la position**. Une étude
   Chroma (2025) sur **18 modèles de pointe** rapporte que **tous** exhibent ce
   comportement, à chaque incrément de longueur testé
   `[NON LU] [RÉSUMÉ-OUTIL]`. **[PRATIQUE → tendance ÉTABLIE]** — travail de
   laboratoire d'éditeur, protocole public mais non revu par les pairs.

**Ce que ça implique** : un agent qui accumule tout son historique dans une
fenêtre de contexte croissante **se dégrade mécaniquement**. La mitigation
« mettre un modèle à contexte plus long » ne résout pas le problème 2. Les
mitigations plausibles — compaction, mémoire externe adressable, remise à zéro
entre segments — sont **[PRATIQUE]**, très répandues, et **je n'ai lu aucune
évaluation comparative qui en isole l'effet.**

### 2.4 Hallucination en chaîne d'outils, et injection indirecte

C'est le mode d'échec le plus dangereux pour une plateforme OSINT, parce que
**l'entrée est par définition du contenu tiers non fiable**.

- L'injection de prompt (directe et indirecte) est en tête de l'OWASP LLM Top 10
  2025 `[NON LU] [RÉSUMÉ-OUTIL]`. L'injection **indirecte** place des
  instructions adverses dans les pages web, documents et courriels que l'agent
  récupère **en fonctionnement normal**.
- Chiffres rapportés : **InjecAgent** et **Agent Security Bench** montrent des
  taux de succès d'attaque **supérieurs à 60 %** sur des modèles de premier plan
  en scénarios multi-outils réalistes ; **PoisonedRAG** atteint **plus de 90 %**
  en injectant cinq documents malveillants ; **AgentDojo** fournit un
  environnement où les outils renvoient des résultats empoisonnés
  `[NON LU] [RÉSUMÉ-OUTIL]`.
- Position de l'OWASP : l'injection de prompt est un **risque architectural
  fondamental** exigeant des contrôles en couches — isolation des entrées non
  fiables, **blocages d'egress déterministes**, défense en profondeur
  `[NON LU] [RÉSUMÉ-OUTIL]`.

> **Statut : [ÉTABLI]** que le problème existe et qu'il est sévère (benchmarks
> publics multiples, convergents, avec taux d'attaque élevés).
> **[NON ÉTABLI]** qu'une défense générale fonctionne. **Aucune source consultée
> ne prétend le contraire.** La seule mitigation qui fasse consensus est
> **architecturale, pas prompt-based** : ne pas donner à un agent qui lit du
> contenu non fiable les moyens d'agir de façon irréversible.

**Note d'ironie utile** : le système V1 possède déjà l'invariant qui compte —
« le LLM ne fetch jamais » et « collecte déterministe ≠ raisonnement LLM ». Un
LLM qui ne peut ni fetcher ni écrire n'est pas un vecteur d'action pour un
injecteur. **Cet invariant est un contrôle de sécurité, pas seulement une
élégance d'architecture. La refonte ne doit pas le perdre par distraction.**

### 2.5 Non-reproductibilité — le résultat le plus sous-estimé

**Thinking Machines Lab, « Defeating Nondeterminism in LLM Inference »
(billet de recherche, 2025)** `[NON LU]`.

Le fait rapporté : échantillonner **1 000 complétions à température 0** avec
Qwen3-235B-Instruct produit **80 sorties distinctes**, la divergence apparaissant
au **token 103** `[RÉSUMÉ-OUTIL]`.

La cause identifiée n'est **pas** la concurrence GPU au sens naïf, mais
l'**absence d'invariance au batch** : normalisation, multiplication matricielle
et attention ne sont pas invariantes à la taille du lot, et le serveur regroupe
les requêtes en lots variables dans le temps. La sortie d'une requête dépend donc
de **ce que les autres utilisateurs faisaient au même instant**. Avec des noyaux
invariants au batch, les auteurs obtiennent des sorties **bit-à-bit
identiques** sur 1 000 exécutions (Qwen3-8B), au prix d'environ **61,5 % de
débit** dans leur implémentation de référence `[RÉSUMÉ-OUTIL]`.

> **Statut : [ÉTABLI] pour le phénomène** (mécanisme numérique explicable,
> reproduction décrite, correctif publié). **[RÉSUMÉ-OUTIL] pour tous les
> chiffres.**

**Portée pour la refonte — c'est décisif.** « Température 0 » **ne garantit pas**
la reproductibilité derrière une API partagée. Toute promesse de
reproductibilité qui repose sur `temperature=0` est **fausse**. Un système qui a
besoin de rejouer un diagnostic à l'identique (audit, contestation client,
conformité) doit :

- soit **journaliser la sortie** et rejouer depuis le journal, pas depuis le
  modèle ;
- soit **rendre déterministe tout ce qui n'a pas besoin du LLM** et confiner le
  LLM à ce qui est rejouable depuis un cache.

Le système V1 fait déjà les deux (grand livre `api_usage.log` append-only, cache
disque dans `api_io`, repli déterministe sans clé). **C'est un actif, pas un
héritage à liquider.**

### 2.6 Coût non borné

- Le multiplicateur ~15× tokens du multi-agents (§1.5) est la mesure la plus
  citable `[NON LU] [RÉSUMÉ-OUTIL]`.
- **Kapoor, Stroebl, Siegel, Nadgir, Narayanan, « AI Agents That Matter »
  (arXiv 2407.01502, 2 juillet 2024)** `[NON LU]` : le diagnostic central est que
  **la focalisation étroite sur l'exactitude, sans attention au coût, produit
  des agents SOTA inutilement complexes et coûteux**, et que **des lignes de base
  simples égalent des modèles complexes à bien moindre coût**. Les auteurs
  proposent l'**évaluation à coût contrôlé** et l'optimisation conjointe
  exactitude/coût `[RÉSUMÉ-OUTIL]`.

> **Statut : [ÉTABLI].** C'est, avec MAST et Huang et al., l'une des trois
> références que la refonte doit lire intégralement dès qu'un accès réseau est
> disponible.

**Résonance directe** : l'ADR 0002 (GreenIT) a déjà instrumenté coût, énergie et
CO₂e par appel dans `LedgerEntry`, avec routage de modèle déterministe piloté par
YAML. La littérature dit que c'est le bon axe. Elle dit aussi, en creux, que
**publier une exactitude sans le coût qui l'a produite est une mauvaise pratique
d'évaluation.**

---

## 3. Évaluation des systèmes agentiques

C'est la section la plus importante pour la refonte, parce que le système V1
possède déjà un dispositif — la **porte de cohérence à 97 %** — et veut le
conserver sous une forme défendable.

### 3.1 Les benchmarks de référence, et leurs failles

| Benchmark | Objet | Réf. |
|---|---|---|
| **SWE-bench** (Jimenez et al., ICLR 2024) | résolution d'issues GitHub réelles | `[NON LU]` `[MÉMOIRE : arXiv 2310.06770]` |
| **GAIA** (Mialon et al., 2023) | assistants généralistes, questions multi-étapes | `[NON LU]` `[MÉMOIRE : arXiv 2311.12983]` |
| **WebArena** (Zhou et al., 2023) | agents web en environnement réaliste | `[NON LU]` `[MÉMOIRE : arXiv 2307.13854]` |
| **τ-bench** (Yao et al., 2024, arXiv 2406.12045) | interaction outil-agent-utilisateur, domaines réels | `[NON LU]` |
| **AgentDojo** | robustesse à l'injection indirecte | `[NON LU]` |
| **CORE-bench** (arXiv 2409.11363) | reproductibilité computationnelle de publications | `[NON LU]` |

**Failles documentées :**

- **Contamination.** Il est rapporté qu'un audit OpenAI de SWE-bench a trouvé un
  recouvrement avec les données d'entraînement **sur tous les modèles de
  pointe**, et que **59,4 % des tâches « hard » avaient des tests défectueux**
  `[NON LU] [RÉSUMÉ-OUTIL]`. ⚠️ **Chiffre non vérifié, à ne pas citer en
  externe.** Des estimations de **5 à 15 points** d'inflation des scores dues à
  contamination, échafaudage et rapport en exécution unique circulent également
  `[RÉSUMÉ-OUTIL]`.
- **GAIA résiste mieux par conception** : questions écrites à la main, jeu de
  test non public (seule la validation est publiée), nombreuses questions
  référençant des documents postérieurs `[NON LU] [RÉSUMÉ-OUTIL]`.
- **Le rapport en exécution unique** (pass@1) est le défaut le plus structurel —
  voir §3.2.

> **Le constat qui vaut pour toute la refonte** : *un bon score sur un benchmark
> prouve une capacité dans le domaine du benchmark, pas une aptitude à votre cas
> d'usage — cela exige vos propres évaluations sur vos données réelles*
> `[RÉSUMÉ-OUTIL]`. **[ÉTABLI]**, banal, et systématiquement ignoré.

### 3.2 `pass^k` — la mesure que la V2 doit adopter

**τ-bench (Yao et al., 2024)** `[NON LU]` introduit **`pass^k`** : la fraction de
`k` tentatives indépendantes de la **même** tâche qui réussissent **toutes**.

Ce n'est pas une variante cosmétique de `pass@k`. `pass@k` mesure « au moins une
réussite sur k » — c'est une mesure de **capacité**. `pass^k` mesure « k
réussites sur k » — c'est une mesure de **consistance**. Un système de production
a besoin des deux, et **seul `pass^k` prédit le comportement en exploitation.**

Chiffres rapportés : les agents de pointe réussissaient **moins de 50 %** des
tâches, et un agent GPT-4o tombait à **~25 % en `pass^8`** sur τ-retail, soit
**une chute d'environ 60 %** par rapport à son `pass^1`
`[NON LU] [RÉSUMÉ-OUTIL]`.

> **Statut : [ÉTABLI]** comme méthodologie ; les chiffres restent
> `[RÉSUMÉ-OUTIL]`.

**Implication frontale pour la porte à 97 %.** Le taux actuel du projet est
`assertions vérifiées / assertions totales` sur **une** exécution. Pour les
assertions **déterministes** (tests unitaires, marche AST, `git diff` vide,
conformité de contrat JSON), une exécution suffit : la répéter donne le même
résultat, par construction. **Pour toute assertion touchant une sortie LLM, une
exécution ne suffit pas** — c'est un `pass^1` déguisé, et §2.5 explique pourquoi
il ne se reproduira pas.

### 3.3 LLM-as-judge : biais documentés

Trois biais sont établis et convergents :

| Biais | Description | Références |
|---|---|---|
| **Position** | le choix d'un juge LLM change en **réordonnant simplement** les réponses candidates ; forte préférence pour la première option en comparaison par paires | *Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge* (arXiv 2410.02736) `[NON LU]` ; Zheng et al., MT-Bench, NeurIPS 2023 D&B `[NON LU]` `[MÉMOIRE : arXiv 2306.05685]` |
| **Verbosité / longueur** | les juges notent mieux les réponses longues, indépendamment de la qualité | idem `[RÉSUMÉ-OUTIL]` |
| **Auto-préférence** | un juge favorise les réponses qu'il a lui-même produites | *Self-Preference Bias in LLM-as-a-Judge* (arXiv 2410.21819) `[NON LU]` |

> **Statut : [ÉTABLI]** — plusieurs travaux indépendants, biais reproduits,
> mitigation partielle connue (permuter l'ordre et moyenner) et **elle-même
> évaluée**, ce qui est rare.

**Une nuance essentielle, et rassurante** : MAST (§2.1) montre qu'un juge LLM
**peut** atteindre une fiabilité utile — 94 % d'exactitude, κ = 0,77 vs experts —
**mais à une condition précise** : la tâche du juge y est une **classification
dans une taxonomie fermée de 14 modes d'échec**, calibrée contre **1 642 traces
annotées par 6 experts** avec κ inter-annotateurs de 0,88
`[NON LU] [RÉSUMÉ-OUTIL]`.

> **La leçon est nette : un juge LLM est utilisable quand il *classe* contre une
> grille close et calibrée. Il n'est pas fiable quand il *apprécie* librement une
> qualité.** La différence entre « ce texte est-il bon ? » et « à laquelle de ces
> 14 catégories cette trace appartient-elle ? » est la différence entre un
> instrument et une impression.

### 3.4 Métriques de grounding

- **Distinction fondamentale** : la **factualité** est la vérité par rapport au
  monde ; la **fidélité (faithfulness / grounding)** est la vérité par rapport
  au contexte fourni `[NON LU] [RÉSUMÉ-OUTIL]`. **[ÉTABLI]** et souvent confondu.
  Un système peut être parfaitement fidèle à une source fausse.
- **RAGAS** (Es et al.) `[NON LU]` `[MÉMOIRE : arXiv 2309.15217, démo EACL 2024]` :
  Faithfulness, Answer Relevancy, Context Precision, Answer Correctness. La
  fidélité y quantifie si la réponse est soutenue par les passages récupérés.
- **FActScore** (Min et al., EMNLP 2023) `[NON LU]`
  `[MÉMOIRE : arXiv 2305.14251]` : décompose une génération en faits atomiques
  et évalue chacun. **La granularité atomique est le point qui compte** — voir
  la limite ci-dessous.
- **AIS / Attributable to Identified Sources** (Rashkin et al., *Computational
  Linguistics*, 2023) `[NON LU]` `[MÉMOIRE]` : cadre d'évaluation de
  l'attribution. ⚠️ **Cette référence n'est pas apparue dans les résultats de
  recherche de cette session.** Elle vient de ma mémoire seule. **À vérifier
  avant toute citation.**

**Limite documentée** : *juger un paragraphe entier « globalement vrai » est
problématique — une réponse peut être factuelle à 90 % et hallucinée à 10 %, et
ces 10 % peuvent être la partie critique* `[RÉSUMÉ-OUTIL]`. **[PRATIQUE]** —
c'est une observation d'ingénierie de bon sens, pas un résultat mesuré, mais
elle motive directement la granularité atomique de FActScore.

**Résonance avec l'existant** : la règle QA du système V1 — « aucune affirmation
non adossée aux failles réelles » — **est** une contrainte de grounding, formulée
avant d'en connaître le nom. Sa force est qu'elle est **structurelle** (la
synthèse ne reçoit que des faits déjà établis par les collecteurs) plutôt que
**mesurée a posteriori**. La littérature ne dit pas laquelle des deux approches
est meilleure ; l'approche structurelle a l'avantage de ne pas dépendre d'un
juge.

### 3.5 Le facteur humain : la porte humaine n'est pas gratuite

Le système V1 fait reposer une garantie forte sur la **porte humaine**
(`diagnostique → valide` réservé à l'opérateur dans Obsidian). La littérature en
facteurs humains dit que **cette garantie s'érode** :

- **Parasuraman & Riley, « Humans and Automation: Use, Misuse, Disuse, Abuse »,
  *Human Factors* 39(2), 1997** `[NON LU]` : typologie mésusage
  (sur-confiance) / désusage (rejet) `[RÉSUMÉ-OUTIL]`.
- **Parasuraman & Manzey, « Complacency and Bias in Human Use of Automation: An
  Attentional Integration », *Human Factors* 52(3), 2010** `[NON LU]` :
  **complaisance induite par l'automatisation** — les opérateurs cessent de
  surveiller la sortie, **surtout quand la charge est élevée et que l'aide
  automatisée a « généralement raison »** `[RÉSUMÉ-OUTIL]`.
- Le **règlement européen sur l'IA, art. 14(4)(b)** oblige les fournisseurs à
  permettre aux personnes chargées de la supervision de **rester conscientes de
  la tendance au biais d'automatisation** `[NON LU] [RÉSUMÉ-OUTIL]`.
- Formulation la plus dure rencontrée : la supervision humaine dans la boucle
  *fonctionne d'abord comme une architecture de responsabilité juridique plutôt
  que comme un mécanisme de sécurité effectif*
  `[NON LU] [RÉSUMÉ-OUTIL] [2026 — NON VÉRIFIABLE ICI]`. **[COMMERCIAL /
  POSITION]** — c'est une thèse critique, pas un résultat.

> **Statut : [ÉTABLI]** pour le biais d'automatisation et la complaisance
> (littérature en facteurs humains, plusieurs décennies, hors IA générative).
> **[NON ÉTABLI]** pour son ampleur exacte dans le cas précis d'un opérateur
> validant des fiches prospects dans Obsidian.

**Conséquence désagréable et à assumer** : plus le système sera *bon*, plus
l'opérateur validera vite et regardera moins. Une porte humaine qui approuve
99 % de ce qui lui est présenté **n'est plus une porte**. Il faut la mesurer —
c'est exactement ce que le `motif_rejet` du Lot 0 (ADR 0004, non fait)
permettrait, et c'est une raison de plus de le faire.

---

## 4. Détection de signaux faibles

### 4.1 Le socle théorique

- **Ansoff, « Managing Strategic Surprise by Response to Weak Signals »,
  *California Management Review*, 1975** `[NON LU]` `[MÉMOIRE : vol. 18, n° 2]` :
  origine du concept, lié au **strategic issue management**.
- **Holopainen & Toivonen, « Weak signals: Ansoff today », *Futures*, 2012**
  `[NON LU]` (ScienceDirect S0016328711002540 — l'identifiant est apparu dans
  les résultats).
- **Hiltunen, « The future sign and its three dimensions », *Futures*, 2008**
  `[NON LU]` `[MÉMOIRE]` : le « signe futur » à trois dimensions — signal,
  problème, interprétation.
- **Rossel, « Early detection, warnings, weak signals and seeds of change: A
  turbulent domain of futures studies », *Futures*, 2012** `[NON LU]` `[MÉMOIRE]`.
- **Mendonça, Cardoso, Caraça, « The strategic strength of weak signal
  analysis », *Futures*, 2012** `[NON LU]` `[MÉMOIRE]`.
- **Système d'alerte précoce stratégique (SEWS)** : dispositif organisationnel
  visant à détecter tôt de nouveaux motifs, tendances ou événements
  `[NON LU] [RÉSUMÉ-OUTIL]`.

Une définition consensuelle : un signal faible est **vague, flou, difficile à
interpréter**, et **se précise graduellement** en devenant un signal fort
`[NON LU] [RÉSUMÉ-OUTIL]`.

### 4.2 Ce qui est établi — et c'est peu

> **La formulation la plus importante de toute cette section**, rapportée par la
> recherche documentaire : **« la théorie manque d'assise empirique, ce qui pose
> la question de l'existence et de l'utilité même des signaux faibles »**, et
> **« il existe des discontinuités qui surviennent sans être annoncées par aucun
> signal faible — les *wild cards* »** `[NON LU] [RÉSUMÉ-OUTIL]`.

**Statut : [NON ÉTABLI].** Ce n'est pas moi qui le dis prudemment ; c'est la
littérature du domaine qui le dit d'elle-même. Ce qui est établi :

- **[ÉTABLI]** — le concept existe, est stabilisé, structure un champ de la
  prospective depuis 50 ans, et fournit un **vocabulaire opératoire** (signal,
  interprétation, issue, discontinuité, wild card).
- **[ÉTABLI]** — les **échecs de mise en œuvre** des SEWS sont documentés (voir
  la littérature sur les *pitfalls in implementing a strategic early warning
  system* `[NON LU]`). On sait mieux pourquoi ça rate que pourquoi ça marche.
- **[NON ÉTABLI]** — **la valeur prédictive d'un signal faible observable
  publiquement**. Je n'ai trouvé **aucune** étude fournissant une mesure de
  précision, de rappel, de lift ou de valeur prédictive positive d'un dispositif
  de détection de signaux faibles sur une population de cibles commerciales.

### 4.3 Le cas particulier du B2B intent data

C'est la transposition commerciale directe de la question, et c'est un point
noir.

Ce que la recherche a renvoyé : une étude Forrester Consulting **commanditée par
Bombora**, décrite comme « sans doute l'évaluation tierce la plus rigoureuse du
ROI des données d'intention à ce jour », rapportant **5,4 M$ de bénéfices
quantifiés, 342 % de ROI, 10 % de réduction du churn** pour une organisation
composite `[NON LU] [RÉSUMÉ-OUTIL]`. **[COMMERCIAL]** — étude commanditée,
organisation *composite* (c'est-à-dire modélisée, pas observée), publiée par le
fournisseur. **Non utilisable comme preuve.**

Et le constat explicite du moteur de recherche, que je reproduis parce qu'il est
le résultat :

> **« Les résultats de recherche ne contiennent pas d'études académiques
> évaluées par les pairs traitant spécifiquement du scepticisme sur la validité
> prédictive des données d'intention, ni d'évaluations académiques indépendantes
> distinctes de la recherche commanditée par les fournisseurs. »**
> `[RÉSUMÉ-OUTIL]`

**C'est l'exact équivalent, pour la V2, de la phrase actée dans l'ADR 0004 :**
« aucune source ne franchit le dernier pas entre signal ouvert observé et cette
PME va acheter du conseil en branding. » **La situation n'a pas changé.** La
recherche documentaire de 2026-08 ne l'a pas plus franchi que celle de 2026-08-03.

**La méthode d'évaluation, elle, est claire et non contestée** : mesurer le
**lift incrémental contre un groupe témoin apparié** — « les comptes marqués par
un signal convertissent-ils plus qu'un groupe de contrôle comparable ? »
`[RÉSUMÉ-OUTIL]`. **[ÉTABLI]** comme méthode ; **[NON FAIT]** dans ce projet.
C'est précisément ce que le `motif_rejet` du Lot 0 et les états `rdv`/`client`
rendraient possible, et rien d'autre ne le rendra possible.

---

## 5. OSINT — cadre méthodologique et limites

### 5.1 L'échelle Admiralty / OTAN

Le cadre de référence pour la fiabilité de source est le **code Admiralty**,
développé par l'Amirauté britannique pendant la Seconde Guerre mondiale, puis
adopté par l'OTAN (**AJP-2.1**) `[NON LU] [RÉSUMÉ-OUTIL]`. Notation
alphanumérique à deux composantes indépendantes :

- **Fiabilité de la source : A → F** (historique, accès à l'information, biais
  connus)
- **Crédibilité de l'information : 1 → 6** (corroboration, plausibilité,
  cohérence avec les faits connus)

**Deux critiques documentées, toutes deux importantes pour la conception :**

1. **Les deux échelles ne sont pas indépendantes en pratique.** Une analyse de
   **plus de 1 400 rapports de renseignement de terrain de l'armée** trouve que
   **87 % des notations tombent sur la diagonale** (A1, B2, C3…)
   `[NON LU] [RÉSUMÉ-OUTIL]`. Autrement dit : les analystes notent la
   crédibilité de l'information **d'après** la fiabilité de la source, ce qui
   détruit l'apport de la seconde dimension.
   ⚠️ **Chiffre `[RÉSUMÉ-OUTIL]`, à revérifier avant citation.**
2. **En environnement OSINT à haut volume, la majorité du matériel entrant
   arrive en F6** — source sans historique établi, information non corroborée —
   ce qui est le **point de départ de la plupart des sources ouvertes**
   `[NON LU] [RÉSUMÉ-OUTIL]`.

> **Statut : [ÉTABLI]** comme cadre normatif institutionnel (doctrine OTAN).
> **[ÉTABLI]** que sa mise en œuvre humaine souffre d'un défaut de corrélation
> entre ses deux axes. **[NON ÉTABLI]** qu'une notation Admiralty améliore la
> qualité des décisions — je n'ai vu aucune évaluation de ce type.

**Lecture pour la V2** : le champ `fiabilite` déjà présent sur
`EvenementIntention` (ADR 0004) est dans le bon esprit. Le piège documenté est
de le laisser **corréler mécaniquement** avec l'origine de la donnée. Si la
fiabilité est calculée depuis le collecteur, ce n'est pas une seconde dimension,
c'est le même chiffre écrit deux fois.

### 5.2 Chaîne de preuve et reproductibilité

C'est le point faible reconnu de l'OSINT : une page web observée à l'instant *t*
peut avoir disparu à *t+1*, et **rien ne prouve après coup ce qu'elle contenait**.

Ce que j'ai trouvé : les bonnes pratiques recommandées — attribuer une notation
de fiabilité et de crédibilité à chaque source pour **hiérarchiser
l'information** et rendre les produits **transparents et défendables**
`[NON LU] [RÉSUMÉ-OUTIL]`. **[PRATIQUE]** — recommandation professionnelle
(SOS Intelligence, Blockint, EOS), **pas** un standard évalué.

Je n'ai trouvé **aucun standard de chaîne de preuve OSINT faisant autorité et
évalué**, comparable à ce qui existe en forensique numérique. Le domaine
académique le plus proche renvoyé — *From Agent Traces to Trust: A Survey of
Evidence Tracing and Execution Provenance in LLM Agents* `[NON LU]`
`[2026 — NON VÉRIFIABLE ICI]` — porte sur la traçabilité des agents, pas des
sources.

> **Conséquence de conception** : la **capture horodatée de l'observation** (pas
> seulement de sa conclusion) est la seule chose qui rende un diagnostic OSINT
> défendable a posteriori. Le système V1 a `VaultIO.append_historique()`
> — infrastructure **posée et non exploitée**. La V2 devrait l'exploiter, et
> capturer **l'octet observé**, pas seulement le signal dérivé.

### 5.3 Contraintes d'accès : robots.txt, ToS, rate limits

Cadre juridique tel que rapporté (⚠️ **je ne suis pas juriste et ceci n'est pas
un avis juridique** ; le projet a déjà posé la validation juridique comme
pré-condition dure de J6) :

**États-Unis**
- *Van Buren v. United States* (Cour suprême, 2021) `[NON LU]` : lecture
  restrictive du volet « exceeds authorized access » du CFAA, pour éviter de
  criminaliser toute violation d'une politique d'usage `[RÉSUMÉ-OUTIL]`.
- *hiQ Labs v. LinkedIn* (9e circuit, 2022) `[NON LU]` : le scraping de données
  **publiques** n'est pas une violation du CFAA — là où une page est ouverte à
  tous sans authentification, il n'y a pas de barrière d'autorisation à franchir
  `[RÉSUMÉ-OUTIL]`.
- **Mais** : après avoir gagné sur le CFAA, **hiQ a perdu sur le contrat**. En
  novembre 2022, la cour a jugé qu'il avait violé le *User Agreement* de
  LinkedIn (accepté en créant des comptes) ; l'affaire s'est terminée par un
  jugement d'accord `[NON LU] [RÉSUMÉ-OUTIL]`.

> **La formulation à retenir, telle que rapportée** : *« le CFAA vous protège
> des accusations de piratage sur des pages publiques ; il ne vous protège pas
> des contrats que vous avez acceptés. »* **[ÉTABLI]** comme état de la
> jurisprudence rapportée ; **[NON VÉRIFIÉ]** juridiquement par un praticien.

**Union européenne**
- **Directive (UE) 2019/790, art. 3 et 4** `[NON LU]` : deux exceptions
  obligatoires de fouille de textes et de données. L'art. 3 vise la recherche ;
  **l'art. 4 vise tout bénéficiaire et tout usage, mais peut être neutralisé par
  un opt-out** du titulaire de droits `[RÉSUMÉ-OUTIL]`.
- Pour du contenu mis en ligne publiquement, l'opt-out doit être exprimé par des
  **moyens lisibles par machine** — et **il n'existe aujourd'hui aucun standard
  technique universellement accepté** pour cela ; `robots.txt` est le véhicule
  de fait `[NON LU] [RÉSUMÉ-OUTIL]`. La Commission a lancé une étude de
  faisabilité sur un **registre central d'opt-outs** `[NON LU]`.

**Statut de robots.txt**
- *« robots.txt n'est pas une loi, et l'ignorer n'est pas automatiquement
  illégal. Mais les tribunaux et les régulateurs le traitent comme un signal de
  bonne ou de mauvaise foi ; plusieurs décisions le citent en pesant les
  prétentions de trespass et de contrat, et les garde-fous de la CNIL attendent
  que vous honoriez les opt-outs. »* `[NON LU] [RÉSUMÉ-OUTIL]`

> **[ÉTABLI]** que robots.txt n'a pas de force contraignante autonome.
> **[ÉTABLI]** qu'il est le véhicule de fait de l'opt-out TDM européen, donc
> **qu'il acquiert une portée juridique indirecte dans l'UE**. Le respecter
> n'est plus seulement poli : c'est la seule façon lisible de constater un
> opt-out.

**Dette identifiée dans le système V1** : le `CLAUDE.md` note que l'escalade
« page carrières » de `WebsiteCollector` (ADR 0004, Lot 2) **ne vérifie pas
robots.txt**. Au vu de ce qui précède, c'est plus qu'une inélégance. **La V2 doit
poser un contrôle robots.txt au niveau du bus I/O — un seul endroit — plutôt que
par collecteur.**

---

## 6. Tendances 2025-2026 de l'industrie agentique

Toute cette section est le terrain le plus miné du document. J'y sépare
agressivement les trois niveaux.

### 6.1 « Service-as-software » et agents verticaux

**La thèse [COMMERCIAL]** — Foundation Capital, *A System of Agents brings
service as software to life* `[NON LU]` : quand un système d'agents accomplit une
tâche complète, il se catégorise comme **coût de personnel** plutôt que comme
dépense logicielle, ce qui ouvre un marché bien plus grand. Chiffrage avancé :
**4,6 T$** — les budgets IT représentant 1-2 % du PIB, le travail et les
services traditionnels plus de 15 % ; Salesforce génère ~35 Md$/an face à
~1,1 T$ dépensés mondialement en salaires de vente et marketing
`[RÉSUMÉ-OUTIL]`.

**Statut : [COMMERCIAL].** C'est une thèse d'investisseur, publiée par un fonds
qui investit dans cette thèse. Le raisonnement (« viser la ligne salaires du
P&L, pas la ligne logiciel ») est **stratégiquement lucide et directement
pertinent** pour le positionnement de la V2. Le chiffre de 4,6 T$ est un TAM
théorique, **pas un marché adressable**. **Ne jamais le citer comme un fait.**

Une projection de marché « agents verticaux : 8,1 Md$ en 2025 → 182,9 Md$ en
2034, TCAC 49,6 % » `[RÉSUMÉ-OUTIL]` provient d'un cabinet d'études de marché
vendant le rapport. **[COMMERCIAL]. Sans valeur probante.**

### 6.2 Le taux d'échec — les deux chiffres qui circulent

**(a) MIT NANDA, *The GenAI Divide: State of AI in Business 2025*** `[NON LU]`

- Rapporté : malgré **30-40 Md$** d'investissement en entreprise, **95 % des
  projets d'IA générative ne produisent aucun retour mesurable**
  `[RÉSUMÉ-OUTIL]`.
- **Méthode rapportée** : 150 entretiens de dirigeants, enquête auprès de 350
  employés, analyse de 300 déploiements publics — certaines sources mentionnant
  des granularités différentes (52 entretiens, 153 réponses)
  `[RÉSUMÉ-OUTIL]`.
- **Réserve des auteurs eux-mêmes**, rapportée : *les scores reflètent une
  fréquence déclarée plutôt qu'une mesure objective de l'impact des obstacles*
  `[RÉSUMÉ-OUTIL]`.
- Thèse centrale : l'obstacle principal est **l'apprentissage**, pas
  l'infrastructure, la régulation ou le talent — *« la plupart des systèmes GenAI
  ne conservent pas le retour, ne s'adaptent pas au contexte, ne s'améliorent pas
  avec le temps »* `[RÉSUMÉ-OUTIL]`.

**Statut : [COMMERCIAL / RAPPORT NON RELU PAR LES PAIRS].** Le chiffre de 95 %
est devenu un lieu commun médiatique (Forbes, Fortune/Yahoo, Virtualization
Review l'ont tous repris). L'incohérence des tailles d'échantillon selon les
reprises est en soi un signal : **le chiffre a été amplifié plus qu'il n'a été
vérifié.** ⚠️ **Aucune critique méthodologique académique n'a été trouvée** —
absence d'évaluation, pas validation.

**(b) Gartner, communiqué du 25 juin 2025** `[NON LU]`

- **Plus de 40 % des projets d'IA agentique seront annulés d'ici fin 2027**,
  pour coûts croissants, valeur métier floue ou contrôles de risque insuffisants.
  Base : sondage auprès de **plus de 3 400 organisations** investissant
  activement `[RÉSUMÉ-OUTIL]`.
- **« Agent washing »** : rebaptisage d'assistants, de RPA et de chatbots
  existants sans capacité agentique substantielle. **Gartner estime que ~130
  seulement des milliers de fournisseurs d'IA agentique sont réels**
  `[RÉSUMÉ-OUTIL]`.
- Prédiction inverse du même communiqué : **au moins 15 % des décisions de
  travail quotidiennes prises de façon autonome d'ici 2028**, contre 0 % en 2024
  `[RÉSUMÉ-OUTIL]`.

**Statut : [COMMERCIAL].** Gartner vend des prédictions. Le communiqué contient
simultanément un chiffre pessimiste et un chiffre optimiste — **c'est la
signature d'un produit d'analyste, pas d'une mesure**. La notion d'« agent
washing » est en revanche **descriptive et utile** : elle nomme un phénomène
observable.

**Ce qui est réellement solide dans cette section :** l'écart massif entre
expérimentation et déploiement à l'échelle. Les chiffres varient énormément selon
la source — **31 %** d'entreprises avec au moins un agent en production
(S&P Global / McKinsey) contre **51 %** (Ringly.io) ; McKinsey 2025 rapportant
**aucune fonction métier au-dessus de 10 % de mise à l'échelle** ; **~21 %**
seulement disposant d'un modèle mature de gouvernance des agents
`[RÉSUMÉ-OUTIL]`. **La dispersion elle-même est le résultat** : personne ne
mesure la même chose, et « en production » n'a pas de définition partagée.

### 6.3 Tarification : à l'usage vs au résultat

Les chiffres disponibles proviennent **massivement** de blogs d'éditeurs de
facturation (Flexprice, Monetizely, Pickaxe, Nevermined) — **acteurs dont le
produit est la facturation à l'usage**. Conflit d'intérêt structurel.

Rapporté `[RÉSUMÉ-OUTIL]` :

| Affirmation | Source | Statut |
|---|---|---|
| 43 % des acheteurs préfèrent la consommation, 27 % le résultat ; < 1/5 le per-user | Futurum, enquête 1S 2026 | **[COMMERCIAL]** — cabinet d'analystes, méthode non lue |
| Hybride (abonnement + dépassement à l'usage) = 41 % des éditeurs IA, contre 27 % en 2025 | blog éditeur | **[COMMERCIAL]** |
| Per-seat de 21 % → 15 % du SaaS en 12 mois | blog éditeur | **[COMMERCIAL]** |
| 73 % des éditeurs IA facturent séparément les fonctions IA | blog éditeur | **[COMMERCIAL]** |
| Marges brutes de 94 % en outcome-based vs parfois négatives en usage pur | blog éditeur | **[COMMERCIAL]** — invraisemblable en l'état, **à écarter** |

**Le seul élément non commercial trouvé** : Deloitte a publié un
*Technology Spotlight* sur la **comptabilisation** de la tarification au résultat
pour un produit agentique (4 juin 2026) `[NON LU]` `[2026 — NON VÉRIFIABLE ICI]`.
**Qu'un grand cabinet comptable publie sur la reconnaissance de revenu d'un
modèle est un signal d'existence bien plus crédible qu'une statistique
d'adoption** : on n'écrit pas de doctrine comptable pour un phénomène qui n'a
pas lieu.

> **Ce qui est réellement établi ici : rien de chiffré.** Ce qui est *plausible*
> et cohérent entre sources indépendantes : (1) le per-seat s'effrite pour les
> produits IA ; (2) l'hybride abonnement + usage est le mode dominant ; (3) la
> tarification au résultat existe, suscite un intérêt réel, et **transfère le
> risque d'exécution au fournisseur** — ce qui est la vraie question de
> conception, pas le pourcentage d'adoption.

**Question directe pour la V2** : facturer au résultat un diagnostic OSINT
suppose de **définir le résultat**. Or §4.3 vient d'établir qu'**aucune source ne
démontre le lien entre un signal détecté et une conversion commerciale**. **On ne
peut pas facturer un résultat qu'on ne sait pas mesurer.** C'est un blocage
logique, pas commercial.

### 6.4 Interopérabilité : MCP et A2A

**Adoption rapportée** `[RÉSUMÉ-OUTIL]` :
- **41 %** des organisations logicielles interrogées en production limitée ou
  large avec des serveurs MCP (rapport Stacklok 2026) — **[COMMERCIAL]**.
- **9 652** enregistrements de serveurs « latest » et **28 959**
  serveur/version dans le registre officiel MCP au 24 mai 2026
  `[2026 — NON VÉRIFIABLE ICI]`. Un décompte de registre est **plus vérifiable**
  qu'une enquête déclarative — c'est le chiffre le moins mauvais de cette
  section.
- Spécification **MCP 2026-07-28** avec fenêtre de dépréciation de 12 mois ;
  candidat de version incluant un **cœur de protocole sans état**, un cadre
  d'**extensions**, les **Tasks**, les **MCP Apps**, un durcissement de
  l'autorisation et une politique formelle de dépréciation
  `[NON LU] [2026 — NON VÉRIFIABLE ICI]`.

**Sécurité — le point qui doit peser dans la décision** `[RÉSUMÉ-OUTIL]` :
- La NSA a publié un document *Cybersecurity Information Sheet* sur MCP
  (media.defense.gov, juin 2026) `[NON LU] [2026 — NON VÉRIFIABLE ICI]`.
  **Qu'une agence de sécurité nationale publie sur un protocole est un indicateur
  de maturité *et* de préoccupation.**
- Rapporté : **30+ CVE** déposées en janvier-février 2026 ; **CVE-2025-6514**
  dans le paquet `mcp-remote` (injection de commande shell) affectant
  **437 000+** environnements de développeurs ; fuite inter-tenants chez Asana ;
  traversée de chemin chez Smithery exposant 3 243 applications
  `[2026 — NON VÉRIFIABLE ICI]`. ⚠️ **Chiffres non vérifiés. Ne pas citer.**
- Thèse rapportée : *le protocole a standardisé une surface d'attaque sans
  précédent en privilégiant la commodité du développeur et une exécution non
  opinionée* `[RÉSUMÉ-OUTIL]`.

**A2A (Google)** : la composition entre MCP et les protocoles agent-à-agent est
décrite comme **une question ouverte** suivie par l'écosystème
`[RÉSUMÉ-OUTIL]`. Je n'ai rien trouvé de substantiel. **Ne pas parier dessus.**

> **Statut : [ÉTABLI]** que MCP est le point de convergence de fait pour
> l'intégration d'outils. **[ÉTABLI]** que sa surface de sécurité est une
> préoccupation active et documentée. **[NON ÉTABLI]** que l'interopérabilité
> multi-fournisseurs fonctionne réellement en production à l'échelle.

### 6.5 Agents comme produit vs agents comme fonctionnalité

Je n'ai trouvé **aucune donnée** permettant de trancher. Le débat existe dans la
littérature d'investisseurs (Bessemer, Menlo, Euclid Ventures, Foundation
Capital, tous `[NON LU]` `[COMMERCIAL]`), avec une thèse récurrente : **les
agents verticaux ne concurrencent pas des budgets IT mais des budgets de
main-d'œuvre** `[RÉSUMÉ-OUTIL]`.

**Statut : [COMMERCIAL] intégral.** C'est une thèse d'allocation de capital, pas
un résultat. Elle est **utile comme cadrage** — elle dit où chercher le
consentement à payer — et **sans valeur comme preuve**.

---

## 7. Ce que la recherche ne dit PAS

**Section la plus importante du document.** Chaque point ci-dessous est une
question que la refonte devra trancher **sans appui scientifique**. Les trancher
est légitime ; prétendre qu'elles sont tranchées par la littérature ne l'est pas.

### 7.1 Elle ne dit pas qu'un signal faible observable publiquement prédit un achat

**C'est le trou central, et il est inchangé depuis l'ADR 0004.** La littérature
sur les signaux faibles reconnaît elle-même manquer d'assise empirique (§4.2). La
littérature sur le B2B intent data est **entièrement commanditée par les
fournisseurs** (§4.3), et la recherche documentaire de cette session a **échoué à
trouver la moindre évaluation académique indépendante**.

> Formulation à reprendre telle quelle : **aucune source ne franchit le dernier
> pas entre « signal ouvert observé » et « cette PME va acheter du conseil en
> branding ». Cette hypothèse appartient à la consultante, pas à la recherche.**
> Une année de littérature supplémentaire n'y a rien changé.

**Corollaire dur** : toute tarification au résultat, toute promesse de taux de
conversion, tout classement par « quadrant » présenté comme prédictif, repose sur
**une hypothèse métier non validée**. Le seul remède est **la mesure interne**
(groupe témoin apparié, `motif_rejet`, états `rdv`/`client`) — pas une citation.

### 7.2 Elle ne dit pas que le multi-agents bat le mono-agent

À budget de calcul égal, plusieurs évaluations indépendantes disent **le
contraire** (§1.5). Les justifications valides du multi-agents sont
opérationnelles (parallélisme, isolation, permissions, contextes séparés), pas
cognitives. **Choisir une architecture multi-agents « parce que c'est plus
intelligent » n'a pas d'appui. Le choisir pour isoler des permissions en a un.**

### 7.3 Elle ne quantifie pas l'écart planificateur LLM vs orchestration déterministe

Le **mécanisme** de la dégradation est établi (§1.6, §2.5). **L'ampleur** ne
l'est pas : je n'ai lu **aucun** chiffre lisible d'écart de taux d'échec entre
les deux stratégies de contrôle. Une étude au protocole exactement adapté existe
(COBOL→Python, toutes variables tenues constantes sauf la stratégie de contrôle)
et **je n'ai pas pu en lire le résultat**. **À lire dès qu'un accès réseau est
disponible — c'est la lecture la plus rentable de toute cette liste.**

### 7.4 Elle ne dit pas quelle architecture de mémoire choisir

Le vocabulaire est stabilisé (épisodique / sémantique / procédurale / travail),
les implémentations de référence existent (Generative Agents, MemGPT), les
benchmarks se multiplient — **et aucune comparaison croisée ne fait autorité**
(§1.7). Le seul repère utile est qualitatif : le domaine détermine la mémoire
dominante.

### 7.5 Elle ne dit pas comment évaluer un système agentique en production

Les benchmarks mesurent des capacités sur des tâches figées, et sont contaminés
(§3.1). `pass^k` mesure la consistance mais suppose des tâches rejouables — **or
un diagnostic OSINT n'est pas rejouable : le web a changé entre deux
exécutions.** Je n'ai trouvé **aucune méthodologie établie** pour évaluer un
agent dont l'environnement dérive entre les exécutions. C'est un problème
ouvert, et il est **au cœur** de ce que la V2 doit faire.

### 7.6 Elle ne dit pas où placer le seuil d'un juge LLM

MAST montre qu'un juge LLM atteint 94 % / κ = 0,77 **sur une classification en
taxonomie fermée calibrée sur 1 642 traces expertes** (§3.3). Elle ne dit pas :
- quel κ est « suffisant » pour une décision donnée ;
- combien de traces annotées il faut pour calibrer ;
- ce que devient la fiabilité quand le juge évalue une qualité ouverte plutôt
  qu'une classe fermée. **Les biais documentés suggèrent : mal.**

### 7.7 Elle ne dit pas qu'une porte humaine reste efficace dans la durée

Le biais d'automatisation et la complaisance sont établis (§3.5). **Leur ampleur
dans ce cas d'usage précis ne l'est pas.** Une porte humaine qui approuve
massivement n'est plus un contrôle — et **rien dans la littérature ne dit à
partir de quel taux d'approbation elle cesse d'en être un.** À mesurer, pas à
supposer.

### 7.8 Elle ne dit pas comment défendre un agent contre l'injection indirecte

Les attaques dépassent 60-90 % de succès sur les benchmarks publics (§2.4).
**Aucune défense générale n'est démontrée.** Le seul consensus est architectural :
séparer ce qui lit du contenu non fiable de ce qui peut agir. **Ce n'est pas une
mitigation, c'est un renoncement organisé — et c'est aujourd'hui l'état de
l'art.**

### 7.9 Elle ne valide aucun chiffre de marché ni de tarification

§6.1 et §6.3 sont intégralement `[COMMERCIAL]`. Le TAM de 4,6 T$, les 95 %
d'échec, les 40 % d'annulation, les 94 % de marge brute : **aucun n'a de statut
probant.** Ils décrivent un climat, pas une réalité mesurée. Les utiliser dans un
document interne de cadrage est acceptable **s'ils sont marqués**. Les utiliser
face à un client ne l'est pas.

### 7.10 Elle ne dit pas si l'agnosticité multi-verticale se paie

L'ambition de la V2 est un socle agnostique dont le marketing est la première
verticale. **Je n'ai trouvé aucune étude comparant le coût et la performance d'un
socle générique + configuration par verticale, contre des systèmes verticaux
dédiés.** La thèse investisseur (§6.5) pousse à la verticalisation ; la thèse
ingénierie (ADR 0003 du projet) pousse à la configuration. **Aucune des deux
n'est appuyée par une mesure.** C'est un pari, et il doit être nommé comme tel.

### 7.11 Elle ne dit rien sur ce projet en particulier

Aucune des sources ne porte sur : des PME de 5 à 50 salariés, un marché
québécois ou romand, un diagnostic de marque, un volume de quelques dizaines de
prospects par mois. **Toutes les extrapolations d'échelle sont des paris.** À ce
volume, un dispositif statistique n'atteindra jamais la puissance nécessaire pour
départager des variantes — ce qui est déjà noté dans l'ADR 0004 et reste vrai.

---

## 8. Implications pour la refonte

Dix recommandations. Chacune porte sa traçabilité, et **celles qui ne reposent
que sur du jugement le disent**.

---

### R1 — Garder l'orchestration déterministe comme colonne vertébrale ; n'introduire de l'autonomie LLM que par exception explicite et bornée

**Fondement** : §1.6 (le couplage planification/exécution dégrade
reproductibilité et prévisibilité du coût — mécanisme **[ÉTABLI]**), §2.5
(non-déterminisme d'inférence **[ÉTABLI]**), §2.2 (compoundage d'erreurs sur
horizon long **[ÉTABLI]** arithmétiquement), §1.1 (recommandation Anthropic de
simplicité — **[PRATIQUE]**).

**Ce que ça donne** : le graphe reste une **donnée** ; l'agentivité LLM est
déclarée nœud par nœud, avec un budget de tokens, un plafond d'itérations et un
critère d'arrêt vérifiable. Un nœud sans ces trois bornes n'est pas déployable.

**Réserve honnête** : l'**ampleur** de l'avantage n'est pas mesurée (§7.3). Cette
recommandation est fondée sur un mécanisme établi, pas sur un écart chiffré.

---

### R2 — Ne jamais déployer un agent vérificateur sans signal externe exécutable

**Fondement** : §1.4 (Huang et al., ICLR 2024, **[ÉTABLI]**), §2.1 (MAST : les
vérificateurs existants sont superficiels ; corriger exige des changements
architecturaux et des **contrôles symboliques**, pas des prompts — **[ÉTABLI]**),
§1.3 (dégénérescence de la pensée sur Reflexion).

**Ce que ça donne** : `agent-revue` **ré-exécute** — c'est déjà l'invariant du
projet et la recherche le valide. La V2 doit l'inscrire dans le socle : **tout
verdict de qualité doit être reproductible par une commande.** Un verdict qui ne
peut pas être re-produit par une commande est une opinion.

**C'est la recommandation la mieux fondée du document.**

---

### R3 — Passer la porte de cohérence de `pass^1` à un régime à deux vitesses

**Fondement** : §3.2 (`pass^k`, τ-bench — **[ÉTABLI]** comme méthode), §2.5
(température 0 ≠ déterminisme — **[ÉTABLI]**), §7.5 (aucune méthodologie établie
pour un environnement dérivant — **[NON ÉTABLI]**).

**Ce que ça donne** :

| Type d'assertion | Régime | Seuil |
|---|---|---|
| **Déterministe** (tests, marche AST, `git diff` vide, conformité de contrat, invariants de bus) | **une exécution suffit** — par construction | **100 %, zéro échec dur** |
| **Non déterministe** (toute assertion touchant une sortie LLM) | **`pass^k` avec k ≥ 3 déclaré**, contre des entrées gelées et rejouables | seuil **distinct et déclaré**, jamais mêlé au précédent |

**Ce que ça préserve** : le taux à 97 % reste défendable **précisément parce que
l'essentiel de ses assertions sont déterministes**. C'est une force du dispositif
actuel, rare, et il faut la nommer. **Ce qu'il faut cesser** : agréger dans un
seul pourcentage des assertions dont l'une est reproductible et l'autre non. Ce
mélange fait passer un `pass^1` pour une garantie.

**Jugement, non fondé sur la littérature** : la valeur `k ≥ 3` est arbitraire.
Aucune source ne dit quel `k` choisir. **À calibrer, comme les seuils YAML de
l'ADR 0004 — un `[À CALIBRER]`, pas une mesure.**

---

### R4 — Traiter le grand livre de coût comme une métrique d'évaluation de premier rang, pas comme de la comptabilité

**Fondement** : §2.6 (Kapoor et al., « AI Agents That Matter » — **[ÉTABLI]** :
l'exactitude sans coût produit des agents inutilement complexes), §1.5 (~15×
tokens en multi-agents — **[RÉSUMÉ-OUTIL]**).

**Ce que ça donne** : **aucun chiffre d'exactitude n'est publiable sans le coût
qui l'a produit.** L'infrastructure existe déjà (`api_usage.log`, `LedgerEntry`,
7 champs GreenIT). La V2 doit rendre le couple **(qualité, coût)** obligatoire à
la sortie de chaque évaluation. Un rapport d'évaluation sans coût est incomplet
et doit être refusé par le garde-fou.

---

### R5 — Confiner le LLM hors de tout chemin de fetch et de toute écriture — et le documenter comme un contrôle de sécurité

**Fondement** : §2.4 (injection indirecte, > 60 % de succès sur InjecAgent /
Agent Security Bench, > 90 % sur PoisonedRAG — **[ÉTABLI]** que le problème est
sévère ; **[NON ÉTABLI]** qu'une défense générale existe), position OWASP
(isolation des entrées non fiables, **blocages d'egress déterministes**).

**Ce que ça donne** : les invariants V1 « le LLM ne fetch jamais », « `api_io.py`
est le seul module au contact du réseau », « `vault_io.py` est le seul à écrire »
**sont des contrôles de sécurité** et doivent être reclassés comme tels dans la
documentation V2 — pas comme des préférences de style. La marche AST qui les
vérifie devient un **contrôle de sécurité automatisé**, avec le statut qui va
avec.

**Risque de la refonte, à nommer** : une plateforme agentique « moderne » avec
MCP donne par défaut aux agents des outils qui **fetchent et écrivent**. **C'est
exactement la régression contre laquelle §2.4 met en garde.** Adopter MCP sans
reconstituer cette séparation, c'est perdre le contrôle sans s'en apercevoir.

---

### R6 — Placer le contrôle robots.txt / opt-out dans le bus I/O, une seule fois

**Fondement** : §5.3 (robots.txt sans force contraignante autonome
— **[ÉTABLI]** ; mais véhicule de fait de l'opt-out TDM art. 4 de la directive
(UE) 2019/790, et **signal de bonne foi** retenu par tribunaux et régulateurs
— **[ÉTABLI]** tel que rapporté), dette identifiée dans `CLAUDE.md` sur
l'escalade « page carrières ».

**Ce que ça donne** : un contrôle **unique**, au niveau du bus, appliqué à tout
fetch sans exception, avec journalisation de la décision (autorisé / refusé /
robots.txt injoignable). Le placer par collecteur garantit qu'un collecteur
futur l'oubliera — c'est déjà arrivé une fois.

**Réserve** : ceci n'est **pas un avis juridique**. La pré-condition de
validation juridique posée pour J6 reste entière.

---

### R7 — Rendre l'observation capturable et horodatée, pas seulement le signal dérivé

**Fondement** : §5.2 (absence de standard de chaîne de preuve OSINT évalué —
**[NON ÉTABLI]** ; recommandations professionnelles de traçabilité —
**[PRATIQUE]**), §1.7 (mémoire épisodique horodatée adaptée aux domaines à
incertitude), ADR 0004 (l'événement daté, pas le score).

**Ce que ça donne** : exploiter enfin `append_historique()` — et capturer
**l'observation brute horodatée** (extrait, URL, date de fetch, empreinte), pas
seulement la conclusion. Sans cela, un diagnostic contesté trois mois plus tard
est **indéfendable** : la page a changé.

**Bénéfice second, décisif** : c'est aussi ce qui rend possible une évaluation
`pass^k` (R3) **contre des entrées gelées**, seule façon de contourner la dérive
d'environnement pointée en §7.5.

---

### R8 — Mesurer avant de prétendre : instrumenter le dénominateur commercial dès la V2, pas après

**Fondement** : §4.2 (la théorie des signaux faibles reconnaît son propre manque
d'assise empirique — **[NON ÉTABLI]**), §4.3 (aucune évaluation académique
indépendante du B2B intent data ; la méthode du **lift incrémental contre groupe
témoin apparié** est en revanche **[ÉTABLI]**), §3.5 (le biais d'automatisation
impose de mesurer la porte humaine elle-même — **[ÉTABLI]**).

**Ce que ça donne** : le **Lot 0** de l'ADR 0004 (`motif_rejet`, états
`rdv`/`client`) n'est pas une amélioration différable. **C'est la seule chose qui
transformera l'hypothèse commerciale en connaissance.** Il doit être dans le
socle V2 dès le premier jour, avec :
- un **taux d'approbation de la porte humaine** exposé et surveillé (si l'humain
  approuve > 95 %, la porte est décorative — §7.7) ;
- un **groupe témoin** dès qu'un volume le permet.

**Réserve honnête** : à quelques dizaines de prospects/mois, la puissance
statistique sera insuffisante pour départager des variantes fines. **Instrumenter
n'est pas mesurer.** Mais sans instrumentation, on ne mesurera jamais.

---

### R9 — Adopter MCP comme frontière d'intégration, avec un périmètre de confiance explicite

**Fondement** : §6.4 (MCP comme point de convergence de fait — **[ÉTABLI]** ;
registre officiel comme signal quantitatif le moins mauvais ; surface de sécurité
documentée, publication NSA — **[ÉTABLI]** que c'est une préoccupation active),
§7.8 (aucune défense générale contre l'injection indirecte).

**Ce que ça donne** : MCP pour **exposer** les capacités du socle et pour
**consommer** des outils, **mais** avec une classification de confiance explicite
par serveur (interne / vérifié / non fiable) et **un serveur non fiable ne peut
jamais alimenter un chemin d'écriture**. A2A reste hors périmètre : rien de
substantiel trouvé (§6.4).

**Jugement partiel** : la classification de confiance en trois niveaux est ma
proposition, **elle ne vient d'aucune source**. C'est un choix de conception à
débattre.

---

### R10 — Ne pas facturer au résultat tant que le résultat n'est pas mesurable

**Fondement** : §7.1 (aucune source ne relie signal observé et achat), §6.3
(tarification au résultat : intérêt réel, chiffres d'adoption intégralement
**[COMMERCIAL]**, publication comptable Deloitte comme signal d'existence),
§4.3 (méthode du lift établie, mesure non faite).

**Ce que ça donne** : positionner la V2 sur un modèle **hybride** (abonnement +
usage métré, ce que le grand livre sait déjà faire), et n'ouvrir la tarification
au résultat **qu'après** que R8 ait produit une mesure de lift. **On ne peut pas
facturer un résultat qu'on ne sait pas mesurer** — et facturer un résultat non
mesuré, c'est transférer au client un risque qu'on ne sait pas évaluer soi-même.

**Réserve** : c'est un raisonnement logique, **pas** un résultat de recherche. La
littérature ne dit rien sur la tarification des diagnostics OSINT.

---

### Ce que ces dix recommandations ne couvrent pas

- **Le choix de topologie multi-agents** (superviseur / blackboard / marché) :
  §1.2 fournit un vocabulaire, **aucune comparaison contrôlée n'existe**. À
  trancher par jugement d'ingénierie, en le disant.
- **L'architecture de mémoire** : §7.4. Idem.
- **Le pari de l'agnosticité multi-verticale** : §7.10. Aucun appui. À nommer
  comme pari dans l'ADR de refonte, pas à justifier par la littérature.

---

## Annexe A — Table des références et statut de lecture

**Rappel : la colonne « Texte lu » vaut NON pour 100 % des lignes.** La colonne
« ID vu en recherche » indique si l'identifiant/URL est apparu littéralement dans
les résultats `WebSearch` de cette session (OUI) ou provient de ma mémoire
pré-entraînée (NON, à revérifier).

| # | Référence | Année | Texte lu | ID vu en recherche | Statut |
|---|---|---|---|---|---|
| 1 | Cemri, Pan, Yang et al., *Why Do Multi-Agent LLM Systems Fail?* (MAST), arXiv 2503.13657 | 2025 | **NON** | OUI | [ÉTABLI] |
| 2 | Kapoor, Stroebl, Siegel, Nadgir, Narayanan, *AI Agents That Matter*, arXiv 2407.01502 | 2024 | **NON** | OUI | [ÉTABLI] |
| 3 | Yao et al., *τ-bench*, arXiv 2406.12045 | 2024 | **NON** | OUI | [ÉTABLI] |
| 4 | Huang et al., *LLMs Cannot Self-Correct Reasoning Yet*, arXiv 2310.01798, ICLR 2024 | 2023/24 | **NON** | OUI | [ÉTABLI] |
| 5 | Smit et al., *Should we be going MAD?*, ICML 2024 | 2024 | **NON** | OUI (DOI ACM) | [ÉTABLI] |
| 6 | Wang et al., *Rethinking the Bounds of LLM Reasoning*, arXiv 2402.18272 | 2024 | **NON** | OUI | [ÉTABLI] |
| 7 | Zhou et al., *Least-to-Most Prompting*, arXiv 2205.10625, ICLR 2023 | 2022/23 | **NON** | OUI | [ÉTABLI] |
| 8 | METR (Kwa et al.), *Measuring AI Ability to Complete Long (Software) Tasks*, arXiv 2503.14499 | 2025 | **NON** | OUI | [ÉTABLI] |
| 9 | Liu et al., *Lost in the Middle*, TACL | 2024 | **NON** | NON (arXiv 2307.03172 de mémoire) | [ÉTABLI] |
| 10 | Thinking Machines Lab, *Defeating Nondeterminism in LLM Inference* (billet) | 2025 | **NON** | OUI (URL) | [ÉTABLI] |
| 11 | *Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge*, arXiv 2410.02736 | 2024 | **NON** | OUI | [ÉTABLI] |
| 12 | *Self-Preference Bias in LLM-as-a-Judge*, arXiv 2410.21819 | 2024 | **NON** | OUI | [ÉTABLI] |
| 13 | Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*, NeurIPS D&B | 2023 | **NON** | NON (de mémoire) | [ÉTABLI] |
| 14 | Anthropic, *Building Effective Agents* (déc. 2024) | 2024 | **NON** (403) | OUI (URL) | [PRATIQUE] |
| 15 | Anthropic, *How we built our multi-agent research system* | 2025 | **NON** (403) | OUI (repris) | [PRATIQUE] |
| 16 | Park et al., *Generative Agents*, UIST | 2023 | **NON** | NON (de mémoire) | [ÉTABLI] |
| 17 | Packer et al., *MemGPT* | 2023 | **NON** | NON (de mémoire) | [ÉTABLI] |
| 18 | Yao et al., *ReAct*, ICLR | 2023 | **NON** | NON (de mémoire) | [ÉTABLI] |
| 19 | Shinn et al., *Reflexion*, NeurIPS | 2023 | **NON** | NON (de mémoire) | [ÉTABLI] |
| 20 | *LLM-Based Multi-Agent Orchestration: A Survey…*, Future Internet 18(6):326 | 2026 | **NON** | OUI (DOI) | [2026 — NON VÉRIFIABLE ICI] |
| 21 | Jimenez et al., *SWE-bench*, ICLR | 2024 | **NON** | NON (de mémoire) | [ÉTABLI] |
| 22 | Mialon et al., *GAIA* | 2023 | **NON** | NON (de mémoire) | [ÉTABLI] |
| 23 | Zhou et al., *WebArena* | 2023 | **NON** | NON (de mémoire) | [ÉTABLI] |
| 24 | *CORE-Bench*, arXiv 2409.11363 | 2024 | **NON** | OUI | [ÉTABLI] |
| 25 | *AgentDojo*, *InjecAgent*, *Agent Security Bench*, *PoisonedRAG* | 2024-25 | **NON** | Noms OUI, ID NON | [ÉTABLI] (problème), [NON ÉTABLI] (défense) |
| 26 | OWASP, *AI Agent Security Cheat Sheet* + LLM Top 10 2025 | 2025 | **NON** | OUI (URL) | [PRATIQUE] |
| 27 | Es et al., *RAGAS*, EACL demo | 2024 | **NON** | NON (de mémoire) | [PRATIQUE] |
| 28 | Min et al., *FActScore*, EMNLP | 2023 | **NON** | NON (de mémoire) | [ÉTABLI] |
| 29 | Rashkin et al., *AIS / Measuring Attribution in NLG*, Comput. Linguistics | 2023 | **NON** | **NON — non apparu du tout** | ⚠️ **à vérifier avant citation** |
| 30 | Ansoff, *Managing Strategic Surprise by Response to Weak Signals*, CMR | 1975 | **NON** | Nom OUI, réf. NON | [ÉTABLI] (existence), [NON ÉTABLI] (validité prédictive) |
| 31 | Holopainen & Toivonen, *Weak signals: Ansoff today*, Futures | 2012 | **NON** | OUI (ScienceDirect) | idem |
| 32 | Hiltunen, *The future sign and its three dimensions*, Futures | 2008 | **NON** | NON (de mémoire) | idem |
| 33 | Rossel, *Early detection, warnings, weak signals…*, Futures | 2012 | **NON** | NON (de mémoire) | idem |
| 34 | Mendonça, Cardoso, Caraça, *The strategic strength of weak signal analysis*, Futures | 2012 | **NON** | NON (de mémoire) | idem |
| 35 | Parasuraman & Riley, *Humans and Automation*, Human Factors 39(2) | 1997 | **NON** | Nom OUI | [ÉTABLI] |
| 36 | Parasuraman & Manzey, *Complacency and Bias in Human Use of Automation*, Human Factors 52(3) | 2010 | **NON** | OUI (SAGE) | [ÉTABLI] |
| 37 | *Automation Bias in the AI Act*, arXiv 2502.10036 | 2025 | **NON** | OUI | [PRATIQUE] |
| 38 | NATO AJP-2.1 / code Admiralty | — | **NON** | OUI (via ResearchGate/blogs) | [ÉTABLI] (norme), [NON ÉTABLI] (efficacité) |
| 39 | *Van Buren v. United States*, Cour suprême US | 2021 | **NON** | OUI (via cabinets) | [ÉTABLI] tel que rapporté |
| 40 | *hiQ Labs v. LinkedIn*, 9e circuit + jugement d'accord | 2022 | **NON** | OUI (via cabinets) | idem |
| 41 | Directive (UE) 2019/790, art. 3-4 (TDM) | 2019 | **NON** | OUI (via Kluwer/Oxford/Reed Smith) | idem |
| 42 | MIT NANDA, *The GenAI Divide: State of AI in Business 2025* | 2025 | **NON** | OUI (PDF) | [COMMERCIAL] |
| 43 | Gartner, communiqué du 25 juin 2025 (40 % annulés, agent washing) | 2025 | **NON** | OUI (URL) | [COMMERCIAL] |
| 44 | Foundation Capital, *A System of Agents brings service as software to life* | — | **NON** | OUI (URL) | [COMMERCIAL] |
| 45 | Futurum, enquête 1S 2026 sur la tarification | 2026 | **NON** | OUI (communiqué) | [COMMERCIAL] |
| 46 | Deloitte, *Technology Spotlight — Accounting for Outcome-Based Pricing…* (4 juin 2026) | 2026 | **NON** | OUI (URL) | [2026 — NON VÉRIFIABLE ICI] |
| 47 | NSA, *CSI — Model Context Protocol Security* | 2026 | **NON** | OUI (defense.gov) | [2026 — NON VÉRIFIABLE ICI] |
| 48 | Spécification MCP 2026-07-28 (billet de version candidate) | 2026 | **NON** | OUI (blog officiel) | [2026 — NON VÉRIFIABLE ICI] |

---

## Annexe B — Les trois lectures prioritaires dès qu'un accès réseau existe

Par rentabilité décroissante pour la refonte :

1. **L'étude contrôlée orchestration déterministe vs pilotée par LLM**
   (COBOL→Python, arXiv 2605.09894 tel que renvoyé) — c'est **la seule source
   trouvée dont le protocole isole exactement la variable qui nous intéresse**, et
   c'est le trou nommé en §7.3.
2. **MAST, arXiv 2503.13657** — pour la taxonomie complète des 14 modes d'échec,
   et surtout pour **ce que les interventions ont et n'ont pas corrigé**.
3. **« AI Agents That Matter », arXiv 2407.01502** — pour la méthodologie
   d'évaluation à coût contrôlé, directement réutilisable par la porte de revue.

**Puis** : Huang et al. 2310.01798 (auto-correction) et le billet Thinking
Machines sur le non-déterminisme — les deux résultats qui contraignent le plus
directement la conception de la porte de revue.

---

## Annexe C — Auto-critique de cette note

Ce que le prochain relecteur doit savoir avant de s'appuyer dessus :

1. **Zéro texte intégral lu.** Toutes les affirmations transitent par des résumés
   automatiques. Le niveau de preuve réel de ce document est **inférieur** à
   celui de l'ADR 0004, qui disposait au moins de résumés d'auteurs.
2. **Aucun chiffre de ce document n'est engageant.** Tous les chiffres portent
   `[RÉSUMÉ-OUTIL]` ou sont marqués [COMMERCIAL]. Aucun ne doit sortir dans un
   document client, un devis ou une promesse.
3. **Biais de sélection non contrôlé.** Requêtes ciblées, pas de protocole de
   revue systématique. J'ai activement cherché les résultats négatifs (« negative
   results », « does not outperform », « critique », « flawed ») pour compenser,
   mais je n'ai pas de mesure de ce que j'ai manqué.
4. **Neuf références proviennent de ma seule mémoire** (colonne « ID vu en
   recherche » = NON dans l'annexe A). Elles sont plausibles et je les crois
   exactes, **mais la ligne 29 (AIS / Rashkin et al.) n'est apparue nulle part
   dans les recherches** — c'est la plus fragile du lot et elle est signalée
   comme telle.
5. **Les sources 2026 sont hors de ma coupure de connaissances (mai 2026).** Je
   ne peux attester que du fait qu'un moteur de recherche a renvoyé ces titres à
   ces URL. Rien d'autre.
6. **La section 4 est celle où la littérature est la plus faible**, et c'est
   celle qui fonde le produit. Ce n'est pas confortable. C'est le fait.
