# Approvisionnement en données — challenge des fournisseurs actuels et architecture cible

> **Statut : note d'analyse pour la refonte SaaS (v2). Aucune décision engagée.**
> Rédigé le **2026-08-04**. Portée : `diagnostic/api_io.py`, `diagnostic/collectors/`,
> `diagnostic/discovery.py`, `diagnostic/enrichment.py`, `knowledge/api_pricing.yaml`.
>
> Ce document ne modifie aucun fichier hors `docs/v2/`. Il ne remplace ni l'ADR 0001
> (bus unique) ni l'ADR 0003 (`secteur_id` comme clé de configuration) : il prépare
> une décision qui devra, elle, passer par une ADR.

---

## 0. Méthode, et ce qu'elle vaut

### 0.1 Ce qui a pu être vérifié

| Type d'affirmation | Statut | Comment le relire |
|---|---|---|
| Faits sur le code de ce dépôt | **VÉRIFIÉ** | chemin + numéro de ligne donnés, relisibles à la main |
| Tarifs et clauses de fournisseurs | **NON VÉRIFIÉ À LA SOURCE** | voir 0.2 |

### 0.2 L'accès web direct est bloqué dans cet environnement — conséquence sur tout ce document

`WebFetch` a renvoyé **HTTP 403 sur toutes les URL tentées**, y compris des sites
sans protection anti-robot (`en.wikipedia.org`, `data.gouv.fr`). Le diagnostic du
proxy le confirme :

```
curl -sS "$HTTPS_PROXY/__agentproxy/status"
  "recentRelayFailures": [
    { "kind": "connect_rejected",
      "detail": "gateway answered 403 to CONNECT (policy denial or upstream failure)",
      "host": "arxiv.org:443" },
    { "kind": "connect_rejected", …, "host": "example.com:443" } ]
```

Ce n'est pas un blocage par les fournisseurs : c'est la **politique d'egress de la
session** qui refuse la sortie. Le `README.md` du proxy est explicite — « do not
retry or route around it — report the blocked host ». Aucune tentative de
contournement n'a été faite.

**Conséquence, à lire avant tout chiffre de ce document :**

- **Aucune page tarifaire officielle n'a été ouverte.** Ni `serpapi.com/pricing`,
  ni `apollo.io/pricing`, ni `mapsplatform.google.com/pricing`, ni
  `cloud.google.com/maps-platform/terms/maps-service-terms`, ni
  `apollo.io/terms/api`. **Toutes marquées `[NON LU]`.**
