# Stratégie SaaS — volet économique et stratégique de la refonte v2

> **Statut : note de cadrage stratégique. Aucune décision d'architecture n'est
> prise ici** (voir `docs/adr/` pour les décisions engagées) **et aucune donnée
> de `docs/strategie/` n'est modifiée** — ce document la lit, ne l'écrit pas.
> Rédigé le **2026-08-04**, en réponse au mandat : « concevoir une solution
> technique alignée avec un modèle économique solide, vendeur par nature, à
> forte valeur ajoutée » et « tous les artefacts d'une start-up monopolistique
> à succès ».
>
> Ce document lit intégralement `docs/v2/FOURNISSEURS-DONNEES.md`,
> `docs/v2/RECHERCHE-agentique.md`, `docs/v2/HERITAGE-v1-invariants-a-
> challenger.md`, `docs/adr/0001` à `0005` et `CLAUDE.md`. Il ne relit pas le
> code — il s'appuie sur les faits déjà vérifiés dans ces documents, référencés
> par section (ex. « FOURNISSEURS §5.2 »).

---

## 0. Méthode et convention de marquage — à lire avant tout le reste

Ce document mélange trois registres qui ne doivent **jamais** se confondre.
La confusion des trois est exactement l'erreur que ce projet a déjà nommée
ailleurs (« aucun chiffre non mesuré présenté comme mesuré », invariant I19,
`HERITAGE §I19`) et qu'il applique ici au domaine économique.

| Marque | Signification |
|---|---|
| **[VÉRIFIÉ]** | Constaté dans le dépôt à la date de rédaction (commande exécutée, fichier lu, ligne citée) |
| **[PLANIFIÉ]** | Décidé dans une ADR ou un document du projet, non encore construit |
| **[ESTIMATION MODÉLISÉE]** | Calcul explicite à partir d'hypothèses déclarées — la formule est vraie, les nombres qui l'alimentent sont des paramètres, pas des mesures |
| **[ESTIMATION NON SOURCÉE]** | Un ordre de grandeur est avancé sans qu'aucune source, même secondaire, ne le fonde dans cette session — le pire des registres, à minimiser |
| **[NON VÉRIFIÉ, hérité de FOURNISSEURS/RECHERCHE]** | Chiffre provenant des deux notes de recherche, elles-mêmes déjà bâties sur des résumés de résultats de recherche (`WebFetch` bloqué en HTTP 403 sur toute URL, `WebSearch` seul disponible) — jamais une source de première main |
| **[COMMERCIAL]** | Émane d'un acteur dont le chiffre sert un intérêt (éditeur, cabinet d'analystes, fonds) — peut être vrai, n'est jamais une preuve |
| **[JUGEMENT]** | Avis de conception, assumé comme tel, sans prétention de preuve |
| **[MÉMOIRE, non revérifié en session]** | Connaissance générale de rédaction (ex. l'existence de catégories d'outils SEO/local grand public), non vérifiée par un accès web dans cette session — l'egress est bloqué pour cet agent comme il l'était pour les deux notes précédentes |

**Contrainte physique de cette session, comme pour les deux notes lues** :
aucun accès web sortant. Aucune page de tarification, aucune étude de marché,
aucun site concurrent n'a pu être consulté pour produire ce document. Tout
TAM/SAM/SOM chiffré serait une invention — la section C le traite frontalement
plutôt que de le contourner.

---

## 1. État réel constaté — ce sur quoi cette stratégie doit s'appuyer

