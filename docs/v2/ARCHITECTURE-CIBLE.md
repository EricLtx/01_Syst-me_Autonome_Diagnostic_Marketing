# Architecture cible v2 — un socle de collecte, qualification et jugement de signaux

> **Statut : proposition de conception, non actée.** Ce document argumente une
> cible ; il ne remplace aucune ADR existante et n'en constitue pas une
> lui-même. Si le donneur d'ordre valide l'orientation générale, l'étape
> suivante est une ADR de refonte (`0006-…`) qui tranchera formellement — ce
> n'est pas le rôle de ce document.
>
> Rédigé le 2026-08-04, en s'appuyant sur trois documents produits en amont
> (vague 1), lus intégralement avant d'écrire une ligne de ce qui suit :
> `docs/v2/HERITAGE-v1-invariants-a-challenger.md`,
> `docs/v2/RECHERCHE-agentique.md` (⚠️ 100 % des références `[NON LU]`, traitée
> comme orientation argumentée, jamais comme preuve), `docs/v2/FOURNISSEURS-DONNEES.md`.
> Les renvois `R1`…`R10` pointent vers les dix recommandations de la note de
> recherche (§8) ; les renvois `Cn` vers les six constats de code de la note
> fournisseurs (§1.2).
>
> Convention : **[CERTAIN]** = vérifiable dans le code actuel ou déduction
> logique directe ; **[RECOMMANDÉ]** = jugement d'architecture argumenté, pas
> une preuve ; **[À CALIBRER]** = seuil ou paramètre qui devra être mesuré,
> jamais deviné.

---

## 0. Ce que ce document fait, et dans quel ordre le lire

Le mandat demande cinq choses (A à E). Ce document les traite dans un ordre
délibérément différent de l'énoncé : **la section E (le chemin) vient en
premier**, parce qu'elle conditionne la lecture de tout le reste. Une
architecture élégante lue avant de savoir *quand* elle rencontrera le réel
donne une fausse impression de solidité — c'est exactement l'erreur que la v1
a commise et que `HERITAGE-v1-invariants-a-challenger.md` documente comme
l'échec de méthode le plus coûteux (§ « Ce que la v1 a raté »).

Plan : **§1 le chemin (E)** · **§2 le noyau agnostique (A)** · **§3 les deux
tensions tranchées (B, extrait)** · **§4 deux défauts structurels corrigés par
conception (C)** · **§5 scalabilité et multi-tenant (D)** · **§6 plan
d'exécution séquencé** · **§7 risques résiduels**. Le verdict invariant par
invariant complet (24 lignes) est dans `docs/v2/INVARIANTS-v2.md`, référencé
depuis §3.

---

## 1. Le chemin — pourquoi pas un greenfield, et à quel moment toucher le réel

### 1.1 Le fait qui doit peser plus que tout argument d'élégance

> La v1 n'a **jamais vu une entreprise réelle**. 669 tests, tous contre un
> faux serveur HTTP local. Vault vide. Zéro clé API. Préflight NO-GO
> structurel. Un seul ICP existe pour prouver une généricité annoncée pour
> N secteurs. Le banc d'essai axe intention a produit un artefact trompeur
> (7 prospects sur 9 au même score, parce que la fixture n'expose que deux
> gabarits de site) — **découvert seulement parce que quelqu'un a fini par
> le regarder**, pas parce qu'un test l'a signalé.

Ce fait n'est pas un défaut de la v1 à corriger dans la v2 — c'est **la seule
donnée d'entrée qui doit gouverner la décision de méthode** de la v2. Une
refonte qui produit une architecture plus élégante, plus agnostique, plus
extensible, mais qui répète le geste de bâtir loin du réel avant de la tester
en conditions réelles, aura corrigé la forme et reproduit le fond.

### 1.2 Greenfield ou transformation incrémentale — argumenté, pas par défaut

**Décision : transformation incrémentale, pas un greenfield.** Quatre
arguments, dans l'ordre de poids décroissant :