- Les seuls éléments disponibles proviennent de **`WebSearch`**, qui restitue des
  résumés de pages tierces (blogs comparatifs, agrégateurs de prix). C'est une
  **source secondaire**, souvent commercialement intéressée (la moitié des pages
  citées vendent un produit concurrent de celui qu'elles chiffrent).
- **Tout tarif ci-dessous est donc `[NON VÉRIFIÉ]`**, daté du 2026-08-04, et ne
  doit **jamais** être recopié dans `knowledge/api_pricing.yaml`. Ce fichier
  attend un relevé de première main, avec `releve_le` renseigné — c'est
  exactement la Phase D, et ce document ne la remplace pas.
- Les clauses juridiques (ToS) sont dans le même cas. Elles sont rapportées ici
  comme **pistes de vérification prioritaires pour un juriste**, jamais comme
  un état du droit établi. Aucune n'a été lue dans le texte du contrat.

C'est le même régime de preuve que la note de recherche documentaire de l'ADR
0004, où `WebFetch` avait déjà reçu un 403 systématique. Le précédent existe et
il est traité comme normal.

### 0.3 Ce que ce document ne peut pas faire

**Il ne peut comparer aucune option au coût actuel, parce qu'il n'y a pas de coût
actuel.** `knowledge/api_pricing.yaml` (lu le 2026-08-04) a :

- `releve_le: null` (ligne 17) ;
- `prix_par_unite: 0.0` pour **tous** les endpoints de **tous** les fournisseurs
  (lignes 28-66) ;
- `budgets.serp.unites_max.requetes: 0` et `budgets.apollo.unites_max.credits: 0`
  (lignes 74-81).

Aucun tarif réel n'a jamais été relevé dans ce dépôt. Toute phrase du type
« X coûte moins cher que la solution actuelle » serait une invention.
Le seul chiffre honnête aujourd'hui est : **coût actuel inconnu, budget engagé nul.**

---

## 1. AS-IS — ce que le code consomme réellement

Établi par lecture du code, pas par lecture de la documentation.

### 1.1 Les trois appels sortants

| Fournisseur | Appelant | Endpoint réellement appelé | Unité comptée |
|---|---|---|---|
| SERP | `diagnostic/discovery.py:92-103` | `GET https://serpapi.com/search` (`engine=google`) | `{"requetes": 1.0}` |
| Apollo | `diagnostic/enrichment.py:91-105` | `POST https://api.apollo.io/v1/people/search` | `{"credits": 1.0}` |
| Google Places | `gbp.py:50-56`, `reviews.py:97-117` | `GET https://maps.googleapis.com/maps/api/place/textsearch/json` et `…/place/details/json` | `{"requetes": 1.0}` |

Plus un quatrième flux non contractuel avec un fournisseur : le **crawl propre**
(`website.py`), qui fetch la page d'accueil et, depuis l'ADR 0004 Lot 2, la page
carrières. C'est le seul canal dont le projet est déjà propriétaire de bout en bout.

### 1.2 Six constats de code qui pèsent sur la refonte

Ce ne sont pas des critiques de style. Chacun contraint le choix de fournisseur.

**C1 — L'identité du fournisseur a fui dans la configuration métier.**
`Collector.name` sert de préfixe de signal dans les rubriques
(`ScoringEngine` résout `"gbp.verified"` via `signaux["gbp"]["verified"]`).
Or `knowledge/rubric_persona1.yaml` écrit noir sur blanc :

```yaml
- { signal: gbp.verified,   … }      # gbp = Google Business Profile
- { signal: gbp.has_photos, … }
- { signal: reviews.count,  … }
```

`gbp` **est** le nom du produit Google. Remplacer Google Places par Foursquare ou
OpenStreetMap obligerait soit à renommer le collecteur — et alors **toutes** les
rubriques de **tous** les secteurs cassent — soit à conserver un collecteur nommé
`gbp` qui sert des données non-Google, ce qui est un mensonge de nommage dans le
grand livre. C'est le défaut d'abstraction n°1 et il est structurel : la promesse
« ajouter un secteur = trois YAML, zéro code » (ADR 0003) ne s'étend pas à
« changer de fournisseur = zéro code ».

**C2 — Ajouter un fournisseur exige de modifier `api_io.py`.**
`MESUREURS_DEFAUT` (`api_io.py:54-60`) est un dict **en dur au niveau module** :

```python
MESUREURS_DEFAUT: dict[str, Callable[[Any], dict[str, float]]] = {
    "anthropic": …, "serp": …, "google_places": …, "http": …, "apollo": …,
}
```

Un nouveau fournisseur sans entrée ici retombe sur `lambda r: {"requetes": 1.0}`
(`api_io.py:367`) et son coût est mal compté silencieusement. Le principe maison
« config = données, changer un tarif = éditer le YAML » (invariant J3) ne tient
donc que pour les **prix**, pas pour les **fournisseurs**. Pour un SaaS qui doit
pouvoir substituer une source sous contrainte de ToS, c'est le mauvais partage.

**C3 — Le cache disque n'a aucune expiration.** `cache_ttl_jours: 30` est déclaré
deux fois (`diagnostic/greenit.py:61`, `knowledge/greenit.yaml:106`) et
**n'est lu par aucun code** :

```
$ grep -rn "cache_ttl_jours" --include='*.py' . | grep -v __pycache__
diagnostic/greenit.py:61:        "cache_ttl_jours": 30,
```

`ApiIO._lire_cache()` (`api_io.py:218-224`) fait `path.exists()` puis
`json.loads()`. Pas de `mtime`, pas de TTL. **Une réponse Google Places mise en
cache y reste indéfiniment.** Voir §5.1 : c'est précisément l'objet de la clause
de caching de Google. Le paramètre existe, la borne n'est pas appliquée.

**C4 — Le cache contient des données personnelles et échappe à `opt_out`.**
`.cache/api_io/apollo_people_enrichment_<hash>.json` (clé
`f"apollo:{domaine}"`, `enrichment.py:71`) contient la réponse Apollo brute —
donc **bien plus** que les 6 champs de `Contact`. La minimisation par
`extra="forbid"` protège le **vault**, pas le **cache**. Et `opt_out` n'est
honoré qu'à un seul endroit du dépôt, `diagnostic/export.py:73`. **Un opt-out ne
purge rien dans `.cache/api_io/`.** Pour un pilote c'est un angle mort ; pour un
SaaS multi-clients c'est un défaut à corriger avant le premier prospect réel.

**C5 — L'endpoint Apollo appelé n'est pas celui qui est facturé dans la grille.**
`api_pricing.yaml:59` déclare `people_enrichment`, et c'est le libellé écrit dans
le grand livre (`enrichment.py:67-68`). Le code appelle en réalité
`/v1/people/search` (`enrichment.py:93`) avec `per_page: 5`. *Search* et
*Enrich* sont deux produits distincts chez Apollo, avec deux modèles de crédit
distincts `[NON VÉRIFIÉ — apollo.io/pricing NON LU]`. Le mesureur compte
`{"credits": 1.0}` par **appel**, pas par **enregistrement révélé** : si Apollo
facture par enregistrement, le grand livre sous-compte d'un facteur allant
jusqu'à 5. À vérifier avant tout budget.

**C6 — Le code cible l'API Google Places *legacy*.**
`maps/api/place/textsearch/json` et `maps/api/place/details/json` sont les
endpoints hérités. L'API courante est
`POST https://places.googleapis.com/v1/places:searchText` avec en-tête
`X-Goog-FieldMask` obligatoire. D'après les résultats de recherche du 2026-08-04
`[NON VÉRIFIÉ — developers.google.com NON LU, 403]` : le legacy serait **gelé
depuis mars 2025** (pas de nouvelles fonctionnalités, **indisponible dans les
nouveaux projets Cloud**), maintenu pour les projets existants, avec un préavis
annoncé de 12 mois avant extinction. **Si c'est exact, le code actuel ne peut pas
être mis en service sur un projet Google Cloud créé aujourd'hui.** C'est le point
à vérifier en premier, avant toute discussion de prix : ce n'est pas une question
de coût, c'est une question d'existence.

---

## 2. Cartographie des besoins, sans nommer un seul fournisseur

C'est la couche qui doit survivre à la refonte. Un besoin est une **question à
laquelle le système doit répondre**, pas un endpoint.

### 2.1 Les huit familles

| # | Famille | Question posée | Nature | Périssabilité | Sensibilité RGPD/L25 |
|---|---|---|---|---|---|
| F1 | **Découverte d'entités** | « Quelles entreprises existent dans ce segment × ce territoire ? » | énumération | faible (mois) | nulle (personne morale) |
| F2 | **Firmographie** | « Cette entité est-elle réelle, active, de quelle taille, depuis quand ? » | état | faible (mois) | faible |
| F3 | **Présence web** | « Que dit son propre site, et dans quel état est-il ? » | état | moyenne (semaines) | nulle |
| F4 | **Réputation / avis** | « Que disent les tiers, combien, à quelle note, depuis quand ? » | état | moyenne | indirecte (avis nominatifs) |
| F5 | **Signaux d'activité datés** | « Qu'a-t-elle **fait** récemment, et **quand** ? » | **événement daté** | **forte (jours)** | variable |
| F6 | **Contacts** | « Qui joindre, à quelle adresse, avec quelle preuve de provenance ? » | état | forte | **maximale** |
| F7 | **Registres publics** | « Que dit l'autorité publique de cette entité ? » | état faisant foi | faible (mois) | faible |
| F8 | **Technographie** | « Quelles technologies sa vitrine utilise-t-elle ? » | état | moyenne | nulle |

### 2.2 Ce que le système couvre aujourd'hui

| Famille | Couverture actuelle | Implémentation |
|---|---|---|
| F1 | oui | SERP (`discovery.py`) |
| F2 | **non** | — aucun collecteur firmographique |
| F3 | oui | crawl propre (`website.py`, `seo.py`, `social.py`) |
| F4 | oui | Google Places (`reviews.py`) |
| F5 | oui, **un seul signal** | `website.offre_detectee` (ADR 0004) |
| F6 | oui | Apollo (`enrichment.py`) |
| F7 | **non** | — aucun registre branché |
| F8 | **non** | — `legitimite.py` en est un cousin pauvre (motifs textuels) |

**Trois familles sur huit sont vides, et ce sont les trois les moins chères et
les moins risquées juridiquement** (F2, F7 : registres publics ; F8 :
observable sur le HTML déjà téléchargé). Le système actuel dépense son budget et
son risque ToS exactement là où l'open data ne suffit pas — F1, F4, F6 — ce qui
est cohérent, mais il n'a jamais épuisé le gratuit d'abord.

### 2.3 Pourquoi F5 doit rester architecturalement à part

L'ADR 0004 a déjà tranché : un événement daté n'est pas un état, il périt, il ne
s'agrège pas en score. Cette distinction **doit remonter dans la couche
d'approvisionnement** :

- un état (F2/F3/F4/F7/F8) peut se rafraîchir par lot, sur un rythme mensuel ;
- un événement (F5) n'a de valeur que **frais**, donc il impose une cadence de
  collecte, donc il pilote le coût variable du SaaS.

Un fournisseur qui ne date pas ses données est **inutilisable pour F5**, quel
que soit son prix. C'est un critère d'exclusion, pas une préférence.

### 2.4 L'extensibilité hors marketing dépend de F5, pas du reste

Le mandat parle d'autres verticales OSINT. F1/F2/F3/F7 sont identiques pour
n'importe quelle verticale (due diligence, veille concurrentielle, recrutement,
risque fournisseur). **Ce qui change d'une verticale à l'autre, c'est
exclusivement le catalogue de signaux F5** et la rubrique qui les interprète.
Corollaire d'architecture : F5 doit être **le seul étage configurable par
donnée**, et les sept autres doivent être des services stables. C'est le
prolongement naturel de l'ADR 0003 (`secteur_id`) — appliqué aux sources et non
plus seulement aux rubriques.

---

## 3. Challenge des trois fournisseurs actuels

### 3.1 SERP API (SerpAPI) — famille F1

**Ce qu'il fournit réellement, dans ce code.** `discovery.py` ne lit qu'un seul
champ de toute la réponse : `organic_results[].link`, plus `.title` pour deviner
un nom via découpage sur des séparateurs (`_extraire_nom`, `discovery.py:152-161`).
**Le système paie une réponse SERP complète pour n'en consommer que l'URL.**
C'est le point de levier économique le plus évident du dossier : n'importe quelle
API renvoyant des URL organiques suffit fonctionnellement.

**Coût `[NON VÉRIFIÉ]` — recherche du 2026-08-04, `serpapi.com/pricing` `[NON LU]` (403).**
D'après des comparateurs tiers : Free 250 recherches/mois ; Starter 25 $/mois
pour 1 000 recherches (≈ 0,025 $/recherche) ; Developer 75 $/5 000 ; Production
150 $/15 000 ; Big Data 275 $/30 000 (≈ 9,17 $/1 000). Les quotas non consommés
seraient perdus au renouvellement. **Chiffres non confirmés à la source.**

**Ordre de grandeur du besoin réel.** `icp/persona1-quebec.yaml` : 3 gabarits ×
6 localités = **18 requêtes par run complet** (`generer_requetes()`), toutes
cachées (`cache_key=requete`, `discovery.py:60`). Le pilote tient dans le
palier gratuit. **Le coût SERP n'est pas un problème au pilote ; il le devient
au ×100 en SaaS multi-tenant.**

**Limites.**
- *Couverture géographique.* `_serp_search` ne passe **ni `gl`, ni `hl`, ni
  `location`** (`discovery.py:94-102`). Les résultats sont donc géolocalisés par
  le datacenter du fournisseur, pas par le marché visé. Pour Québec (fr-CA),
  Suisse romande (fr-CH) et France (fr-FR) — trois marchés francophones aux SERP
  très différentes — c'est un défaut fonctionnel réel, indépendant du choix de
  fournisseur. À corriger quel que soit l'arbitrage.