- **[VÉRIFIÉ]** `git log --oneline -10` : le dernier commit de contenu produit
  est `2ed1ef2` (ADR 0005, Lot A, « l'audit devient le produit »), suivi de
  trois notes `docs/v2/` non codées. Aucun commit v2 de code n'existe.
- **[VÉRIFIÉ]** `python -m pytest tests/ --collect-only -q` → **669 tests
  collectés**. `python -m pytest tests/ -q` → **668 passent, 1 échoue**
  (`test_doc_coherence.py::test_nombre_de_controles_preflight_documente`) —
  une dérive documentaire mineure entre `CLAUDE.md` et le nombre réel de
  contrôles préflight, sans rapport avec ce document, à signaler à
  `agent-documentation`.
- **[VÉRIFIÉ]** `python run_preflight.py` → **VERDICT : NO-GO**. Aucune clé
  API, `knowledge/api_pricing.yaml` à 0 partout avec `releve_le: null`, vault
  non initialisé. **Aucun run réel n'a jamais eu lieu.**
- **[VÉRIFIÉ]** (`HERITAGE §Pourquoi ce document existe`) : « La v1 est un
  système de 5 408 lignes qui n'a jamais vu une entreprise réelle : 669 tests,
  tous contre un faux serveur HTTP local ; vault vide ; zéro clé API. »
  **Ce fait domine toute la section F.**
- **[VÉRIFIÉ]** (ADR 0005) : le livrable a changé le 2026-08-03. Ce n'est
  **plus** un score comparatif entre prospects — un score renormalisé sur une
  couverture partielle n'est structurellement pas ordonnable
  (`ADR 0005 §Décision`). Le livrable est un **dossier d'audit** :
  écarts priorisés par gravité déclarée, points forts, dimensions non
  observées transformées en **questions d'entretien**. C'est le socle de la
  proposition de valeur (section A).
- **[VÉRIFIÉ]** (ADR 0003) : le moteur est multi-industrie *par mécanisme*
  (`secteur_id` comme clé de configuration), mais **une seule rubrique existe**
  (`rubric_persona1.yaml`, HVAC). L'extensibilité est une capacité du code,
  pas un fait démontré sur un deuxième cas (`HERITAGE` point 2 : « généricité
  sans deuxième cas d'usage = généricité non prouvée »).
- **[VÉRIFIÉ]** (FOURNISSEURS §3.2, §5.2) : le fournisseur de contacts actuel,
  Apollo, porte des clauses rapportées de source secondaire —
  « solely for internal business purposes », interdiction de sous-licencier,
  vendre, distribuer ou intégrer l'API à son propre produit
  **[NON VÉRIFIÉ, hérité de FOURNISSEURS]**. Contrat non lu (`apollo.io/terms/api`,
  HTTP 403). **Si confirmées, ces clauses interdisent le modèle SaaS lui-même**
  tel que construit aujourd'hui (un tiers qui enrichit des contacts pour le
  compte de ses clients fait exactement les deux choses interdites). Ceci
  n'est **pas** un risque de conformité ordinaire : c'est une contrainte sur
  la forme même du produit, traitée en détail en section D et F.
- **[VÉRIFIÉ]** J6 (outreach) reste `enabled: false`, doublement verrouillé,
  conditionné à une validation juridique jamais faite (CASL/nLPD/RGPD/AI Act).
  Ce document **n'assume pas** que J6 existe ; le modèle économique décrit
  plus bas fonctionne sans lui (le produit vendu est le dossier d'audit, pas
  l'envoi de courriels).

---

## A. Proposition de valeur et wedge

### A.1 Le problème, précisément, pour qui, pourquoi maintenant

**Le problème.** Une consultante marketing/branding indépendante (et, par
généralisation, une petite agence ou un cabinet conseil) passe un temps
disproportionné à **qualifier** un prospect avant de pouvoir lui vendre quoi
que ce soit : visiter son site, chercher sa fiche Google, évaluer sa présence
sociale, deviner ce qui cloche, préparer un angle d'entretien. C'est un travail
de collecte et de mise en forme, pas un travail de jugement — et c'est
exactement le travail qu'un pipeline déterministe peut industrialiser sans
prétendre remplacer le jugement.

**Pour qui, précisément (wedge, pas plateforme).** [VÉRIFIÉ] Le pilote cible
aujourd'hui un seul persona réel avec du contenu métier rédigé : **persona 1,
installateur/détaillant HVAC**, séquence **Québec → Suisse romande → France**.
Ce n'est pas une limite à déplorer, c'est la définition du wedge : un secteur
de PME de services locaux, à faible maturité marketing numérique, où un audit
express crédible a de la valeur parce que **personne dans ce segment n'a de
CMO**.

**Pourquoi maintenant [JUGEMENT, appuyé par RECHERCHE §6.1 marqué COMMERCIAL].**
La thèse « service-as-software » (Foundation Capital, citée en
`RECHERCHE §6.1`, **[COMMERCIAL]**, à ne jamais citer comme un fait de marché)
n'est pas une preuve, mais son raisonnement structurel est solide indépendamment
de la source : un produit qui livre un **résultat fini** (un dossier
utilisable, pas un outil à opérer) se positionne contre un budget de
main-d'œuvre, pas contre un budget logiciel — et le budget de main-d'œuvre
d'une petite agence ou d'une consultante solo est, par construction,
entièrement contraint par ses heures facturables. C'est un argument de
positionnement, pas un chiffre de marché.

### A.2 Ce que le produit livre aujourd'hui, exactement

[VÉRIFIÉ, ADR 0005] Le livrable est un **dossier d'audit marketing express**,
pas un score comparatif. Trois composantes, toutes vérifiables dans
`serializers.py` :
1. les **écarts priorisés** par gravité déclarée puis par score de dimension
   croissant (`_plan_action()`, déterministe, aucun LLM ne réordonne) ;
2. les **points forts** (dimensions où le prospect dépasse un seuil, lui-même
   `[À CALIBRER]`) ;
3. les **dimensions non observées transformées en questions d'entretien** —
   la couverture partielle du système devient une matière de conversation
   plutôt qu'une faiblesse cachée.

Le document se déclare lui-même `audit complet`, `**audit PARTIEL**` ou
`complétude inconnue`. **C'est un choix de positionnement rare et à
valoriser commercialement** : la plupart des produits d'audit automatisé du
marché affichent une confiance uniforme quelle que soit la donnée réellement
disponible ; celui-ci affiche sa propre incertitude. C'est un argument de
vente honnête, pas seulement une contrainte technique.

### A.3 Le wedge étroit, formulé comme une phrase de vente vérifiable

> *« Pour une consultante ou une petite agence qui prospecte des PME de
> services locaux, produire en quelques minutes un dossier d'audit
> marketing défendable — écarts, points forts, questions d'entretien — à la
> place d'une heure de recherche manuelle par prospect, avec les zones
> d'incertitude déclarées plutôt que masquées. »*

Ce que cette phrase **ne** promet pas, et ne doit pas promettre avant d'y être
autorisée par une mesure : un score comparatif entre prospects (ADR 0005 l'a
explicitement écarté), une prédiction d'intention d'achat (RECHERCHE §7.1 :
« aucune source ne franchit le dernier pas entre signal ouvert observé et
cette PME va acheter du conseil en branding »), l'envoi automatisé de
courriels (J6 non activable), une couverture de secteur au-delà du HVAC
(une seule rubrique existe).

### A.4 Wedge → plateforme, sans sauter l'étape

Le socle technique **permet** l'extensibilité (`secteur_id` comme clé de
configuration, ADR 0003 ; huit familles de besoin OSINT identifiées et
classées, `FOURNISSEURS §2`, dont cinq sont agnostiques à la verticale —
F1/F2/F3/F7/F8 ; seule F5, les signaux datés, est spécifique au métier). C'est
une **capacité architecturale**, pas une preuve de marché. `HERITAGE` le dit
sans détour : « une v2 doit valider son extensibilité sur deux verticales
réelles, pas une. »

**Séquence recommandée, explicitement staged :**

| Étape | Contenu | Condition de passage à la suivante |
|---|---|---|
| **Wedge (aujourd'hui → pilote)** | HVAC, Québec, dossier d'audit, opératrice unique | Phase D levée + N dossiers réels livrés et jugés utilisables par la consultante elle-même (section F) |
| **Wedge élargi** | HVAC, Suisse romande puis France (séquence déjà actée, régimes de conformité croissants) | Régime de conformité par marché instruit (Palier 2 ADR 0001, `compliance/*.yaml`) |
| **Deuxième verticale** | Un secteur de PME de services locaux comparable (ex. plomberie, paysagisme — à choisir par jugement métier, pas par ce document) | Rubrique + vocabulaire écrits, mesure de l'effort réel de portage (coût réel vs promesse « trois YAML, zéro code ») |
| **Plateforme (marque blanche, multi-tenant)** | Ouverture à des partenaires (agences, cabinets conseil) | **Seuil de tenants payants défini à l'avance** (Palier 3 ADR 0001, déjà gelé pour cette raison) — jamais une intuition |

**Ce document ne promet pas la plateforme dès le premier jour.** C'est une
demande explicite du mandat et un rappel de méthode : le Palier 3 de l'ADR
0001 est **gelé**, pas refusé, et la condition de dégel (seuil de tenants
payants) n'existe pas encore parce qu'il n'y a **aucun tenant payant**.

---

## B. Modèle économique

### B.1 La structure de coût variable — à poser avant tout modèle de prix

**Contrainte à ne jamais ignorer** : chaque dossier consomme un coût marginal
non nul. L'ignorer serait exactement l'erreur nommée dans le mandat.

[VÉRIFIÉ, FOURNISSEURS §6.2] Sur les huit familles de besoin OSINT, **cinq
peuvent être ramenées à un coût marginal nul ou quasi nul** une fois la
refonte de sourcing appliquée (F1/F2/F7 via registres publics gratuits ;
F3/F8 via le crawl propre déjà possédé). **Une dépendance commerciale dure
subsiste** : F4 (réputation locale, aujourd'hui Google Places) — `FOURNISSEURS
§3.3` conclut qu'il n'existe **aucune alternative crédible** sur les trois
marchés visés. **Une dépendance optionnelle** : F6 (contacts), dont le
fournisseur actuel (Apollo) porte un risque juridique qui peut l'exclure du
modèle SaaS (§A, §D, §F).

**Formule générale du coût marginal par dossier :**

```
coût_dossier = Σ_i (appels_fournisseur_i × prix_unitaire_i)
             + (tokens_entrée + tokens_sortie) × prix_token_modèle
             + coût_stockage_marginal (≈ 0, texte structuré)
```

[VÉRIFIÉ] L'infrastructure pour calculer cette formule **existe déjà** et
n'est pas à construire : `LedgerEntry` (J3/GreenIT) trace, par appel,
`octets_entrants`, `octets_sortants`, `duree_ms`, `energie_wh`, `co2e_g`,
`modele`, `profil` — le grand livre `api_usage.log` est append-only et
recalculable. C'est un actif rare : la plupart des produits IA construisent
cette instrumentation après avoir découvert qu'ils en avaient besoin ; ici
elle précède le premier client payant.

**Ce que la formule ne peut pas encore chiffrer.** [VÉRIFIÉ] Tous les
`prix_unitaire_i` de `knowledge/api_pricing.yaml` valent **0**, avec
`releve_le: null`. Le prix du token Claude n'a été recherché dans **aucune**
des deux notes lues — ni FOURNISSEURS ni RECHERCHE ne l'abordent, et cette
session ne peut pas non plus l'aller chercher (egress bloqué). **Aucun coût
par dossier n'est donc calculable aujourd'hui avec des nombres réels.** La
Phase D (relevé des tarifs, `CLAUDE.md` § Prochaines tâches) est la
pré-condition dure numéro un de tout le reste de cette section B.

**Exemple illustratif [ESTIMATION MODÉLISÉE, paramètres hérités des sources
secondaires marquées `[NON VÉRIFIÉ]` dans FOURNISSEURS §7 — jamais un prix,
seulement une démonstration de la forme du calcul] :**

| Poste | Hypothèse (paramètre, pas une mesure) | Contribution |
|---|---|---|
| Google Places (F4), 2 appels/dossier | ≈ 0,032 $/appel `[NON VÉRIFIÉ, hérité de FOURNISSEURS §3.3]` | ≈ 0,06 $ |
| Découverte SERP (F1), amortie sur un lot | ≈ 0,01–0,03 $/dossier au lot `[NON VÉRIFIÉ, hérité de FOURNISSEURS §3.1]` | ≈ 0,01–0,03 $ |
| Synthèse LLM (profil `standard`, 600 tokens) | prix du token **non recherché dans cette session** | **[ESTIMATION NON SOURCÉE]** |
| Contacts (F6), si Apollo maintenu | fixe (abonnement à 3 sièges min., ≈ 119–149 $/mois `[NON VÉRIFIÉ]`), pas marginal | à répartir sur le volume, pas par dossier |

**Lecture à retenir** : même avec les paramètres les plus favorables, la ligne
la plus lourde du coût marginal (le token LLM) est **la seule que ce document
ne peut même pas approcher**, faute d'avoir été recherchée. **Tout prix public
fixé avant la Phase D serait un pari, pas un calcul.** C'est la raison pour
laquelle la section B.2 présente des *méthodes* de tarification et non des
*tarifs*.

### B.2 Options de tarification, méthode de calcul explicite pour chacune

#### Option 1 — Abonnement par siège

```
revenu_mensuel = nb_sièges × prix_siège
```

**Analyse.** Le persona acheteur du wedge est une **consultante solo**
(bus factor 1, `agent-produit §L'utilisatrice`) — un siège unique. Pour une
petite agence, plusieurs sièges ont un sens. **Défaut structurel** : le
per-seat ne suit pas le coût marginal (B.1) — un compte à un siège qui produit
200 dossiers/mois coûte à l'exploitant bien plus qu'un compte à un siège qui
en produit 5, pour le même revenu. **[JUGEMENT] : à écarter comme modèle
unique**, éventuellement utile comme **plancher** dans un modèle hybride
(option 4).

#### Option 2 — À l'usage (par dossier)

```
revenu = nb_dossiers × prix_dossier,  avec  prix_dossier > coût_dossier (B.1) + marge visée
```

**Analyse.** C'est le modèle le mieux aligné avec la structure de coût
variable et avec le mode d'usage réel (manage-by-exception : l'opératrice
consomme un dossier, pas un abonnement à un outil qu'elle opère). **Risque** :
revenu imprévisible d'un mois à l'autre pour l'exploitant, ce qui complique la
planification de capacité (budget des garde-fous `api_pricing.yaml`, déjà
conçus pour plafonner la dépense par run — un mécanisme de protection côté
coût existe donc déjà, `I5/I6`, `HERITAGE` catégorie B).

#### Option 3 — Au résultat (outcome-based)

```
revenu = nb_résultats_attribués × prix_résultat   (ou : % de la valeur d'un deal conclu)
```

**Analyse — recommandation ferme : NE PAS FAIRE, maintenant.**
[VÉRIFIÉ, RECHERCHE R10 et §7.1] « On ne peut pas facturer un résultat qu'on
ne sait pas mesurer. » Facturer un résultat suppose de définir et de mesurer
ce résultat ; **aucune mesure de lien entre signal détecté et conversion
commerciale n'existe dans ce projet** — le Lot 0 de l'ADR 0004 (`motif_rejet`,
états `rdv`/`client`) est explicitement **non fait**. Facturer un résultat non
mesuré transfère au client un risque que l'exploitant ne sait pas évaluer
lui-même. **Condition de déblocage, nommée explicitement** : Lot 0 construit
**et** une mesure de lift contre un groupe témoin apparié réalisée
(méthode établie en RECHERCHE §4.3, jamais appliquée ici).

#### Option 4 — Hybride (socle + dépassement à l'usage)

```
revenu = abonnement_fixe + max(0, nb_dossiers − quota_inclus) × prix_marginal
```

**Analyse — modèle recommandé à l'horizon du pilote payant.** Le socle fixe
couvre le coût non marginal (support, calibration continue de la rubrique,
temps de revue) ; le dépassement à l'usage aligne le prix sur le coût
variable réel (B.1) dès que la Phase D le rend calculable. C'est aussi le
modèle qui **ne nécessite aucune nouvelle capacité technique** : le grand
livre et les garde-fous budgétaires existants (`I5/I6`) en sont déjà le
squelette. [COMMERCIAL, RECHERCHE §6.3, non probant] : l'hypothèse que
l'hybride serait le mode dominant du marché SaaS IA est rapportée par des
éditeurs d'outils de facturation — intérêt commercial direct, **non utilisée
ici comme preuve**, seulement comme cohérence de direction.

#### Option 5 — Marque blanche pour partenaires (agences, cabinets conseil)

```
revenu_partenaire = redevance_fixe_partenaire + (nb_dossiers_partenaire × prix_dossier_réduit)
```

**Analyse.** C'est le canal de distribution le plus prometteur pour résoudre
le problème structurel du wedge : **la consultante est elle-même le seul
canal de distribution aujourd'hui** (bus factor 1). Un partenaire (agence,
cabinet conseil) apporte une base de clients déjà acquise. **Mais** —
et c'est un point que ce document doit dire sans détour — **la marque blanche
aggrave exactement le risque juridique déjà identifié en Apollo** (§A.4, §D,
§F) : livrer un dossier contenant un contact enrichi par Apollo *à un
partenaire qui le revend à son propre client* est le scénario précis que la
clause rapportée « interdiction de sous-licencier, vendre ou distribuer »
semble viser. **La marque blanche ne doit pas être ouverte tant que la
question juridique Apollo n'est pas tranchée ou que le pivot « contact
d'entreprise publié » (FOURNISSEURS §4.4) n'est pas adopté.**

### B.3 Recommandation

**Wedge (pilote payant, mono-tenant)** : option 2 (à l'usage) ou option 4
(hybride) — la vraie décision (2 vs 4) appartient à la consultante et dépend
de sa préférence pour un revenu prévisible (4) contre un revenu strictement
aligné sur l'usage (2). **Option 3 différée jusqu'à Lot 0 + mesure de lift.
Option 5 différée jusqu'à clarification Apollo ou pivot F6.** Option 1 non
recommandée seule.

---

## C. TAM / SAM / SOM

**Avertissement frontal, à ne pas contourner.** L'egress web est bloqué dans
cet environnement (confirmé par les deux notes lues : `WebFetch` en HTTP 403
sur toute URL testée, y compris des sites sans protection anti-robot).
**Aucune donnée de marché n'a pu être vérifiée pour produire ce document.**
Conformément à l'instruction du mandat, ce document **dit l'absence plutôt que
de l'inventer**. Un TAM inventé serait pire qu'un TAM absent.

### C.1 Ce que ce document NE fait PAS

Il ne fournit **aucun chiffre en dollars** de TAM, SAM ou SOM. Toute valeur
qui circulerait dans un pitch (« marché de X milliards ») proviendrait
nécessairement d'une source non vérifiée dans cette session, exactement le
registre `[COMMERCIAL]` que `RECHERCHE §6.1` documente et écarte explicitement
(le chiffre de 4,6 T$ de Foundation Capital, ou les 8,1 Md$ → 182,9 Md$
d'agents verticaux d'ici 2034, tous deux marqués `[COMMERCIAL]`, « sans valeur
probante »). **Reprendre ce type de chiffre ici serait exactement l'erreur que
le mandat demande d'éviter.**

### C.2 Ce que ce document fait à la place : la méthode, et une piste que le produit peut mesurer lui-même

La bonne nouvelle méthodologique, découverte en lisant `FOURNISSEURS §4.1` :
**le SAM de ce produit n'est pas une donnée de marché à acheter — c'est une
donnée que le produit peut calculer lui-même**, à coût nul, une fois la
refonte de sourcing (F1/F2/F7) en place.

```
TAM = Σ (marchés potentiels) × (valeur moyenne d'un abonnement/dossier
        pour ce segment)                                    — non calculable ici
SAM = nb d'entreprises correspondant à l'ICP (secteur × géographie)
        × taux d'atteignabilité commerciale                 — calculable via
                                                                registres publics
SOM = nb de dossiers que l'exploitant peut effectivement produire
        et vendre sur la période, borné par sa propre capacité
        d'opération (bus factor 1) et par les budgets de garde-fou
        configurés                                           — borné par la
                                                                capacité connue
```

**SAM — la méthode concrète, propre à ce projet.** [VÉRIFIÉ, FOURNISSEURS
§4.1] Trois registres publics couvrent exactement les trois marchés du
pilote et donnent, par code d'activité, **l'univers** des entreprises (pas un
échantillon biaisé par un moteur de recherche) :

| Marché | Registre | Ce qu'il permettrait de compter |
|---|---|---|
| Québec | Registraire des entreprises (REQ), donneesquebec.ca | Nombre d'entreprises actives sous le code d'activité HVAC pertinent, par région |
| Suisse | Zefix (OFRC) | Idem, par canton |
| France | Sirene / API Recherche d'Entreprises (DINUM) | Idem, par code NAF |

**Aucun de ces registres n'est branché aujourd'hui** [VÉRIFIÉ, `FOURNISSEURS
§2.2` : F2/F7 sont marquées « non » couvertes]. Le SAM du wedge HVAC
Québec → Suisse romande → France est donc, littéralement, **une requête que le
produit ne sait pas encore poser à lui-même**. C'est une recommandation
d'architecture qui a une conséquence stratégique directe : **brancher F2/F7
n'est pas seulement une amélioration de couverture (FOURNISSEURS le motive
déjà ainsi) — c'est aussi la façon la moins chère et la plus honnête de
produire un SAM réel**, sans dépendre d'un cabinet d'études.

**SOM — borné par une capacité déjà connue.** [VÉRIFIÉ] `run_preflight.py`
échoue tant que `budgets.serp.unites_max.requetes` et
`budgets.apollo.unites_max.credits` valent 0. Cela signifie que **le SOM du
pilote est aujourd'hui exactement zéro**, non par manque de marché mais par
absence de paramétrage (Phase D). C'est une reformulation utile : le premier
SOM mesurable de ce produit n'est pas une part de marché, c'est **le nombre de
dossiers que la consultante choisit de plafonner dans son propre budget** — une
décision produit, pas une prévision de marché.

### C.3 Ce qu'il faudrait pour produire un TAM crédible

1. Compter le SAM via les trois registres (ci-dessus) — faisable sans accès
   web supplémentaire dans un environnement de développement normal, gratuit,
   redistribuable (licences vérifiées comme favorables en `FOURNISSEURS §4.1`,
   elles-mêmes `[NON VÉRIFIÉ]` mais de nature différente d'un chiffre de
   marché : ce sont des données ouvertes, pas des estimations d'analystes).
2. Estimer un taux de conversion prospect → client payant **mesuré sur le
   pilote réel**, pas supposé — c'est exactement l'objet du Lot 0 (ADR 0004)
   déjà identifié comme non fait.
3. Multiplier SAM × taux de conversion × prix moyen (issu de B.3, calculable
   seulement après Phase D). **Chacun des trois facteurs manque aujourd'hui.**

**Conclusion de la section C, à ne pas édulcorer** : ce document ne fournit
pas de TAM chiffré parce qu'aucun ne serait honnête à produire ici. Il fournit
la méthode et identifie que **le SAM est, exceptionnellement, une capacité du
produit lui-même** — un argument de conception réutilisable en section D
(moat).

---

## D. Le moat

Le donneur d'ordre veut « devenir pionnier et monopole ». La réponse honnête
commence par un refus : **un pipeline OSINT est reproductible et les modèles
sont des commodités** (mandat lui-même). Aucune architecture, aussi propre
soit-elle, n'est un moat en soi. Ce qui suit distingue ce qui pourrait
réellement en constituer un de ce qui n'est qu'une avance temporaire.

### D.1 Ce qui n'est PAS un moat, malgré les apparences

| Candidat apparent | Pourquoi ce n'en est pas un |
|---|---|
| **L'orchestrateur DAG déterministe** (ADR 0001) | Excellente ingénierie, alignée avec la recherche (`RECHERCHE R1`, R2) — mais **reproductible par toute équipe compétente en quelques mois**. C'est un choix de qualité, pas une barrière. |
| **Le routage de modèle GreenIT** (ADR 0002) | Le mandat lui-même le nomme : « les modèles sont des commodités ». Un routage déterministe piloté par YAML est une bonne pratique d'ingénierie frugale, copiable en semaines. |
| **SERP (découverte)** | [VÉRIFIÉ, `FOURNISSEURS §3.1`] Le code ne consomme qu'une URL par résultat. « N'importe quelle API renvoyant des URL organiques suffit fonctionnellement. » C'est même un **passif** : dépendance à un fournisseur dont la continuité dépend d'un contentieux en cours (Google c. SerpApi). |
| **Google Places (réputation)** | C'est une **dépendance dure sans alternative** (`FOURNISSEURS §3.3`), pas un avantage : n'importe quel concurrent paie le même prix pour le même accès, et le contrat semble hostile à la persistance (§5.1). Une dépendance non substituable est un risque partagé par tout le secteur, pas un différenciateur. |
| **Apollo (contacts)** | Pire que neutre : risque juridique propre qui peut **interdire** le modèle SaaS (§A, §F). Le remplacer est une nécessité, pas un choix de moat. |
| **Le fait d'avoir un LLM** | Tous les concurrents en ont un. Le grounding structurel (le LLM ne fetch jamais, `I17`) est une bonne pratique de fiabilité, pas un secret. |

### D.2 Ce qui pourrait réellement en constituer un — et à quelle condition

**D.2.1 — Le dossier longitudinal ancré sur un identifiant de registre.**
[VÉRIFIÉ, `FOURNISSEURS §6.3(4)`] La clé de déduplication actuelle est le
domaine normalisé — volatile (un domaine change, expire, se revend).
`FOURNISSEURS` recommande une clé primaire sur l'identifiant de registre
(NEQ / IDE / SIREN), **non volatile**. Un dossier tenu sur plusieurs années,
ancré sur cet identifiant, accumule une observation historique qu'aucun
concurrent entrant ne peut reconstituer rétroactivement — **c'est la structure
d'un moat de données propriétaires**, mais il faut être honnête sur deux
conditions : (a) il n'existe **pas encore** (`append_historique()` est posée,
non exploitée — `HERITAGE` point 4) ; (b) sa valeur croît linéairement avec le
temps d'opération réelle, pas avec la sophistication du code. **C'est un moat
qui se construit en années d'usage, pas en sprints.**

**D.2.2 — La boucle de rétroaction issue de la validation humaine.**
[PLANIFIÉ, non fait] Le Lot 0 de l'ADR 0004 (`motif_rejet`, états
`rdv`/`client`) transformerait chaque décision de l'opératrice en donnée
d'entraînement pour calibrer la rubrique et, à terme, l'axe intention. C'est
le candidat de moat le plus solide **en théorie** — un système qui apprend de
son usage réel est difficile à rattraper pour un concurrent qui démarre de
zéro — mais [VÉRIFIÉ] **il n'existe aujourd'hui aucune mesure**, et
`RECHERCHE §3.5/§7.7` avertit que la porte humaine elle-même s'érode avec le
biais d'automatisation si elle n'est pas surveillée. Un moat construit sur une
boucle non instrumentée est une intention, pas un actif.

**D.2.3 — L'expertise métier encodée en rubriques.**
[VÉRIFIÉ] `rubric_persona1.yaml`, `vocabulaire_intention_persona1.yaml`,
`intent_persona1.yaml` sont des **brouillons `[À CALIBRER]`**, non validés par
la consultante. Le potentiel est réel — une rubrique calibrée sur des années
d'entretiens réels avec des installateurs HVAC encode un savoir que ni un
concurrent générique ni un LLM seul ne possèdent — mais aujourd'hui, c'est un
squelette de configuration, pas encore du savoir calibré. **Le moat existe
dans la donnée que produira l'usage, pas dans le mécanisme YAML qui
l'accueillera.**

**D.2.4 — L'intégration au flux de travail de l'opératrice.**
[VÉRIFIÉ] Le vault Obsidian + cockpit sont le lieu où l'opératrice travaille
déjà, avec un coût de changement réel s'il fallait migrer d'outil. Mais
`HERITAGE` catégorie C le classe justement comme invariant *lié au produit v1
à réexaminer* : Obsidian n'est pas propriétaire, un concurrent peut recréer la
même intégration. C'est un **coût de changement**, pas un moat au sens strict
— utile en rétention (section E), pas en défensibilité de marché.

**D.2.5 — Distribution et partenariats (marque blanche).**
Un canal de distribution via des agences ou cabinets conseil partenaires
serait un avantage d'**exécution commerciale**, pas technique — défendable
seulement par la qualité de la relation et l'antériorité du partenariat, pas
par le code. Utile, réel, mais **pas un moat au sens où le mandat l'entend**
(barrière technique reproductible seulement à grand effort).

**D.2.6 — La conformité par marché comme coût d'entrée pour un concurrent.**
Le Palier 2 de l'ADR 0001 (`compliance/*.yaml` par marché — CASL, nLPD +
LCD, RGPD, transparence AI Act) est **non fait**, mais s'il l'était, il
représenterait un coût de mise en conformité multi-juridictions que peu de
concurrents généralistes prennent la peine de porter pour un marché de niche.
C'est un **moat d'effort réglementaire régional**, réel mais modeste — pas
une barrière insurmontable pour un acteur bien financé.