1. **La discipline de la v1 est un actif rare, pas une dette.** `vault_io.py`
   (écriture atomique, journal append-only), `api_io.py` (bus unique, budget
   bloquant avant l'appel, cache, grand livre), la règle des trois états
   (I22 — née de trois occurrences du même défaut en une journée), le DAG
   déterministe avec verrou exclusif : ce sont exactement les propriétés que
   `RECHERCHE-agentique.md` identifie comme **manquantes** dans la majorité
   des systèmes agentiques étudiés (non-reproductibilité §2.5, coût non borné
   §2.6, absence de vérificateur qui ré-exécute §2.1/§1.4). La v1 les a déjà,
   payées par des régressions réelles. Un greenfield les re-dériverait au prix
   fort, ou — plus probable sous pression de calendrier — ne les re-déciderait
   pas du tout.
2. **Le filet de 669 tests + 49 backend + 34 front est l'instrument qui a
   recalé quatre chantiers sur huit itérations** (`CLAUDE.md`, §gouvernance).
   Un greenfield démarre sans lui. Reconstruire un filet de cette densité en
   partant de zéro n'est pas gratuit, et le temps qu'il faut pour le
   reconstruire est exactement le temps pendant lequel le nouveau système
   n'a, lui non plus, jamais vu d'entreprise réelle.
3. **Les abstractions cibles (§2) sont atteignables par refactor, pas par
   réécriture.** `scoring.py::_resolve`/`_check_passes` sont déjà les
   primitives génériques du futur moteur de Verdict (elles servent déjà
   deux axes distincts — besoin et intention — depuis l'ADR 0004).
   `Collector`/`safe_collect` sont déjà à 80 % de la séparation
   Source/Signal qu'il reste à faire (§4.1). `secteur_id` (ADR 0003) est déjà
   la moitié de la clé de configuration à trois niveaux visée en §2.4.
   Le travail de généralisation est réel mais **localisé** : quelques modules
   à scinder, un fichier de catalogue de fournisseurs à créer, pas un système
   à repenser.
4. **Le risque principal n'est pas dans le code, il est dans l'absence de
   contact avec le réel** (§1.1). Un greenfield ne réduit pas ce risque d'un
   iota — il le retarde en ajoutant un cycle de reconstruction avant même de
   pouvoir le mesurer.

**Ce qui, en revanche, mérite une réécriture ciblée plutôt qu'un simple
refactor** — à nommer explicitement, pour ne pas prétendre que tout est
mineur :
- La couche de stockage (`vault_io.py`) doit gagner une interface
  (`MagasinIO`, §5.2) dont l'implémentation fichiers-plats-versionnés
  n'est plus la seule — c'est un ajout d'interface, pas une réécriture du
  comportement existant, qui continue de servir tel quel la verticale
  marketing.
- Le catalogue de fournisseurs (`MESUREURS_DEFAUT` en dur, C2) devient une
  vraie déclaration de données neuve — c'est du code additif, pas un
  remplacement.

### 1.3 À quel moment la v2 doit toucher des données réelles

**Réponse : avant toute généralisation au-delà du découplage pragmatique du
§4, pas à la fin de la refonte.** Concrètement, la séquence proposée (détaillée
en §6) place le contact avec le réel en **première étape exécutable**, pas en
jalon final :

1. **Étape 0 (ce document et sa validation).**
2. **Étape 1 — découplage pragmatique, sans généralisation prématurée** :
   renommer `gbp` en un nom agnostique (§4.1), sortir `MESUREURS_DEFAUT` en
   YAML (§4.1), ajouter le balayage générique du garde-fou (§4.2). Ce sont des
   changements **locaux**, review-able en une itération, qui ne demandent
   aucune deuxième verticale pour être validés.
3. **Étape 2 — le canari réel, sur la verticale marketing existante, avant
   toute deuxième verticale.** Phase D telle que déjà documentée dans
   `CLAUDE.md` (§Prochaines tâches) : clés SERP/Apollo réelles, tarifs
   relevés, vault initialisé, `run_pipeline.py --icp persona1-quebec` en
   conditions réelles sur un lot borné de PME HVAC québécoises réelles, un
   humain qui valide ou rejette réellement des fiches dans Obsidian.
   **Aucune généralisation supplémentaire (SourceAdapter multi-fournisseur
   complet, multi-tenant, deuxième verticale) ne démarre avant que cette
   étape ait produit des chiffres réels** : taux de couverture effectif,
   `motif_rejet` (Lot 0 de l'ADR 0004, aujourd'hui non fait — R8), coût réel
   par fiche, taux d'approbation humaine (R8, §3.5 de la recherche : une
   porte qui approuve > 95 % n'en est plus une).
4. **Étape 3 — généralisation informée**, une fois l'étape 2 terminée : c'est
   seulement à ce moment que le socle (§2), la seconde verticale (§2.5) et le
   multi-tenant (§5) se construisent — avec des chiffres réels en entrée
   plutôt qu'avec des hypothèses.

**Pourquoi cet ordre et pas l'inverse.** Construire le socle générique
d'abord, puis le brancher sur le réel, c'est exactement le geste que la v1 a
fait avec le mécanisme multi-industrie (ADR 0003) : un mécanisme prêt, zéro
second secteur écrit, une généricité non éprouvée. `HERITAGE-v1-…` le nomme
explicitement : « généricité sans deuxième cas d'usage = généricité non
prouvée ». La v2 ne doit pas répéter ce geste à l'échelle du système entier.

**Un garde-fou de méthode, pas seulement une intention.** Pour que ce
séquencement ne soit pas qu'une déclaration d'intention oubliée au premier
sprint, il devient lui-même un critère de revue : **aucune ADR de généralisation
(deuxième verticale, multi-tenant, SourceAdapter complet) n'est recevable en
revue tant que l'étape 2 n'a pas produit un rapport contenant au minimum
`motif_rejet` sur un échantillon réel et un coût réel non nul dans
`api_usage.log`.** C'est un critère binaire, vérifiable par
`grep -c motif_rejet vault/…` et par une valeur non nulle dans le grand livre —
donc conforme à la doctrine du §4.2 (vérifié par balayage, pas par promesse).

---

## 2. Le noyau agnostique

### 2.1 Ce que le mandat demande exactement, et la réponse en un paragraphe

*« Qu'est-ce qu'une source, un signal, une preuve, une règle, un verdict, un
livrable ? »* Le socle v2 est un moteur qui transforme des **Sources** en
**Preuves**, des Preuves en **Signaux**, des Signaux jugés par des **Règles**
en **Verdicts**, et des Verdicts en **Livrables**. Le marketing (diagnostic de
marque, signal_chaud, quadrant intention) est **une** instance de ce
pipeline, pas sa définition. Le test de cette conception est donné par le
mandat lui-même : une seconde verticale sans rapport doit être **entièrement**
décrite dans ces six termes, en configuration — §2.5 le démontre.

### 2.2 Les six abstractions

| Terme | Définition | Généralise (v1) | Où ça vit |
|---|---|---|---|
| **Source** | Une famille de besoin (F1…F8, §2.3) + une chaîne d'**adaptateurs** (`SourceAdapter`) qui savent la satisfaire, avec repli déclaré. Le fournisseur concret (Google, Zefix, Apollo, un crawl maison) est un détail d'implémentation d'un adaptateur, jamais un nom exposé au-dessus de cette couche. | `Collector` (mélange aujourd'hui sémantique métier + transport + fournisseur, C1/C2 de `FOURNISSEURS-DONNEES.md`) | `knowledge/fournisseurs.yaml` (déclaration), un module Python par adaptateur (implémentation, inévitable — voir §4.1) |
| **Signal** | Un emplacement nommé, agnostique du fournisseur, dans l'espace de noms `<famille>.<capacité>` (ex. `reputation_locale.verifie`, jamais `gbp.verified`). Porte l'**Observation** courante : `{valeur: ok\|echec\|inconnu, fiabilite, capture_le, perissable, expire_le, preuves: […]}`. | `signaux[collecteur][champ]` (`scoring.py::_resolve`) | Résolu à l'exécution ; déclaré (nom, famille) dans une **Grille** |
| **Preuve** | La capture brute, immuable, horodatée, qui justifie une Observation : `{source_adapter_id, url_ou_endpoint, extrait_ou_hash, capture_le, ttl}`. Jamais réécrite. Un audit contesté trois mois plus tard se rejoue depuis les Preuves, pas depuis une reformulation. | `VaultIO.append_historique()` — **posée, jamais exploitée** en v1 (dette explicite, `CLAUDE.md`) | `EvidenceStore` (généralisation, §4.3 ; R7) |
| **Règle** | Un check déclaratif : `{signal, operateur, valeur_attendue, poids_ou_priorite, nature: etat\|evenement, citable, gabarit_message}`, groupé en **Grille** (généralisation de « rubrique » — le mot « rubrique » porte une connotation d'audit marketing que le socle ne doit plus porter). | une ligne de `rubric_persona1.yaml` | `knowledge/grilles/<verticale_id>/<segment>.yaml` |
| **Verdict** | Le résultat **typé** de l'application d'une Grille aux Signaux courants d'une entité. Deux types reconnus par le socle, jamais un troisième format ad hoc par verticale : **Audit** (agrégation des règles `nature: etat` → score + `_couverture` + gaps + `mode_comparabilite` déclaré) et **Veille** (liste de règles `nature: evenement` → Événements datés, périssables, jamais agrégés). Un Verdict n'est **jamais** un nombre nu : c'est toujours le triplet (résultat structuré, couverture/consistance, provenance). | `Diagnostic` (score + failles) et `evenements_intention` (ADR 0004) — **déjà deux Verdicts distincts en v1, non nommés comme tels** | `VerdictEngine` (généralisation de `ScoringEngine` + `intent.py`) |
| **Livrable** | Le rendu d'un Verdict pour un humain ou un système consommateur, choisi dans un **catalogue socle fermé** de rendus génériques (rapport Markdown, export tabulaire, flux d'observation temps réel, notification interne), configuré par verticale. Toute Livrable marqué `communication_externe: true` applique la **politique de citation** (généralisation d'I24, §3 d'`INVARIANTS-v2.md`). | rapport Markdown (`serializers.py`), export Kemana (`export.py`), flux SSE GreenIT (`webapp/backend/greenit.py`) | catalogue socle + `knowledge/livrables/<verticale_id>.yaml` |

### 2.3 Socle vs verticale — ce qui ne bouge jamais, ce qui est configuration

| Couche | Contenu | Qui la modifie pour ajouter une verticale |
|---|---|---|
| **Socle (code, stable)** | `SourceAdapter` (ABC), `EvidenceStore`, `VerdictEngine` (primitives `_resolve`/`_check_passes` génériques), machine à états paramétrable, `MagasinIO`, `ApiIO` (bus réseau), catalogue de Livrables génériques, orchestrateur DAG, garde-fous par balayage | Personne — c'est le contrat que la verticale ne casse pas |
| **Catalogue socle (données socle, rarement modifiées)** | `knowledge/familles_besoin.yaml` (F1…F8, extensible), `knowledge/fournisseurs.yaml` (adaptateurs disponibles, indépendamment de qui les utilise) | L'équipe plateforme, quand un nouvel adaptateur générique (ex. un nouveau registre public) est ajouté — **jamais** une verticale seule |
| **Verticale (données, par verticale)** | `knowledge/grilles/<verticale_id>/*.yaml`, `knowledge/vocabulaire_<verticale_id>_*.yaml`, machine à états spécifique (si différente du défaut), mapping Verdict → Livrable, périmètres de ciblage (`perimetres/<verticale_id>-<segment>-<marche>.yaml`, généralisation d'`icp/*.yaml`) | La personne qui porte la verticale — **zéro code**, exactement le test demandé |

### 2.4 La clé de configuration à trois niveaux

L'ADR 0003 a posé `secteur_id` comme clé à deux niveaux
(`secteur_id-marche`, aujourd'hui uniquement `personaN-marché`). Le socle v2
ajoute un niveau au-dessus, sans casser le premier :

```
verticale_id / secteur_id (ou segment) / marche
```

- `verticale_id="diagnostic-marketing"` reste implicite pour tout ce qui
  existe déjà (`persona1-quebec` continue de se résoudre exactement comme
  aujourd'hui — **aucun fichier existant ne bouge**). C'est un ajout de
  préfixe optionnel, pas une migration.
- Une nouvelle verticale déclare son propre `verticale_id` dans
  `knowledge/verticales.yaml` (nom, description, type de Verdict par défaut,
  machine à états, catalogue de Livrables utilisés) — **un seul fichier
  neuf**, le reste suit le même schéma que §2.3.

### 2.5 Démonstration — une seconde verticale, sans rapport avec le marketing, en configuration

**Choix : veille de risque fournisseur (due diligence légère B2B).** Ce choix
n'est pas arbitraire : `FOURNISSEURS-DONNEES.md` (§2.4) l'a déjà nommé comme
extension naturelle des familles F1/F2/F3/F7 — « due diligence, veille
concurrentielle, recrutement, risque fournisseur ». Public visé : un service
achats/juridique d'une PME qui veut être alerté si un de ses fournisseurs
clés montre des signes de difficulté. **Aucun rapport avec le marketing** :
acheteur différent, question différente, cadence différente, forme de sortie
différente (alerte, pas audit).

**Ce que le socle fournit déjà, sans une ligne de code neuve pour cette
verticale :**

| Besoin de la verticale | Mécanisme socle réutilisé tel quel |
|---|---|
| Trouver l'univers de fournisseurs d'un secteur (F1/F2) | `SourceAdapter` registre public (Zefix, Sirene, REQ — mêmes adaptateurs que la verticale marketing, §4.1) |
| Suivre des signaux **datés et périssables** (avis de faillite, poursuite déposée, changement de dirigeant) plutôt qu'un score | **Verdict de type Veille** — c'est le même mécanisme que l'axe intention (ADR 0004), déjà construit pour la verticale marketing, jamais spécifique à elle |
| Ne jamais transformer un événement daté en moyenne | Le socle interdit **structurellement** d'agréger une règle `nature: evenement` dans un score (§ « I23 généralisé » d'`INVARIANTS-v2.md`) — ce n'est pas une discipline à réapprendre par verticale, c'est un interdit du moteur |
| Notifier l'opératrice sans attendre un export en fin de run | **Flux d'observation temps réel** — réutilisation directe du mécanisme SSE déjà construit pour l'observabilité GreenIT (`/api/greenit/stream`, `webapp/backend/greenit.py`), généralisé en un flux socle générique alimenté par n'importe quelle source d'événements typés, pas seulement le grand livre de coûts |
| Rester lecture seule côté cockpit, ne jamais agir sur le fournisseur surveillé | Machine à états dédiée déclarée en YAML (§2.6), avec le même mécanisme de porte humaine que la v1, appliqué à un graphe d'états différent |

**Les seuls fichiers neufs pour livrer cette verticale :**

```
knowledge/verticales.yaml                          # + une entrée "veille-fournisseurs"
knowledge/grilles/veille-fournisseurs/pme-manufacturier.yaml
knowledge/vocabulaire_veille-fournisseurs_signaux.yaml
knowledge/machines_etats/veille-fournisseurs.yaml
perimetres/veille-fournisseurs-pme-manufacturier-quebec.yaml
knowledge/livrables/veille-fournisseurs.yaml        # mapping Verdict → flux SSE + export tabulaire
```

Zéro fichier `.py`. Un seul adaptateur potentiellement neuf (un registre de
poursuites/faillites, s'il n'est pas déjà couvert par un adaptateur F7
existant) — et même celui-ci suit un ABC déjà présent dans le socle, donc son
volume de code est celui d'un connecteur, pas d'une fonctionnalité.

**Sketch illustratif de la Grille** (grandeur réelle simplifiée, pas du code
livrable — une donnée) :

```yaml
# knowledge/grilles/veille-fournisseurs/pme-manufacturier.yaml
grille_id: veille-fournisseurs-pme-manufacturier
type_verdict: veille          # jamais audit — aucun score de "risque global"
regles:
  - signal: registre_public.statut_juridique_change
    op: est_egal
    valeur_attendue: "en_liquidation"
    nature: evenement
    priorite: critique
    citable: false             # usage interne seulement, jamais montré au fournisseur surveillé
    gabarit_message: "Statut juridique passé à {valeur} le {date_evenement}"
  - signal: activite_datee.depart_dirigeant_cle
    op: est_vrai
    nature: evenement
    priorite: haute
    citable: false
  - signal: firmographie.age_annees
    op: exists
    nature: etat                # état, pas un événement — n'alimente jamais la Veille
    priorite: contextuelle
```

**Ce que cette démonstration prouve, et ce qu'elle ne prouve pas.** Elle
prouve que les six abstractions (§2.2) ne portent aucune hypothèse
marketing — machine à états, type de Verdict, flux de notification sont tous
réutilisés tels quels. Elle **ne prouve pas** que le socle est bon pour
*toute* verticale OSINT imaginable : elle prouve qu'il l'est pour une
verticale du même profil général (entité B2B, signaux publics, cadence
lente-à-moyenne). `RECHERCHE-agentique.md` (§7.10) le dit explicitement :
« aucune étude ne compare le coût et la performance d'un socle générique
contre des systèmes dédiés » — cette démonstration est un argument
d'ingénierie, **pas** une preuve empirique, et elle doit être **rejouée avec
un vrai second client** avant d'être crue (§1.3, étape 3).

### 2.6 La machine à états devient une donnée, le principe qu'elle sert reste un invariant

Généralisation de I7. `knowledge/machines_etats/<verticale_id>.yaml` déclare
les états, les transitions, et pour chacune deux drapeaux :
`porte_humaine: bool` et `action_irreversible_sur_tiers: bool`. Le socle
interdit structurellement à tout agent de déclencher une transition marquée
`porte_humaine: true` — c'est la même garantie qu'en v1
(`TRANSITIONS_AGENT ⊂ TRANSITIONS_LEGALES`), généralisée à un graphe qui n'est
plus fixé en Python. Détail complet, y compris le mécanisme de vérification
par balayage : `INVARIANTS-v2.md`, « I7 généralisé ».

---

## 3. Deux tensions tranchées

Détail complet, verdict par les 24 invariants : `docs/v2/INVARIANTS-v2.md`.
Cette section traite en profondeur les deux tensions que le mandat interdit
de contourner.

### 3.1 I17 — « le LLM rédige, il ne collecte jamais »

**Tension.** `HERITAGE-v1-…` la formule sans détour : la recherche pousse
vers des agents qui choisissent leurs outils, et l'adoption de MCP en fait
une tendance de fait (`RECHERCHE-agentique.md` §6.4 : 41 % d'organisations en
production limitée ou large avec des serveurs MCP `[COMMERCIAL]`, mais
registre officiel à ~9 600 serveurs `[2026 — NON VÉRIFIABLE ICI]`, chiffre le
moins mauvais de la section).

**Ce qui est établi, et qui pèse plus lourd que la tendance.**
`RECHERCHE-agentique.md` §2.4 : l'injection de prompt (directe et indirecte)
est en tête de l'OWASP LLM Top 10 2025 ; InjecAgent et Agent Security Bench
rapportent des taux de succès d'attaque **supérieurs à 60 %** en scénarios
multi-outils réalistes ; PoisonedRAG dépasse **90 %**. **Aucune défense
générale n'est démontrée.** Le seul consensus rapporté est architectural :
« ne pas donner à un agent qui lit du contenu non fiable les moyens d'agir de
façon irréversible » (§2.4, position OWASP). Un système OSINT est, par
construction, **exposé en permanence à du contenu tiers non fiable** — c'est
la matière première même du produit.

**Décision : la séparation collecte/rédaction est reclassée comme un
CONTRÔLE DE SÉCURITÉ (R5), pas une élégance de style, et elle est
CONSERVÉE dans sa forme dure — avec une seule porte d'entrée étroite pour
l'agentivité de choix d'outils, pas une exception générale.**

Concrètement :

1. **Le LLM n'appelle jamais directement le réseau ni n'écrit jamais
   directement le magasin.** Invariant inchangé dans sa lettre — c'est
   `api_io.py`/`vault_io.py` généralisés (`ApiIO`/`MagasinIO`).
2. **Un nœud PEUT être déclaré `agentivite.active: true`** (§3.2) — mais
   uniquement pour **choisir parmi un petit catalogue d'outils déjà
   passés par le bus, en lecture seule, pré-déclarés dans la Grille ou le
   manifeste du nœud.** L'agent ne peut ni inventer un endpoint, ni écrire,
   ni déclencher une action à effet externe. Le « choix d'outil » se limite
   à *dans quel ordre lire des Signaux déjà collectés de façon
   déterministe*, jamais *quoi fetcher*.
3. **Tout contenu qui a transité par un LLM et qui influence un Verdict doit
   être traçable jusqu'à des Preuves établies avant l'étape LLM.** Le
   contrôle de grounding (Palier 2 de l'ADR 0001, toujours prévu) reste
   déterministe et en aval, jamais un second LLM qui « juge » le premier
   (§3.3 de la recherche : un juge LLM n'est fiable que sur une
   classification fermée calibrée, jamais sur une appréciation ouverte).

**Ce que ça règle, et ce que ça ne règle pas.** Ça règle la tension en la
refusant : MCP est adopté comme **frontière d'intégration** (R9), pas comme
accès général. Un serveur MCP non classifié « interne, vérifié » ne peut
jamais alimenter un chemin d'écriture — ça reste vrai même si l'écosystème
MCP grandit. Ça ne règle pas le risque zéro : un outil de lecture peut encore
renvoyer du contenu empoisonné qui biaise un choix d'ordre de lecture. C'est
un risque résiduel accepté, borné par l'absence totale de capacité d'écriture
ou de fetch libre côté LLM — noté en §7.

### 3.2 I9/I8 — orchestration déterministe vs planificateur LLM

**Tension.** L'ADR 0001 a refusé un superviseur-planificateur LLM
(coût, non-déterminisme, charge cognitive). `RECHERCHE-agentique.md` §1.5
établit que **la supériorité du multi-agents sur le mono-agent, à budget de
calcul égal, n'est pas établie** — et va plus loin : plusieurs évaluations
indépendantes (Smit et al. ICML 2024, Wang et al. arXiv 2402.18272, un
travail plus récent normalisant le budget sur FRAMES/MuSiQue) concluent dans
le sens **inverse** de la thèse commerciale. Le multiplicateur de coût
rapporté est **~15× tokens** pour un système multi-agents `[RÉSUMÉ-OUTIL]`.

**Décision : le DAG reste la colonne vertébrale, intégralement
déterministe au niveau de l'ordonnancement des nœuds. Une agentivité locale,
bornée et journalisée est admise À L'INTÉRIEUR d'un nœud déclaré, jamais
au niveau du graphe.**

Argument, en trois temps :

1. **Le mécanisme établi (§1.6, §2.5 de la recherche) porte sur le couplage
   planification/exécution** : coupler les deux introduit une variabilité de
   comportement d'exécution qui casse reproductibilité et prévisibilité de
   coût. Ce mécanisme s'applique à *qui décide de la séquence des étapes*,
   pas à *un choix borné à l'intérieur d'une étape déjà fixée*. Le DAG reste
   la seule autorité sur « quel nœud s'exécute après quel autre » — c'est ce
   qui rend le manifeste de run (`.cache/orchestrator/<run_id>.json`)
   reconstituable et le grand livre corrélable, propriétés que la recherche
   valide indirectement en soulignant leur absence ailleurs (§2.5).
2. **Le multiplicateur de coût (~15×) s'applique au multi-agents qui
   raisonnent ensemble**, pas à un LLM qui choisit parmi trois lectures déjà
   en cache. Un nœud « agentivité bornée » (§3.1, point 2) n'ajoute pas de
   round-trips de raisonnement inter-agents : il ajoute au maximum
   `iterations_max` appels supplémentaires au même bus, avec le même budget
   et la même journalisation qu'un appel non-agentique.
3. **Ce qui justifie une agentivité locale n'est jamais « les agents
   raisonnent mieux ensemble »** (§7.2 de la recherche : cette justification
   n'a aucun appui) — **c'est un besoin opérationnel concret et déclaré**,
   par exemple : sur une entité pour laquelle deux registres publics
   divergent sur le statut juridique, laisser un nœud choisir d'interroger un
   troisième registre plutôt que de coder en dur une règle de priorité qui
   ne généraliserait pas entre marchés. C'est une **spécialisation d'outils**
   au sens de la recherche (§1.5, justification reconnue valide), pas une
   promesse de raisonnement supérieur.

**Ce que ça règle, et ce que ça ne règle pas.** Ça évite de réintroduire le
superviseur-planificateur refusé par l'ADR 0001, en le distinguant nettement
de l'agentivité bornée. Ça ne règle pas l'ampleur de l'avantage d'une
agentivité locale — `RECHERCHE-agentique.md` §7.3 est explicite : aucune
mesure chiffrée de l'écart de taux d'échec entre planification déterministe
et pilotée par LLM n'a pu être lue. **Toute agentivité bornée introduite doit
donc être mesurée en `pass^k` (R3, §3.3 ci-dessous) avant d'être généralisée**
— elle démarre en YAML `agentivite.active: false` par défaut sur tout nœud
neuf, activée nœud par nœud après mesure, jamais par défaut.

**Convergence notable entre les deux tensions.** Les deux résolutions
(§3.1 et §3.2) aboutissent au même mécanisme concret — agentivité bornée,
outils pré-vetted, lecture seule, journalisée, rejouable — depuis deux
raisonnements indépendants (sécurité pour I17, reproductibilité/coût pour
I9). Ce n'est pas une coïncidence de rédaction : c'est le signe qu'un seul
et même dispositif (§3.3) répond aux deux préoccupations à la fois, ce qui
est un bon indicateur de conception plutôt qu'un hasard heureux.

### 3.3 Le dispositif commun : « agentivité bornée »

Nouveau concept socle, déclaré en donnée, jamais en dur :

```yaml
# manifeste d'un nœud du DAG (extrait illustratif, pas du code livrable)
agentivite:
  active: true
  outils_autorises: [lire_signal_registre_a, lire_signal_registre_b]  # tous déjà derrière ApiIO/EvidenceStore, lecture seule
  budget_tokens_max: 4000
  iterations_max: 3
  critere_arret: "reponse conforme au schema VerdictPartiel"          # déterministe, vérifiable
  rejouable_depuis_cache: true
```

Cinq bornes obligatoires pour qu'un nœud soit déployable — un nœud sans les
cinq n'est pas déployable, point vérifié par validation de schéma
(`AgentiviteConfig`, Pydantic) au chargement du DAG, pas par convention.
Détail de vérification : `INVARIANTS-v2.md`, invariant « agentivité bornée ».

---

## 4. Deux défauts structurels corrigés par conception

### 4.1 Défaut 1 — un nom de produit Google figé dans la configuration métier

**Constat vérifié** (`FOURNISSEURS-DONNEES.md`, C1) : `rubric_persona1.yaml`
déclare `signal: gbp.verified`. `gbp` est un nom de produit, pas un concept
métier. Remplacer Google Places par un autre fournisseur casse toutes les
rubriques de tous les secteurs, sans exception.

**Conception cible : scinder `Collector` en deux couches, avec un catalogue
de fournisseurs en donnée (C2).**

*Couche haute — sémantique métier, invariable par fournisseur.* Une
**Capacité** est un nom agnostique dans l'espace `<famille>.<capacite>` :
`reputation_locale.verifie` remplace `gbp.verified`,
`reputation_locale.a_des_photos` remplace `gbp.has_photos`,
`reputation_locale.nombre_avis` remplace `reviews.count`. C'est **la seule**
chose qu'une Grille a le droit de référencer.

*Couche basse — `SourceAdapter`, un fournisseur, un transport.*

```
# plan, pas du code livrable
class SourceAdapter(ABC):
    """Un fournisseur concret pour UNE OU PLUSIEURS Capacités d'UNE famille."""
    adapter_id: str          # ex. "google_places_new", "zefix", "req_quebec"
    famille: str              # ex. "reputation_locale", "firmographie"
    capacites_couvertes: list[str]

    @abstractmethod
    def fetch(self, entite: Entite, capacite: str, api_io: ApiIO) -> ObservationBrute: ...
```

*Le catalogue, en donnée (corrige C2 explicitement).*

```yaml
# knowledge/fournisseurs.yaml — plan, pas la valeur finale
reputation_locale:
  adaptateurs:
    - id: google_places_new
      priorite: 1
      capacites: [verifie, a_des_photos, nombre_avis, note_moyenne]
      unites: { requetes: 1.0 }
      retention_max_jours: 30        # corrige C3 — lu et appliqué par le bus, §4.1 point suivant
      fiabilite_declaree: B          # échelle Admiralty-inspirée, décorrélée du signal (§I22, INVARIANTS-v2.md)
    - id: yelp_fusion
      priorite: 2                    # repli si google_places_new indisponible/budget épuisé
      capacites: [note_moyenne, nombre_avis]
```

**Ce que ce découplage corrige, précisément :**
- **C1 résolu** : plus aucun nom de fournisseur dans une Grille. La
  substitution de Google Places par un autre adaptateur ne touche **aucune**
  Grille — seul `fournisseurs.yaml` change.
- **C2 résolu** : `MESUREURS_DEFAUT` (aujourd'hui un dict Python en dur,
  `api_io.py:54-60`) devient une lecture de `fournisseurs.yaml`. Ajouter un
  fournisseur = ajouter une entrée YAML + un module d'adaptateur (code
  inévitable, c'est un connecteur réseau réel) — mais **jamais** une
  modification du bus lui-même.
- **C3 devient corrigeable structurellement** : la rétention (`retention_max_jours`)
  est désormais une propriété du fournisseur, lue par le même mécanisme que
  le budget (`ApiIO`), pas un paramètre déclaré deux fois et lu nulle part.
  C'est la même remarque que fait `FOURNISSEURS-DONNEES.md` §6.3(3) : « le
  bus est déjà le bon endroit, c'est le pendant naturel du budget ».
- **Migration en une passe, testée une fois** : le renommage `gbp.*` →
  `reputation_locale.*` est une rupture de contrat sur les rubriques
  existantes. `FOURNISSEURS-DONNEES.md` (§6.3.1) le dit sans détour : « à
  faire une seule fois, dans la refonte v2, avec un test de non-régression
  sur `signal_chaud` ». Chaque secteur écrit aujourd'hui avec `gbp.*` ancre
  un peu plus le nom du produit ; le coût de la migration ne fait que
  croître si on attend.

### 4.2 Défaut 2 — un invariant qui exige une action manuelle sera violé

**Constat vérifié** (`invariants.md`, note sur I4 ; `HERITAGE-v1-…`, point 5) :
la règle « tout nouveau module de ce type doit être ajouté à la liste du
garde-fou » a été violée cinq fois (`greenit.py`, `intent.py`,
`serializers.py`, `legitimite.py`, `_decay.py` absents de
`_check_garde_fous_bus`). L'invariant a tenu **par accident** — un second
filet générique en `rglob` existait déjà et a rattrapé l'oubli — pas par le
mécanisme annoncé.

**Principe de conception, appliqué systématiquement à tout invariant v2
proposé dans ce document et dans `INVARIANTS-v2.md` :**

> **Ne jamais maintenir une liste de "quoi surveiller" — elle grossit à
> chaque fichier ajouté et se désynchronise silencieusement. Toujours
> maintenir, à la place, une liste courte et stable de "ce qui est interdit"
> (primitives, imports, appels), et balayer TOUT le code source à chaque
> vérification, sans exception nominative.**

Application concrète pour chaque famille de garde-fou v2 :

| Garde-fou | Ce qu'on NE fait pas (liste qui pourrit) | Ce qu'on fait (balayage stable) |
|---|---|---|
| Un seul chemin réseau | Lister « les modules qui ne doivent pas importer `requests`/`anthropic` » | `rglob("**/*.py")` sur tout le socle, exclusion unique du module bus lui-même, appliqué à chaque commit |
| Un seul écrivain du magasin | Lister « les modules qui ne doivent pas appeler le pilote de stockage » | `rglob` + recherche des symboles de pilote bas niveau (`os.replace`, `sqlite3.connect`, `boto3.client`, …) déclarés dans une liste **courte et stable** de primitives interdites, hors du module magasin lui-même |
| Aucun nom de fournisseur dans une Grille | Lister « les Grilles à vérifier » | Balayage de **tous** les fichiers sous `knowledge/grilles/**` contre la liste des `adapter_id` déclarés dans `fournisseurs.yaml` — un `adapter_id` trouvé dans une Grille est un échec |
| Agentivité bornée respectée | Lister « les nœuds agentiques à vérifier » | Validation de schéma (`AgentiviteConfig`) appliquée à **chaque** nœud du DAG au chargement, pas à une liste de nœuds réputés agentiques |

Ce principe est lui-même formulé comme un méta-invariant vérifiable dans
`INVARIANTS-v2.md`, §0 — pas seulement énoncé ici en prose.

---

## 5. Scalabilité et multi-tenant

### 5.1 Isolation par tenant

**Ce qui change maintenant.** `tenant_id` devient un champ obligatoire de
**tout** objet du socle dès la première ligne de code de la refonte —
`Entite`, `Observation`, `Preuve`, `Verdict`, `LedgerEntry`, verrou de run.
**[RECOMMANDÉ], jugement d'ingénierie, pas issu de la littérature lue** (le
mandat de `RECHERCHE-agentique.md` ne couvre pas l'ingénierie SaaS
multi-tenant) : retrofiter un `tenant_id` après coup sur des données
existantes est le type de migration la plus coûteuse en pratique — c'est un
fait d'ingénierie ordinaire, pas un résultat de recherche, et il est signalé
comme tel.

**Ce qui reste simple.** L'isolation n'exige **pas** de bases de données
séparées par tenant dès le premier client payant. Une colonne/clé
`tenant_id` filtrée à chaque requête, avec un test qui vérifie qu'aucune
requête ne peut omettre ce filtre (balayage des points d'accès au magasin,
§4.2), suffit tant que le volume reste celui d'un pilote élargi. La
séparation physique (schémas distincts, bases distinctes) est un palier
ultérieur, conditionné (§5.5).

### 5.2 Magasin de données

**Ce qui change maintenant.** `VaultIO` devient une implémentation derrière
une interface `MagasinIO` :

```
# plan, pas du code livrable
class MagasinIO(Protocol):
    def write_fiche(self, tenant_id: str, entite: Entite, contenu: FicheProspect) -> None: ...
    def transition(self, tenant_id: str, entite_id: str, cible: str, acteur: str) -> None: ...
    def query(self, tenant_id: str, **filtres) -> Iterator[FicheProspect]: ...
    # … signatures inchangées dans leur esprit, tenant_id en préfixe partout
```

**Ce qui reste simple, délibérément.** L'implémentation fichiers-plats +
`os.replace()` + journal JSONL **continue de servir la verticale marketing
telle quelle**, sous forme `tenants/<tenant_id>/vault/…` — **pas** de
migration vers une base de données au premier client. C'est exactement le
choix déjà pris et documenté pour le Palier 3 de l'ADR 0001 (« fragments
multi-tenant, conditionnés à un seuil de tenants payants défini à
l'avance ») : ce document **confirme** ce choix plutôt que de le rejuger.
Le vault reste la source de vérité, jamais un read-model — invariant
inchangé.

**Le déclencheur de bascule doit être écrit avant d'être atteint, pas décidé
sous pression.** [À CALIBRER] — nombre de tenants payants et/ou volume
d'écritures/jour au-delà duquel `MagasinIO` bascule vers un backend
transactionnel (ex. Postgres avec row-level security par `tenant_id`). Ce
seuil n'est **pas** fixé par ce document — le fixer sans donnée réelle serait
répéter l'erreur nommée en §1.1.

### 5.3 Mesure du coût par tenant

**Ce qui change maintenant.** `LedgerEntry` gagne un champ `tenant_id`
(rétro-compatible par défaut `None`, même patron que les 7 champs GreenIT
ajoutés sans migration en v1). `ApiIO` devient instanciée **par run de
tenant** — généralisation, pas abandon, d'I11 : toujours une seule instance
par run, mais « run » est maintenant scopé à un tenant. Le budget devient une
**chaîne à deux garde-fous** : précontrôle du budget du tenant (son forfait,
son plan) **puis** précontrôle du budget global du fournisseur (protection
plateforme) — les deux avant l'appel, jamais après (I6 inchangé dans sa
lettre).

**Ce qui reste simple.** Un seul grand livre physique (`api_usage.log`
généralisé, partitionnable par tenant à la lecture, pas nécessairement à
l'écriture) suffit tant que le volume d'écriture reste modeste — pas besoin
d'un système de streaming d'événements dédié pour un pilote élargi. La
duplication de calcul déjà identifiée en v1 (`usage.py` vs
`webapp/backend/greenit.py`, tenue par un test de convergence croisée) doit
être résolue **avant** la duplication, pas après : une seule fonction
d'agrégation, deux vues — c'est une dette déjà nommée en v1, qu'il ne faut
pas reporter dans la v2.

### 5.4 Exécution concurrente

**Ce qui change maintenant.** Le verrou de run (`os.open(O_CREAT|O_EXCL)`,
aujourd'hui global à tout le système) devient scopé `(tenant_id, cible)` —
même primitive système, même sémantique (exclusif, libéré en
`try/finally`), juste un chemin de fichier qui inclut le tenant. Deux
tenants s'exécutent en parallèle sans se gêner ; au sein d'un même tenant,
l'exécution reste séquentielle (inchangé).

**Ce qui reste simple, délibérément — et c'est le point le plus important
de cette section.** **Aucun orchestrateur distribué (Airflow, Temporal, un
bus de messages) n'est nécessaire au démarrage.** Chaque tenant a son propre
DAG, son propre verrou, sa propre file d'attente légère (une table ou un
répertoire « runs en attente », pas un broker). La montée en charge se fait
par **réplication horizontale du même processus léger**, un worker qui prend
un tenant à la fois dans la file — pas par une réécriture de l'orchestrateur.
**[RECOMMANDÉ]** : introduire un vrai orchestrateur distribué seulement
quand la latence de la file d'attente devient mesurée et gênante, jamais par
anticipation. C'est le pendant, côté infrastructure, du principe déjà tenu
côté produit par le Palier 3 gelé de l'ADR 0001.

### 5.5 Synthèse — ce qui doit changer maintenant vs ce qui peut attendre un seuil mesuré

| Dimension | Maintenant (dès la refonte) | Attend un seuil mesuré [À CALIBRER] |
|---|---|---|
| `tenant_id` sur tous les objets | Oui — coûteux à retrofiter | — |
| Interface `MagasinIO` (découplage fichiers/DB) | Oui — l'interface, pas la migration | Bascule vers un backend transactionnel |
| Budget à deux niveaux (tenant + fournisseur) | Oui | — |
| Verrou scopé par tenant | Oui | — |
| Base de données multi-tenant physique | Non | Seuil de tenants payants ou de volume d'écriture |
| Orchestrateur distribué | Non | Latence de file mesurée et gênante |
| Facturation au résultat (R10) | Non — le résultat n'est pas mesurable (§7.1 de la recherche) | Mesure de lift incrémental (R8, Lot 0) disponible |

---

## 6. Plan d'exécution séquencé

Ce plan est un enchaînement d'étapes exécutables par `agent-dev-python`,
chacune review-able indépendamment. Il concrétise la séquence de §1.3.

**Étape 1 — découplage pragmatique (aucune deuxième verticale, aucun
multi-tenant).**
1. `knowledge/fournisseurs.yaml` : extraire `MESUREURS_DEFAUT`
   (`api_io.py:54-60`) en données. Tests : le comportement de mesure des
   unités reste identique bit-à-bit pour les quatre fournisseurs existants
   (test de non-régression sur `test_api_io.py`).
2. Renommer `gbp.*` → `reputation_locale.*` dans `rubric_persona1.yaml` et le
   module `gbp.py` → un nom agnostique (ex. `reputation_locale_places.py`
   ou, mieux, fusion dans un futur `SourceAdapter` — cette fusion peut
   attendre l'étape 3). Test bloquant : `signal_chaud` identique avant/après
   sur le banc d'essai existant (`scripts/benchmark_intention.py`).
3. Garde-fou par balayage (§4.2) : remplacer/compléter
   `_check_garde_fous_bus` par un balayage `rglob` générique déjà présent en
   filet (`test_requests_pas_importe_niveau_module_hors_api_io`) — le
   promouvoir en mécanisme principal, documenté comme tel, la liste
   nominative devenant strictement informative.
4. Ajouter `cache_ttl_jours` réellement lu et appliqué dans
   `ApiIO._lire_cache()` (corrige C3, indépendant de tout choix de
   fournisseur — déjà recommandé par `FOURNISSEURS-DONNEES.md` §7.3).

**Étape 2 — le canari réel (Phase D, déjà planifiée dans `CLAUDE.md`, non
redécrite ici).** Condition de sortie vérifiable, §1.3 : `motif_rejet`
présent sur un échantillon réel, coût réel non nul dans `api_usage.log`.

**Étape 3 — généralisation informée, seulement après l'étape 2.**
5. `SourceAdapter` (ABC) + scission de `Collector` en Capacité/Adaptateur
   (§4.1), informée par ce qui s'est réellement passé en étape 2 (quelles
   Capacités ont réellement compté, lesquelles étaient du bruit).
6. `EvidenceStore` : exploitation réelle d'`append_historique()` (R7),
   capture de la Preuve horodatée, pas seulement du signal dérivé.
7. Régime de revue à deux vitesses (R3) : séparer, dans la porte de
   cohérence à 97 %, les assertions déterministes (une exécution suffit) des
   assertions touchant une sortie LLM (`pass^k`, k [À CALIBRER] ≥ 3),
   contre des entrées gelées grâce à l'`EvidenceStore` de l'étape 6.
8. `tenant_id` (§5.1-5.3), `MagasinIO` (§5.2), verrou scopé (§5.4).
9. Deuxième verticale réelle (pas la démonstration §2.5, un vrai second
   client), pour éprouver la généricité — sans elle, la promesse
   d'agnosticité reste non prouvée (§1.1, leçon #2 de `HERITAGE-v1-…`).

---

## 7. Risques résiduels

Nommés explicitement, pas dissimulés dans l'enthousiasme de la conception.

1. **L'agentivité bornée (§3.3) reste un vecteur résiduel d'injection
   indirecte**, même limitée à la lecture : un outil de lecture peut renvoyer
   du contenu qui biaise l'ordre ou le choix des lectures suivantes, même
   sans capacité d'écriture. Le risque est borné, pas nul. Mitigation
   prévue : aucun Verdict ne dépend de la sortie brute du LLM, seulement des
   Preuves qu'il a fini par sélectionner, elles-mêmes vérifiables
   indépendamment — mais ceci n'a **pas** été testé sous attaque réelle et
   devrait l'être avant toute mise en production sur une verticale à enjeu
   élevé.
2. **La comparabilité des Verdicts de type Audit reste un problème ouvert**
   (§2.4 de ce document, `mode_comparabilite` [À CALIBRER]) : le socle rend
   le problème *visible* (couverture publiée) mais ne le *résout* pas. Un
   Verdict Audit à couverture 40 % et un autre à 90 % ne sont toujours pas
   comparables sans une décision produit explicite par verticale.
3. **La démonstration de la seconde verticale (§2.5) est un exercice de
   configuration, pas un client réel.** Elle peut échouer en pratique sur des
   dimensions non anticipées (une famille F9 non couverte par F1…F8, un type
   de Verdict qui n'est ni Audit ni Veille). C'est un pari nommé, pas une
   preuve — cohérent avec le constat §7.10 de `RECHERCHE-agentique.md`.
4. **Le séquencement (§1.3) dépend d'une discipline organisationnelle**, pas
   seulement d'un mécanisme technique : rien n'empêche techniquement de
   construire le multi-tenant avant le canari réel si personne ne fait
   respecter le critère de sortie de l'étape 2. Le critère est vérifiable
   (`grep`, `api_usage.log` non nul) mais **quelqu'un doit l'exécuter** avant
   d'accepter une ADR de généralisation.
5. **Le régime de revue à deux vitesses (R3) introduit un `k` arbitraire**
   ([À CALIBRER], proposé ≥ 3 sans appui empirique) — un mauvais choix de
   `k` donnerait une fausse impression de rigueur sur les assertions
   touchant une sortie LLM.
6. **La clause Apollo (§3.2 de `FOURNISSEURS-DONNEES.md`) reste non
   tranchée juridiquement.** Ce document ne prend pas position sur son usage
   futur — la vérification juridique (priorité 1 du §8 de
   `FOURNISSEURS-DONNEES.md`) reste un préalable bloquant, hors du périmètre
   de cette conception.