- *ToS.* `serpapi.com/legal` **`[NON LU]`**. Le modèle même du service consiste à
  restituer du contenu Google : les conditions de Google, elles, interdisent le
  scraping de son contenu (§5.1). Le fournisseur s'interpose, et propose un
  « U.S. Legal Shield » sur les plans Production et supérieurs
  `[NON VÉRIFIÉ]`. **La portée réelle de cette garantie n'a pas pu être lue.**

**Risque de continuité — le point le plus important de cette section.**
D'après les résultats de recherche du 2026-08-04 `[NON VÉRIFIÉ, sources
secondaires — décisions de justice NON LUES]` : **Google a poursuivi SerpApi**
(DMCA, contournement de protections anti-robot) ; un juge fédéral aurait
**rejeté les principales prétentions DMCA le 20 juillet 2026**, au motif que des
résultats de recherche publics ne sont pas couverts par le droit d'auteur, Google
disposant de 21 jours pour amender sa plainte sur le périmètre restreint des
*Knowledge Panels*. Une **action distincte de Reddit** contre SerpApi serait
également en cours.

L'issue est favorable au fournisseur à ce stade, mais la lecture pour un SaaS est
autre : **la disponibilité de cette famille de service dépend d'un contentieux en
cours, pas d'un contrat commercial.** Un SaaS dont la découverte d'entités repose
sur un seul intermédiaire de scraping SERP porte un risque d'extinction de source
qu'aucun SLA ne couvre. Cela ne condamne pas SerpApi — cela condamne le fait de
**dépendre d'un seul** acteur de cette catégorie.

**Verdict : ABSTRAIRE, et dé-prioriser.** La valeur consommée (une liste d'URL)
est faible, le risque de continuité est élevé, et F1 est largement récupérable
par les registres publics (§4.1). SERP doit devenir une source de **complément**
derrière une interface, jamais le socle de la découverte.

### 3.2 Apollo — famille F6

**Ce qu'il fournit réellement, dans ce code.** `_extraire_contact`
(`enrichment.py:109-131`) ne retient que 6 champs : `first_name`, `last_name`,
`title`, `email`, `email_status`, `linkedin_url`. Le reste de la réponse est
ignoré. La minimisation est réelle et bien faite **côté vault** — mais voir C4
pour le cache.

**Coût `[NON VÉRIFIÉ]` — recherche du 2026-08-04, `apollo.io/pricing` `[NON LU]` (403).**
D'après des comparateurs tiers : Free (crédits très limités) ; Basic ≈ 49-59 $
/utilisateur/mois ; Professional ≈ 79-99 $ ; Organization ≈ 119-149 $ avec
**minimum 3 sièges**. Les crédits expireraient en fin de cycle sans report.
**Point le plus structurant, à confirmer en priorité :** plusieurs sources
concordantes indiquent que **l'accès API « avancé » est réservé au plan
Organization**. Si c'est exact, le coût d'entrée réel n'est pas « quelques
crédits » mais **un abonnement à 3 sièges minimum** — soit un ordre de grandeur
au-dessus de ce que suggère la structure `credits` de `api_pricing.yaml`.

**Limites.**
- *Couverture.* Apollo est un annuaire nord-américain d'abord. Sur une PME HVAC
  de Trois-Rivières ou de Bulle (FR, Suisse), le taux de correspondance est
  probablement faible. **Aucune mesure n'existe dans ce dépôt** : le banc d'essai
  `scripts/benchmark_intention.py` tourne sur un faux serveur, sans Apollo. Le
  taux de couverture réel est **inconnu** et devrait être la première chose
  mesurée en Phase D, avant d'acheter quoi que ce soit.
- *Qualité de l'email.* `email_status` est stocké comme `email_source`
  (`enrichment.py:127`), ce qui est excellent pour l'audit RGPD. Mais le code ne
  **filtre pas** sur cette valeur : un email `guessed` entre dans le vault au
  même titre qu'un `verified`. Pour un envoi CASL/nLPD, cette distinction n'est
  pas cosmétique.
- *ToS — le point bloquant.* `apollo.io/terms/api` **`[NON LU]` (403)**. Les
  résultats de recherche du 2026-08-04 rapportent, en substance
  `[NON VÉRIFIÉ]` : licence **non exclusive, non transférable, révocable**,
  d'usage des API **« solely for internal business purposes »** ; interdiction de
  **sous-licencier, vendre ou distribuer** ; interdiction d'**intégrer les API à
  son propre produit ou service** sans autorisation d'Apollo.

**Si ces clauses sont confirmées, elles sont incompatibles avec le modèle SaaS
visé, et pas marginalement.** Un SaaS qui enrichit des contacts pour le compte de
ses clients fait exactement les deux choses interdites : il **intègre l'API dans
son produit**, et il **distribue le résultat à un tiers** (son client). L'usage
actuel — une consultante unique qui prospecte pour elle-même — reste, lui,
plausiblement dans le périmètre « internal business purposes ». **La bascule
pilote → SaaS change la qualification juridique de l'usage sans changer une ligne
de code.** C'est le constat le plus important de tout ce document.

**Verdict : REMPLACER pour la v2 SaaS.** Non pour des raisons de prix ou de
qualité, mais parce que le modèle de licence semble exclure la revente. À
confirmer par un juriste sur le texte du contrat — et, si confirmé, à traiter
comme une décision d'architecture, pas comme une négociation commerciale.

### 3.3 Google Places — famille F4 (et un peu F2)

**Ce qu'il fournit réellement, dans ce code.** Cinq signaux, pas un de plus :
`business_status == "OPERATIONAL"`, présence de photos (`gbp.py:70-73`),
`user_ratings_total`, `rating`, présence d'une réponse propriétaire et date du
dernier avis (`reviews.py:59-88`). **Aucun texte d'avis n'est conservé.** Le
`place_id` transite (`reviews.py:61`) mais **n'est jamais persisté** dans
`FicheProspect`. C'est important pour §5.1, et c'est un hasard heureux plutôt
qu'une décision : rien dans le code ne l'interdit.

**Coût `[NON VÉRIFIÉ]` — recherche du 2026-08-04, pages Google `[NON LU]` (403).**
D'après des sources tierces : le modèle par SKU aurait remplacé l'ancien crédit
mensuel de 200 $ par des **franchises gratuites par SKU** ; Text Search
« Essentials (IDs Only) » serait gratuit et illimité mais ne renverrait que des
identifiants ; « Pro » ≈ **32 $/1 000 requêtes** avec ≈ 5 000 appels gratuits par
mois ; « Enterprise » ≈ 35 à 40 $/1 000, **le simple fait de demander `rating`
faisant basculer au palier supérieur, et `reviews` au palier le plus cher**.

Si cette structure est exacte, elle a une conséquence directe et désagréable :
`reviews.py:112` demande `fields=rating,user_ratings_total,reviews,photos`.
**`reviews` est précisément le champ qui coûte le plus cher**, et le code n'en
extrait que deux booléens (`owner_answer` présent, date max). Sur l'API *New*, un
`FieldMask` bien serré ferait la même chose au palier inférieur. **Marge
d'optimisation réelle, chiffrable seulement après relevé des vrais tarifs.**

**Limites.**
- *Legacy* : voir C6. Question d'existence avant question de prix.
- *Couverture* : c'est le fournisseur le plus solide des trois sur les trois
  marchés visés. Une PME de services locaux sans fiche Google est rare.
- *ToS* : voir §5.1 — c'est là que tout se joue.

**Verdict : GARDER pour F4, ABSTRAIRE, et migrer vers l'API *New*.** C'est le
seul des trois qui fournit une donnée difficilement remplaçable (le volume et la
note d'avis d'un établissement local n'ont pas d'équivalent ouvert). Mais son
contrat interdit vraisemblablement d'en faire un dossier persistant (§5.1), ce
qui impose un traitement particulier — pas un remplacement.

---

## 4. Alternatives sérieuses, y compris non-API

### 4.1 F1 + F2 + F7 — registres publics (la piste la plus sous-exploitée)

Aucun de ces trois registres n'est branché aujourd'hui. Tous couvrent exactement
les trois marchés du pilote.

| Marché | Source | Ce qu'elle donne | Coût | Fraîcheur | Licence / risque |
|---|---|---|---|---|---|
| Québec | **Registraire des entreprises (REQ)** — données ouvertes sur donneesquebec.ca | Nom légal, NEQ, adresse, statut, activité, dates | Gratuit `[NON VÉRIFIÉ]` | **Mensuelle** `[NON VÉRIFIÉ]` | Licence de Données Québec `[NON LU]`. Personnes physiques (actionnaires, administrateurs) **anonymisées à la source** `[NON VÉRIFIÉ]` — plutôt favorable |
| Suisse | **Zefix** (OFRC) — API REST + jeu opendata.swiss | Raison sociale, IDE/UID, siège, adresse, forme juridique | Gratuit `[NON VÉRIFIÉ]` | **Quotidienne** pour le jeu opendata `[NON VÉRIFIÉ]` | Registre public, consultable librement `[NON VÉRIFIÉ]` |
| France | **Sirene / INSEE** + **API Recherche d'Entreprises** (DINUM) | SIREN/SIRET, NAF, effectifs, adresse, dates | Gratuit | Sirene : régulière ; Recherche d'Entreprises : **7 appels/s** `[NON VÉRIFIÉ]` | **Licence Ouverte / Open Licence 2.0 (Etalab)** `[NON VÉRIFIÉ]` — **redistribution commerciale explicitement permise** |

**Pourquoi c'est décisif et pas un détail de complétude.** Ces sources
apportent :

1. **F2, aujourd'hui totalement absente.** Un installateur HVAC immatriculé en
   2003 et un immatriculé en 2024 n'ont pas le même besoin de branding. Le
   système ne sait pas aujourd'hui distinguer les deux.
2. **Un dénominateur pour F1.** SERP donne « ce que Google veut bien montrer » —
   un échantillon biaisé, non stable, non reproductible. Le registre donne
   **l'univers**. Un ICP « installateurs HVAC de la Capitale-Nationale » devient
   une requête sur un code d'activité, pas une supplication à un moteur.
3. **Une réconciliation d'identité (F7).** Aujourd'hui la clé de déduplication est
   le **domaine normalisé** (`_normaliser_domaine`, `discovery.py:132-138`). Un
   domaine change, expire, se revend. Un NEQ / IDE / SIREN, non. **Pour un SaaS
   qui construit un dossier persistant sur plusieurs années, l'identifiant de
   registre est le seul candidat sérieux au rôle de clé primaire.**
4. **Un profil de risque nul.** Registres publics, redistribution prévue par la
   licence, aucun ToS hostile à la conservation. C'est le seul socle de données
   sur lequel un SaaS peut bâtir **sans demander la permission**.

**Effort d'intégration.** Modéré et hétérogène : trois schémas, trois cadences,
un import par lot plutôt qu'un appel par fiche — ce que le bus `api_io` actuel,
pensé par appel unitaire avec cache par clé, ne modélise pas naturellement.
C'est un vrai chantier, pas un collecteur de plus. Voir §6.3.

**Ce que ces registres ne donnent pas :** ni site web, ni avis, ni contact
nominatif, ni signal daté d'activité. Ils fondent l'identité, ils ne remplacent
ni F4 ni F6.

### 4.2 F1 — alternatives d'index web et de SERP

| Option | Coût `[NON VÉRIFIÉ]`, recherche 2026-08-04 | Fraîcheur | Effort | Risque |
|---|---|---|---|---|
| **Serper.dev** | ≈ 50 $ / 50 000 requêtes ; jusqu'à ≈ 0,30 $/1 000 à l'échelle ; crédits expirant à 6 mois | temps réel | faible (même forme d'appel) | même catégorie juridique que SerpAPI |
| **DataForSEO** | ≈ 0,60 $/1 000 (standard, file ~5 min), 1,20 $ (priorité), 2,00 $ (live) ; top-up min. 50 $, crédits sans expiration | temps réel | faible-moyen (mode asynchrone) | idem |
| **Brave Search API** | ≈ 0,003-0,005 $/requête ; palier gratuit remplacé par 5 $ de crédits prépayés | temps réel | faible | **index propre** — ne restitue pas Google, profil ToS distinct et plus sain |
| **Google Custom Search JSON** | 100 requêtes/jour gratuites `[NON VÉRIFIÉ]` | temps réel | faible | contractuel avec Google, mais **très bridé** |
| **Common Crawl** | **gratuit** (Registry of Open Data on AWS) ; coût = calcul + stockage | **par lot**, mensuel | **élevé** (WARC/WET/CDX, pipeline batch) | faible |
| **Crawl propre étendu** | coût d'infrastructure seul | maîtrisée | moyen-élevé | à gérer soi-même (robots.txt, politesse) |

**À noter au passage :** l'API de recherche Bing a été **retirée le 11 août 2025**
`[NON VÉRIFIÉ]`, la voie de remplacement passant par Azure AI Foundry. C'est
l'illustration la plus nette du risque de cette famille : **une API de recherche
peut disparaître du jour au lendemain par décision unilatérale du fournisseur.**
Argument d'abstraction, pas argument de prix.

**Lecture.** Serper et DataForSEO sont des substituts fonctionnels immédiats
(le code ne lit que `organic_results[].link`) et déplacent le curseur de prix
d'un ordre de grandeur `[NON VÉRIFIÉ]`. Brave change de **catégorie de risque**
puisqu'il exploite son propre index. Common Crawl est la seule option qui
supprime toute dépendance à un moteur — au prix d'un pipeline batch et d'une
fraîcheur mensuelle, acceptable pour F1 (les entreprises n'apparaissent pas et ne
disparaissent pas quotidiennement), inacceptable pour F5.

### 4.3 F4 — alternatives sur les avis

| Option | Ce qu'elle donne | Coût `[NON VÉRIFIÉ]` | Limite |
|---|---|---|---|
| **Yelp Fusion / Places** | Note, volume, **extraits** d'avis | ≈ 7,99 $/1 000 appels (Starter), 9,99 $ (Plus), 14,99 $ (Enterprise) | **Couverture faible hors grandes villes US**. Québec partiel, Suisse/France quasi nuls. **Display Requirements** contraignants `[NON LU]` |
| **Foursquare Places** | POI, catégories, peu d'avis | Basic gratuit (1 000 req/h), Pro ≈ 599 $/mois | Peu d'avis exploitables ; pas un substitut à F4 |
| **OpenStreetMap / Overpass** | POI, catégorie, adresse, parfois site et horaires | **gratuit** | **Aucun avis, aucune note.** Substitut à F2/F1 local, pas à F4 |
| **Trustpilot, Pages Jaunes, annuaires sectoriels** | Avis | variable | Couverture très inégale, ToS à examiner un par un `[NON LU]` |

**Conclusion nette : F4 n'a pas d'alternative crédible à Google sur les trois
marchés visés.** C'est le seul point de dépendance vraiment dure du dossier. Il
faut donc le traiter non pas en cherchant un remplaçant, mais en **limitant ce
qu'on en conserve** (§5.1 et §6.4).

**Note sur ODbL (OpenStreetMap).** La licence est *share-alike* : une **base
dérivée** redistribuée doit rester sous ODbL, tandis qu'une **œuvre produite**
(un rapport, un audit PDF) peut être sous les termes de son choix, à charge
d'offrir l'accès à la base sous-jacente sur demande `[NON VÉRIFIÉ]`. Pour un
SaaS, la frontière entre « je livre un audit » (œuvre produite, sain) et « je
livre un export CSV de fiches » (base dérivée, contaminante) **passe exactement
au milieu de ce produit** — `run_export.py` produit un CSV. À qualifier avant
d'intégrer la moindre donnée OSM.

### 4.4 F6 — alternatives sur les contacts

| Option | Modèle | Coût `[NON VÉRIFIÉ]` | Posture RGPD |
|---|---|---|---|
| **Dropcontact** (FR) | **Algorithmique** : déduit et vérifie sans base de personnes achetée | ≈ 24 €/mois pour 1 000 crédits ; ≈ 79 €/mois pour 5 000 | Positionné comme conforme RGPD, « pas de base de données personnelles stockée », audit CNIL revendiqué `[NON VÉRIFIÉ]` |
| **Hunter.io** | Recherche d'emails par domaine, sources citées | non relevé `[NON VÉRIFIÉ]` | Cite ses sources publiques — utile pour l'obligation d'information |
| **Cognism** | Base B2B, orientation conformité UE | sur devis, ordre de 15 000-25 000 $/an | Documentation par pays (UK, DACH, France, Nordics) `[NON VÉRIFIÉ]` |
| **Formulaire de contact du site** | crawl propre | ~0 | **Zéro donnée personnelle collectée** |
| **Registres** (§4.1) | représentant légal, quand publié | 0 | Publication légale |

**Le pivot le plus intéressant n'est pas un fournisseur, c'est un changement de
cible.** Le système cherche aujourd'hui **une personne** (`titres_cibles` :
propriétaire, président, directeur — `icp/persona1-quebec.yaml:37-45`). Sur une
PME de 5 à 30 personnes, l'adresse générique publiée sur le site
(`info@`, `contact@`) atteint le décideur presque aussi sûrement, et elle est
**publiée par l'entreprise elle-même pour être contactée**. Le collecteur
`website.py` détecte déjà un moyen de contact (`has_contact`,
`website.py:146`) — il ne l'extrait simplement pas.

Bascule de « contact nominatif » à « contact d'entreprise publié » :

- supprime le fournisseur F6 et son coût ;
- supprime la clause de revente d'Apollo (§3.2) ;
- **fait sortir la donnée du champ de l'obligation d'information de l'art. 14
  RGPD** (collecte indirecte), puisqu'il n'y a plus de collecte indirecte de
  donnée personnelle ;
- affaiblit la personnalisation du message.

Ce dernier point est un arbitrage produit, pas technique. Il appartient à la
consultante. **Mais il doit être posé avant de signer un contrat Apollo
Organization à 3 sièges.**

### 4.5 F8 — technographie

| Option | Coût `[NON VÉRIFIÉ]` | Effort |
|---|---|---|
| **Détection maison sur le HTML déjà téléchargé** | **0** | faible |
| **Wappalyzer** | ≈ 250 $/mois (Pro) à 450 $/mois (Business, API) | faible |
| **BuiltWith** | ≈ 295 $ à 995 $/mois + ≈ 0,05 $/lookup | faible |

**Recommandation immédiate : maison.** `website.py` télécharge déjà le HTML et
`legitimite.py` (`legitimite.py:55-59`) fait déjà de la détection de motifs
textuels **sans le moindre appel réseau**, avec la bonne discipline à trois états.
Détecter WordPress, Wix, Shopify, un pixel Meta ou Google Analytics relève
exactement du même patron — **zéro coût marginal, zéro risque ToS, zéro
fournisseur**. Payer 250 $/mois pour ce que le HTML en mémoire contient déjà
serait le pire rapport valeur/dépendance du dossier.

---

## 5. Le critère décisif : le droit de STOCKER et de REVENDRE

C'est le point qui décide de l'architecture, avant tout argument de prix ou de
qualité. Un SaaS qui construit un **dossier persistant** et le **livre à un
client** fait deux choses que la plupart des contrats d'API interdisent
séparément.

### 5.1 Google Places — la clause de caching de 30 jours

**Source : résultats de recherche du 2026-08-04. Le texte du contrat
(`cloud.google.com/maps-platform/terms/maps-service-terms`) est `[NON LU]` — 403.
Tout ce paragraphe est `[NON VÉRIFIÉ]` et doit être relu par un juriste sur le
texte contractuel.**

Éléments rapportés de façon concordante :

- mise en cache **temporaire** des valeurs de latitude/longitude issues de Places
  autorisée **jusqu'à 30 jours calendaires consécutifs**, suppression ensuite ;
- le **`place_id` est l'exception** : conservable **indéfiniment** ;
- interdiction générale d'« export, extract, or otherwise scrape Google Maps
  Content for use outside the Services », la mise en cache étant prohibée sauf
  autorisation expresse des Service Specific Terms.

**Conséquence pour ce système, telle qu'elle est aujourd'hui :**

1. **Le cache viole probablement déjà la borne.** C3 l'établit : `_lire_cache()`
   ne regarde aucune date, `cache_ttl_jours: 30` n'est lu nulle part. Une réponse
   Places de janvier est encore servie en août. Le paramètre existe, le mécanisme
   qui l'applique n'existe pas.
2. **Le vault stocke des dérivés, pas du contenu brut — et c'est ce qui sauve la
   situation.** `serializers.py` persiste des booléens et des agrégats
   (`verified`, `count`, `avg`), jamais un texte d'avis, jamais des coordonnées,
   jamais un nom d'auteur d'avis. La qualification d'un booléen dérivé au regard
   de « Maps Content » est une question juridique ouverte `[NON VÉRIFIÉ]`, mais
   la posture est bien plus défendable que si le système archivait des avis.
3. **Le `place_id` n'est pas persisté** — alors que c'est le **seul** élément que
   Google autoriserait à conserver indéfiniment. C'est un manque à gagner : il
   devrait devenir l'identifiant de réconciliation F4 (§6.4).

**Traduction en contrainte d'architecture :** un dossier prospect **permanent**
alimenté par Places est en tension directe avec ce contrat. La forme viable est
un dossier permanent dont les **champs d'origine Places sont datés, purgés à
30 jours et recalculés à la demande** — pas archivés. C'est une contrainte de
schéma, pas un simple réglage de TTL.

### 5.2 Apollo — la clause d'usage interne

Voir §3.2. `apollo.io/terms/api` **`[NON LU]` (403)**. Les éléments rapportés
— « solely for internal business purposes », interdiction de sous-licencier /
vendre / distribuer, interdiction d'intégrer les API à son propre produit —
sont, **s'ils sont exacts, incompatibles avec la revente de dossiers enrichis.**

À vérifier en priorité absolue, car cette clause seule peut invalider un pan du
modèle économique. Trois questions à poser au juriste, dans cet ordre :

1. « Internal business purposes » couvre-t-il un usage **pour le compte d'un
   client** ?
2. Livrer à un client une fiche **contenant** un email issu d'Apollo est-il une
   « distribution » ?
3. Existe-t-il une licence Apollo **OEM / revendeur**, et à quel prix ?

### 5.3 SERP — la revente n'est pas la question, la légitimité de la source l'est

`serpapi.com/legal` **`[NON LU]`**. Le sujet n'est pas tant « ai-je le droit de
revendre » que « mon fournisseur a-t-il le droit de me fournir ». Le contentieux
Google c. SerpApi et l'action Reddit (§3.1) portent exactement là-dessus. Un SaaS
peut prendre ce risque **s'il est indemnisé contractuellement** (le « Legal
Shield », dont la portée est `[NON LU]`) **et s'il peut basculer de fournisseur
en une journée** (§6). L'abstraction n'est pas ici une élégance de conception :
c'est la mesure de mitigation du risque.

### 5.4 La couche qui n'a pas de propriétaire : le crawl propre

`website.py` fetch le site du prospect. Cette donnée n'a **aucun fournisseur**,
donc **aucune clause de revente**. C'est la seule matière première dont le projet
soit pleinement propriétaire.

Deux réserves honnêtes, déjà consignées dans `CLAUDE.md` :

- **robots.txt n'est pas vérifié** sur l'escalade « page carrières » (ADR 0004,
  Lot 2). Pour un pilote c'est une négligence mineure ; pour un SaaS qui crawle à
  l'échelle, c'est la première chose qu'un plaignant regardera.
- Le contenu d'une page reste protégé par le droit d'auteur : on peut en **tirer
  des observations factuelles** (« pas de HTTPS », « pas de balise viewport »),
  on ne peut pas en **redistribuer le texte**. C'est déjà ce que fait le système
  — il produit des booléens, pas des copies. Bonne posture, à préserver
  explicitement dans la v2.

### 5.5 Le contact : deux régimes juridiques, trois marchés

| Marché | Régime pour un contact professionnel | Conséquence |
|---|---|---|
| **Québec** | La Loi 25 ne traite **pas** comme renseignement personnel l'information liée à **l'exercice d'une fonction** au sein d'une entreprise — nom, titre, courriel, adresse, téléphone professionnels `[NON VÉRIFIÉ]` | Régime **nettement plus permissif** |
| **France / UE** | RGPD art. 14 : collecte indirecte ⇒ **obligation d'informer** la personne, au plus tard sous **1 mois** ou dès le premier contact `[NON VÉRIFIÉ]`. La CNIL a sanctionné l'usage de données achetées à des courtiers pour de la prospection sans consentement valide (affaire HUBSIDE.STORE) `[NON VÉRIFIÉ]` | Régime **strict** |
| **Suisse** | nLPD + art. 3 LCD — **non recherché dans cette session** | **À instruire** |

Deux enseignements pour l'architecture, pas seulement pour la conformité :

1. **Le régime applicable dépend du marché de la fiche**, exactement comme la
   rubrique dépend de `secteur_id` (ADR 0003). La conformité est donc une
   **donnée par marché**, pas une règle globale — ce que le Palier 2 de l'ADR
   0001 avait déjà anticipé sous le nom « conformité-par-donnée ». Ce document
   confirme ce besoin par un autre chemin.
2. **La séquence pilote Québec → Suisse est la bonne**, et pour une raison qui
   n'était peut-être pas explicite : elle va du régime le plus permissif vers le
   plus strict. Il faut simplement s'assurer que rien de ce qui est construit
   pour le Québec ne devienne implicitement la règle pour la Suisse et la France.

### 5.6 Ce que je peux vérifier et ce que je ne peux pas — récapitulatif sans ambiguïté

| Affirmation | Vérifiable ici ? |
|---|---|
| Le cache n'a pas de TTL, `cache_ttl_jours` n'est lu par aucun code | **OUI** — `grep`, `api_io.py:218-224` |
| Le vault ne stocke ni texte d'avis ni coordonnées | **OUI** — lecture de `serializers.py`, `reviews.py` |
| Le `place_id` n'est pas persisté | **OUI** — `reviews.py:61`, absent de `vault_schema.py` |
| `opt_out` ne purge pas le cache | **OUI** — `opt_out` n'apparaît que dans `export.py:73` |
| Le code appelle l'API Places *legacy* | **OUI** — `gbp.py:50`, `reviews.py:97` |
| Les prix 2026 de SerpAPI / Apollo / Places | **NON** — `[NON LU]`, 403 sur toutes les pages tarifaires |
| Le texte exact des ToS Google / Apollo / SerpApi | **NON** — `[NON LU]`, 403 |
| La légalité de conserver un dérivé booléen de Maps Content | **NON** — question juridique, pas technique |
| Le taux de couverture réel d'Apollo au Québec / en Suisse | **NON** — jamais mesuré dans ce dépôt |
| L'état du contentieux Google c. SerpApi | **NON** — sources secondaires seulement, décisions `[NON LU]` |

---

## 6. Recommandation — architecture d'approvisionnement

### 6.1 Principe directeur

> **La famille de besoin est stable et publique ; le fournisseur est volatil et
> privé. Le code ne doit connaître que la première.**

C'est la transposition, au domaine des données, de ce que l'ADR 0003 a fait pour
les rubriques et l'ADR 0001 pour l'ordonnancement. Le projet a déjà deux fois
appliqué ce geste avec succès ; il ne l'a jamais appliqué aux sources.

### 6.2 Noyau recommandé, par famille

| Famille | Socle (noyau) | Repli 1 | Repli 2 | Justification du socle |
|---|---|---|---|---|
| F1 découverte | **Registres publics** (REQ, Zefix, Sirene) | Brave Search API | SERP managé (Serper/DataForSEO) | Gratuit, exhaustif, redistribuable, identifiant stable |
| F2 firmographie | **Registres publics** | — | — | Aucun substitut commercial ne fait mieux qu'un registre officiel |
| F3 présence web | **Crawl propre** | — | Common Crawl | Aucun fournisseur, aucune clause |
| F4 réputation | **Google Places (API New)** | Yelp (US/QC partiel) | — | **Pas d'alternative crédible.** Dépendance assumée, périmètre borné |
| F5 signaux datés | **Crawl propre ciblé** | flux publics datés | — | La date est l'information ; seul le crawl la garantit |
| F6 contacts | **Contact d'entreprise publié** (crawl) | Dropcontact (UE) | Apollo (si licence de revente obtenue) | Sort du champ art. 14, supprime la clause de revente |
| F7 registres | **Registres publics** | — | — | Clé primaire du dossier |
| F8 technographie | **Détection maison sur HTML** | Wappalyzer | — | Coût marginal nul, donnée déjà en mémoire |

Lecture d'ensemble : **cinq familles sur huit passent à des sources gratuites,
publiques et redistribuables.** Une seule dépendance commerciale dure subsiste
(F4/Google), et une dépendance commerciale optionnelle (F6, seulement si la
personnalisation nominative est jugée indispensable au produit).

### 6.3 Ce qui doit passer derrière une abstraction — précisément

Le mandat demande d'être explicite. Voici le découpage, avec l'état actuel.

**(1) `SourceAdapter` — nouvelle interface, par famille et non par fournisseur.**

Aujourd'hui `Collector` (`collectors/base.py`) mélange trois responsabilités :
*quel fournisseur*, *quel transport*, *quels signaux*. Il faut les séparer :

- `Collector` garde la **sémantique métier** et le nom de namespace du signal ;
- un `SourceAdapter` porte le **fournisseur** et son transport, et se choisit par
  configuration.

Corollaire dur, et c'est le point douloureux : **`gbp` doit être renommé en
`reputation_locale` (ou équivalent agnostique), et `rubric_*.yaml` mis à jour.**
Rupture de contrat sur les rubriques, à faire **une seule fois**, dans la refonte
v2, avec un test de non-régression sur `signal_chaud`. Le faire plus tard coûtera
plus cher : chaque nouveau secteur écrit aujourd'hui ancre un peu plus `gbp.*`
dans la configuration métier.

**(2) `MESUREURS_DEFAUT` doit devenir une donnée.**

`api_io.py:54-60`. Déplacer vers `api_pricing.yaml` (ou un
`knowledge/fournisseurs.yaml`) une déclaration `{fournisseur → chemin d'unités}`,
pour qu'ajouter un fournisseur n'exige **plus** de modifier le bus. C'est la
mise en conformité de `api_io.py` avec le principe que le projet applique déjà
partout ailleurs.

**(3) Une politique de rétention par fournisseur, appliquée par le bus.**

Aujourd'hui : cache unique, sans TTL, pour toutes les sources (C3). Cible : le
TTL est une propriété **du fournisseur**, déclarée en donnée à côté de son prix.
`google_places: retention_max_jours: 30` doit être une valeur **lue et appliquée**
par `_lire_cache()`, pas un commentaire. Et le bus doit exposer une purge, que
`opt_out` puisse appeler (C4).

`ApiIO` est déjà le bon endroit : c'est le point de passage unique de tout le
réseau. La rétention est le pendant naturel du budget — même mécanisme, même
place, autre grandeur. C'est l'ADR 0001 qui rend cette correction facile.

**(4) Une clé d'entité indépendante du fournisseur et du domaine.**

Aujourd'hui : domaine normalisé (`discovery.py:132-138`). Cible : identifiant de
registre (NEQ / IDE / SIREN) en clé primaire, le domaine devenant un attribut,
le `place_id` un attribut de réconciliation F4 — et **le seul champ Places
conservable indéfiniment** (§5.1). Sans cette clé, un SaaS ne peut pas tenir un
dossier sur plusieurs années sans le fragmenter à chaque changement de site.

**(5) Ce qui doit rester en dur, et pourquoi.**

L'abstraction a un coût cognitif. Ne **pas** abstraire :

- le **crawl propre** — il n'y a rien à substituer, on en est propriétaire ;
- le **schéma `FicheProspect`** — c'est le contrat de sortie, il doit être stable
  quand les sources bougent, c'est même tout l'intérêt ;
- la **règle des trois états** (`ok`/`echec`/`inconnu`) — elle **gagne** en
  importance ici : un fournisseur substitué qui ne couvre pas une dimension doit
  produire `None`, jamais `False`. La discipline existante (P4, ADR 0003
  anti-fuite de vocabulaire) est **exactement** le mécanisme qui rend la
  substitution de fournisseur sûre. Elle n'a pas été conçue pour ça, et c'est
  elle qui rend cette refonte possible à coût raisonnable.

### 6.4 Traitement particulier de F4 (la dépendance dure)

Puisque Google Places n'a pas de substitut et que son contrat semble hostile à la
persistance :

1. Migrer vers l'API **New** avec un `FieldMask` minimal — ne demander `reviews`
   que si `repond_aux_avis` est réellement utilisé par une rubrique active
   (aujourd'hui : oui, un seul check à 20 points dans `rubric_persona1.yaml`).
2. Persister le **`place_id`** — seul champ conservable indéfiniment.
3. Marquer tout champ d'origine Places d'une **date de collecte** et d'une
   **échéance à 30 jours** dans le schéma. Le mécanisme existe déjà :
   `EvenementIntention.expire_le` (ADR 0004) fait exactement cela pour les
   événements. **L'étendre aux champs d'état d'origine contrainte** est une
   réutilisation, pas une invention.
4. Au-delà de l'échéance : recalculer, ou afficher « non observé » — jamais
   servir une valeur périmée comme si elle était fraîche. C'est, une fois de
   plus, la règle des trois états.

---

## 7. Tableau de décision

Coût : `[V]` = vérifié à la source officielle, `[NV]` = non vérifié (source
secondaire), `[NL]` = page non lue (403). **Aucune ligne n'est `[V]`** — voir §0.2.

### 7.1 Fournisseurs actuels

| Fournisseur | Famille | Coût affiché | Risque ToS | Remplaçabilité | Verdict |
|---|---|---|---|---|---|
| **SerpAPI** | F1 | 25 $/1 000 → 9,17 $/1 000 selon palier `[NV]`, page `[NL]` | **Élevé** — contentieux Google et Reddit en cours `[NV]` ; portée du « Legal Shield » `[NL]` | **Élevée** — le code ne lit que `organic_results[].link` | **ABSTRAIRE + DÉPRIORISER** — repli sur registres publics ; garder en complément derrière interface |
| **Apollo** | F6 | Basic ≈ 49-59 $/u/mois, Organization ≈ 119-149 $ avec 3 sièges min. ; API avancée = Organization `[NV]`, page `[NL]` | **Critique** — « internal business purposes », interdiction de distribuer et d'intégrer à son produit `[NV]`, contrat `[NL]` | Moyenne — Dropcontact (UE) ou bascule vers contact d'entreprise publié | **REMPLACER pour la v2** — la clause semble exclure la revente. Vérification juridique en préalable bloquant |
| **Google Places** | F4 (+F2) | Text Search Pro ≈ 32 $/1 000, Enterprise 35-40 $/1 000 selon champs ; ≈ 5 000 appels/mois gratuits `[NV]`, page `[NL]` | **Élevé mais gérable** — caching 30 j, `place_id` seul conservable `[NV]`, contrat `[NL]` | **Faible** — pas d'alternative crédible sur QC/CH/FR | **GARDER + ABSTRAIRE + MIGRER** vers l'API New, FieldMask minimal, rétention 30 j appliquée |

### 7.2 Alternatives évaluées

| Source | Famille | Coût | Risque ToS | Remplaçabilité | Verdict |
|---|---|---|---|---|---|
| **REQ (Québec)** | F1/F2/F7 | gratuit `[NV]` | **Faible** — données ouvertes, personnes physiques anonymisées `[NV]` | n/a (socle) | **ADOPTER** — priorité 1 |
| **Zefix (Suisse)** | F1/F2/F7 | gratuit `[NV]` | **Faible** — registre public `[NV]` | n/a (socle) | **ADOPTER** |
| **Sirene / API Recherche d'Entreprises (FR)** | F1/F2/F7 | gratuit, 7 appels/s `[NV]` | **Très faible** — Licence Ouverte Etalab 2.0, redistribution commerciale prévue `[NV]` | n/a (socle) | **ADOPTER** |
| **Crawl propre** | F3/F5/F6/F8 | infrastructure seule | **Faible, sous conditions** — robots.txt à vérifier (dette ADR 0004) ; pas de redistribution de texte | n/a (socle) | **GARDER ET ÉTENDRE** — la seule matière première possédée |
| **Serper.dev** | F1 | ≈ 50 $/50 000, jusqu'à 0,30 $/1 000 `[NV]`, page `[NL]` | Élevé (même catégorie que SerpAPI) | Élevée | **REPLI** derrière l'abstraction F1 |
| **DataForSEO** | F1 | ≈ 0,60 $/1 000 standard `[NV]`, page `[NL]` | Élevé (idem) | Élevée | **REPLI** — crédits sans expiration, utile en usage irrégulier |
| **Brave Search API** | F1 | ≈ 0,003-0,005 $/requête `[NV]`, page `[NL]` | **Moyen** — index propre, pas de restitution de Google | Élevée | **REPLI PRÉFÉRÉ** — meilleur profil juridique de la catégorie |
| **Common Crawl** | F1/F3 | gratuit (Registry of Open Data on AWS) `[NV]` | Faible | n/a | **ÉTUDIER** — pipeline batch, hors périmètre v2.0 |
| **Dropcontact** | F6 | ≈ 24 €/1 000 crédits `[NV]`, page `[NL]` | **Faible à moyen** — approche algorithmique, positionnement RGPD `[NV]` | Élevée | **REPLI F6** si le contact nominatif reste requis |
| **Hunter.io** | F6 | non relevé `[NL]` | à instruire | Élevée | **À ÉVALUER** |
| **Cognism** | F6 | ≈ 15 000-25 000 $/an `[NV]`, page `[NL]` | à instruire | Élevée | **ÉCARTER** — hors gabarit économique d'un pilote |
| **Yelp Fusion** | F4 | 7,99-14,99 $/1 000 `[NV]`, page `[NL]` | Display Requirements `[NL]` | Faible | **ÉCARTER** — couverture QC/CH/FR insuffisante |
| **Foursquare** | F4/F1 | Basic gratuit, Pro ≈ 599 $/mois `[NV]`, page `[NL]` | à instruire | Faible sur F4 | **ÉCARTER pour F4** |
| **OpenStreetMap / Overpass** | F1/F2 | gratuit | **Moyen — ODbL share-alike** : un export CSV pourrait constituer une base dérivée contaminante `[NV]` | Moyenne | **PRUDENCE** — qualifier « œuvre produite » vs « base dérivée » avant tout usage |
| **Wappalyzer / BuiltWith** | F8 | 250-450 $/mois / 295-995 $/mois + 0,05 $/lookup `[NV]`, pages `[NL]` | Faible | Élevée | **ÉCARTER** — détection maison sur HTML déjà téléchargé |

### 7.3 Dette technique à corriger indépendamment du choix de fournisseur

Ces cinq points sont **vérifiés dans le code** et fautifs quel que soit
l'arbitrage retenu.

| # | Constat | Emplacement | Gravité |
|---|---|---|---|
| C3 | `cache_ttl_jours: 30` déclaré, lu par aucun code ; cache sans expiration | `api_io.py:218-224`, `greenit.py:61` | **Haute** — probable non-conformité au caching Google |
| C4 | Données personnelles Apollo en cache, hors du champ de `opt_out` | `.cache/api_io/`, `export.py:73` | **Haute** — RGPD, rétention |
| C6 | Appel de l'API Places *legacy*, gelée et indisponible aux nouveaux projets Cloud `[NV]` | `gbp.py:50`, `reviews.py:97` | **Haute** — risque de non-démarrage en Phase D |
| C5 | Endpoint `people/search` journalisé sous le libellé `people_enrichment` ; 1 crédit compté par appel, pas par enregistrement | `enrichment.py:67,93` | Moyenne — coût sous-estimé |
| — | Aucun paramètre de géolocalisation SERP (`gl`/`hl`/`location`) | `discovery.py:94-102` | Moyenne — pertinence dégradée sur les 3 marchés |
| C1 | `gbp.*` (nom de produit Google) figé dans les rubriques métier | `rubric_persona1.yaml` | Moyenne — coût croissant avec chaque secteur ajouté |
| C2 | `MESUREURS_DEFAUT` en dur : ajouter un fournisseur = modifier le bus | `api_io.py:54-60` | Basse — contredit « config = données » |

---

## 8. Ce qu'il faut vérifier avant toute décision

Ce document ne conclut pas. Il **cadre** une décision qui exige trois relevés que
cet environnement ne pouvait pas faire.

**Priorité 1 — juridique, bloquant (un juriste, sur le texte des contrats).**
1. Apollo `apollo.io/terms/api` : « internal business purposes » couvre-t-il un
   usage pour le compte d'un client ? Existe-t-il une licence de revente ?
2. Google Maps Platform Service Specific Terms : un **dérivé booléen** de Maps
   Content (« a plus de 10 avis ») est-il soumis à la règle des 30 jours ?
3. Régime suisse du contact professionnel (nLPD + art. 3 LCD) — **non instruit
   dans cette session**.

**Priorité 2 — tarifaire (Phase D, opératrice).**
4. Relever les vrais tarifs sur les pages officielles, avec `releve_le`
   renseigné dans `knowledge/api_pricing.yaml`. **Aucun chiffre de ce document ne
   doit y être recopié.**
5. Vérifier si l'accès API Apollo impose bien le plan Organization (3 sièges).
6. Vérifier le statut de l'API Places *legacy* et la faisabilité d'un projet
   Cloud neuf (C6) — **avant** toute question de prix.

**Priorité 3 — mesure (aucune ne peut se déduire, toutes exigent un run réel).**
7. Taux de correspondance Apollo sur un échantillon QC / Suisse romande. Sans ce
   chiffre, le débat « Apollo vs Dropcontact vs contact d'entreprise » est une
   discussion d'opinions.
8. Taux de recouvrement entre découverte SERP et découverte par registre : le
   registre trouve-t-il ce que SERP trouve, et quoi de plus ?
9. Part des fiches où l'email d'entreprise publié suffirait à l'usage commercial
   réel — c'est la mesure qui tranche §4.4, et elle appartient à la consultante.

**Note de méthode, dans l'esprit de la porte de cohérence 97 %.** Les constats de
§1.2 et §7.3 sont ré-exécutables : chemins, numéros de ligne et commandes `grep`
sont donnés. Les tarifs et les clauses ne le sont pas : ils sont marqués
`[NON VÉRIFIÉ]` / `[NON LU]` et datés du 2026-08-04. Un relecteur qui voudrait
confirmer un prix de ce document **ne le pourra pas** — c'est voulu, et c'est la
seule chose honnête à écrire depuis un environnement dont l'egress est fermé.

---

## Sources consultées

Toutes via `WebSearch` le **2026-08-04**. **Aucune n'a pu être ouverte
(`WebFetch` → HTTP 403, blocage d'egress de la session).** Ce sont donc des
**résumés de résultats de recherche**, pas des lectures de première main.

Tarification et conditions des fournisseurs actuels :
- [SerpApi Pricing Explained (2026) — apiserpent.com](https://apiserpent.com/blog/serpapi-pricing-explained)
- [SerpApi Pricing 2026 — costbench.com](https://costbench.com/software/web-scraping/serpapi/)
- [Apollo Pricing 2026 — warmly.ai](https://www.warmly.ai/p/blog/apollo-pricing)
- [Apollo.io Pricing 2026 — saleshandy.com](https://www.saleshandy.com/blog/apolloio-pricing/)
- [Terms of Service - API — apollo.io](https://www.apollo.io/terms/api) `[NON LU]`
- [Google Places API Pricing 2026 — safegraph.com](https://www.safegraph.com/guides/google-places-api-pricing/)
- [Google Places API Pricing — woosmap.com](https://www.woosmap.com/blog/google-places-api-pricing)
- [Google Maps Platform Service Specific Terms — cloud.google.com](https://cloud.google.com/maps-platform/terms/maps-service-terms) `[NON LU]`
- [Policies and attributions for Places API — developers.google.com](https://developers.google.com/maps/documentation/places/web-service/policies) `[NON LU]`
- [Migrate to Text Search (New) — developers.google.com](https://developers.google.com/maps/documentation/places/web-service/legacy/migrate-text) `[NON LU]`
- [Google Places API (Legacy) Is Frozen — mapatlas.eu](https://mapatlas.eu/blog/google-places-api-legacy-deprecation-eu)

Contentieux et continuité de service :
- [Judge tosses Google's DMCA suit against scraper SerpApi — aiweekly.co](https://aiweekly.co/alerts/judge-tosses-googles-dmca-suit-against-scraper-serpapi)
- [Google loses key DMCA claims against SerpApi — searchengineland.com](https://searchengineland.com/google-loses-key-dmca-claims-against-serpapi-in-scraping-lawsuit-483185)
- [SerpApi Asks a Federal Court to Dismiss Reddit's Scraping Lawsuit — almcorp.com](https://almcorp.com/blog/reddit-serpapi-lawsuit-scraping-dmca/)
- [Scraper Legal Protection — SerpApi's U.S. Legal Shield](https://serpapi.com/us-legal-shield) `[NON LU]`
- [Bing Search API Retired: 5 Real Replacements Tested — apiserpent.com](https://apiserpent.com/blog/bing-search-api-alternatives)

Alternatives :
- [SERP API Pricing Comparison 2026 — apiserpent.com](https://apiserpent.com/blog/serp-api-pricing-comparison)
- [SERP API Cost Per Query: All Providers Compared (2026) — scavio.dev](https://scavio.dev/blog/serp-api-cost-per-query-all-providers-2026)
- [Brave Search API Pricing 2026 — costbench.com](https://costbench.com/software/ai-search-apis/brave-search-api/)
- [Dropcontact Review 2026: Pricing, GDPR Compliance — derrick-app.com](https://derrick-app.com/tools/dropcontact-review)
- [Best Technographic Data APIs in 2026 — theirstack.com](https://theirstack.com/en/blog/best-technographic-data-apis)
- [BuiltWith vs Wappalyzer (2026) — tomba.io](https://tomba.io/blog/builtwith-vs-wappalyzer)
- [API Terms of Use — Yelp](https://terms.yelp.com/developers/api_terms/20250113_en_us/) `[NON LU]`
- [Yelp Places API Plan Details — docs.developer.yelp.com](https://docs.developer.yelp.com/docs/plans) `[NON LU]`
- [Common Crawl — Registry of Open Data on AWS](https://registry.opendata.aws/commoncrawl/) `[NON LU]`
- [Licence and Legal FAQ — OpenStreetMap Foundation](https://osmfoundation.org/wiki/Licence/Licence_and_Legal_FAQ) `[NON LU]`
- [Open Database License — OpenStreetMap Wiki](https://wiki.openstreetmap.org/wiki/Open_Database_License) `[NON LU]`

Registres publics :
- [Données ouvertes du Registraire des entreprises — donneesquebec.ca](https://www.donneesquebec.ca/donnees-ouvertes-registraire-entreprises/) `[NON LU]`
- [Registre des entreprises — Données Québec](https://www.donneesquebec.ca/recherche/dataset/registre-des-entreprises) `[NON LU]`
- [Registre du commerce, Zefix et Regix — bj.admin.ch](https://www.bj.admin.ch/fr/registre-du-commerce-zefix-et-regix) `[NON LU]`
- [Zefix — Central Business Name Index, LINDAS](https://register.ld.admin.ch/.well-known/dataset/foj-zefix) `[NON LU]`
- [API Sirene open data — data.gouv.fr](https://www.data.gouv.fr/dataservices/api-sirene-open-data) `[NON LU]`
- [API Recherche d'Entreprises — data.gouv.fr](https://www.data.gouv.fr/dataservices/api-recherche-dentreprises) `[NON LU]`
- [Catalogue des API publiques — api.gouv.fr](https://api.gouv.fr/) `[NON LU]`

Conformité :
- [Article 14 RGPD — gdpr-expert.eu](https://www.gdpr-expert.eu/article.html?id=14) `[NON LU]`
- [Article 14 RGPD : guide et cas pratiques — monexpertrgpd.com](https://monexpertrgpd.com/article-14/) `[NON LU]`
- [Principaux changements apportés par la Loi 25 — cai.gouv.qc.ca](https://www.cai.gouv.qc.ca/protection-renseignements-personnels/sujets-et-domaines-dinteret/principaux-changements-loi-25) `[NON LU]`
- [Tout ce que vous devez savoir sur la Loi 25 — cfib-fcei.ca](https://www.cfib-fcei.ca/en/site/qc-law-25) `[NON LU]`