### D.3 Barrière réelle vs avance temporaire — synthèse

| Type | Éléments | Horizon de défendabilité |
|---|---|---|
| **Barrière réelle possible** | Dossier longitudinal ancré registre (D.2.1) + boucle de rétroaction mesurée (D.2.2) + rubrique calibrée par l'usage (D.2.3) | **Années**, mais conditionnée à des lots non faits (Lot 0, append_historique exploité) et à un volume réel d'usage qui n'existe pas encore |
| **Avance temporaire** | Qualité d'ingénierie (DAG déterministe, GreenIT, discipline à trois états, garde-fous de bus), intégration Obsidian | **Mois**, copiable par une équipe compétente |
| **Non-moat / passif** | SERP, Google Places (dépendance dure sans alternative), Apollo (risque juridique) | Coûts et risques partagés par tout le secteur, jamais un avantage |

### D.4 Verdict honnête sur le mot « monopole »

**[JUGEMENT, à assumer frontalement.** Il n'existe aujourd'hui **aucune base
factuelle** pour parler de monopole. Un monopole suppose un effet de réseau,
un coût de changement prohibitif, ou une barrière réglementaire — aucun des
trois n'existe à ce stade : zéro client payant, zéro donnée propriétaire
accumulée, zéro effet de réseau possible (le produit n'est même pas
multi-tenant, et le Palier 3 qui le permettrait est explicitement gelé). Ce
que ce document peut honnêtement dire : **la structure d'un moat de données
longitudinales existe en germe**, et elle est atteignable **si** trois choses
non faites aujourd'hui sont faites (Lot 0 mesuré, `append_historique()`
exploité, deuxième verticale validée) **et si** le produit accumule des années
d'usage réel. Prétendre au monopole avant cela serait vendre une intention
comme un fait — exactement ce que ce document doit refuser.

---

## E. Les artefacts de startup

### E.1 Vision et récit

**Vision (horizon 3-5 ans, [JUGEMENT], pas une prévision) :** devenir la
mémoire longitudinale des PME de services locaux pour les professionnels qui
les conseillent — un dossier vivant par entreprise, alimenté par de
l'observation publique horodatée et par le jugement humain qui le valide,
extensible à toute question OSINT qu'un professionnel se pose sur une PME
(marketing aujourd'hui ; recrutement, veille concurrentielle, diligence
raisonnable demain — familles F1-F3/F7/F8 déjà agnostiques à la verticale,
`FOURNISSEURS §2.4`).

**Récit fondateur, honnête :** le produit n'est pas né d'une intuition de
marché mais d'un besoin opérationnel réel d'une praticienne — c'est un actif
de crédibilité (le premier product-market fit testé est celui de la
créatrice elle-même), à condition de ne jamais le confondre avec une
validation de marché plus large (section F).

### E.2 Positionnement

*« Le dossier d'audit marketing qui dit ce qu'il sait et ce qu'il ne sait pas
— pas un score de plus, une conversation prête à avoir. »*

Différenciation revendiquée, avec sa preuve et sa limite :
- **complétude vérifiable** (ADR 0005) — preuve : le mécanisme existe dans le
  code (`_couverture`), limite : seuils `[À CALIBRER]` ;
- **frugalité mesurée** (GreenIT) — preuve : `LedgerEntry` instrumenté,
  limite : coûts affichés à 0 tant que Phase D n'est pas faite ;
- **discipline anti-hallucination structurelle** — preuve : le LLM ne fetch
  jamais, aucune affirmation non adossée à une faille réelle ; c'est un
  argument défendable **techniquement**, rarement mis en avant par des
  concurrents génériques.

### E.3 ICP et personas

| ICP réel aujourd'hui | Statut |
|---|---|
| **Persona 1 — installateur/détaillant HVAC**, Québec | [VÉRIFIÉ] Seul persona avec rubrique et vocabulaire rédigés (`icp/persona1-quebec.yaml`) |
| Persona 1, Suisse romande / France | [PLANIFIÉ] Fichiers ICP à créer, mécanisme prêt (ADR 0003) |
| Persona 2 (tout secteur) | **N'existe pas.** `rubric_persona2.yaml` cité comme tâche future dans `CLAUDE.md`, indépendante de J6 |
| **Acheteur du wedge : la consultante solo elle-même** | Persona validé par construction — c'est elle qui a spécifié le produit |
| **Acheteur de la marque blanche (agences, cabinets conseil)** | [ESTIMATION NON SOURCÉE] Persona hypothétique, jamais interviewé dans ce projet |

### E.4 Matrice concurrentielle

**[JUGEMENT / MÉMOIRE, non vérifié en session — aucune recherche web
possible ; catégories génériques, pas des fiches produits vérifiées]**

| Catégorie | Exemple de nature (générique, non vérifié) | Où ce produit se différencie | Où ce produit est en retard |
|---|---|---|---|
| Consultants/agences généralistes | Travail 100 % manuel | Vitesse, coût marginal, cohérence documentaire | Aucun jugement humain fin sans la consultante elle-même |
| Outils grand public d'audit SEO/local | Rapports automatisés génériques, souvent scores comparatifs sans déclaration de couverture | Honnêteté de couverture (ADR 0005), frugalité mesurée | Notoriété, intégrations existantes, volume de trafic déjà établi |
| Fournisseurs de données d'intention B2B (intent data) | Scores d'intention agrégés, souvent vendus comme prédictifs | Refus explicite de sur-promettre (RECHERCHE §7.1) | Absence totale de preuve de valeur prédictive — un désavantage marketing assumé, pas caché |
| Nouveaux entrants agentiques génériques | Agents autonomes multi-outils | Discipline anti-hallucination structurelle, coût mesuré | Portefeuille de fonctionnalités probablement plus large côté nouveaux entrants bien financés |

**Cette matrice est qualitative et non vérifiée.** Elle sert à cadrer la
discussion, pas à fonder une décision de prix ou de positionnement définitif.

### E.5 Mise sur le marché

**Phase 1 (wedge)** : la consultante est le canal — elle utilise le produit
sur ses propres prospects, ce qui est aussi le test de valeur le moins cher
(section F). **Phase 2** : preuve d'usage réelle (dossiers livrés, jugés
utiles) comme matériau de vente pour approcher 2-3 partenaires potentiels
(agences, cabinets) en conversations informelles, **avant** toute
construction d'infrastructure marque blanche. **Phase 3** : marque blanche,
conditionnée à la clarification du risque Apollo (§B.2 Option 5).

### E.6 Tarification publique

**[ESTIMATION MODÉLISÉE, à publier seulement après Phase D]** Squelette de
grille, structure hybride (Option 4, §B.2) — **aucun chiffre n'est publiable
avant que B.1 soit calculable avec des tarifs réels** :

```
Palier « solo » : abonnement_fixe_bas + quota_inclus dossiers/mois + dépassement à prix_marginal
Palier « équipe/agence » : abonnement_fixe_moyen + quota_inclus plus large + sièges additionnels
Palier « marque blanche » : sur devis — conditionné à la levée du risque Apollo (§B.2 Option 5)
```

### E.7 Métriques nord

| Métrique | Définition opérationnelle | Source de la mesure |
|---|---|---|
| **Activation** | Premier dossier livré **et validé par l'opératrice** (transition `diagnostique → valide` observée) | `runs.log`, machine à états du vault |
| **Rétention** | Dossiers produits/mois soutenus sur ≥ 3 mois consécutifs | Agrégat `api_usage.log` / vault |
| **Expansion** | Croissance du volume de dossiers ou du nombre de sièges par compte | Grand livre + comptes |
| **Marge brute par dossier** | `prix_dossier − coût_dossier` (formule §B.1) | **Non calculable avant Phase D** |
| **Taux d'approbation de la porte humaine** | Part des dossiers `diagnostique → valide` sans modification | [PLANIFIÉ, recommandé par `RECHERCHE R8`] — un taux > 95 % est un signal d'alerte (porte décorative), pas un signal de succès |

### E.8 Plan à 12 mois, trois scénarios

**Hypothèses communes aux trois scénarios, déclarées** : Phase D complétée au
mois 1 ; aucune promesse d'outreach automatisé (J6 reste hors périmètre) ;
aucune promesse de deuxième verticale avant validation de la première.

| | **Prudent** | **Attendu** | **Agressif** |
|---|---|---|---|
| **Hypothèse centrale** | Le produit reste un outil interne de la consultante ; aucun client externe payant en 12 mois | Un pilote payant limité (quelques comptes, wedge HVAC QC/CH) démontre une valeur mesurable | Traction rapide justifiant l'ouverture anticipée à des partenaires marque blanche |
| **Jalons 12 mois** | Phase D faite ; N dossiers réels produits et jugés utiles par la consultante ; Lot 0 instrumenté | + 2-5 comptes payants ; première mesure de lift (même à faible puissance statistique) ; persona 1 étendu à la Suisse romande | + white-label avec 1-2 partenaires (sous condition Apollo résolue) ; début persona 2 |
| **Ce qui invaliderait ce scénario s'il ne se produit pas** | Même le scénario prudent échoue si la consultante elle-même ne juge pas les dossiers utiles sur des entreprises réelles — voir F.3 | Échoue si aucun compte externe n'accepte de payer même au tarif d'entrée — voir F.4 | Échoue si le risque Apollo n'est pas levé à temps, ou si la calibration de rubrique reste `[À CALIBRER]` sans retour terrain suffisant |
| **Statut du chiffrage** | Aucun chiffre en dollars fourni ci-dessus : conforme à la section C, faute de TAM/SAM/SOM chiffrable | idem | idem |

### E.9 Risques et signaux d'invalidation (résumé — développés en F)

Voir section F pour le détail. Résumé des risques structurants : dépendance
Apollo (juridique), dépendance Google Places (pas d'alternative), absence de
preuve prédictive de l'axe intention, absence totale de client réel, seconde
verticale non prouvée, porte humaine potentiellement décorative à l'échelle.

---

## F. Ce qui invaliderait ce plan — la section la plus importante

**Fait dominant, à ne jamais perdre de vue en lisant ce qui suit** : [VÉRIFIÉ]
**le système n'a jamais vu une entreprise réelle, ni un client payant.**
669 tests, tous contre un faux serveur HTTP local (`HERITAGE §Pourquoi ce
document existe`). Toute la stratégie ci-dessus repose donc sur des
hypothèses non testées. Les nommer est plus utile que de les taire.

Classées par **coût de l'expérience qui les teste**, de la moins chère à la
plus chère — l'ordre logique d'exécution, pas l'ordre d'importance.

### F.1 Hypothèse : le système produit des audits utilisables sur des entreprises réelles

**Si fausse : tout le reste de ce document est sans objet.**
**Coût du test : le plus bas de la liste.** Compléter la Phase D (paramétrage
YAML + variables d'environnement, aucune ligne de code, déjà documenté dans
`CLAUDE.md`), lancer `run_preflight.py` jusqu'à GO, puis produire 10-20
dossiers réels sur des entreprises HVAC québécoises existantes et demander à
la consultante elle-même de les juger utilisables tels quels ou après
correction mineure.

### F.2 Hypothèse : la clause Apollo n'interdit pas le modèle SaaS

**Si fausse : le canal de contacts actuel (F6) est illégal à revendre, et
toute marque blanche impliquant Apollo l'est a fortiori.**
**Coût du test : quasi nul.** Lire le texte de `apollo.io/terms/api` (bloqué
dans *cet* environnement, trivial dans un environnement de développement
normal) et poser les trois questions déjà formulées dans `FOURNISSEURS §5.2`
à un juriste. C'est la vérification la moins chère de toute cette liste et
elle conditionne une part significative du modèle économique (§B.2 Option 5).
**Recommandation immédiate, indépendante du résultat** : engager en parallèle
le pivot « contact d'entreprise publié » (`FOURNISSEURS §4.4`), qui supprime
la question en la rendant non pertinente.

### F.3 Hypothèse : l'API Google Places *legacy* reste utilisable pour un nouveau déploiement

**Si fausse : F4 (réputation locale), la seule famille sans alternative
crédible, ne démarre pas du tout sur un projet Cloud neuf.**
**Coût du test : faible.** [VÉRIFIÉ, `FOURNISSEURS` C6] Le code cible l'API
Places *legacy*, rapportée `[NON VÉRIFIÉ]` comme gelée depuis mars 2025 et
indisponible aux nouveaux projets Google Cloud. Créer un projet Cloud réel et
tenter l'appel tranche la question en quelques minutes, avant toute question
de prix.

### F.4 Hypothèse : au moins un client est prêt à payer pour ce dossier

**La question la plus fatale de toutes, et la moins chère à tester tôt.**
**Coût du test : faible à modéré.** Livrer manuellement (au besoin
semi-manuellement, en s'appuyant sur le pipeline existant) 5-10 dossiers à
des prospects ou pairs réels de la consultante, et demander soit un paiement
réel, soit une lettre d'intention. **Aucune ligne de ce document n'a de sens
si cette hypothèse est fausse** — c'est pourquoi la section C refuse
explicitement tout TAM chiffré tant que ce test n'a pas eu lieu.

### F.5 Hypothèse : le cache Google Places respecte la contrainte de rétention à 30 jours

**Si fausse : usage à risque de suspension de compte dès le premier volume
réel, pas seulement de non-conformité théorique.**
**Coût du test : bas (correctif de code, pas une expérience de marché).**
[VÉRIFIÉ, `FOURNISSEURS` C3] `cache_ttl_jours: 30` est déclaré deux fois et
lu par aucun code. Corriger avant tout usage réel de Places à volume.

### F.6 Hypothèse : la deuxième verticale coûte réellement « trois YAML, zéro code »

**Si fausse : la promesse d'extensibilité qui justifie le récit « plateforme »
(section A.4) ne tient pas, et le produit reste mono-verticale indéfiniment.**
**Coût du test : modéré.** Écrire réellement une rubrique et un vocabulaire
pour un secteur adjacent (ex. plomberie), mesurer le temps humain réel
(rédaction, calibration, premiers tests), comparer à la promesse. `HERITAGE`
le nomme déjà : « généricité sans deuxième cas d'usage = généricité non
prouvée. »

### F.7 Hypothèse : un signal d'intention observable publiquement prédit une conversion

**Si fausse : le quadrant besoin × intention (ADR 0004) n'apporte aucune
valeur commerciale au-delà d'un habillage, et ne doit jamais être vendu comme
prédictif.**
**Coût du test : modéré, nécessite du volume.** [VÉRIFIÉ, RECHERCHE §7.1 et
§4.3] Aucune preuve, académique ou commerciale indépendante, n'existe. Seul
test valable : Lot 0 (ADR 0004, `motif_rejet`, états `rdv`/`client`) **et**
une mesure de lift contre un groupe témoin apparié. **Tant que ce test n'a pas
eu lieu, ne jamais présenter le quadrant comme prédictif à un client — seul
un usage interne de priorisation heuristique est défendable.**

### F.8 Hypothèse : la porte humaine reste un vrai contrôle à l'échelle

**Si fausse : le manage-by-exception, présenté comme le mode nominal du
produit, devient une façade — l'opératrice valide sans lire, et la valeur
perçue du produit (fiabilité, honnêteté) s'effondre silencieusement.**
**Coût du test : bas, une fois le volume atteint.** [VÉRIFIÉ, RECHERCHE §3.5,
§7.7] Le biais d'automatisation est établi dans la littérature en facteurs
humains ; son ampleur dans ce cas précis ne l'est pas. Instrumenter le **taux
d'approbation** (E.7) et alerter si il dépasse durablement 95 %.

### F.9 Hypothèse : les coûts marginaux réels, une fois connus, laissent une marge brute exploitable

**Si fausse : même avec des clients payants, le produit perd de l'argent par
dossier, et aucun volume ne corrige un prix mal calé.**
**Coût du test : bas, mécanique.** Compléter la Phase D (relevé de tarifs
réels), calculer `coût_dossier` (formule §B.1) avec des nombres réels, le
comparer au prix envisagé **avant** toute promesse de tarif public.

### F.10 Hypothèse : un partenaire marque blanche a un intérêt réel à intégrer ce produit plutôt qu'à construire ou acheter une alternative

**Si fausse : le canal de distribution central de la section E.5 (Phase 2)
n'existe pas, et le produit reste dépendant de la seule consultante comme
canal — ce qui plafonne durement le SOM (§C.2).**
**Coût du test : bas.** Conversations informelles avec 2-3 agences ou
cabinets conseil cibles, **avant** toute construction d'infrastructure marque
blanche — et après clarification Apollo (F.2), pour ne pas démarrer une
conversation commerciale sur un produit qu'on ne peut pas légalement livrer en
marque blanche.

---

## Récapitulatif des risques et dépendances

**Les deux pré-conditions dures du projet dominent toute cette stratégie,
avant même les dix hypothèses de la section F** (rappel de
`agent-produit §Les deux pré-conditions dures`) :

1. **Phase D non faite** — aucune clé API, `api_pricing.yaml` à 0,
   `releve_le: null`, vault non initialisé, `run_preflight.py` en NO-GO
   **[VÉRIFIÉ, cette session]**. Tant qu'elle n'est pas faite, **aucun coût
   par dossier n'est engageant** (§B.1) et aucun test de F.1/F.4/F.9 ne peut
   avoir lieu. **C'est la tâche la plus rentable de tout ce document, et ce
   n'est pas une tâche de développement.**
2. **J6/outreach non activable**, verrouillé jusqu'à validation juridique. Ce
   document n'en a pas eu besoin (le produit vendu est le dossier, pas
   l'envoi), mais toute évolution future vers un outreach automatisé reste
   soumise à cette même pré-condition, inchangée.

**Risque juridique nouveau identifié par cette lecture, à traiter au même
niveau de priorité que les deux pré-conditions ci-dessus** : la clause Apollo
rapportée (F.2) peut interdire, à elle seule, le modèle SaaS de revente tel
que le code le permettrait techniquement aujourd'hui. **C'est un risque de
modèle économique, pas seulement de conformité** — c'est la raison pour
laquelle il est traité en première ligne des sections A, B, D et F plutôt
qu'en annexe.

**Dépendance structurelle sans alternative** : Google Places (F4) reste, dans
l'état actuel de la recherche, la seule famille de besoin sans substitut
crédible sur les trois marchés visés — un risque partagé par tout acteur du
secteur, à surveiller (statut de l'API legacy, clause de rétention à 30
jours) plutôt qu'à espérer voir disparaître.

---

## Ce qui est explicitement écarté de cette stratégie, et le signal qui la ferait reconsidérer

| Écarté maintenant | Signal de reconsidération |
|---|---|
| Tarification au résultat (Option 3, §B.2) | Lot 0 construit **et** lift mesuré contre groupe témoin |
| Marque blanche multi-tenant (Palier 3 ADR 0001) | Seuil de tenants payants **défini à l'avance** par la consultante — jamais une intuition |
| Toute promesse chiffrée de TAM/SAM/SOM | Accès web disponible **et** SAM calculé via les registres publics (§C.2) |
| Le mot « monopole » dans toute communication externe | Moat de données longitudinales effectivement constitué (des années d'usage réel, pas des mois) |
| Deuxième verticale annoncée au marché | Rubrique + vocabulaire écrits **et** effort réel mesuré contre la promesse « zéro code » (F.6) |
| Continuité d'Apollo dans le produit tel quel | Confirmation juridique explicite que la clause ne s'applique pas à l'usage SaaS, **ou** pivot déjà réalisé vers le contact d'entreprise publié |
| Toute affirmation prédictive sur l'axe intention face à un client | Lot 0 + mesure de lift (identique à la ligne tarification au résultat — c'est la même dépendance) |

---

## Sources et limites de méthode de ce document

- Ce document ne cite **aucune** nouvelle source externe : il synthétise
  `FOURNISSEURS-DONNEES.md`, `RECHERCHE-agentique.md`,
  `HERITAGE-v1-invariants-a-challenger.md`, les ADR 0001-0005 et `CLAUDE.md`,
  tous déjà marqués selon leurs propres conventions de preuve.
- **Aucun chiffre en dollars nouveau n'est introduit ici.** Les seuls chiffres
  qui apparaissent sont soit vérifiés dans le dépôt (tests, préflight, commits),
  soit explicitement hérités et re-marqués `[NON VÉRIFIÉ, hérité de
  FOURNISSEURS]`, soit des formules dont les paramètres sont nommés comme
  inconnus.
- La section E.4 (matrice concurrentielle) est la partie la plus faible de ce
  document en termes de preuve : elle est qualitative, non vérifiée en
  session, et ne doit pas être citée comme une étude concurrentielle.
- Ce document **ne se substitue pas** à une revue juridique (Apollo, Google
  Places, conformité par marché) ni à une étude de marché financée. Il cadre
  ce qu'il faudrait vérifier, dans l'ordre de coût croissant (section F).
