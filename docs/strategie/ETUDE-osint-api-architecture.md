# Étude OSINT, fournisseurs d'API et challenge d'architecture

### Orchestration CMO · COO · Architecte · Analystes marché · Revue anti-hallucination

*Généré le 2026-08-02 — 11 agents, 5 phases.*


> ⚠️ **AVERTISSEMENT SUR LES CHIFFRES.** Aucune page tarifaire officielle n'a pu être lue
> depuis cet environnement (HTTP 403 sur serpapi.com, apollo.io, developers.google.com,
> brave.com, hunter.io, dropcontact.com…). Les seuls tarifs vérifiés sont ceux d'Anthropic.
> **Aucun chiffre de ce document n'autorise une saisie dans `knowledge/api_pricing.yaml`.**
> `releve_le` reste à `null` jusqu'à un relevé humain, page par page, depuis un navigateur
> non bloqué. Usage décisionnel uniquement.


> **Aval des revues** — Revue des chiffres : `approuvé avec réserves`, aval **accordé** (94,2 %).
> Revue d'architecture : **aval REFUSÉ** (55,2 %). Le chef de projet entérine le refus :
> le schéma OSINT complet et la feuille de route cumulée sont **rejetés en l'état** et réduits.


---

## Sommaire

1. [Synthèse décisionnelle (chef de projet)](#s1)
2. [Besoin marketing — CMO](#s2)
3. [Processus commercial — COO](#s3)
4. [Marché : API SERP](#s4)
5. [Marché : enrichissement contact](#s5)
6. [Sources OSINT](#s6)
7. [Conformité & FinOps](#s7)
8. [Challenge d'architecture](#s8)
9. [Schéma du dossier OSINT](#s9)
10. [Revues anti-hallucination](#s10)


---


<a id="s1"></a>

## 1. Synthèse décisionnelle — chef de projet


# SYNTHÈSE DÉCISIONNELLE — Kemana-Flow / Système Autonome de Diagnostic Marketing
**Décisions arrêtées le 2026-08-02 par l'agent chef de projet. Contrôles re-exécutés dans le dépôt avant rédaction (voir §5.4).**

---

## 0. TRAITEMENT PRÉALABLE DE L'AVAL REFUSÉ

La revue d'architecture rend **`aval: false`** (taux 55,2 % sur l'ensemble des affirmations chiffrées, très en dessous de la porte 97 %). Je ne le contourne pas, je le tranche :

**L'aval est refusé à bon droit, et j'entérine le refus.** Les deux artefacts d'architecture ne peuvent pas partir en implémentation en l'état. Mais le refus ne porte pas sur le même objet dans ses deux moitiés, et il faut le dire :

| Objet | Verdict | Décision |
|---|---|---|
| Diagnostic du défaut central (le système ne distingue pas « faille observée » de « rien observé ») | **Confirmé par re-exécution indépendante**, sortie identique au caractère près | **Retenu, c'est le fondement de tout le plan** |
| Palier 0 — les 7 correctifs de code | Validé « sans réserve » par le reviewer, chaque point re-vérifié par lui dans le code | **Approuvé, part en premier** |
| Chiffrages externes (22 assertions, 0 sourcée) | 0 % de fiabilité | **Supprimés du plan. Aucun n'entre nulle part.** |
| Schéma OSINT complet (9 blocs, ~90 champs, porte `pret_a_contacter`) | 4 affirmations fausses, porte arithmétiquement inatteignable, ~30 seuils inventés | **Rejeté en l'état. Réduit à 3 blocs (§4).** |
| Feuille de route cumulée (~10 collecteurs, 15 fichiers de données, 3 marchés) | « Ce n'est pas un trimestre de travail à temps partiel » | **Rejetée. Réduite à 4 collecteurs (§3).** |

**Les 6 conditions de levée posées par la revue deviennent des pré-conditions bloquantes du lot 0.** Elles sont reprises telles quelles au §6, avec le nom du responsable. Aucune ligne de code au-delà du lot 0 ne part avant qu'elles soient traitées.

Trois arbitrages que je rends moi-même, parce que la revue les laisse ouverts :
1. **`domaine.py` (DNS/MX) est supprimé du plan**, pas arbitré. La contradiction entre les deux artefacts (via le bus / hors bus) disparaît si le module n'existe pas. Le signal était faible ; le risque d'invariant ne valait pas la peine.
2. **La porte `pret_a_contacter` et les disqualifications automatiques sont annulées**, pas recalibrées. On ne pose pas de seuil avant d'avoir une distribution réelle.
3. **`_check_garde_fous_bus` passe au `rglob`**, il n'accueille plus de liste de noms à la main. La revue a raison : ajouter 9 modules à une liste explicite rouvre exactement la dette n°2 du CLAUDE.md à chaque itération.

---

## 1. LE BESOIN EN UNE PAGE

### 1.1 Le problème résolu

**Ce n'est pas « trouver des prospects ». C'est prouver sa valeur avant de facturer, sans consommer d'heures facturables.**

Le branding pour PME souffre d'une asymétrie de preuve : l'acheteur ne peut pas juger la compétence avant l'achat. La seule façon de la lever, en solo, est de livrer un fragment d'audit **avant** la vente. À la main, ce fragment coûte 45 à 90 minutes ; il n'est donc jamais produit en prospection. Le système convertit un coût variable non facturable en coût fixe amorti.

Second effet, aussi important : il découple la production de pipeline de la disponibilité de la consultante. Le cycle famine/festin du solo vient de ce qu'on prospecte quand il n'y a plus de mandats — c'est-à-dire trop tard. Le problème est de **cadence**, pas de volume.

**Le seul actif qui prend de la valeur avec le temps est la rubrique YAML** — le jugement métier encodé. Collecteurs, bus, cockpit sont des commodités. C'est pourquoi tout l'investissement va vers la qualité du diagnostic, pas vers le débit.

**Le risque corrélé, qui est le risque n°1 du projet** : un diagnostic faux ou générique ne fait pas gagner du temps, il détruit la seule chose qu'elle vend. La porte humaine Obsidian n'est pas une prudence d'architecte, c'est le cœur du modèle d'affaires.

### 1.2 Ce qui est réellement automatisé

| Étape | Automate |
|---|---|
| 1. Définition de l'ICP | **Humain** (édition YAML) |
| 2–4. Génération des requêtes, découverte, filtrage, dédup | Machine |
| 5. Écriture fiche `decouvert` | Machine |
| 6. Enrichissement décideur | Machine (plafond `max_enrichissements: 25`) |
| 7–9. Collecte de faits, scoring, rédaction | Machine |
| 10. Transition `decouvert → diagnostique` | Machine (**seule transition autorisée à l'agent**) |
| **11. PORTE HUMAINE — `diagnostique → valide` / `rejete`** | **Humain, dans Obsidian** |
| 12. Export liste | Machine (lecture seule, `opt_out` exclu sans exception) |
| **13. Priorisation, personnalisation, envoi, relance, RDV, closing** | **100 % humain, hors système** |
| **14. `valide → contacte` / `rejete`** | **Humain** |

**Formulation à retenir : ce n'est pas un système de prospection, c'est un moteur de constitution de dossiers de prospect qualifiés.** Il automatise le sourcing et la qualification technique. Il n'automatise rien de ce qui produit du chiffre d'affaires.

### 1.3 Le goulot, et pourquoi il commande tout le reste

Débit réel = min(débit machine, capacité de validation humaine, capacité d'exécution commerciale).

Le facteur limitant n'est pas le SERP : c'est `max_enrichissements: 25` puis, très en dessous, la capacité d'une consultante seule qui livre aussi ses mandats. Volume cible réaliste : **20 à 40 contacts par mois**, pas 400.

**Conséquence directe, et c'est la ligne directrice de toutes les décisions qui suivent : produire plus de fiches n'améliore rien.** La variable à optimiser est le taux de fiches `valide` par heure de validation, et le taux `valide → RDV`. Tout run de découverte au-delà de la capacité humaine est du coût pur.

Corollaire économique : le poste variable (tokens LLM) est négligeable devant le socle d'abonnement. **Optimiser les tokens pendant que la porte humaine est le goulot est une erreur d'allocation.** Je ne peux pas chiffrer l'écart — voir §5.

---

## 2. VERDICT SUR LES FOURNISSEURS

### 2.0 Avertissement liminaire, non négociable

**Aucune page tarifaire officielle n'a pu être lue dans cet environnement.** WebFetch et curl renvoient HTTP 403 sur serpapi.com, apollo.io, developers.google.com, mapsplatform.google.com, brave.com, hunter.io, dropcontact.com. Les quatre études et la revue chiffrée l'ont subi identiquement. **Les seuls tarifs vérifiés du lot sont ceux d'Anthropic.**

La revue chiffrée donne l'aval (94,2 %) **au seul usage décisionnel**, et exclut formellement l'usage de configuration. Je reprends ce périmètre à mon compte :

> **Aucun chiffre de ce document n'autorise une saisie dans `knowledge/api_pricing.yaml`. `releve_le` reste à `null` jusqu'à un relevé humain, page par page, depuis un navigateur non bloqué.**

Corrections apportées par la revue chiffrée, que j'entérine et qui invalident trois arguments économiques des études :
- **Brave Search** : le palier « 2 000 requêtes/mois gratuit » est **périmé** (supprimé en février 2026, remplacé par ~5 USD de crédit mensuel sous condition d'attribution publique). L'argument « pilote à coût nul » tombe ; seul l'argument juridique (index indépendant, hors CGU Google) survit.
- **Apollo** : le plan Organization impose un **minimum de 3 sièges**. Le plancher du statu quo n'est pas ~1 428 USD/an mais **~4 284 USD/an** — sous réserve que l'accès API exige bien ce palier, ce qui n'est pas établi.
- **Anymailfinder** : le palier à 14 USD/mois paraît périmé (page officielle affichant « from $29/mo »). Il perd sa place de meilleur ajustement du panel.
- **SerpApi** : palier gratuit à **100/mois**, pas 250. Le scénario FinOps « 500 fiches/mois → SERP à 0 $ » est invalidé.
- **Google Places** : le code appelle `maps.googleapis.com`, c'est-à-dire l'**API legacy**. Toute la modélisation en SKU Essentials/Pro/Enterprise (API New) est rattachée à la mauvaise grille.

### 2.1 SERP — décision

**RETENU : Google Places API (New), Text Search, comme source primaire de découverte. SerpApi est abandonné avant souscription. Une route SERP est conservée en collecteur de signal, sur Serper.dev.**

Justification, par ordre de force :

1. **Pertinence — l'argument décisif, et il n'est pas économique.** Une API SERP renvoie ce que Google classe bien. La consultante vend à ceux qui sont mal classés : dans `rubric_persona1.yaml`, un score bas est un prospect chaud. Découvrir par le SERP sur-échantillonne mécaniquement le mauvais prospect. Aucun réglage tarifaire ne corrige une anti-corrélation.
2. **Forme de donnée.** `icp/persona1-quebec.yaml` consacre 9 lignes à `domaines_exclus` + `exiger_domaine_propre`, et `discovery.py` 15 lignes de plateformes hébergées. Ces 24 lignes n'existent que pour réparer l'inadéquation de la source. Une API de lieux ne renvoie pas pagesjaunes.ca.
3. **Coût de migration nul.** `google_places` est **déjà câblé** : présent dans `api_pricing.yaml`, appelé par `gbp.py` et `reviews.py` via le bus. Zéro clé nouvelle, zéro budget nouveau, un seul grand livre. Et `api_io.call()` enveloppe une closure arbitraire : le POST + `X-Goog-FieldMask` exigé par Places New passe **sans toucher au bus**.
4. **Pré-alimentation du score.** `rating` et `userRatingCount` arrivent dès la découverte. Les 45 points sur 100 aujourd'hui fabriqués à zéro deviennent connus **avant** de dépenser le moindre token — gain GreenIT non spéculatif, on priorise avant de diagnostiquer.
5. **Continuité de service.** Google a assigné SerpApi le 2025-12-19 ; le rejet des demandes DMCA du 20 juillet 2026 laisse la procédure ouverte, Google ayant confirmé amender. Custom Search JSON API est fermée aux nouveaux clients (fin 2027-01-01), Bing Search API est morte depuis 2025-08-11. Bâtir l'unique canal de découverte sur un intermédiaire de scraping en litige avec son fournisseur amont est une fragilité structurelle. **Le coût de sortie est nul aujourd'hui — aucune clé n'est souscrite. Il ne le sera plus après le premier abonnement.**

**Contrepartie assumée, et elle est réelle** : les Maps Platform Terms interdisent la persistance durable de la plupart des champs Places (`place_id` excepté). Le vault persiste par conception. **Contre-mesure obligatoire, intégrée au design et non rattrapée après** : ne persister que `place_id` + des dérivés non reconstituables (`a_fiche_gbp: bool`, `note_bucket: "4-4.5"`, `avis_bucket: "10-24"`, `repond_aux_avis: bool`), purger les valeurs brutes après scoring, et **implémenter réellement le TTL de cache** (aujourd'hui inexistant — voir §5.4). Le score n'a besoin que des dérivés. Ce point part au dossier du juriste avec J6.

**Rôle résiduel du SERP, qui n'est pas une consolation** : une fois la découverte assurée par Places, « cette entreprise ressort-elle sur `chauffagiste Lévis` ? » cesse d'être un moyen de la trouver et devient **la mesure directe de sa faiblesse SEO locale** — un fait que le prospect vérifie en dix secondes. C'est aussi ce qui alimente le benchmark de cohorte (§3.3). Fournisseur retenu pour cet usage : **Serper.dev** (prépayé, sans abonnement, palier gratuit couvrant tout le pilote). **Sous réserve de vérification** de la règle « 11–100 résultats = 2 crédits » : l'ICP est calé à `max_resultats_par_requete: 10`, exactement au seuil de doublement.

**Écarté : OSM/Overpass** (champ `website` trop inégalement renseigné, or l'URL est l'entrée obligatoire de J1) sauf en recoupement — « absent d'OSM ET absent de Places » est en soi un signal de présence locale nulle. **Écartés pour raison d'invariant, indépendamment du prix : Apify et le mode Standard de DataForSEO** (asynchrones, ils cassent le contrat synchrone de `api_io.call` et son pré-contrôle budgétaire).

### 2.2 Enrichissement contact — décision

**RETENU : cascade déterministe à trois étages. Aucun abonnement d'enrichissement n'est souscrit. Apollo reste câblé mais rétrogradé en recours conditionnel.**

Le raisonnement qui tranche n'est pas le prix, c'est le **régime juridique de la provenance** :

```
site_officiel:<url>#<date>   preuve auto-portée (URL + date + extrait)
apollo:verified              provenance tierce, obligation d'information renforcée
apollo:guessed | likely      déduit par algorithme — ne fonde rien
(absent)                     fiche non actionnable
```

Une adresse extraite du site **fournit sa propre preuve**. Une adresse achetée prouve seulement qu'un tiers la détenait : ce n'est pas le même fait juridique. Et une adresse fonctionnelle (`contact@`) n'identifie pas une personne physique — c'est un cran entier de régime en moins, parfaitement cohérent avec le `Contact` à 6 champs déjà revendiqué.

**Correction de fait, importante** : `enrichment.py` stocke aujourd'hui dans `contact_email_source` le champ `email_status` d'Apollo, c'est-à-dire un **statut de vérification**, pas une provenance. Le champ ne remplit donc pas la fonction de piste d'audit qu'on lui prête. Il doit porter la provenance ; le statut de vérification va dans un champ distinct.

**Les trois étages :**
- **Étage 1 — `contact_site.py`** (nouveau collecteur, palier 0, coût marginal zéro). `website.py` télécharge déjà le HTML via le bus. On en extrait les adresses publiées (`mailto:`, `/contact`, `/a-propos`, mentions légales, JSON-LD Organization), et une mention de refus de prospection détectée sur la page devient `opt_out: true`.
- **Étage 2 — registres publics, en dump local**, pour les données **d'entreprise** uniquement (REQ Québec bimensuel, puis Zefix/UID, puis Sirene). Un dump n'est pas un appel réseau par prospect : c'est de la ROM locale, coût marginal nul, excellent GreenIT. **Aucun nom de dirigeant n'est recopié** — voir §4.
- **Étage 3 — enrichisseur payant, en recours strict sur le résidu**, au coup par coup, modèle « payé au résultat » de préférence. Dropcontact en premier choix (recomposition algorithmique sans base, éditeur français, indifférent à la notoriété de la cible — le seul dont la couverture ne s'effondre pas sur une TPE francophone).

**Verdict sur Apollo** : ne pas souscrire. Sa couverture se dégrade hors SaaS nord-américain, et notre cible est le pire cas possible — un installateur de 5 à 30 personnes à Lévis ou Bulle, dont le dirigeant n'a souvent aucun profil exploitable. Il n'existe **aucune mesure publique** du taux de succès de ces outils sur ce segment : je ne vais pas en inventer une. Le code reste en place, `PersonEnrichment` est proprement isolé derrière `api_io.call` ; le remplacer coûte une trentaine de lignes.

**Règle de décision posée AVANT le test, pour ne pas être rationalisée après** — test sur 50 domaines HVAC québécois réels, coût zéro, paliers gratuits uniquement :
- socle interne > 60 % de couverture → **aucun abonnement**, recours au coup par coup ;
- 40–60 % → socle + Dropcontact au palier le plus bas ouvrant l'API, sur le résidu ;
- < 40 % → examiner d'abord **pourquoi** : sur des entreprises à domaine propre, un taux bas signale plus probablement un défaut du collecteur qu'une absence réelle d'adresse publiée.
- Symétriquement : si les enrichisseurs gratuits échouent sur plus d'un domaine sur deux, **aucun abonnement payant n'est justifiable, quel que soit son prix**.

### 2.3 Modélisation tarifaire — deux règles pour la Phase D

1. Pour un fournisseur à abonnement, le `prix_par_unite` honnête n'est **pas** le prix nominal du crédit mais le **plancher mensuel divisé par les unités réellement consommées**. À 25–50 unités/mois, 86 à 95 % de la dotation d'un palier d'entrée est perdue chaque mois. Saisir le prix nominal ferait sous-estimer le coût réel d'un facteur 10 à 20 dans `api_usage.log` et sur l'écran GreenIT du cockpit. Prévoir une entrée de **coût fixe mensuel distincte** du coût à l'unité.
2. `budgets.apollo.unites_max.credits` doit être calé sur `max_enrichissements` (25/run), pas sur la dotation du plan : le garde-fou reflète l'intention d'usage, pas la générosité du vendeur. Et **les budgets SERP et Apollo doivent être posés ensemble** : la consommation réelle est de 18 requêtes SERP pour ≤ 25 crédits Apollo par run, donc les valeurs suggérées (500/50) font mordre Apollo 13 fois plus tôt que le SERP.

---

## 3. DÉCISION D'ARCHITECTURE

### 3.1 LOT 0 — Véracité (bloquant absolu, aucune clé requise, part immédiatement)

Ce lot n'est pas une amélioration. **Tant qu'il n'est pas livré, aucun run réel ne doit avoir lieu et aucun message ne doit partir**, parce que le système fabrique aujourd'hui des affirmations fausses et les met en tête d'export.

Reproduction vérifiée sur un site parfait sur tous les signaux observables, sans clé Places :

```
site_web 100 | presence_locale 0 | avis 0 | seo_local 100 | identite_visuelle 100 | global 55.0
haute | presence_locale | "Fiche Google Business non vérifiée (à confirmer en J3)"
SIGNAL_CHAUD -> "Fiche Google Business non vérifiée (à confirmer en J3)"
```

Le meilleur prospect possible plafonne à 55/100 et repart avec quatre affirmations fausses, dont une en tête de l'export Kemana. **Chaque ligne de l'export part aujourd'hui avec la même accroche non vérifiée.** Ce n'est pas un biais, c'est une fabrication, et elle viole frontalement l'invariant J1 n°4.

| # | Module | Nature | Contenu |
|---|---|---|---|
| 0.1 | `diagnostic/scoring.py` | MODIFIER | Trois états `ok`/`échec`/`inconnu`. `_check_passes` cesse de retourner `False` sur `None`. Renormalisation du score sur les seules dimensions connues. **Aucune faille émise pour un signal inconnu.** |
| 0.1b | `diagnostic/collectors/website.py` | MODIFIER | **Ajouté au lot par la revue, non négociable.** Sur échec de fetch, le collecteur retourne `https: False` — pas `None`. Un timeout continuerait donc d'émettre « Pas de HTTPS » après 0.1. Et les deux chemins d'échec du module divergent (sans URL, `https` est absent → `None` ; sur fetch raté, `https` = `False`). À unifier sur `None`. **Sans ce point, 0.1 ne ferme pas la fabrication qu'il vise.** |
| 0.1c | `knowledge/greenit.yaml` | MODIFIER | **Ajouté au lot par la revue.** 0.1 supprime des failles et renormalise le score à la hausse (55 → ~100 sur mon repro). Les seuils d'escalade sont `nb_failles >= 6` et `score_global >= 75` : après 0.1, ce sont **les meilleurs prospects qui basculent systématiquement sur le modèle cher**. Recalibrer dans le même lot, sinon l'invariant « escalade à déclencher, pas à subir » tombe. |
| 0.2 | `knowledge/rubric_*.yaml` + `scoring.py` | MODIFIER | Champ `gravite` explicite par check. Aujourd'hui `_severity` divise par le total de la dimension : `site_web` a 6 checks, son ratio maximal est 0,25 → **« Site web inaccessible » ne peut jamais être classé « haute »**, tandis que `gbp.verified` (0,6) l'est toujours. La gravité est un jugement marketing, pas une division. **Test de non-régression obligatoire sur `signal_chaud`** : 0.2 redistribue `hautes[0]`, donc change la colonne « Signal chaud » de tout export existant. |
| 0.3 | `diagnostic/collectors/gbp.py` | MODIFIER | `verified = business_status == "OPERATIONAL"` signifie « pas fermé », **pas** « fiche vérifiée par son propriétaire ». Le libellé de faille est faux **même avec une clé valide**. Renommer signal et faille, ou trouver le champ Places qui porte réellement l'information. |
| 0.4 | `diagnostic/serializers.py` | MODIFIER | Règle dure : **`signal_chaud` ne peut être dérivé que d'un signal dont la valeur est non nulle et vérifiée.** Un `Gap` issu d'un signal inconnu ne peut jamais y accéder. |
| 0.4b | `diagnostic/serializers.py` | MODIFIER | **Correction d'une affirmation fausse de la revue OSINT** : en l'absence de failles, `signal_chaud` retombe sur `diag.accroche`, c'est-à-dire du **texte LLM non marqué exporté en CSV**. Branche atteignable dès qu'une clé Places est présente sur un bon prospect. Marquage IA à traiter là, pas seulement dans `diagnostic_to_rapport_md`. |
| 0.5 | `diagnostic/enrichment.py` | MODIFIER | `_nb_enrichissements` n'est incrémenté **que si un contact est extrait** (vérifié). Un appel Apollo infructueux consomme le fournisseur sans consommer le quota : `max_enrichissements` ne plafonne pas les appels facturés. |
| 0.6 | `diagnostic/api_io.py` | MODIFIER | **Le TTL de cache n'existe pas.** `greenit.yaml` déclare `cache_ttl_jours: 30`, `greenit.py` le lit, `_lire_cache` ne teste que `path.exists()` (vérifié). Conséquences : le levier GreenIT n°3 est inerte, rejouer un ICP ne produira jamais rien, et la limite contractuelle de 30 jours des Maps Platform Terms n'est pas tenue. **TTL par fournisseur**, pas global. |
| 0.7 | `diagnostic/collectors/website.py` | MODIFIER | Cache autonome qui écrit sur disque sans émettre de `LedgerEntry`. À faire passer par le bus. |
| 0.8 | `diagnostic/api_schema.py` | MODIFIER | `compute_cout` retourne `0.0` sur `KeyError` : un fournisseur mal orthographié dans le YAML produit un coût nul silencieux. À faire lever. |
| 0.9 | `diagnostic/preflight.py` | MODIFIER | `_check_garde_fous_bus` passe de la **liste explicite de 8 modules au `rglob`** sur `diagnostic/**`. Ferme la classe de défaut au lieu de la rouvrir à chaque nouveau module. Referme au passage la dette technique n°2 du CLAUDE.md. |

**Effort : moyen. Gain : le système cesse de mentir.** Aucune clé, aucun coût, tout reproductible hors ligne.

### 3.2 LOT 1 — Câbler ce qui est déjà collecté et jeté (coût API : zéro)

Cinq signaux sont produits par les collecteurs et absents de la rubrique : `reviews.repond_aux_avis`, `reviews.date_dernier_avis`, `website.derniere_maj` / `fraicheur_mois`, `social.plateformes_mentionnees`, `website.title_len`. Ces données sont **déjà payées**. Les intégrer est une pure édition YAML — et ce sont précisément celles que la recherche sectorielle désigne comme discriminantes (récence et réponse aux avis).

À recalibrer dans le même geste : `reviews.count >= 10` est trop bas (barème : `< 10` critique, `10–24` faible, `≥ 25` correct). `reviews.avg >= 4.0` est à peu près juste mais non discriminant — la quasi-totalité des installateurs est au-dessus.

**Effort : faible. Gain : élevé.** Meilleur rapport du chantier après le lot 0.

### 3.3 LOT 2 — Collecteurs gratuits à fort rendement — DÉCISION TRANCHÉE

**RETENUS — trois collecteurs, tous palier 0, tous sur du HTML déjà téléchargé, tous héritant de `Collector` et passant par `api_io` :**

| Module | Nature | Justification |
|---|---|---|
| `diagnostic/contact_site.py` | **AJOUTER** | Étage 1 de la cascade (§2.2). Coût marginal nul, provenance auto-portée, détection d'opt-out. **Effort réel supérieur à l'annonce** : doit porter `robots.txt` (jamais consulté aujourd'hui — vérifié), avec son propre cache et sa politesse par hôte, plus 3 chemins de repli d'URL. On passe de « une requête par cible » à ~4 : la convention doit être amendée explicitement, pas contournée. |
| `diagnostic/legitimite.py` | **AJOUTER** | Regex sur HTML déjà en mémoire : licence RBQ (Québec), mention RGE (France — **gate dur sur MaPrimeRénov'**, donc le signal le plus discriminant du marché français), suissetec (Suisse), et mention nominative du programme de subvention en vigueur. Gratuit, très discriminant, spécifique au marché. Le code de sous-catégorie RBQ doit être sourcé avant d'entrer dans le YAML. |
| Extension de `website.py` — joignabilité | **MODIFIER** | Aujourd'hui un seul booléen `has_contact` à 5 % du score total, alors que la vitesse de réponse est le levier de conversion le plus cité du secteur. Signaux sans appel supplémentaire : lien `tel:` (le sélecteur **existe déjà**), nombre de champs du formulaire, prise de RDV en ligne, horaires publiés, mention urgence/24-7. |
| Benchmark de cohorte | **AJOUTER** (dérivé, 0 appel) | J4 récupère déjà jusqu'à 10 concurrents par requête. Calculer la médiane de cohorte et y positionner le prospect ne coûte **rien**. « Vous êtes 8e sur 10 sur la récence des avis dans votre secteur » vaut dix fois « 62/100 ». **Plus gros gain de valeur perçue pour le coût le plus faible du lot.** |

**ÉCARTÉS, et c'est une décision, pas un report indéfini :**

| Module | Décision | Motif |
|---|---|---|
| `domaine.py` (DNS/MX) | **SUPPRIMÉ du plan** | Signal faible, et les deux artefacts se contredisent sur son passage par le bus. Ne pas créer un risque d'invariant pour ça. |
| `registre.py` (REQ/Zefix/Sirene) | **REPORTÉ, hors périmètre à 6 mois** | Effort élevé, point dur non résolu (rapprochement d'entités sans faux positif). Aucune porte bloquante ne doit en dépendre. |
| `archive.py`, `perf.py`, `stack.py`, `emploi.py` | **ÉCARTÉS** | Quotas non sourcés, dépendances instables (crt.sh sur endpoint non documenté), rendement marginal. Une micro-structure sans astreinte ne prend pas ces dépendances. |
| Meta Ad Library | **NON RETENU** | Accès conditionné à une application approuvée et une identité vérifiée ; l'interrogation automatisée de l'interface web est contraire aux conditions de Meta. Aucun des deux artefacts ne le signalait. |
| BuiltWith / Wappalyzer payants | **NON ACHETÉS** | La détection de stack se fait sur le HTML déjà en mémoire. La « licence MIT » du fork proposé est une affirmation juridique non sourcée : nommer le fork et lire son `LICENSE` avant toute intégration. |

### 3.4 LOT 3 — Deux axes au lieu d'un score

**Décision : séparer le score de faille (gravité du problème) du score de capacité (orthogonal), et croiser.**

Mélanger les deux dans un score unique est une erreur de conception, et la relation est non monotone : score 15–25 = besoin maximal mais souvent artisan sans budget (faux positif classique) ; 80+ = aucun besoin perçu ; **40–70 = investit déjà mais mal, a prouvé sa disposition à payer, et le problème est démontrable.** C'est la bande utile.

**Correction d'une affirmation fausse à ne pas propager** : `run_export.py` ne trie **pas** sur `score_global` — vérifié, il ne trie **pas du tout** (`collect_fiches_exportables` renvoie l'ordre brut de `vault_io.query()`). Le vrai défaut n'est pas un biais de tri, c'est un ordre de sortie non déterministe.

Signaux de capacité, dont **trois sont déjà collectés** : `reviews.count` (meilleur proxy gratuit de taille — et sous un plancher bas, critère de **disqualification**, pas de faille à mentionner), `website.derniere_maj` (un site figé depuis 4 ans = entreprise qui n'investit pas), `reviews.repond_aux_avis` (quelqu'un s'occupe du marketing = décideur sensibilisé), et la qualité de l'email (`guessed` ≠ contactable — **prédit un bounce, qui dégrade la délivrabilité du domaine émetteur pour tous les prospects suivants**).

**Sous contrainte impérative de la revue** : tous les seuils sont marqués `[À CALIBRER]`, sortis dans un YAML unique, et **aucune disqualification automatique n'est activée** tant qu'un run borné n'a pas produit une distribution réelle. Les seuils des artefacts étaient calibrés sur le score d'avant le lot 0 — celui que le lot 0 déplace.

### 3.5 LOT 4 — Instrumentation de la boucle d'apprentissage

| # | Objet | Contenu |
|---|---|---|
| 4.1 | `motif_rejet` | **Le trou le plus coûteux du système.** `vault_io` journalise « ancien→nouveau acteur=X » et rien d'autre. Sans motif, un taux de rejet de 60 % ne dit pas s'il faut corriger l'ICP, les filtres, la rubrique ou l'enrichissement. Liste fermée de 5–6 motifs. `extra="allow"` sur `FicheProspect` le permet sans changer le schéma. |
| 4.2 | Jointure des journaux | `api_usage.log` identifie une fiche par nom d'entreprise, `runs.log` par slug. Tant que la jointure n'est pas faite, **le coût par prospect *qualifié* — la seule métrique de coût qui intéresse un commercial — n'est pas calculable.** Journaliser le slug **en plus** du nom dans `LedgerEntry` (champ optionnel, rétro-compatible, exactement comme les 7 champs GreenIT). |
| 4.3 | Export enrichi | Trois champs **déjà présents dans `FicheProspect`** sont absents des 10 colonnes : `gaps_majeurs` (le commercial n'a qu'une seule preuve ; si le prospect la balaie, la conversation est morte), `accroche` (on paie un LLM pour une phrase que personne ne voit) et `date_diagnostic` (**une preuve non datée n'est pas utilisable** — si le constat a six semaines et que le site a été refait, l'accroche se retourne contre l'émetteur). Plus le lien vers le rapport, la ville, le téléphone. Cible 13–15 colonnes. `export.py` doit gagner le support des chemins pointés (3 lignes). **Pure édition YAML pour le reste.** |
| 4.4 | États `rdv` et `client` | Avec date et montant. Sans eux, aucun coût par rendez-vous ni ROI n'est calculable, et l'ensemble du système reste **invérifiable économiquement**. |

**Métrique la plus importante, et elle est déjà calculable sans une ligne de code** : le délai de validation humaine (Δ entre le `ts` de `diagnostique` acteur=agent et celui de `valide`/`rejete` acteur=humain). **Personne ne la calcule.**

### 3.6 Ce qui est explicitement REPORTÉ hors périmètre 6 mois

Trois rubriques et trois ICP par marché (juste sur le fond — le régime de consentement, le moteur de demande et la grammaire de légitimité diffèrent, pas seulement la langue — mais c'est un trimestre, pas une semaine) · `registre.py` · les 9 blocs et ~90 champs du schéma OSINT complet · les 4 pipelines d'ingestion de dumps · le nœud « Conformité » bloquant · J6 sous toutes ses formes.

**Confirmé sans réserve : la séquence Québec → Suisse → France reste la bonne**, mais pour une raison différente de celle attendue. Ce n'est pas la difficulté juridique croissante (le Québec est le plus strict, CASL étant en opt-in y compris B2B), c'est la **ligne de base de confiance décroissante** : on apprend là où l'accueil est neutre, on affine là où le ticket est élevé, on n'attaque la France qu'avec un livrable déjà irréprochable.

---

## 4. LE DOSSIER OSINT CIBLE

Le schéma à 9 blocs est rejeté. **Trois blocs sont retenus**, tous alimentés par des collecteurs qui existent ou qui sont au lot 2.

| Bloc | Contenu | Palier | Source |
|---|---|---|---|
| **Noyau existant** | Inchangé, ne pas toucher | — | déjà là |
| **`presence_numerique`** | Signaux site (https, mobile, meta, logo, fraîcheur), joignabilité (tel, formulaire, RDV, horaires), SEO local, plateformes sociales | **gratuit** | `website.py`, `seo.py`, `social.py` |
| **`reputation_locale`** | `place_id`, `a_fiche_gbp`, `note_bucket`, `avis_bucket`, `repond_aux_avis`, `recence_dernier_avis` | **payant, quota gratuit** | Places, **dérivés uniquement** |
| **`legitimite`** | RBQ / RGE / suissetec, mention du programme de subvention | **gratuit** | `legitimite.py` (regex, HTML déjà en mémoire) |
| **`tracabilite`** | Provenance réelle de l'email (URL + date), statut de vérification, horodatage par bloc | **gratuit** | dérivé |

**Ce qui est gratuit porte l'essentiel de la valeur** — et c'est la correction stratégique la plus importante du diagnostic d'architecture : aujourd'hui 45 points sur 100 dépendent d'une clé absente, pendant que la couche de collecte gratuite et déterministe est sous-développée (cinq collecteurs, dont deux produisent un booléen chacun, dont un — `social` — n'est câblé à aucune règle de la rubrique). **Toutes les décisions ci-dessus déplacent le poids du score vers ce qui s'observe sans clé.**

### La ligne rouge de minimisation, que je ne franchis pas

1. **`Contact` reste figé à 6 champs, `extra="forbid"` inchangé.** Toute métadonnée de conformité va dans un bloc séparé : c'est de la métadonnée de traitement, pas de la donnée sur la personne. La revendication « 6 champs » reste littéralement vraie.
2. **Aucun nom de dirigeant issu d'un registre public n'entre dans le vault.** Recopier ces noms transforme un registre légal en fichier de prospection nominatif : c'est un changement de finalité. On persiste des données d'**entreprise** (`anciennete_annees`, `forme_juridique`, `tranche_effectif`, `statut_administratif`). Si la consultante veut le nom du dirigeant, elle ouvre le registre à la main, prospect par prospect — c'est exactement à cela que sert la porte humaine. **L'argument est juridique ; je retire le chiffrage « trente secondes par prospect » qui n'est adossé à rien.**
3. **`adresse_siege` est retirée du schéma.** Dès que l'entreprise est individuelle — cas fréquent en HVAC — c'est l'adresse du **domicile**. Aucun check de scoring ne l'utilise, aucune finalité n'est déclarée. Collecter sans usage est du gonflement pur.
4. **Zéro scraping LinkedIn / Facebook.** Inchangé, déjà tenu par construction.
5. **`opt_out: true` → exclusion absolue**, sans exception, de tout export et de tout outreach. Inchangé.
6. **Préférer systématiquement l'adresse fonctionnelle** (`contact@`) à l'adresse nominative : ce n'est pas un pis-aller, c'est un régime juridique en moins. Le champ `contact_type` **n'est pas** une réduction d'exposition (il ajoute un 6e champ personnel au niveau fiche) — il permet de préférer, c'est tout. Formulation à corriger, champ à garder.
7. **Liste de suppression** : si elle est créée, elle doit avoir un **écrivain unique et journalisé**, et un mécanisme de durabilité. Un fichier gitignoré est perdu au premier reclonage — ce qui réactiverait silencieusement l'enrichissement de personnes qui s'y sont opposées, précisément le scénario qu'il prétend éviter. Un hash d'email reste une donnée pseudonymisée au sens du RGPD.
8. **Sirene et le REQ exposent des entrepreneurs individuels.** Sirene applique un statut de diffusion restreinte pour ceux qui s'y sont opposés : **c'est un opt-out réglementaire qui doit se propager dans le champ `opt_out`** et son exclusion absolue à l'export.
9. **La grille d'utilisabilité juridique de la provenance email est marquée `[À VALIDER PAR UN JURISTE], par marché.** L'artefact d'architecture écrivait « site_officiel → CASL/nLPD/RGPD : utilisable ». Le raisonnement CASL tient ; l'extension aux trois régimes ne tient pas. En Suisse, l'art. 3 al. 1 let. o LCD vise la publicité de masse **sans égard** au fait que l'adresse soit publiée. Côté RGPD, l'extraction automatisée depuis des sites tiers est de la collecte indirecte au sens de l'art. 14, avec obligation d'information **dans le mois** — que le schéma rattachait au premier message J6, donc potentiellement bien après. **Dans un projet dont l'invariant est « J6 exige un juriste avant tout envoi », cette grille tranchait par anticipation la question centrale. Elle ne tranche plus rien.**

**Écart de conformité confirmé et ouvert** : `robots.txt` n'est jamais consulté avant le fetch (`grep -rn "robots" --include=*.py` ne retourne rien), et il n'existe aucune notion de conservation, purge ou rétention dans `vault_io.py` ni `vault_schema.py`.

---

## 5. CE QUI RESTE NON ÉTABLI

### 5.1 L'état du système, sans euphémisme

**`knowledge/api_pricing.yaml` a tous ses prix et budgets à `0`, `releve_le: null`. `run_preflight.py` renvoie NO-GO, code de sortie 1 — re-exécuté à l'instant.** 9 familles de contrôles, **14 assertions bloquantes en échec** : 2 clés API absentes, 6 tarifs à zéro, 2 budgets à zéro, 4 répertoires de vault absents.

*(Au passage, l'incohérence signalée par la revue chiffrée entre « 9 contrôles » du CLAUDE.md et « 14 contrôles bloquants en échec » du mandat est levée : les deux sont exacts, à deux granularités différentes — 9 fonctions de contrôle, 14 assertions bloquantes en échec. À formuler explicitement pour ne pas la reposer.)*

**Aucun coût affiché par ce système ne vaut autre chose que 0,00 et n'est engageant. Aucun run réel n'a jamais eu lieu. Le vault n'est pas initialisé.**

### 5.2 Chiffres non vérifiés — aucun n'engage quoi que ce soit

| Sujet | Statut |
|---|---|
| SerpApi, Apollo, Google Places, Brave, Serper, Dropcontact, Hunter, Anymailfinder, BuiltWith, Wappalyzer | **Aucune page tarifaire lue.** 403 sur toutes. Tous les chiffres viennent de recherches web sur des agrégateurs. |
| Accès API Apollo — quel palier ? | **NON TROUVÉ, et bloquant.** Si Organization est requis (min. 3 sièges), le statu quo passe de ~588 à ~4 284 USD/an et le classement économique s'inverse. |
| Places — quel SKU pour notre masque de champs ? | **NON ÉTABLI.** Le quota gratuit varie d'un facteur 5 selon la réponse (5 000 Pro vs 1 000 Enterprise). Et le code appelle l'API **legacy**, qui a sa propre grille. |
| Places — `place_details`, pagination | **NON TROUVÉ.** Chaque page de Text Search est un appel facturé : les estimations « coût par run » supposent un appel unique et **sous-estiment**. |
| Couverture réelle des enrichisseurs sur des TPE de 5–30 personnes au Québec / en Suisse romande | **AUCUNE mesure publique n'existe.** Toute la partie « couverture » repose sur une inférence argumentée, jamais sur une mesure. |
| Part des sites de TPE publiant une adresse email exploitable | **AUCUNE étude trouvée.** L'hypothèse centrale du socle gratuit est **plausible et non démontrée**. C'est précisément pourquoi on la mesure avant de dépenser. |
| Coût LLM par fiche, part des postes dans le coût variable | **Non mesurable.** Les tokens d'entrée sont une estimation, aucun appel LLM n'a jamais eu lieu, tous les prix du grand livre valent 0. Les « 0,5 à 2 cents » et les « ~95 % » sont retirés. La conclusion (le token n'est pas le levier) tient sur `max_tokens_sortie: 600`, qui est vérifiable. |
| Chiffres « speed to lead » du secteur HVAC (78 %, 73 %, 42 min) | **Blogs de fournisseurs de logiciels HVAC — parties prenantes, non audités.** Le fond est solide, les pourcentages ne le sont pas. **Ne jamais les citer comme faits dans un audit livré à un client.** |
| Quotas gratuits (PageSpeed, Overpass, France Travail, Wayback) | Non sourcés, non datés. À traiter comme `api_pricing.yaml` : donnée YAML avec `releve_le`, pas constante de document. |

**Attention au mécanisme précis par lequel une étude devient une décision budgétaire fausse** : la formule « Coût réel pour le volume du projet : 0,00 USD » énoncée au présent de l'indicatif dans un verdict, alors que les montants et quotas sous-jacents sont rapportés par des tiers. **Tout énoncé de coût reste au conditionnel jusqu'à la Phase D.**

### 5.3 Réserves de revue non levées

- **Aval architecture toujours `false`.** Les 6 conditions sont portées au lot 0 (§6). Le lot 1 ne part pas avant qu'elles soient traitées.
- **Tension Maps Platform Terms non résolue** : le cache disque a un TTL global de 30 jours **non implémenté**, et le vault persiste des valeurs Places brutes. Les recommandations qui étendent l'usage de Places **aggravent** l'exposition sans la lever. La contre-mesure (dérivés uniquement + TTL par fournisseur + purge après scoring) conditionne la recommandation §2.1. **Au dossier du juriste avec J6.**
- **Contradiction suisse non tranchée** : nLPD (pas d'opt-in B2B préalable) vs art. 3 al. 1 let. o LCD (consentement préalable pour la publicité de masse). Les sources se contredisent. **C'est exactement pourquoi le double verrou sur J6 reste en place.**
- **Licences de réutilisation non vérifiées** : Données Québec / REQ, RBQ, Zefix, Sirene, ODbL d'OSM, CGU du répertoire CMMTQ. Aucune n'a été lue. Pré-condition bloquante avant toute intégration.
- **Note AI Act, à ne pas sur-interpréter** : l'art. 50 s'applique depuis aujourd'hui. Le risque réel n'est pas l'étiquette, **c'est de qualifier de « diagnostic » un résultat produit par des stubs.** On règle la véracité (lot 0) avant l'étiquetage. Analyse de périmètre, pas avis juridique.

### 5.4 Ce que j'ai vérifié moi-même dans le code avant de trancher

`scoring.py::_check_passes` retourne bien `False` sur `None` · `_severity` divise bien par le total de dimension · `api_io::_lire_cache` ne teste que `path.exists()`, aucun TTL · `enrichment.py` n'incrémente `_nb_enrichissements` que si un contact est extrait · `website.py` retourne `https: False` sur fetch raté et omet la clé sans URL — deux chemins d'échec incohérents · `export.py` ne trie pas du tout · seuils de routage GreenIT confirmés à `nb_failles >= 6` et `score_global >= 75` · `run_preflight.py` NO-GO, exit 1, 14 assertions bloquantes en échec · **536 tests verts en 14,11 s, sans aucune clé API.**

---

## 6. PROCHAINES ACTIONS ORDONNANCÉES

### Étape 1 — DÉVELOPPEMENT — Lot 0 « Véracité » + les 6 conditions de levée d'aval
**Effort : moyen (une itération pleine). Gain : le système cesse d'émettre des affirmations fausses. BLOQUANT ABSOLU.**

Les 12 correctifs du §3.1, **plus** les 6 conditions posées par la revue, traitées comme des assertions de la porte 97 % :
1. Corriger les 4 affirmations fausses des artefacts, dont les 2 qui portaient une conclusion (le tri de l'export ; le texte LLM dans le CSV et sa conséquence art. 50).
2. Acter par écrit la suppression de `domaine.py` (contradiction de bus close par élimination).
3. Déclarer la porte `pret_a_contacter` et les disqualifications automatiques **annulées**, non recalibrées.
4. Intégrer `website.py` (`https: False` → `None`) et la recalibration des seuils GreenIT au lot 0.1, et retirer la thèse « trente lignes dans `scoring.py` ».
5. Retirer ou marquer `[NON SOURCÉ]` les 22 chiffres externes, en particulier les coûts en cents et les deux pourcentages de coût.
6. Requalifier `[À VALIDER PAR UN JURISTE]` la grille de provenance email pour la Suisse et la France ; reclasser Meta Ad Library (non retenu) et crt.sh (écarté).

Plus : test de non-régression `signal_chaud` (0.2 le redistribue), et `test_doc_coherence` recompté.

### Étape 2 — DÉVELOPPEMENT — Lot 1 « Signaux déjà payés »
**Effort : faible (édition YAML + tests). Gain : élevé.** Récence et réponse aux avis, fraîcheur du site, plateformes sociales, recalibrage des seuils d'avis. Zéro appel API.

### Étape 3 — PARAMÉTRAGE (opératrice) — Le relevé tarifaire réel
**Effort : une demi-journée. Gain : lève le NO-GO structurel.**
Ouvrir, dans un navigateur non bloqué : `serpapi.com/pricing` (pour mémoire, on en sort), `apollo.io/pricing` **et `docs.apollo.io` pour trancher le palier d'accès API**, `developers.google.com/maps/billing-and-pricing/pricing` **champ par champ pour établir le SKU réel**, `serper.dev`, `dropcontact.com/pricing`, `platform.claude.com/docs/en/pricing`. Puis saisir dans `api_pricing.yaml` avec `releve_le: 2026-XX-XX`, en appliquant les deux règles de modélisation du §2.3. **Aucun chiffre de ce document ne sert à cette étape — il sert à savoir quelles pages ouvrir.**

### Étape 4 — PARAMÉTRAGE (opératrice) — Le test à coût zéro qui tranche
**Effort : une après-midi. Gain : remplace toutes les inférences de couverture par des mesures.**
Sur les 6 localités de l'ICP et 50 domaines HVAC réels, avec les paliers gratuits uniquement :
- **Places Text Search vs Serper** : nombre d'établissements HVAC trouvés, **taux de renseignement du site web** (critère éliminatoire — sans URL, pas de J1), disponibilité de la note et du nombre d'avis.
- **Socle interne vs enrichisseurs gratuits** (Prospeo, Hunter, Apollo free) : taux d'extraction d'une adresse exploitable vs taux de découverte d'un décideur nommé avec email vérifié.
- **Appliquer la règle de décision du §2.2, posée à l'avance.**

### Étape 5 — PARAMÉTRAGE (opératrice) — Premier run borné
`python init_vault.py` · `python run_preflight.py` jusqu'à **GO** · `run_discovery.py --icp persona1-quebec --dry-run` · puis `run_pipeline.py --icp persona1-quebec --dry-run` · puis **un** run réel, 18 requêtes, ≤ 25 contacts.
**Mesurer les trois chiffres qui manquent depuis le début : temps de validation par fiche, taux de rejet, coût réel par prospect qualifié.**

### Étape 6 — DÉVELOPPEMENT — Lot 4 « Boucle d'apprentissage »
**Effort : faible à moyen. Gain : le meilleur rapport valeur/effort du chantier après le lot 0.**
`motif_rejet` · jointure des journaux par slug · export à 13–15 colonnes (essentiellement du YAML). **Sans `motif_rejet`, il n'y a pas de boucle d'apprentissage : un taux de rejet de 60 % ne dit rien.**

### Étape 7 — DÉVELOPPEMENT — Lot 2 « Collecteurs gratuits »
`contact_site.py` (avec `robots.txt` et sa politesse — l'effort est supérieur à l'annonce) · `legitimite.py` · extension joignabilité de `website.py` · **benchmark de cohorte** (0 appel, plus gros gain de valeur perçue du lot).

### Étape 8 — DÉVELOPPEMENT — Lot 3 « Deux axes », seuils `[À CALIBRER]`
Uniquement **après** que l'étape 5 ait produit une distribution réelle. Aucune disqualification automatique activée avant.

### Étape 9 — JURIDIQUE, en parallèle et sans dépendance
Un seul dossier, un seul juriste : régime CASL (consentement tacite par publication manifeste) · contradiction nLPD / art. 3 al. 1 let. o LCD · LIA RGPD documentée pour la France · conservation des champs Google Places dans le vault au regard des Maps Platform Terms · licences de réutilisation des registres publics · périmètre AI Act art. 50. **C'est un prérequis daté, pas une tâche de fond, et il conditionne J6 en totalité.**

---

## LA PHRASE À RETENIR

Le système sait produire des dossiers de prospect à coût marginal négligeable. Il ne sait pas encore **dire lesquels valent la peine d'être contactés**, ni **prouver qu'un contact produit du revenu** — et surtout, **il affirme aujourd'hui des choses qu'il n'a jamais observées.** L'ordre des priorités en découle mécaniquement : d'abord ne plus mentir, puis exploiter ce qui est déjà collecté, puis mesurer, et seulement ensuite dépenser. Le double verrou sur J6 reste en place, et le NO-GO du préflight est un garde-fou qui fonctionne — pas un obstacle à contourner.

---


<a id="s2"></a>

## 2. Besoin marketing — CMO


# Qualification du besoin marketing — Kemana-Flow / persona 1 HVAC

Relevé du 2026-08-02. Toutes les affirmations sur le code sont vérifiées par lecture directe des fichiers cités. Toutes les affirmations de marché portent leur source et leur niveau de fiabilité.

---

## 1. Le vrai problème marketing de la consultante

**Ce n'est pas « trouver des prospects ». C'est « prouver sa valeur avant de facturer, sans y laisser ses heures facturables ».**

Job-to-be-done, formulé du côté de la contrainte réelle :

> *Quand j'ai trois heures libres entre deux livrables clients, je veux arriver au premier échange en sachant déjà mieux que le dirigeant ce qui cloche dans sa marque — de façon vérifiable — pour vendre un audit payant au lieu d'en offrir un gratuitement.*

Trois mécaniques derrière ça :

- **L'asymétrie de preuve.** Le branding pour PME se vend mal parce que l'acheteur ne peut pas juger la compétence avant l'achat. La seule façon de lever ça en solo est de livrer un fragment d'audit *avant* la vente. Fait à la main, ce fragment coûte 45–90 min par prospect, donc il n'est produit que pour les prospects déjà chauds — c'est-à-dire jamais en prospection. Le système transforme un coût variable non facturable en coût fixe amorti.
- **Le cycle famine/festin du solo.** Elle prospecte quand elle n'a plus de mandats, c'est-à-dire trop tard. L'orchestrateur découplé (`run_pipeline.py`) permet à la production de pipeline de continuer pendant les semaines de livraison. C'est un problème de *cadence*, pas de volume.
- **Ce qui est réellement rare, ce n'est pas le prospect, c'est son attention.** La rubrique YAML est son jugement métier encodé. C'est le seul actif du système qui prend de la valeur avec le temps et qui se transporte d'un persona et d'un marché à l'autre. Le reste (collecteurs, bus, cockpit) est une commodité.

**Le corollaire, qui est aussi le risque n°1** : si le système produit un diagnostic faux ou générique, il ne fait pas gagner du temps — il détruit la seule chose qu'elle vend, sa crédibilité de diagnosticienne. La « porte humaine » Obsidian n'est pas une prudence d'architecte, c'est le cœur du modèle d'affaires. Voir §3, défauts A1–A3 : en l'état, le système produit exactement ce type de faux.

---

## 2. Le problème marketing du prospect (installateur HVAC)

**Lui ne pense pas avoir un problème de marque. Il pense avoir un problème de prix.**

Ce qu'il vit : il est appelé en 3e position sur une soumission, il se fait comparer au dollar près, il perd des chantiers dont il ne saura jamais pourquoi il les a perdus. Sa conclusion spontanée : « les gens ne regardent que le prix ». Job-to-be-done du prospect :

> *Quand un propriétaire demande trois soumissions, je veux être celui qu'il rappelle en premier et avec qui il ne négocie pas — sans baisser mon prix.*

C'est ça, la marque, traduite dans sa langue. Pas « identité visuelle », pas « storytelling » : **être trouvé, être crédible en 90 secondes, être joignable en 5 minutes.**

Ce qu'un diagnostic lui apprend qu'il ne sait pas déjà — il faut être honnête, c'est une liste courte, et c'est celle-là qu'il faut viser :

1. **Ce que voit un inconnu, pas ce qu'il voit lui.** Il connaît son site par cœur ; il n'a jamais mesuré la fraîcheur de ses avis, ni vu que son numéro n'est pas cliquable sur mobile.
2. **Sa position *relative*.** Un score de 62/100 ne veut rien dire pour lui. « Trois de vos cinq concurrents directs sur *installateur thermopompe Lévis* ont reçu un avis dans les 30 derniers jours ; votre dernier date de mars 2025 » est une information qu'il ne peut obtenir nulle part et qui le pique.
3. **Le coût en dollars de chaque faille**, pas sa gravité esthétique.
4. **Le décalage avec la demande subventionnée du moment** (voir §5) — s'il n'affiche pas le programme que tout le monde tape dans Google, il est invisible sur l'intention d'achat la plus chaude du marché.

**Le piège actuel du marché** : la demande est portée par les subventions (LogisVert au Québec — jusqu'à ~1 700–7 840 $ pour une thermopompe air-air selon les sources sectorielles ; Programme Bâtiments en Suisse ; MaPrimeRénov' en France, guichet rouvert le 23 février 2026 avec 3,6 Md€). Il est donc **occupé**, et un installateur occupé croit que son marketing va bien. L'accroche ne peut pas être « vous manquez de clients ». Elle doit être « vous prenez les clients qui vous tombent dessus, pas ceux que vous choisissez » — c'est-à-dire la marge, pas le volume.

---

## 3. Challenge de la rubrique — c'est ici que le travail est le plus rentable

Verdict court : **la rubrique mesure correctement l'hygiène numérique de base, mais elle est aujourd'hui structurellement incapable de produire un diagnostic fiable, et elle ne mesure pas ce qui fait perdre les chantiers.** Trois familles de problèmes, par ordre de gravité commerciale.

### A. Défauts structurels du moteur (à corriger avant toute discussion de pondération)

**A1 — « Inconnu » est scoré comme « échec ».** `diagnostic/scoring.py::_check_passes` retourne `False` dès que `value is None`. Or, sans `GOOGLE_PLACES_API_KEY` (état vérifié aujourd'hui), `gbp.py` renvoie `{"verified": None, "has_photos": None}` et `reviews.py` `{"count": None, "avg": None, ...}`. Conséquence arithmétique : **`presence_locale` = 0/100 et `avis` = 0/100 pour *tous* les prospects, soit 45 % de la pondération fabriquée à zéro.** Et le moteur émet des failles dont le texte l'admet lui-même — « Fiche Google Business non vérifiée (à confirmer en J3) ». Une faille « à confirmer » est une affirmation non adossée à un fait : cela viole frontalement l'invariant J1 n°4 (« aucune affirmation non adossée aux failles réelles »).
*Correctif* : trois états (`ok` / `échec` / `inconnu`), renormalisation du score global sur les seules dimensions connues, et **aucune faille émise pour un signal inconnu**. C'est un changement de `scoring.py`, assumé et testable.

**A2 — La gravité est un artefact du nombre de checks, pas du poids commercial.** `_severity(points, max_points)` divise par le total de la dimension. `site_web` a 6 checks (total 100) : le plus lourd, `mentions_offre`, pèse 0,25 → jamais « haute ». `presence_locale` a 2 checks : `gbp.verified` pèse 0,60 → toujours « haute ». Résultat concret : **« Site web inaccessible ou inexistant » est classé *moyenne*** — la faille la plus grave qu'un prospect puisse avoir est mécaniquement dégradée parce qu'elle cohabite avec cinq autres checks.
*Correctif* : `gravite` explicite par check dans le YAML. La gravité est un jugement marketing, pas une division.

**A3 — Conséquence commerciale directe : `signal_chaud` est constant.** `serializers.py` prend `hautes[0].preuve`, et les failles sont empilées dans l'ordre des dimensions (`site_web`, `presence_locale`, …). Comme `site_web` ne produit jamais de « haute », **la première « haute » est toujours `gbp.verified`**. Autrement dit : aujourd'hui, chaque ligne de l'export Kemana part avec la même accroche — *« Fiche Google Business non vérifiée (à confirmer en J3) »* — une affirmation jamais vérifiée, identique pour tout le monde. C'est le défaut le plus dangereux du système : il transforme un outil de diagnostic en générateur de spam générique. **À corriger avant tout premier envoi.**

### B. Signaux déjà collectés et jetés (coût API marginal : zéro)

Cinq signaux sont produits par les collecteurs et **absents de la rubrique** :

| Signal produit | Fichier | Utilisé par la rubrique ? |
|---|---|---|
| `reviews.repond_aux_avis` | `collectors/reviews.py:79` | **non** |
| `reviews.date_dernier_avis` | `collectors/reviews.py:80` | **non** |
| `website.derniere_maj` / `fraicheur_mois` / `copyright_year` | `collectors/website.py:92-93` | **non** |
| `social.plateformes_mentionnees` | `collectors/social.py:29` | **non** |
| `website.title_len` | `collectors/website.py:83` | **non** |

Ces données sont **déjà payées** (appel Places déjà émis, HTML déjà téléchargé). Les intégrer est une pure édition YAML. Et ce sont précisément celles que la recherche sectorielle désigne comme discriminantes :

- **Récence des avis** : Whitespark 2026 place les signaux d'avis à ~20 % du poids du local pack (contre 16 % en 2023) et la récence dans le top 5 de son fondateur ; 74 % des consommateurs cherchent des avis de moins de trois mois, 32 % de moins de deux semaines ([Whitespark](https://whitespark.ca/local-search-ranking-factors/), [BrightLocal LCRS](https://www.brightlocal.com/research/local-consumer-review-survey/)).
- **Réponse aux avis** : composante explicite des signaux d'avis dans la même étude.

### C. Seuils mal calés contre les données

- `reviews.count >= 10` : **trop bas**. BrightLocal 2026 : **47 % des consommateurs n'utiliseront pas une entreprise ayant moins de 20 avis** ; l'édition 2018 relevait un besoin moyen de ~40 avis pour croire à la note. Passer à un barème (`< 10` critique, `10–24` faible, `≥ 25` correct).
- `reviews.avg >= 4.0` : à peu près juste, mais **non discriminant** — la quasi-totalité des installateurs sont au-dessus. Ce qui discrimine, c'est la récence et la réponse.
- **Aucun check de récence** aujourd'hui, alors que la donnée est collectée (B).

### D. Ce qui manque entièrement — les dimensions qui font vraiment perdre des chantiers

**D1. Réactivité / joignabilité — la plus sous-pondérée.** Aujourd'hui : un seul booléen `has_contact` à 20/100 de `site_web`, soit **5 % du score total**. Or la vitesse de réponse est le levier de conversion le plus cité du secteur. ⚠️ *Attention à la qualité des sources ici* : les chiffres qui circulent (« 78 % des chantiers vont au premier qui répond », « 73 % de prise de RDV sous 60 s », « médiane 42 min ») proviennent de **blogs de fournisseurs de logiciels HVAC** ([Hatch](https://www.usehatchapp.com/blog/hvac-speed-to-lead-response-rates), [PowerChord](https://www.powerchord.com/blog/hvac-speed-to-lead), [PushLeads](https://pushleads.com/how-contractor-lead-response-time-is-killing-your-conversions-and-the-5-minute-f/)) — parties prenantes, non audités. **Ne pas les citer comme faits dans un audit livré au client.** Le fond (la vitesse compte énormément) est solide et remonte à l'étude InsideSales/MIT ; les pourcentages précis ne le sont pas.
Signaux observables sans appel réseau supplémentaire : lien `tel:` présent, formulaire présent + nombre de champs, prise de RDV en ligne, WhatsApp/SMS, chat, horaires publiés, mention urgence/24-7.

**D2. Preuve de légitimité réglementaire — gratuite, très discriminante, spécifique au marché.**
Québec : la licence **RBQ sous-catégorie 15.10** est obligatoire pour installer une thermopompe résidentielle, et le registre RBQ est public et gratuit ([RBQ](https://www.rbq.gouv.qc.ca/en/you-are/citizen/check-a-contractors-licence/)) ; l'appartenance CMMTQ est un marqueur secondaire. Détecter `RBQ\s*:?\s*\d{4}-\d{4}-\d{2}` dans le texte du site coûte zéro appel.
France : la mention **RGE** (Qualibat / Qualit'EnR / QualiPAC) est **obligatoire pour ouvrir droit à MaPrimeRénov'** ([ecologie.gouv.fr](https://www.ecologie.gouv.fr/politiques-publiques/label-reconnu-garant-lenvironnement-rge), [France Rénov'](https://france-renov.gouv.fr/annuaires-professionnels/artisan-rge-architecte)). Un installateur français sans RGE affiché est coupé de la demande subventionnée : c'est le signal le plus discriminant du marché français.
Suisse : IDE/CHE + appartenance **suissetec** (~3 600 entreprises membres ; seuls les membres peuvent afficher le logo — [suissetec](https://suissetec.ch/fr/portrait.html)).

**D3. Ancrage sur la demande subventionnée.** Le site mentionne-t-il nommément le programme en vigueur (LogisVert / Rénoclimat / MaPrimeRénov' / CEE / Programme Bâtiments) ? Détection par regex, coût nul, et corrélé à l'intention de recherche dominante du moment.

**D4. Chemin de conversion commercial** : « soumission gratuite », financement affiché, fourchettes de prix, zone de service explicite.

**D5. Cohérence NAP** (nom / adresse / téléphone identiques entre site, GBP et réseaux) — c'est *ça*, l'identité de marque opérationnelle, bien plus que « a un logo ».

### E. Repondération proposée

`identite_visuelle` à 15 avec `has_logo` + `image_count >= 3` **ne mesure pas la marque** : un site WordPress générique passe les deux checks. Soit on en fait une vraie dimension (cohérence nom/logo/couleurs site ⇄ GBP ⇄ social, photos de chantiers réelles vs banque d'images, cohérence NAP), soit on baisse son poids.

| Dimension | Actuel | Proposé | Justification |
|---|---:|---:|---|
| `presence_locale` (GBP) | 25 | **25** | GBP ≈ 32 % du poids du local pack (Whitespark 2026) |
| `avis` (volume + **récence** + **réponse**) | 20 | **25** | ≈ 20 % du local pack ; 47 % refusent < 20 avis |
| `site_web_conversion` (joignabilité, RDV, formulaire, mobile) | 25 | **20** | recentré sur la conversion, pas la présence |
| `seo_local` | 15 | **15** | inchangé |
| `legitimite_conformite` (RBQ / RGE / suissetec, subventions) | — | **10** | nouveau, gratuit, spécifique au marché |
| `identite_marque` (cohérence NAP, photos réelles) | 15 | **5** | rétrogradée tant qu'elle n'est pas mesurée sérieusement |

### F. L'axe manquant : la capacité à payer — **et ce n'est pas un poids, c'est un second axe**

La question posée est double : repérer une entreprise qui a un vrai problème **et** le budget. Mélanger les deux dans un score unique est une erreur de conception. Il faut un **score de faille** (gravité du problème) et un **score de capacité** (orthogonal), puis croiser :

- faille haute × capacité haute → **cible prioritaire**
- faille basse × capacité haute → pas un prospect (il va bien)
- faille haute × capacité basse → puits de temps

Signaux de capacité observables, par ordre de valeur :

1. **Achat de publicité** — une entreprise qui achète du Google Ads a un budget d'acquisition et une douleur mesurée. SerpApi renvoie un bloc `ads` ; le collecteur existe déjà, il suffit de ne plus le jeter.
2. **Recrutement actif** — page « carrières » / offre d'emploi : croissance + masse salariale.
3. **Badge fabricant** — *Carrier Factory Authorized Dealer*, *Lennox Premier Dealer* (40 h de formation usine exigées + audit satisfaction indépendant), *Daikin Comfort Pro* ([Carrier](https://www.carrier.com/us/en/residential/carrier-factory-authorized-dealers/), [Lennox](https://www.lennox.com/residential/locate/)). Ces programmes exigent un investissement et s'accompagnent souvent de fonds de co-op marketing : c'est une entreprise qui **investit déjà** et qui a de l'argent fléché.
4. **Fraîcheur du site** (`fraicheur_mois` — déjà collecté !) : un site mis à jour dans les 12 mois signifie que quelqu'un est payé pour ça.
5. **Volume d'avis** et **nombre de localités servies** comme proxys de taille.

⚠️ **Défaut commercial actuel** : l'export Kemana trie sur `score_global` seul. Il remonte donc systématiquement les entreprises **les plus petites, les plus cassées et les moins solvables**. C'est l'inverse de la cible.

### G. Le benchmark pairs — le plus gros gain de valeur perçue pour le coût le plus faible

J4 exécute déjà une requête SERP par gabarit × localité et récupère jusqu'à 10 concurrents. Calculer la **médiane de cohorte** (même requête, même localité) et positionner le prospect dedans ne coûte **aucun appel supplémentaire**. « Vous êtes 8e sur 10 sur la récence des avis dans votre secteur » vaut dix fois « 62/100 ». C'est aussi ce qui transforme le livrable en produit défendable.

---

## 4. Ce qui rend une accroche crédible pour ce persona

**Le point de départ est négatif.** Dirigeant-opérateur, lit sur son téléphone entre deux chantiers, sollicité en permanence par des agences SEO. Hypothèse par défaut : c'est du spam. L'accroche ne doit pas convaincre — elle doit **survivre trois secondes**.

Quatre conditions cumulatives :

1. **Un fait vérifiable en 10 secondes, qu'il ne connaissait pas.** Pas une opinion. « Votre dernier avis Google date du 14 mars 2025 » se vérifie ; « votre identité de marque manque d'impact » ne se vérifie pas et se lit comme une insulte.
2. **Une comparaison, pas un absolu.** Le signal déclencheur le plus fort pour ce persona est le concurrent nommé ou dénombré. C'est la fonction du §3.G.
3. **Une traduction en dollars, pas en design.** « 3 soumissions par mois qui partent chez le premier qui répond » et non « votre taux de conversion est sous-optimal ».
4. **Aucune demande autre qu'un oui/non.** Pas de lien de calendrier, pas de PDF de 12 pages en pièce jointe froide.

**Hiérarchie des signaux déclencheurs**, du plus fort au plus faible :
1. Écart mesuré contre les concurrents directs sur la récence des avis.
2. Absence du programme de subvention en vigueur sur le site (= invisible sur l'intention d'achat dominante).
3. Chemin de conversion cassé et démontrable (numéro non cliquable sur mobile, formulaire en erreur).
4. Absence d'affichage de la licence/qualification (RBQ 15.10 / RGE) — touche l'orgueil professionnel autant que le SEO.

**Ne déclenchent rien** : un score sur 100 sans contexte, « votre logo », « votre storytelling », « j'ai remarqué que votre site… » suivi d'une généralité.

**Règle dure à inscrire dans le code** : l'accroche ne doit être générée **que** depuis un signal dont la valeur est non-nulle et vérifiée. Le système viole cette règle aujourd'hui (§3.A3). **C'est le correctif n°1 de crédibilité, et c'est un correctif de code, pas de copywriting.**

**Saisonnalité** : la fenêtre est *avant* la saison, jamais pendant. Québec : février–avril (avant la clim) et août–septembre (avant le chauffage). Un installateur contacté pendant une canicule ne lit rien.

**Note AI Act (à ne pas sur-interpréter)** : l'art. 50 s'applique depuis le 2 août 2026. L'obligation de marquage des textes générés vise les textes « publiés dans le but d'informer le public sur des questions d'intérêt public » — un courriel commercial personnalisé n'entre probablement pas dans ce périmètre ; l'obligation d'information sur l'interaction avec une IA vise les chatbots ([artificialintelligenceact.eu](https://artificialintelligenceact.eu/article/50/), [Commission européenne](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act)). **Le risque réel n'est pas l'étiquette AI Act, c'est de qualifier de « diagnostic » un résultat produit par des stubs.** Régler la véracité avant l'étiquetage. *(Analyse de périmètre, pas un avis juridique — à faire confirmer, comme prévu pour J6.)*

---

## 5. Ce qui change d'un marché à l'autre

Le fait structurant : **ce n'est pas la traduction qui change, c'est le régime de consentement, le moteur de demande et la grammaire de légitimité.** Cela justifie **trois rubriques distinctes**, pas une seule — exactement ce que permet l'invariant « la rubrique est une donnée ».

| | **Québec** | **Suisse romande** | **France** |
|---|---|---|---|
| **Régime prospection** | CASL : **opt-in**, y compris B2B. Consentement tacite possible via *publication manifeste* de l'adresse, sous conditions (message pertinent au rôle, aucune mention de refus), valide ~2 ans (6 mois sur demande de renseignements). Sanctions jusqu'à 10 M$ CAD. ([ISED](https://ised-isde.canada.ca/site/canada-anti-spam-legislation/en/getting-consent-send-email), [CRTC](https://crtc.gc.ca/eng/com500/guide.htm)) | nLPD : pas d'opt-in préalable exigé en B2B, **mais** art. 3 al. 1 let. o LCD interdit la publicité de **masse** par courriel sans consentement. Le critère opérant est *masse vs individualisé*. ([PFPDT](https://www.edoeb.admin.ch/fr/publicite-et-marketing), [swissprivacy.law](https://swissprivacy.law/412/)) | RGPD art. 6.1.f + L34-5 CPCE : **opt-out** en B2B sur intérêt légitime, si le message concerne la fonction, opposition en un clic, et **LIA documentée**. Purge à 3 ans d'inactivité. ([CNIL/synthèses sectorielles](https://www.donneespersonnelles.fr/prospection-commerciale-rgpd)) |
| **Conséquence système** | `contact_email_source` doit porter **l'URL de publication + la date**, pas « apollo ». Le champ existe ; sa sémantique doit être durcie, plus un compteur d'expiration. | Volume bas et personnalisation réelle deviennent une **obligation** — c'est-à-dire exactement ce que le diagnostic permet. **Avantage concurrentiel, pas contrainte.** | Produire et versionner la LIA **avant** J6. C'est un livrable, pas une case à cocher. |
| **Moteur de demande** | LogisVert / Rénoclimat (Hydro-Québec) ; électricité bon marché ; thermopompe = clim + sortie du mazout | Programme Bâtiments, cantonal (portail `portal.leprogrammebatiments.ch`) ; remplacement de chauffages fossiles ; PAC air-eau ~30–40 kCHF | MaPrimeRénov' (guichet rouvert 23/02/2026, 3,6 Md€) ; **PAC air/air exclue** du parcours par geste depuis 2025 |
| **Grammaire de légitimité** | Licence **RBQ 15.10** + CMMTQ | **suissetec** + IDE/CHE | **RGE** (Qualibat / Qualit'EnR / QualiPAC) — **gate dur** sur MaPrimeRénov' |
| **Vocabulaire** | « thermopompe », « soumission », « entrepreneur » | « PAC », « devis », « installateur », CHF | « pompe à chaleur », « devis », « artisan » |
| **Ligne de base de confiance** | neutre | **haute** (marché dense, logique de recommandation → le froid doit être irréprochable, mais le ticket élevé justifie un audit payant) | **négative** (secteur saturé par les revendeurs de leads et marqué par le démarchage abusif → l'audit doit arriver comme un document, pas comme une promesse) |
| **AI Act** | non applicable | non applicable (hors UE) | **applicable** |

Trois conséquences opérationnelles :
- **Trois rubriques** : `rubric_persona1-quebec.yaml`, `-romandie`, `-france`. Un installateur français sans RGE devrait être quasi-disqualifié ; un installateur suisse sans avis Google devrait être moins pénalisé (parcours d'achat plus prescriptif/recommandation).
- **Trois ICP**, avec gabarits de requêtes et domaines exclus propres (pagesjaunes.ca ≠ local.ch ≠ pagesjaunes.fr).
- **La séquence Québec → Suisse → France est bien ordonnée**, mais pour une raison différente de celle attendue : ce n'est pas la difficulté juridique croissante (le Québec est le plus strict), c'est la **ligne de base de confiance décroissante**. On apprend là où l'accueil est neutre, on affine là où le ticket est élevé, on n'attaque la France qu'avec un livrable déjà irréprochable.

---

## Annexe — Tarifs API (garde-fou anti-hallucination appliqué)

**Aucun de ces chiffres ne doit être saisi dans `knowledge/api_pricing.yaml` sans relevé direct sur la page tarifaire officielle.** `WebFetch` a été bloqué (HTTP 403) sur serpapi.com, apollo.io et developers.google.com depuis cet environnement ; ce qui suit provient de **snippets de recherche restreints aux domaines officiels**, pas de la lecture des pages.

| Fournisseur | Chiffre | Niveau de fiabilité |
|---|---|---|
| **SerpApi** | Developer 50 $/mois pour 5 000 recherches ; Big Data 30 000/mois pour 250 $ ; Enterprise à partir de 3 750 $/mois avec 100 000 recherches ; réservé supplémentaire 2,75 $/1 000 ; à la demande 7,50 $/1 000 | **Rapporté par recherche sur serpapi.com — page NON LUE directement (403). À CONFIRMER sur https://serpapi.com/pricing** |
| **Apollo.io** | — | **NON TROUVÉ.** Ni fetch ni snippet exploitable. Ne rien inventer : relever manuellement sur https://www.apollo.io/pricing (plans, crédits e-mail vs crédits export — la distinction est déterminante pour `budgets.apollo.unites_max.credits`) |
| **Google Places API (New)** | Structure confirmée : SKU en paliers **Essentials / Pro / Enterprise** selon les champs demandés ; `Text Search` et `Place Details` sont **facturés séparément** — ce qui est cohérent avec les deux endpoints déclarés dans `api_pricing.yaml`. **Prix par 1 000 requêtes : NON TROUVÉ.** | Structure : vérifiée sur [developers.google.com](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing). Prix : **à relever sur https://developers.google.com/maps/billing-and-pricing/pricing** ⚠️ `reviews.py` appelle `text_search` **puis** `place_details` → **deux SKU par prospect**, à budgéter en conséquence |
| **Anthropic** | Haiku 4.5 (`claude-haiku-4-5`) : **1,00 $ / 5,00 $** par MTok (contexte 200K). Sonnet 5 (`claude-sonnet-5`) : **3,00 $ / 15,00 $** (tarif d'introduction 2,00 $ / 10,00 $ jusqu'au 31/08/2026). Sonnet 4.6 : 3,00 $ / 15,00 $ | Table de référence Anthropic **datée du 2026-06-24**. À revérifier sur https://platform.claude.com/docs/en/pricing avant saisie |

**Deux observations issues de la lecture de `knowledge/greenit.yaml` :**
- Le profil `standard` route vers `claude-haiku-4-5-20251001` — ID complet valide.
- Le profil `qualite` route vers **`claude-sonnet-4-5`**, qui est un modèle *legacy* (encore actif). Le Sonnet courant est `claude-sonnet-5`. À arbitrer consciemment : rester sur 4.5 est un choix défendable de stabilité, mais ce doit être un choix, pas un oubli.
- ⚠️ Rappel : `releve_le: null` dans `api_pricing.yaml` **et** dans `greenit.yaml`. Tant que c'est le cas, aucun coût ni aucune empreinte affichés ne sont engageants, et `run_preflight.py` reste en NO-GO structurel. C'est correct et doit le rester jusqu'au relevé réel.

---

## Les cinq actions par ordre de rentabilité

1. **Corriger A1/A2/A3** (`scoring.py` + `serializers.py`). Sans ça, le système envoie à tous les prospects la même accroche non vérifiée. Bloquant avant tout envoi.
2. **Câbler dans la rubrique les 5 signaux déjà collectés** (récence des avis, réponse aux avis, fraîcheur du site, plateformes sociales). Pure édition YAML, coût API nul, et ce sont les signaux les mieux documentés du secteur.
3. **Ajouter la dimension `legitimite_conformite`** (RBQ 15.10 / RGE / suissetec + mention du programme de subvention). Regex sur du HTML déjà téléchargé, coût nul, très discriminant, spécifique au marché.
4. **Séparer le score de capacité à payer du score de faille**, et trier l'export sur le croisement. Corrige le biais actuel qui remonte les entreprises les plus pauvres.
5. **Calculer le benchmark de cohorte** depuis les résultats SERP déjà en mémoire. Plus gros gain de valeur perçue pour le coût le plus faible du lot.

Les points 2, 3 et 5 n'exigent **aucun appel API supplémentaire** — ils sont donc réalisables et testables aujourd'hui, sans clé, sans lever le NO-GO préflight.

**Sources :** [BrightLocal LCRS](https://www.brightlocal.com/research/local-consumer-review-survey/) · [Whitespark 2026](https://whitespark.ca/local-search-ranking-factors/) · [Search Engine Land — récence des avis](https://searchengineland.com/85-of-consumers-disregard-local-reviews-more-than-3-months-old-309192) · [RBQ](https://www.rbq.gouv.qc.ca/en/you-are/citizen/check-a-contractors-licence/) · [ecologie.gouv.fr — RGE](https://www.ecologie.gouv.fr/politiques-publiques/label-reconnu-garant-lenvironnement-rge) · [France Rénov'](https://france-renov.gouv.fr/annuaires-professionnels/artisan-rge-architecte) · [suissetec](https://suissetec.ch/fr/portrait.html) · [PFPDT — publicité et marketing](https://www.edoeb.admin.ch/fr/publicite-et-marketing) · [ISED — consentement CASL](https://ised-isde.canada.ca/site/canada-anti-spam-legislation/en/getting-consent-send-email) · [AI Act art. 50](https://artificialintelligenceact.eu/article/50/) · [Commission européenne — FAQ art. 50](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act) · [Carrier](https://www.carrier.com/us/en/residential/carrier-factory-authorized-dealers/) · [Lennox](https://www.lennox.com/residential/locate/) · [Google Places — usage & billing](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing)

---


<a id="s3"></a>

## 3. Processus commercial — COO


## QUALIFICATION DU PROCESSUS COMMERCIAL — Kemana-Flow

### Note de sourçage (règle anti-hallucination appliquée)

Les pages tarifaires officielles de **SerpAPI, Apollo et Google Maps Platform ont toutes renvoyé HTTP 403** à la récupération directe, et `platform.claude.com/docs/en/pricing.md` un 404. **Aucun prix ci-dessous n'est « vérifié sur la page officielle ».** Statut de chaque chiffre indiqué en ligne. Relevé du 2026-08-02.

| Fournisseur | Chiffre | Statut |
|---|---|---|
| SerpAPI | Free 250 recherches/mois ; $25/1 000 ; $75/5 000 ; $150/15 000 ; $275/30 000. Abonnement mensuel uniquement, **pas de pay-as-you-go**, **pas de report** des crédits non consommés | **Rapporté par des tiers** (comparateurs), page officielle inaccessible (403) |
| Apollo | Basic $49/utilisateur/mois annuel ($59 mensuel), **1 000 crédits d'export/mois** ; Professional $79 annuel ($99 mensuel), 2 000 crédits | **Rapporté par des tiers**, page officielle inaccessible (403) |
| Apollo | **À quel palier l'accès API `people/search` est-il inclus** | **NON TROUVÉ** — bloquant, à confirmer avant tout achat |
| Apollo | Prix unitaire catalogue d'un crédit | **NON TROUVÉ** (seul un coût dérivé abonnement ÷ crédits est calculable) |
| Google Places | Text Search **Pro $32/1 000**, **Enterprise $35/1 000** | **Rapporté par des tiers**, page officielle inaccessible (403) |
| Google Places | Text Search **Essentials** (le SKU le moins cher) | **NON TROUVÉ** |
| Google Places | `place_details` — prix du SKU | **NON TROUVÉ** |
| Google Places | Depuis 2025-03-01, le crédit universel de $200/mois est supprimé, remplacé par des seuils gratuits par SKU : 10 000 appels Essentials, 5 000 Pro, 1 000 Enterprise par mois, non reportables | **Rapporté par des tiers** |
| Anthropic | Haiku 4.5 : $1,00 / $5,00 par million de tokens (entrée/sortie). Sonnet 5 : $3,00 / $15,00 (intro $2/$10 jusqu'au 2026-08-31) | **Relevé indirect** — table de référence Anthropic embarquée, datée 2026-06-24. À reconfirmer sur anthropic.com/pricing |

**Conséquence directe pour `knowledge/api_pricing.yaml` : aucune de ces valeurs ne doit y être saisie en l'état.** Elles servent à dimensionner une décision, pas à alimenter un fichier de configuration qui produit des coûts affichés. Le champ `releve_le` ne doit passer à une date que quand quelqu'un a ouvert les quatre pages tarifaires connecté et recopié les chiffres.

---

## 1. Cartographie du processus commercial réel

| # | Étape | Exécutant | Preuve dans le code | Sortie |
|---|---|---|---|---|
| 1 | Définition de l'ICP | **Humain** (édition YAML) | `icp/persona1-quebec.yaml` | 3 gabarits × 6 localités |
| 2 | Génération de la liste de requêtes | Machine | `IcpConfig.generer_requetes()` — produit cartésien | **18 requêtes SERP/run** |
| 3 | Interrogation SERP | Machine | `DiscoveryCollector.discover()` | ≤ 180 résultats bruts (`num=10`) |
| 4 | Filtrage + dédup | Machine | `_passe_filtres` (8 domaines exclus + 13 plateformes hébergées) + dédup par domaine normalisé | n domaines uniques — **jamais mesuré, aucune clé** |
| 5 | Écriture fiche `decouvert` | Machine | `vault_io.write_fiche()`, dédup inter-runs via `exists()` | Fiches Markdown |
| 6 | Enrichissement décideur | Machine | `PersonEnrichment` (Apollo) | **plafond dur `max_enrichissements: 25`** |
| 7 | Collecte de faits (5 collecteurs) | Machine | `website` (palier 0, réseau) ; `seo`+`social` (dérivés, zéro réseau) ; `gbp`+`reviews` (palier 1, Places) | dict de signaux |
| 8 | Scoring | Machine | `scoring.py` + `rubric_persona1.yaml` (5 dimensions / 100) | score + liste de `Gap` |
| 9 | Rédaction mini-audit + accroche | Machine (LLM ou repli déterministe) | `synthesis.py`, routage GreenIT YAML | texte |
| 10 | Transition `decouvert → diagnostique` | Machine | seule transition autorisée à l'agent (`TRANSITIONS_AGENT`) | fiche `diagnostique` |
| **11** | **PORTE HUMAINE — `diagnostique → valide` ou `→ rejete`** | **Humain, dans Obsidian** | `transition(acteur="humain")` ; `ValueError` si un agent tente | fiche `valide` |
| 12 | Export liste | Machine | `run_export.py`, 10 colonnes, lecture seule, `opt_out` exclu sans exception | CSV/JSONL |
| **13** | **Priorisation, personnalisation, envoi, relance, prise de RDV, closing** | **100 % HUMAIN, hors système** | `dag_pipeline.yaml` : `outreach.enabled: false` **+** `_run_outreach()` renvoie `bloque` | — |
| **14** | **`valide → contacte`, `→ rejete`** | **Humain** | machine à états | — |

**Lecture COO :** la machine automatise **le sourcing et la qualification technique**, c'est-à-dire les étapes 2 à 10. Elle n'automatise **rien après** la porte humaine. Ce qui reste manuel est exactement ce qui produit du chiffre d'affaires : décider, contacter, relancer, convertir.

Le système n'est donc **pas** un « système de prospection ». C'est un **moteur de constitution de dossiers de prospect qualifiés**. C'est la bonne façon de le vendre en interne, et ça évite de mesurer le mauvais objet.

---

## 2. Le goulot d'étranglement

Le débit réel du pipeline = **min(débit machine, capacité de validation humaine, capacité d'exécution commerciale humaine)**.

**Débit machine — plafonné bien plus bas qu'il n'y paraît.** Le facteur limitant n'est pas le SERP mais `max_enrichissements: 25`. Même si les 18 requêtes rendent 120 domaines uniques, **25 fiches au maximum repartent avec un décideur identifié par run**. Une fiche sans email est exportable mais génère une anomalie dans `valider_ligne` — elle n'est pas actionnable.

**Incohérence de dimensionnement à corriger avant la Phase D.** Les budgets suggérés dans `CLAUDE.md` sont `serp: 500 requêtes` et `apollo: 50 crédits`. Or 500 ÷ 18 = **27 runs de découverte possibles côté SERP**, contre **2 runs côté Apollo**. Le garde-fou budgétaire qui mordra est Apollo, **13 fois plus tôt** que le SERP. Ces deux budgets doivent être posés dans le même rapport que leur consommation réelle (18 requêtes SERP pour ≤25 crédits Apollo, soit un ratio ≈ 0,72 crédit par requête), sinon on paie un abonnement SERP qu'on ne consomme jamais.

**Capacité de validation humaine — inconnue et non instrumentée à ce jour.** Le vault n'est pas initialisé, `runs.log` n'existe pas encore, donc aucun temps de validation n'a jamais été observé. C'est la première chose à mesurer au pilote.

**Capacité d'exécution commerciale — le vrai plafond.** Une consultante indépendante seule, qui livre aussi ses missions, ne traite pas 100 conversations de prospection par mois. Les repères d'un SDR à temps plein sont d'environ **14,6 rendez-vous décrochés par mois** *(rapporté par des tiers, agrégats de cabinets)*. Une solo qui consacre une fraction de son temps à la prospection est structurellement en dessous.

**Conséquence opérationnelle, et c'est le point central :** produire plus de fiches n'améliore pas le résultat. Le système peut saturer la porte humaine en un run. **La variable à optimiser n'est pas le volume de découverte, c'est le taux de fiches `valide` par heure de validation et le taux de conversion `valide → RDV`.** Tout run de découverte au-delà de la capacité de traitement humaine est du coût pur : il consomme des crédits SERP et Apollo non reportables pour produire des fiches qui vieilliront dans le vault.

**Corollaire économique — le variable ne compte presque pas.** Modèle de coût, prix laissés en variables (toutes les valeurs numériques sont des chiffres tiers non vérifiés) :

```
Coût_découverte(run)   = 18 × P_serp + n_enrich × P_apollo          (n_enrich ≤ 25)
Coût_diagnostic(fiche) = P_text_search + P_place_details
                       + (T_in × P_in + T_out × P_out)
```

Le second `text_search` est un **cache hit à coût zéro** — `gbp` et `reviews` partagent la `cache_key` `places:{query}`, vérifié dans `api_usage.log`. `T_out` est plafonné à **600 tokens** par le profil GreenIT `standard`, `T_in` borné par le plafond de prompt de 8 000 caractères (≈ 2 000–2 600 tokens, **estimation non mesurée**).

Avec les chiffres tiers : le poste LLM ressort autour de **$0,006/fiche** contre **$0,03 minimum pour le seul `text_search`** (`place_details` non trouvé, donc plancher). **Le LLM représente de l'ordre de 5 % du coût variable ; la donnée en représente ~95 %.** Le chantier GreenIT optimise donc 5 % d'un poste lui-même écrasé par les abonnements : SerpAPI ($25/mois minimum) + Apollo ($49/utilisateur/mois) ≈ **$74/mois de socle fixe indépendant du volume**. À 25 prospects/mois, l'abonnement représente ~95 % du coût par prospect ; à 500/mois, ~50 %.

**Donc : le levier de coût n'est pas le token, c'est le taux d'utilisation de l'abonnement.** Soit on cadence les runs pour saturer le palier tarifaire acheté, soit le coût par prospect explose mécaniquement.

Ces ordres de grandeur ne survivront pas au relevé réel : ils indiquent où regarder, pas quoi budgéter.

---

## 3. Métriques commerciales à piloter

### 3.1 Déjà instrumentables sans une ligne de code

`runs.log` (JSONL, `vault_io._journal`) porte `{ts, agent, op, fiche, resultat, detail}`, avec `op ∈ {write_fiche, transition, write_rapport}` et, pour les transitions, un `detail` de la forme `"ancien→nouveau acteur=agent|humain"`.

| Métrique | Dérivation | Confiance |
|---|---|---|
| Volume par état, par période | comptage des `op=transition` | directe |
| **Taux de rejet** | `transitions → rejete` ÷ `transitions → diagnostique` | directe |
| Taux de conversion `diagnostique → valide` | idem | directe |
| **Délai de validation humaine** | Δ entre le `ts` de `diagnostique` (`acteur=agent`) et celui de `valide`/`rejete` (`acteur=humain`), joints par nom de fiche | **directe — c'est la métrique la plus importante et elle est déjà calculable, personne ne la calcule** |
| Débit de validation (fiches/heure ouvrée) | même série, agrégée | directe |
| Séparation agent/humain | champ `acteur=` dans `detail` | directe |

`api_usage.log` (`LedgerEntry`) porte `cout_estime`, `fiche`, `cache_hit`, `fournisseur`, `endpoint` + les 7 champs GreenIT. `usage.py::agreger` produit déjà un coût **par fiche**.

| Métrique | Statut |
|---|---|
| **Coût par fiche diagnostiquée** | agrégé nativement (`Usage.par_fiche`) |
| Taux de cache (levier de coût direct) | `Usage.taux_cache` |
| Coût par fournisseur | agrégé nativement |
| Coût par prospect **qualifié** (`valide`) | **nécessite une jointure `api_usage.log` ⇄ `runs.log`** |

### 3.2 Défaut de jointure à corriger (peu coûteux, forte valeur)

`api_usage.log` identifie une fiche par son **nom d'entreprise** (`"fiche": "Climatisation Test"`), tandis que `runs.log` l'identifie par son **nom de fichier slugifié** (`"fiche": "climatisation-test.md"`). La jointure est déterministe mais exige d'appliquer `_slugify` côté analyse. **Tant qu'elle n'est pas faite, le coût par prospect *qualifié* — la seule métrique de coût qui intéresse un commercial — n'est pas calculable.** Le coût par fiche *diagnostiquée* l'est, mais il inclut tous les rejets. Correctif recommandé : journaliser le slug **en plus** du nom dans `LedgerEntry` (champ optionnel, rétro-compatible, cohérent avec la façon dont les 7 champs GreenIT ont été ajoutés).

### 3.3 Ce qui manque et qu'aucun journal ne pourra produire

| Métrique | Pourquoi elle manque |
|---|---|
| **Motif de rejet** | `transition → rejete` n'enregistre aucune raison. **C'est le trou le plus coûteux du système** : sans motif, un taux de rejet de 60 % ne dit pas s'il faut corriger l'ICP, les filtres, la rubrique ou l'enrichissement. La boucle d'apprentissage est ouverte. Correctif : champ libre `motif_rejet` dans le frontmatter (`extra="allow"` le permet déjà sans changer le schéma) + une liste fermée de 5–6 motifs. |
| **Coût par rendez-vous / par client** | La machine à états s'arrête à `contacte`. Il n'y a ni état `rdv`, ni état `client`, ni date de RDV, ni montant. Le dénominateur commercial n'existe pas. |
| Taux de réponse, de RDV, de closing | Aucun événement post-`contacte` n'est capté. |
| Temps humain de préparation d'un contact (hors validation) | Non instrumenté et probablement non instrumentable — à estimer par échantillonnage manuel au pilote. |
| Valeur du prospect | Aucun champ de taille, effectif, ancienneté, chiffre d'affaires. Voir §4. |

**Repères externes pour cadrer les objectifs** *(tous rapportés par des agrégateurs tiers, qualité inégale, à traiter comme des ordres de grandeur et non comme des cibles)* : taux de réponse moyen en cold email B2B ≈ **3,4 %** en 2026 (top 8–12 %) ; taux de RDV décroché 0,8–1,5 % des emails envoyés pour un « bon » niveau, 1,5–3 % en quartile supérieur ; coût par rendez-vous qualifié **$200–350** en B2B courant, **$766** dans le modèle SDR salarié US, $150–600 en appointment-setting externalisé ; coût par SQL ≈ **$1 630**. Ces repères viennent du SaaS B2B et **ne transposent pas** à une consultante solo vendant du branding à des installateurs HVAC — cycle plus court, ticket différent, pas d'équipe. Ils servent à une seule chose : montrer que **le coût API (quelques dollars par prospect) est deux à trois ordres de grandeur sous le coût d'un rendez-vous.** Optimiser les tokens pendant que la porte humaine est le goulot serait une erreur d'allocation.

---

## 4. Qualification : ce qui sépare « à contacter » de « à jeter »

### 4.1 Non, le score de marque ne suffit pas — il mesure le mauvais axe

`rubric_persona1.yaml` mesure **la sévérité du problème**, pas **la valeur du prospect**. Les deux sont décorrélés, et pire, la relation est non monotone :

- **Score 15–25** : l'entreprise n'a quasiment rien. Besoin maximal — mais souvent artisan seul, sans budget, sans intention d'investir. **Faux positif classique du scoring mono-axe.**
- **Score 80+** : déjà bien outillée. Aucun besoin perçu. Rejet.
- **Score 40–70** : investit déjà (site, fiche Google, avis) mais mal. **A prouvé sa disposition à payer, et le problème est démontrable.** C'est la bande utile.

Il faut donc **inverser la logique dans le filtre commercial** : le score sert de critère de *besoin*, mais un score très bas doit **baisser** la priorité, pas la monter. Aujourd'hui rien dans le code ne fait ça — `run_export.py` exporte toutes les fiches `valide` sans tri ni seuil, et la colonne `Score` est une donnée d'affichage.

### 4.2 Second axe requis : capacité + accessibilité

Matrice de décision à instaurer, en quatre cases : **Besoin (score inversé, bande 35–75) × Capacité/Accessibilité**. Seule la case « besoin démontré × capacité avérée × décideur joignable » part en contact.

### 4.3 Signaux de capacité — trois sont **déjà collectés** et inexploités

| Critère | Disponible ? | Où |
|---|---|---|
| **Nombre d'avis Google** | **OUI, déjà collecté** | `reviews.count`. Aujourd'hui utilisé **uniquement** comme faille (« <10 avis = preuve sociale faible »). C'est aussi le meilleur proxy gratuit de taille et d'activité commerciale. **Double usage à instaurer : sous un seuil plancher (ex. 3 avis), c'est un critère de *disqualification*, pas une faille à mentionner.** |
| **Dernière mise à jour du site** | **OUI, déjà collecté** | `website.derniere_maj` (copyright). Un site figé depuis 4 ans = entreprise qui n'investit pas. Signal d'abandon, actuellement inutilisé en qualification. |
| **Répond aux avis** | **OUI, déjà collecté** | `reviews.repond_aux_avis`. Une entreprise qui répond à ses avis a quelqu'un qui s'occupe du marketing — décideur identifiable et sensibilisé. |
| **Qualité de l'email** | **OUI, déjà collecté** | `contact_email_source` (statut Apollo `verified` / `guessed`). Aujourd'hui c'est une piste d'audit RGPD. **Un email `guessed` n'est pas contactable en pratique** — il doit être un critère de qualification à part entière, pas une note de bas de page. |
| Effectif / ancienneté | **NON** | Serait une donnée d'**entreprise**, pas de personne. **Important : la minimisation RGPD porte sur l'objet `Contact` (6 champs, `extra="forbid"`), pas sur `FicheProspect`.** Ajouter `effectif` et `anciennete_domaine` à `FicheProspect` ne touche donc pas au garde-fou RGPD. |
| **Signal d'intention** | **NON — trou structurel** | Rien dans le système ne capte « cette entreprise investit *maintenant* » : recrutement en cours, refonte de site engagée, nouvelle succursale, campagne publicitaire active. C'est le signal qui fait la différence entre un taux de réponse à 3 % et un taux à 10 %. Proxys faibles et juridiquement propres, dérivables de ce qui est déjà collecté : avis récents, `derniere_maj` fraîche, page « nous recrutons » détectée par `website.py`. |

### 4.4 Règle de disqualification à écrire (aucune n'existe aujourd'hui)

Rejet automatique proposé, à câbler dans l'export ou en amont de la porte humaine :
`opt_out = true` (déjà appliqué, absolu) · absence d'email · email `guessed` non corroboré · `reviews.count` sous plancher · site injoignable **et** absence de fiche Google · domaine hors zone géographique de l'ICP.

Objectif : **ne pas faire arbitrer par un humain ce qu'une règle déterministe peut trancher.** Chaque disqualification automatisée est du temps rendu au goulot identifié en §2.

---

## 5. Ce qu'il faut dans un dossier de prospect

Les 10 colonnes actuelles (`export_kemana.yaml`) : Nom, Titre, Boîte, ICP, Email, Source email, Site, Score, Signal chaud, Statut.

**Verdict : insuffisant pour ouvrir une conversation sans rouvrir Obsidian.** Le plus frappant est que **trois champs déjà présents dans `FicheProspect` sont absents de l'export** — le correctif ne demande que d'éditer un YAML, `export_kemana.yaml` étant explicitement de la donnée :

| Manquant | Existe déjà ? | Pourquoi c'est bloquant |
|---|---|---|
| **`gaps_majeurs`** | **OUI, dans `FicheProspect`** | Le commercial n'a **qu'une seule** preuve (`signal_chaud`). Si le prospect la balaie, la conversation est morte — les 2 ou 3 autres failles restent dans le vault. |
| **`accroche`** | **OUI, dans `FicheProspect`** | Générée par `synthesis.py`, jamais exportée. On paie un LLM pour produire une phrase que le commercial ne voit pas. |
| **`rapport`** | **OUI** (wikilink `[[30-Diagnostics/…]]`) | Le mini-audit est le livrable de valeur. Sans le lien, il n'existe pas pour celui qui vend. |
| **`date_diagnostic`** | **OUI, dans `FicheProspect`** | **Une preuve non datée n'est pas utilisable.** « Votre site n'est pas adapté au mobile » — constaté quand ? Si c'est vieux de six semaines et que le site a été refait, l'accroche se retourne contre l'émetteur. |
| Ville / région précise | Partiellement (`marche` = quebec) | Impossible de prioriser par tournée, de contextualiser (« vos concurrents à Lévis… »), ou de router vers le bon fuseau. La localité d'origine est dans `source` (`serp:chauffagiste Lévis`) mais n'est pas un champ. |
| Téléphone | **NON** | Pas de canal alternatif à l'email. Sur du HVAC, le téléphone est souvent le meilleur canal — et il échappe aux contraintes CASL/LCD sur les messages électroniques. |
| **Réserve de fiabilité par faille** | **NON** | Voir défaut rouge n°1 ci-dessous. |

**Dossier minimal cible (13–15 colonnes) :** identité + rôle + canal (email **avec son statut de vérification** + téléphone + ville) · **2–3 preuves datées avec leur niveau de confiance** · l'accroche · le lien vers le rapport · le score **et** son axe capacité · le statut.

Une colonne « Source email » qui vaut `guessed` doit être **visuellement traitée comme un avertissement**, pas comme une donnée neutre : elle prédit un bounce, et un bounce dégrade la délivrabilité du domaine émetteur pour tous les prospects suivants.

---

## 6. Trois défauts rouges vérifiés dans le code, à traiter avant tout run réel

### 🔴 6.1 Sans clé Google Places, le système fabrique de fausses failles — et les met en avant

Chaîne vérifiée :
1. Sans `api_io`, `gbp.py` renvoie `{"verified": None, "has_photos": None}` (l. 30-31) et `reviews.py` `{"count": None, "avg": None}` (l. 34-35).
2. `scoring.py::_check_passes` : `if value is None: return False` (l. 29-30).
3. Un check qui échoue produit **un `Gap` au libellé identique à celui d'une vraie faille** (l. 65-69).
4. **`presence_locale` (poids 25) et `avis` (poids 20) tombent donc à 0 — soit 45 % du score global — pour une raison purement technique.**
5. `_severity` : `gbp.verified` pèse 60/100 (ratio 0,6) et `reviews.count` 50/100 (0,5), tous deux **≥ 0,4 → gravité `haute`**.
6. `serializers.py` : `signal_chaud = hautes[0].preuve` — **la première faille haute**.

**Résultat : sans clé Places, le « signal chaud » poussé en tête de l'export est, avec forte probabilité, « Fiche Google Business non vérifiée » — une affirmation sur laquelle le système n'a strictement aucune donnée.** La rubrique porte bien la réserve « (à confirmer en J3) », mais elle **n'est pas propagée à l'export** : elle reste dans le libellé du `Gap` et le commercial reçoit une preuve nue.

Un prospect qui répond « ma fiche est vérifiée depuis 2019 » a raison, et le rendez-vous est perdu. C'est un risque commercial **et** un risque de conformité (AI Act art. 50 sur la transparence, applicable depuis aujourd'hui).

**Correctif minimal : un `Gap` issu d'un signal `None` ne doit jamais pouvoir devenir `signal_chaud`.** Distinguer « check échoué » de « signal indisponible » dans `_check_passes`, ou exclure les failles palier 1 de la sélection du signal chaud tant que le collecteur correspondant n'a pas retourné de donnée réelle.

### 🔴 6.2 `gbp.verified` ne mesure pas ce que son libellé affirme

`gbp.py` l. 64 : `"verified": place.get("business_status") == "OPERATIONAL"`.

`business_status == OPERATIONAL` signifie « l'établissement n'est ni fermé définitivement ni temporairement ». **Cela n'a aucun rapport avec la vérification d'une fiche Google Business par son propriétaire.** La faille émise — « Fiche Google Business non vérifiée » — est donc **un mauvais libellé même avec une clé API valide**. C'est une affirmation factuelle, adressée à un prospect, que le collecteur ne soutient pas. Soit on renomme le signal et la faille (`gbp.actif` / « établissement signalé comme non opérationnel »), soit on trouve le champ Places qui porte réellement l'information.

### 🟠 6.3 Le budget Apollo mord 13× plus tôt que le budget SERP

Voir §2. Les valeurs suggérées (500 / 50) sont incohérentes avec la consommation réelle du pipeline (18 requêtes SERP pour ≤25 crédits Apollo par run). À reposer ensemble, pas indépendamment, au moment de la Phase D.

---

## 7. Processus commercial cible à 6 mois — outreach automatisé bloqué

**Le blocage juridique est réel et n'est pas un détail administratif.** Points relevés :
- **CASL (Québec)** : pas d'exemption B2B générale. La voie praticable est le **consentement tacite par publication manifeste**, soumis à un test en trois volets : adresse publiée publiquement, absence de mention refusant les messages non sollicités, **et message pertinent au rôle du destinataire**. Sanctions annoncées jusqu'à **10 M$ CAD par violation** *(rapporté par des tiers ; à faire confirmer par un juriste canadien)*.
- **Suisse** : les sources sont **contradictoires**. L'art. 3 al. 1 let. o LCD est présenté comme exigeant le **consentement préalable** pour la publicité de masse par voie électronique ; d'autres sources affirment que la nLPD autorise la prospection B2B sans opt-in préalable sous conditions (identification de l'émetteur, opt-out à chaque envoi, arrêt immédiat sur refus). **Cette contradiction est exactement la raison pour laquelle le double verrou sur J6 doit rester en place.**
- **UE / AI Act art. 50** : obligation de transparence en vigueur **depuis aujourd'hui, 2026-08-02**. Un mini-audit généré par un LLM et envoyé à un tiers entre dans le périmètre.

**Le blocage juridique ne doit pas être vécu comme une contrainte à contourner, mais comme une contrainte de conception qui pointe le bon processus cible.**

### La cible : ne pas viser l'automatisation de l'envoi, viser l'accélération de la porte humaine

Deux raisons convergentes : l'outreach automatisé est bloqué juridiquement, **et** le goulot identifié en §2 n'est pas l'envoi mais la validation et l'exécution. Automatiser l'envoi ne débloquerait rien.

**Mois 1–2 — Instrumenter et calibrer (aucun envoi)**
- Relever les quatre grilles tarifaires réelles, remplir `api_pricing.yaml`, poser `releve_le`, dimensionner les budgets SERP/Apollo dans le bon rapport. Objectif : `run_preflight.py` = **GO**.
- Traiter les défauts rouges 6.1 et 6.2 **avant** le premier run réel.
- Initialiser le vault, exécuter un run borné (1 run = 18 requêtes, ≤25 contacts).
- **Mesurer les trois chiffres qui manquent aujourd'hui** : temps de validation par fiche, taux de rejet, coût réel par prospect qualifié.
- Faire trancher la question suisse et le régime CASL par un juriste. C'est un prérequis daté, pas une tâche de fond.

**Mois 2–4 — Affûter la qualification, pas augmenter le volume**
- Instaurer le champ `motif_rejet` (liste fermée) — **sans lui il n'y a pas de boucle d'apprentissage**.
- Câbler l'axe capacité à partir des trois signaux déjà collectés (§4.3) et les règles de disqualification automatique (§4.4).
- Enrichir l'export à 13–15 colonnes (édition de `export_kemana.yaml` seule).
- Réinjecter les motifs de rejet dans l'ICP et la rubrique. **Cible : diviser par deux le nombre de fiches nécessaires pour produire un `valide`.**

**Mois 3–6 — Outreach humain assisté, à volume délibérément faible**
- La consultante envoie elle-même, depuis sa propre boîte, en s'appuyant sur le dossier et l'accroche. **Journaliser manuellement** l'envoi, la réponse et le RDV via un champ de frontmatter (`extra="allow"` le permet déjà sans modification de schéma). C'est ce qui donne les premières données de conversion réelles.
- Volume cible réaliste : **20–40 contacts par mois**, pas 400. Sur les repères tiers cités (0,8–3 % de RDV par email envoyé), 40 contacts produisent moins d'un RDV par mois en cold pur — d'où l'exigence d'une qualification très serrée plutôt que du volume, et le besoin d'un canal complémentaire (téléphone, réseau, recommandation) que le système peut alimenter mais pas exécuter.
- Ajouter les états `rdv` et `client` à la machine à états, avec date et montant. **Sans eux, aucun coût par rendez-vous ni ROI n'est calculable — et l'ensemble du système reste invérifiable économiquement.**

**Ce que la cible à 6 mois ne doit PAS être :** ni un moteur d'envoi automatisé (bloqué, et hors goulot), ni un système à plus fort volume de découverte (le volume n'est pas la contrainte), ni un superviseur LLM d'orchestration (refusé par l'ADR 0001, à ne pas réintroduire par la porte du routage).

**La phrase à retenir pour la direction :** le système sait produire des dossiers de prospect qualifiés à un coût marginal négligeable. Il ne sait pas encore **dire lesquels valent la peine d'être contactés**, ni **prouver qu'un contact produit du revenu**. Ces deux trous — le motif de rejet et les états post-contact — se comblent avec quelques champs de frontmatter et une jointure de journaux. C'est le meilleur rapport valeur/effort du chantier, très loin devant toute optimisation de tokens.

---

### Sources consultées

**Tarifs (pages officielles inaccessibles — 403/404, tous les chiffres sont des relevés tiers ou indirects)**
- [SerpApi Pricing 2026 — costbench.com](https://costbench.com/software/web-scraping/serpapi/) · [SerpApi Pricing Explained — apiserpent.com](https://apiserpent.com/blog/serpapi-pricing-explained) · [SerpApi Pricing 2026 — trustradius.com](https://www.trustradius.com/products/serpapi/pricing)
- [Apollo.io Pricing Plans 2026 — phantombuster.com](https://phantombuster.com/blog/ai-automation/apollo-pricing/) · [Apollo Pricing 2026 — warmly.ai](https://www.warmly.ai/p/blog/apollo-pricing) · [Apollo.io Pricing — salesmotion.io](https://salesmotion.io/blog/apollo-pricing)
- [Google Places API Pricing 2026 — safegraph.com](https://www.safegraph.com/guides/google-places-api-pricing/) · [Google Maps API Pricing 2026 — mapatlas.eu](https://mapatlas.eu/blog/google-maps-api-pricing-2026) · [Google Places API Limits 2026 — mapsleads.co](https://www.mapsleads.co/blog/google-places-api-limits-2026-complete-reference)

**Repères sales ops (agrégateurs tiers, qualité inégale)**
- [B2B Cold Email Benchmarks 2026 — astragtm.io](https://astragtm.io/guides/cold-email-benchmarks-2026) · [Cold Email Meeting Booked Rate Benchmarks 2026 — leadhaste.com](https://leadhaste.com/blog/cold-email-meeting-booked-rate-benchmarks-2026) · [Cold Email Response Rate 2026 — cleanlist.ai](https://www.cleanlist.ai/blog/2026-02-18-cold-email-response-rate-statistics)
- [SDR Benchmarks 2026 — albatalent.io](https://albatalent.io/tools/sdr-benchmarks-2026) · [Cost Per Meeting for Outbound 2026 — danishleadco.io](https://danishleadco.io/blog/what-is-the-cost-per-meeting-for-outbound-in-2026) · [Cost Per Qualified Lead Benchmarks 2026 — leadhaste.com](https://leadhaste.com/blog/cost-per-qualified-lead-benchmarks-2026)

**Conformité**
- [CRTC — FAQ sur la LCAP/CASL](https://crtc.gc.ca/eng/com500/faq500.htm) *(source officielle)* · [CASL Cold Email Compliance 2026 — prospeo.io](https://prospeo.io/s/casl-cold-email) · [Cold Email Canada CASL 2026 — puzzleinbox.com](https://puzzleinbox.com/blog/cold-email-canada-casl-2026/)
- [PFPDT — Publicité et marketing](https://www.edoeb.admin.ch/fr/publicite-et-marketing) *(source officielle suisse)* · [Droit suisse et emailing — mailpro.com](https://fr.mailpro.com/legislation/droit-suisse-emailing.asp) · [Suisse et consentement : nLPD — ratecard.fr](https://ratecard.fr/suisse-et-consentement-ce-que-change-la-nouvelle-lpd/)

**Fichiers de référence (chemins absolus)**
`/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/diagnostic/scoring.py` (l. 29-30 et 65-69 — traitement des signaux `None`) · `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/diagnostic/collectors/gbp.py` (l. 30-31, 64) · `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/diagnostic/collectors/reviews.py` (l. 34-35) · `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/diagnostic/serializers.py` (l. 28-32 — dérivation `signal_chaud`) · `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/diagnostic/vault_io.py` (l. 134-146 `_journal`, l. 224-260 `transition`) · `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/diagnostic/api_schema.py` (l. 18-45 `LedgerEntry`) · `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/knowledge/export_kemana.yaml` · `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/icp/persona1-quebec.yaml` · `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/knowledge/rubric_persona1.yaml`

---


<a id="s4"></a>

## 4. Marché — API SERP / découverte


**Recommandation.**

SYNTHÈSE — Trois décisions, dont une qui remet en cause le choix d'outil lui-même.

=== 1. RÉPONSE À LA QUESTION DE FOND : NON, UNE API SERP N'EST PAS LE BON OUTIL POUR DÉCOUVRIR DES INSTALLATEURS HVAC LOCAUX ===

L'argument décisif n'est ni le prix ni le droit : c'est un BIAIS DE SÉLECTION QUI TRAVAILLE CONTRE L'ICP.

Une API SERP renvoie ce que Google CLASSE BIEN. Or la consultante vend un diagnostic de marque à des entreprises dont la présence en ligne est FAIBLE — c'est toute la logique de rubric_persona1 (site_web 25, presence_locale 25, avis 20, seo_local 15, identite_visuelle 15 : un score BAS est un prospect CHAUD). Découvrir par le SERP, c'est donc sur-échantillonner exactement les entreprises qui ont le MOINS besoin du service, et sous-échantillonner la cible réelle. Le gabarit « installateur thermopompe Sherbrooke » fait remonter en priorité celui qui a déjà investi en SEO — le mauvais prospect. C'est une contradiction structurelle entre l'outil de découverte et la proposition de valeur, et aucun réglage de prix ne la corrige.

Trois autres écarts confirment le diagnostic :

(a) MAUVAISE FORME DE DONNÉE. Un SERP renvoie des PAGES ; le pipeline a besoin d'ÉTABLISSEMENTS. La preuve est dans l'ICP lui-même : toute la section filtres (domaines_exclus = pagesjaunes.ca, yelp, facebook, linkedin, 411.ca, houzz, kijiji, groupon + exiger_domaine_propre) n'existe QUE pour défaire les dégâts de la source. On paie une API pour recevoir du bruit, puis on écrit du code pour l'enlever. Une API de lieux ne renvoie pas d'annuaires : le filtre devient sans objet.

(b) AUCUN CONTRÔLE DU TERRITOIRE. L'ICP énumère 6 localités et 3 gabarits parce que le SERP n'offre aucune primitive géographique — on approxime une couverture par un produit cartésien de requêtes textuelles, avec 10 résultats par requête, sans jamais savoir ce qu'on a manqué. Places API expose locationRestriction (rectangle ou cercle) : on couvre une zone, et l'exhaustivité devient mesurable au lieu d'être espérée.

(c) SIGNAUX MANQUANTS À LA DÉCOUVERTE. Places renvoie rating et userRatingCount dès le premier appel : 45 des 100 points de la rubrique (avis 20 + presence_locale 25) sont pré-alimentés AVANT le diagnostic. On peut donc PRIORISER les fiches decouvert par potentiel avant de dépenser le moindre token Claude — un gain GreenIT direct et non spéculatif.

=== 2. ARCHITECTURE CIBLE RECOMMANDÉE ===

PRIMAIRE — Google Places API (New), Text Search, en découverte.
Le fournisseur google_places est DÉJÀ câblé : gbp.py:49 et reviews.py:89/99 l'appellent via api_io, et api_pricing.yaml expose déjà google_places.text_search / place_details / nearby_search. On ne migre pas vers un fournisseur : on étend l'usage d'un fournisseur existant. Zéro clé supplémentaire, un seul budget, un seul grand livre. Bénéfice en cascade : la découverte ramène le place_id, que gbp.py et reviews.py réutilisent en J1 — un text_search économisé par prospect diagnostiqué. Coût réel au volume du projet : 0,00 USD (1 000 appels Enterprise gratuits/mois ≈ 55 runs complets). Dette à traiter au passage : le code appelle maps.googleapis.com, c'est-à-dire l'API LEGACY, dont Google publie le guide de migration vers places.googleapis.com. Le faire maintenant évite de le faire deux fois.

SECONDAIRE — Brave Place Search, à évaluer en parallèle.
5 USD/1 000 tous champs inclus, 2 000 requêtes/mois gratuites, et surtout le SEUL fournisseur du panel entièrement hors du risque CGU Google (index indépendant). C'est la couverture d'assurance contre une dépendance à Google. Réserve non levée : la profondeur d'un index indépendant sur les PME de Lévis ou Trois-Rivières est probablement inférieure — à mesurer, le test est gratuit.

RÉSIDUEL — une route SERP conservée, mais rétrogradée au signal de marque.
Le SERP garde une utilité réelle mais différente : vérifier si une entreprise RESSORT sur ses propres mots-clés (c'est un signal de faiblesse SEO exploitable dans le mini-audit), et détecter les entreprises sans fiche Google Business Profile. Pour cet usage, Serper.dev : 2 500 requêtes gratuites (tout le pilote couvert), prépayé sans abonnement, ~0,001 USD/requête, environ 25x moins cher que SerpApi, et un endpoint Places en réserve. DataForSEO en second choix si le volume monte (0,0006 USD/requête, pay-as-you-go, mais dépôt de 50 USD et mode Standard asynchrone incompatible avec le contrat synchrone de api_io — n'utiliser que le mode Live).

COMPLÉMENT GRATUIT — registres officiels en couche de VÉRIFICATION, pas de découverte.
INSEE Sirene (France, NAF 4322B, exhaustif, gratuit) et Données Québec / REQ (SCIAN, gratuit) pour valider, dédoublonner et dater les candidats. Zefix (CH) est en revanche faible pour ce besoin : ni classification NOGA, ni téléphone, ni email. Blocage commun : aucun registre ne fournit d'URL de site web ni de données d'avis — donc rien pour alimenter J1. Un registre dit qui EXISTE, pas qui a une présence numérique faible.

=== 3. SORTIR DE SERPAPI : DÉCISION À PRENDRE MAINTENANT, TANT QU'ELLE EST GRATUITE ===

SerpApi cumule trois défauts, et le moment est idéal pour en sortir puisque AUCUNE clé n'est encore souscrite (SERP_API_KEY absente, préflight en NO-GO) : le coût de sortie est nul aujourd'hui, il ne le sera plus après le premier abonnement.
- ÉCONOMIQUE : abonnement mensuel à quota non reportable. À raison d'un run de 18 requêtes par mois, le plan d'entrée revient à ~1,39 USD PAR RECHERCHE. C'est le pire modèle possible pour une consultante solo à usage sporadique.
- JURIDIQUE : Google a assigné SerpApi le 2025-12-19. La juge Yvonne Gonzalez Rogers a rejeté les demandes DMCA en juillet 2026 (les URLs, extraits et données factuelles d'index ne sont pas des œuvres protégées), MAIS Google a confirmé amender sa plainte. Litige EN COURS au 2026-08-02 : c'est un risque de continuité de service sur l'unique canal de découverte.
- STRATÉGIQUE : Google Custom Search JSON API — la seule route SERP juridiquement irréprochable — est FERMÉE AUX NOUVEAUX CLIENTS et s'arrête le 2027-01-01 ; Bing Search API est MORTE depuis le 2025-08-11 (HTTP 410). Les deux voies officielles vers des résultats de recherche généralistes se sont fermées en 18 mois. Bâtir le cœur de la découverte sur un intermédiaire de scraping en litige avec son fournisseur de données amont, c'est accepter une fragilité structurelle. Places API est une API officielle sous contrat : c'est l'inverse exact de ce profil de risque.

=== 4. CE QUI EST DÉJÀ ACQUIS, TECHNIQUEMENT ===

Vérifié dans le code : api_io.call(fournisseur, endpoint, fn, ...) — diagnostic/api_io.py:294-301 — enveloppe une CLOSURE fournie par l'appelant. Le bus est donc AGNOSTIQUE au verbe HTTP, aux en-têtes et au corps de requête. Conséquence concrète : le POST + en-tête X-Goog-FieldMask exigé par Places API (New) passe SANS TOUCHER AU BUS, et changer de fournisseur SERP se limite à réécrire la closure dans discovery.py (~10 lignes) plus le remappage du JSON vers Candidate. La contrainte « une fonction qui fait un simple appel HTTP et renvoie du JSON » est en réalité plus permissive que ce que l'énoncé du mandat suppose. Aucun invariant n'est menacé par les migrations proposées.

Deux exceptions à signaler : Apify (asynchrone + coût non prévisible AVANT l'appel) casse le pre-check budgétaire de api_io._verifier_budget et devrait être écarté pour cette seule raison, indépendamment de son prix ; le mode Standard de DataForSEO pose le même problème d'asynchronisme.

=== 5. SÉQUENCE D'ACTION PROPOSÉE (aucune ne dépend d'un engagement financier) ===

1. TESTER AVANT DE PAYER, sur les 6 localités de l'ICP, avec les paliers gratuits : Places Text Search (1 000 appels Enterprise/mois gratuits), Brave Place Search (2 000/mois), Serper (2 500 à vie), OSM Overpass (gratuit). Mesurer sur chacun : nombre d'établissements HVAC trouvés, TAUX DE RENSEIGNEMENT DU SITE WEB (critère éliminatoire — sans URL, pas de diagnostic J1), disponibilité de la note et du nombre d'avis. Ce protocole coûte 0 USD et tranche empiriquement le choix.
2. NE PAS SAISIR DE PRIX DANS api_pricing.yaml SUR LA BASE DE CETTE ÉTUDE SEULE. Voir les incertitudes ci-dessous : aucune page tarifaire n'a pu être ouverte directement. Les montants ici sont des ordres de grandeur pour DÉCIDER, pas des valeurs pour CONFIGURER.
3. Une fois le fournisseur tranché, relever le tarif sur la page officielle, renseigner releve_le au format AAAA-MM-JJ, poser des budgets volontairement bas pour un pilote borné, puis run_preflight.py jusqu'au GO.
4. Faire trancher par le juriste, dans le même dossier que J6 : la durée de conservation des champs Google Places dans le vault au regard des Maps Platform Terms (le place_id est cachable sans limite, la plupart des autres champs non) ; et, si OSM est retenu, la portée de la clause de partage à l'identique de l'ODbL 1.0 sur une liste de prospection.
5. Anticiper un point RGPD non couvert aujourd'hui : Sirene et le REQ exposent des ENTREPRENEURS INDIVIDUELS, dont les données sont personnelles. Sirene applique un statut de diffusion restreinte pour les personnes qui s'y sont opposées — c'est un opt_out réglementaire qui doit se propager dans le champ opt_out de FicheProspect et son exclusion absolue à l'export. Un installateur HVAC en entreprise individuelle est un cas fréquent, pas une hypothèse d'école.


### Comparatif des fournisseurs

| Verdict | Fournisseur | Modèle tarifaire | Prix constaté (statut de vérification) | Couverture QC/CH/FR |
|---|---|---|---|---|
| **a_considerer** | SerpApi (fournisseur ACTUEL — diagnostic/discovery.py:92) | Abonnement mensuel avec quota de recherches. Pas de pay-as-you-go. Quo | SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, via recherche restreinte au domaine serpapi.com ; page NON ouverte, WebFetch bloqué) : plan Free = 100 recherches/mois san | Paramètres gl/hl/location permettant un ciblage Québec (gl=ca, hl=fr), Suisse (gl=ch) et France (gl=fr). Moteu |
| **recommande** | Serper.dev | Crédits prépayés (pas d'abonnement). 1 crédit = 1 requête jusqu'à 10 r | Palier gratuit : SOURCE OFFICIELLE INDIRECTE (serper.dev, 2026-08-02) — 2 500 requêtes gratuites, sans carte bancaire. --- Grille payante : RAPPORTÉ PAR UN TIERS UNIQUEME | Paramètres gl/hl/location. Endpoints multiples confirmés sur le domaine officiel : Search, Images, News, Maps, |
| **a_considerer** | DataForSEO | Pay-as-you-go strict, prix fixe par requête, dépôt minimum de 50 USD u | SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à dataforseo.com) : dépôt minimum 50 USD. Google Organic SERP, page 1 (10 résultats) — Live 0,002 USD | Ciblage par location_code / location_name et language_code, couvrant Canada, Suisse et France. L'endpoint Goog |
| **a_considerer** | Bright Data — SERP API | Facturation par tranche de 1 000 requêtes RÉUSSIES (les échecs ne sont | SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à brightdata.com) : 1,50 USD / 1 000 requêtes en pay-as-you-go, dégressif jusqu'à 1,00 USD / 1 000 à  | Ciblage géographique fin (pays, ville, code postal) via le réseau de proxys résidentiels — c'est l'argument di |
| **a_considerer** | Oxylabs — SERP Scraper API | Abonnement mensuel par paliers, tarifé au millier de résultats. | SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à oxylabs.io) — CHIFFRES CONTRADICTOIRES dans les extraits : 'à partir de 1,6 USD par 1 000 résultats | Ciblage par pays/ville revendiqué, réseau de proxys mondial. Couverture Canada / Suisse / France attendue. NON |
| **a_considerer** | SearchApi.io | Abonnement mensuel avec quota de recherches. Sans engagement. Les rech | SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à searchapi.io) : plan gratuit = 100 requêtes, sans carte bancaire ; plan Developer = 40 USD/mois pou | Paramètres gl/hl/location, gamme d'endpoints large (Search, Shopping, Autocomplete, AI Overview, AI Mode). NON |
| **ecarte** | ValueSERP (Traject Data) | Abonnement mensuel avec quota de crédits. | RAPPORTÉ PAR UN TIERS UNIQUEMENT (costbench, denebrixai, 2026-08-02 — aucune confirmation obtenue sur trajectdata.com) : 25 000 crédits à 50 USD/mois ; 200 000 crédits à  | Ciblage par location et paramètres Google standards. NON VÉRIFIÉ pour Québec / Suisse / France. |
| **ecarte** | Zenserp | Abonnement mensuel avec quota, remise annuelle de 20%. | RAPPORTÉ PAR UN TIERS (coldiq, lupagedigital, 2026-08-02 — page officielle non consultée) : plan gratuit 50 recherches/mois ; à partir de 49,99 USD/mois pour 5 000 recher | Paramètres de localisation standards. NON VÉRIFIÉ pour les marchés visés. |
| **ecarte** | ScraperAPI | Abonnement mensuel en crédits API, avec un MULTIPLICATEUR par domaine  | SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à scraperapi.com) : plan à 49 USD/mois pour 100 000 crédits API, soit 4 000 recherches Google (100 00 | Géociblage disponible sur l'endpoint Google SERP (revendiqué sur le domaine officiel). Couverture Canada/Suiss |
| **ecarte** | Apify (place de marché d'acteurs, notamment Google Maps Scraper) | Hybride : abonnement à la plateforme + tarification par acteur (souven | SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à apify.com) : plan gratuit = 5 USD de crédits d'usage chaque mois ; plan Starter = 29 USD/mois. Acte | Bonne : scraping de Google Maps par zone géographique, donc Québec / Suisse / France couverts au même titre qu |
| **ecarte** | Google Custom Search JSON API / Programmable Search Engine | Quota quotidien gratuit puis facturation au millier de requêtes, plafo | SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à developers.google.com) : 100 requêtes/jour gratuites ; 5 USD par 1 000 requêtes au-delà ; plafond d | Paramètres gl/cr/lr couvrant Canada, Suisse et France. Sans objet. |
| **ecarte** | Bing Search API (Microsoft) | Sans objet — service supprimé. | SOURCE OFFICIELLE (Microsoft Lifecycle, relevé 2026-08-02) : les API Bing Search ont été RETIRÉES le 11 août 2025. La création de nouvelles ressources Bing Search dans Az | Sans objet. |
| **recommande** | Brave Search API — Web Search ET Place Search | Pay-as-you-go au millier de requêtes, avec un palier gratuit récurrent | SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à brave.com) : palier gratuit = 2 000 requêtes/mois, 1 requête/seconde, carte utilisée pour vérificat | Index INDÉPENDANT (Brave n'interroge pas Google). Paramètres country/search_lang. POINT DE VIGILANCE MAJEUR ET |
| **recommande** | Google Places API (New) — Text Search / Nearby Search [ALTERNATIVE STR | Pay-as-you-go par SKU. Le SKU facturé dépend des CHAMPS demandés via l | Structure et quotas : SOURCE OFFICIELLE INDIRECTE (developers.google.com, relevé 2026-08-02) — depuis le 1er mars 2025, le crédit mensuel de 200 USD est remplacé par des  | La meilleure du panel, sans discussion. locationBias / locationRestriction par rectangle ou par cercle permett |
| **a_considerer** | OpenStreetMap / Overpass API | Gratuit, sans frais d'usage. Service public communautaire soumis à une | SOURCE OFFICIELLE INDIRECTE (wiki OSM + OSMF Operations, relevé 2026-08-02) : aucun frais d'usage sur les serveurs publics Overpass. Usage considéré comme sûr en dessous  | TRÈS INÉGALE, et c'est le problème. La couverture des commerces (POI) dans OSM est bonne en France et en Suiss |
| **recommande** | Registres officiels d'entreprises — INSEE Sirene (FR), Données Québec  | Gratuit. Service public / open data. Sirene : API gratuite après créat | SOURCE OFFICIELLE INDIRECTE (insee.fr, economie.gouv.fr, data.gouv.fr, donneesquebec.ca, bj.admin.ch, opendata.swiss — relevé 2026-08-02) : gratuité confirmée pour les tr | EXHAUSTIVE ET FAISANT AUTORITÉ sur les trois marchés — par construction, ce sont les registres légaux. Aucune  |

### Détail par fournisseur


#### SerpApi (fournisseur ACTUEL — diagnostic/discovery.py:92) — *a_considerer*

- **URL tarifs** : https://serpapi.com/pricing (+ https://serpapi.com/enterprise)
- **Prix constaté** : SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, via recherche restreinte au domaine serpapi.com ; page NON ouverte, WebFetch bloqué) : plan Free = 100 recherches/mois sans carte ; plan Developer = 5 000 recherches/mois ; plan Big Data = 30 000 recherches/mois à 250 USD/mois ; Enterprise à partir de 3 750 USD/mois pour 100 000 recherches ; dépassement 'reserved' 2,75 USD/1 000 et 'on-demand' 7,50 USD/1 000. --- RAPPORTÉ PAR UN TIERS (trustradius, apiserpent, costbench, 2026-08-02) et EN CONTRADICTION avec ce qui précède : Free = 250 recherches/mois, Starter 25 USD/1 000, Developer 75 USD/5 000, Production 150 USD/15 000, Big Data 275 USD/30 000. --- DISCORDANCE NON TRANCHÉE sur le palier gratuit (100 vs 250) et sur Big Data (250 vs 275 USD) : à confirmer sur la page avant toute saisie dans api_pricing.yaml.
- **Coût unitaire** : Entre 0,0083 et 0,025 USD par recherche selon le palier (250 USD / 30 000 = 0,0083 ; 25 USD / 1 000 = 0,025). Pour le run type de l'ICP persona1-quebec (3 gabarits x 6 localités = 18 requêtes) : 0,15 à 0,45 USD par run, MAIS un abonnement mensuel minimum de 25 USD est engagé quoi qu'il arrive — soit un coût réel de ~1,39 USD par recherche si l'on ne fait qu'un run de 18 requêtes par mois. C'est le pire modèle économique possible pour une consultante solo à usage sporadique.
- **Palier gratuit** : 100 recherches/mois sans carte bancaire (source officielle indirecte) OU 250/mois (source tierce). Contradiction non résolue.
- **Couverture** : Paramètres gl/hl/location permettant un ciblage Québec (gl=ca, hl=fr), Suisse (gl=ch) et France (gl=fr). Moteur google_maps / google_local disponible en plus de google. Qualité locale réputée bonne (proxy de Google lui-même). NON VÉRIFIÉ : la granularité réelle du paramètre 'location' pour des villes comme Lévis ou Trois-Rivières.
- **Pertinence** : C'est l'incumbent : déjà câblé, SERP_BASE_URL/SERP_API_KEY, format de réponse déjà mappé vers Candidate. Mais il répond à la mauvaise question — voir la recommandation. Il renvoie des PAGES WEB qu'il faut ensuite filtrer (domaines_exclus : pagesjaunes.ca, yelp, facebook, linkedin, 411.ca, houzz, kijiji, groupon + exiger_domaine_propre). Cette couche de filtres n'existe que pour réparer l'inadéquation de la source.
- **Conformité** : RISQUE JURIDIQUE ET DE CONTINUITÉ LE PLUS ÉLEVÉ DU PANEL. Google a assigné SerpApi le 2025-12-19 (DMCA §1201 + violation des CGU, contournement de 'SearchGuard' par rotation d'IP, fingerprinting et résolution automatisée de CAPTCHA). La juge Yvonne Gonzalez Rogers a REJETÉ les demandes DMCA en juillet 2026 (les URLs, extraits et données factuelles d'index ne sont pas des œuvres protégées) — mais Google a confirmé publiquement amender sa plainte dans la fenêtre de 21 jours. Litige EN COURS au 2026-08-02. Les CGU Google interdisent explicitement l'envoi de requêtes automatisées sans autorisation préalable ; en UE, l'arrêt CJUE Ryanair c/ PR Aviation (C-30/14) confirme qu'un exploitant peut interdire contractuellement le scraping même sur une base non protégée par le droit sui generis. Aucun impact RGPD direct (données d'entreprises, pas de personnes), mais un risque d'interruption de service et de réputation pour une consultante dont c'est l'unique canal de découverte.
- **Intégration** : NUL — déjà intégré. diagnostic/discovery.py:92 lit SERP_BASE_URL (défaut https://serpapi.com) et SERP_API_KEY. api_pricing.yaml a déjà les endpoints serp.search / serp.maps / serp.reviews à 0,0.
- **Justification** : Conserver comme source SECONDAIRE de signal de marque, pas comme moteur de découverte primaire. Trois raisons de le rétrograder : (1) modèle par abonnement mensuel non reportable, absurde pour un usage solo sporadique ; (2) litige Google en cours, risque de continuité ; (3) biais de sélection rédhibitoire — voir recommandation. Ne PAS le supprimer : il est déjà câblé, testé, et le coût de sortie est nul puisqu'aucune clé n'est encore engagée.

#### Serper.dev — *recommande*

- **URL tarifs** : https://serper.dev/ (page tarifaire non séparée du site principal)
- **Prix constaté** : Palier gratuit : SOURCE OFFICIELLE INDIRECTE (serper.dev, 2026-08-02) — 2 500 requêtes gratuites, sans carte bancaire. --- Grille payante : RAPPORTÉ PAR UN TIERS UNIQUEMENT (coldiq, apiserpent, serp.fast, 2026-08-02) — 50 USD / 50 000 crédits ; 375 USD / 500 000 ; 1 250 USD / 2,5 M ; 3 750 USD / 12,5 M, soit environ 1,00 USD à 0,30 USD par 1 000 requêtes en profondeur par défaut. La recherche restreinte au domaine officiel N'A PAS confirmé ces montants — à vérifier avant saisie dans api_pricing.yaml.
- **Coût unitaire** : ~0,001 USD par recherche au premier palier payant (50 USD / 50 000). Run type de 18 requêtes = 0,018 USD. Les 2 500 requêtes gratuites couvrent environ 138 runs complets de l'ICP persona1-quebec — soit la totalité d'un pilote, à coût nul.
- **Palier gratuit** : 2 500 requêtes gratuites à l'inscription, sans carte (source officielle indirecte). C'est le palier gratuit le plus généreux du panel SERP.
- **Couverture** : Paramètres gl/hl/location. Endpoints multiples confirmés sur le domaine officiel : Search, Images, News, Maps, PLACES, Videos, Shopping, Scholar, Patents, Autocomplete. L'existence d'un endpoint Places/Maps est un atout majeur : il permettrait de basculer la découverte vers des établissements sans changer de fournisseur. NON VÉRIFIÉ : le coût en crédits de l'endpoint Places, et la qualité des résultats sur Québec / Suisse romande.
- **Pertinence** : Meilleur rapport qualité/prix du panel SERP pur, ET porte d'entrée vers une découverte par établissements via son endpoint Places. Le modèle prépayé sans abonnement colle exactement au profil d'usage (une consultante solo, quelques runs par mois).
- **Conformité** : Même nature juridique que SerpApi : intermédiaire de scraping des SERP Google, donc exposé au même raisonnement CGU / Ryanair. N'est pas partie au litige Google à ce jour (2026-08-02) — mais le rejet des demandes DMCA en juillet 2026 profite à tout le secteur, et l'amendement annoncé par Google le menace tout autant. Aucun enjeu RGPD direct (données d'entreprises).
- **Intégration** : FAIBLE. api_io.call() accepte une closure fn arbitraire (diagnostic/api_io.py:294-301) : elle est agnostique au verbe HTTP, aux en-têtes et au corps de requête. Basculer de fournisseur = réécrire la closure de requête dans discovery.py (environ 10 lignes) + remapper la forme du JSON vers Candidate + ajouter/renseigner l'entrée serp dans api_pricing.yaml. Le schéma JSON de Serper n'est PAS compatible SerpApi : la seule variable SERP_BASE_URL ne suffit pas.
- **Justification** : Si l'on conserve une route SERP, c'est celle-là : 2 500 requêtes gratuites (pilote entier couvert à zéro euro), prépayé sans abonnement mensuel, environ 25x moins cher que SerpApi au crédit, et un endpoint Places qui ouvre la migration vers une découverte par établissements chez le même fournisseur. Réserve : la grille payante n'est confirmée que par des tiers.

#### DataForSEO — *a_considerer*

- **URL tarifs** : https://dataforseo.com/apis/serp-api/pricing — https://dataforseo.com/pricing/serp/google-organic-serp-api — https://dataforseo.com/pricing/serp/google-maps-serp-api
- **Prix constaté** : SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à dataforseo.com) : dépôt minimum 50 USD. Google Organic SERP, page 1 (10 résultats) — Live 0,002 USD, Standard priorité normale 0,0006 USD, Standard priorité haute 0,0012 USD. Google Maps SERP — facturé par tranche de 100 résultats, même fourchette 0,0006 (Standard) à 0,002 USD (Live). Des paramètres optionnels peuvent renchérir la requête (page 'The cost of all additional SERP API parameters explained' non consultée).
- **Coût unitaire** : 0,0006 USD par recherche en Standard, 0,002 USD en Live. Run type de 18 requêtes = 0,011 USD (Standard) à 0,036 USD (Live). Le dépôt de 50 USD représente environ 25 000 recherches en Live ou 83 000 en Standard — soit plusieurs années de pilote au rythme envisagé. C'est le prix unitaire le plus bas du panel, mais avec un ticket d'entrée de 50 USD.
- **Palier gratuit** : Aucun palier gratuit récurrent identifié. Dépôt minimum de 50 USD (source officielle indirecte). NON VÉRIFIÉ : l'existence d'un bac à sable gratuit ou d'un crédit d'essai.
- **Couverture** : Ciblage par location_code / location_name et language_code, couvrant Canada, Suisse et France. L'endpoint Google Maps SERP est explicitement positionné pour le SEO local et renvoie des fiches d'établissement. NON VÉRIFIÉ : la granularité des location_code au niveau des villes québécoises visées par l'ICP.
- **Pertinence** : Le modèle pay-as-you-go sans abonnement est le mieux aligné avec un système dont le préflight est en NO-GO et dont l'usage réel sera sporadique. Le mode Standard asynchrone (tâche postée puis récupérée) impose en revanche un aller-retour à deux temps, moins naturel derrière api_io.call() qui attend un appel synchrone unique ; le mode Live coûte 3x plus cher mais reste synchrone.
- **Conformité** : Même exposition CGU/Ryanair que les autres intermédiaires SERP. À noter : DataForSEO publie une page d'analyse juridique 'Is Scraping Google SERPs Legal?' — signe d'une prise en compte explicite du sujet, mais un article de blog fournisseur n'est pas un avis juridique opposable. Aucun enjeu RGPD direct.
- **Intégration** : MOYEN. Le mode Live tient dans une closure api_io.call() classique. Le mode Standard (le seul à 0,0006 USD) est asynchrone : POST d'une tâche, puis polling — cela ne rentre PAS dans le contrat 'un appel HTTP qui renvoie du JSON' sans une couche d'attente, qui devrait vivre dans la closure et non dans api_io. Recommandation : n'utiliser que le mode Live si l'on retient ce fournisseur.
- **Justification** : Prix unitaire imbattable et modèle pay-as-you-go idéal, mais deux frictions : un dépôt d'entrée de 50 USD sans palier gratuit pour tester, et un mode asynchrone qui complique l'intégration derrière le bus. À retenir si le volume monte (Suisse + France en plus du Québec) ; surdimensionné pour un premier pilote face aux 2 500 requêtes gratuites de Serper.

#### Bright Data — SERP API — *a_considerer*

- **URL tarifs** : https://brightdata.com/pricing/serp — https://docs.brightdata.com/scraping-automation/serp-api/pricing-and-billing
- **Prix constaté** : SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à brightdata.com) : 1,50 USD / 1 000 requêtes en pay-as-you-go, dégressif jusqu'à 1,00 USD / 1 000 à partir de 2 M de requêtes/mois. Seules les requêtes réussies sont facturées. Le titre de la page produit annonce '5K Requests/Month for Free' — palier gratuit NON CONFIRMÉ dans le corps de la page (non consultée).
- **Coût unitaire** : 0,0015 USD par recherche en pay-as-you-go. Run type de 18 requêtes = 0,027 USD. Si le palier de 5 000 requêtes/mois gratuites se confirme, le pilote entier est couvert à coût nul (environ 277 runs/mois).
- **Palier gratuit** : 5 000 requêtes/mois gratuites selon le titre de la page produit (https://brightdata.com/products/serp-api) — NON VÉRIFIÉ dans le détail : conditions, durée, carte bancaire requise ou non.
- **Couverture** : Ciblage géographique fin (pays, ville, code postal) via le réseau de proxys résidentiels — c'est l'argument différenciant de Bright Data pour les résultats locaux. Couverture Canada / Suisse / France sans réserve attendue. NON VÉRIFIÉ sur la page officielle.
- **Pertinence** : Le modèle 'requêtes réussies uniquement' est vertueux pour un budget serré et s'accorde bien avec le grand livre api_usage.log (pas de ligne facturée pour un échec). Reste un fournisseur SERP : même inadéquation de fond que SerpApi.
- **Conformité** : Point de vigilance spécifique : le réseau de proxys RÉSIDENTIELS de Bright Data a fait l'objet de controverses documentées sur le consentement des pairs dont la bande passante est utilisée. Pour une consultante qui vend du conseil en marque et qui opère sous CASL/nLPD/RGPD, la chaîne d'approvisionnement du fournisseur fait partie du risque réputationnel. Même exposition CGU Google que les autres. Fournisseur israélien — transferts hors UE à documenter dans le registre RGPD si des données personnelles transitaient (ce n'est pas le cas ici : requêtes d'entreprises).
- **Intégration** : FAIBLE. API HTTP synchrone renvoyant du JSON, compatible avec le contrat de api_io.call().
- **Justification** : Bon rapport prix/qualité et facturation à la réussite, mais le risque réputationnel du réseau de proxys résidentiels est un vrai sujet pour une activité de conseil en marque, et le palier gratuit annoncé n'est pas vérifié. Derrière Serper et DataForSEO.

#### Oxylabs — SERP Scraper API — *a_considerer*

- **URL tarifs** : https://oxylabs.io/products/scraper-api/serp — https://oxylabs.io/pricing
- **Prix constaté** : SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à oxylabs.io) — CHIFFRES CONTRADICTOIRES dans les extraits : 'à partir de 1,6 USD par 1 000 résultats' d'une part, 'plan Micro à partir de 0,5 USD par 1 000 résultats' d'autre part. Essai gratuit : jusqu'à 2 000 résultats, sans carte bancaire. Le prix d'entrée réel du plan Micro et son montant mensuel minimum n'ont PAS été établis.
- **Coût unitaire** : Entre 0,0005 et 0,0016 USD par résultat selon la source. Run type de 18 requêtes x 10 résultats = 180 résultats = 0,09 à 0,29 USD. ATTENTION : la facturation au RÉSULTAT et non à la REQUÊTE change le calcul par rapport à Serper ou SerpApi — max_resultats_par_requete: 10 dans l'ICP devient directement un levier de coût.
- **Palier gratuit** : Essai gratuit jusqu'à 2 000 résultats, sans carte bancaire (source officielle indirecte). Il s'agit d'un essai ponctuel, pas d'un palier gratuit récurrent.
- **Couverture** : Ciblage par pays/ville revendiqué, réseau de proxys mondial. Couverture Canada / Suisse / France attendue. NON VÉRIFIÉ.
- **Pertinence** : Fournisseur solide et mature, mais orienté entreprise. La facturation au résultat plutôt qu'à la requête complique légèrement la modélisation dans api_pricing.yaml (l'unité 'requetes' devrait devenir 'resultats' pour ce fournisseur) — faisable, la grille est une donnée.
- **Conformité** : Même exposition CGU/Ryanair. Comme Bright Data, s'appuie sur un réseau de proxys résidentiels : même question de chaîne d'approvisionnement. Oxylabs communique sur un cadre de conformité et des audits — non vérifié ici.
- **Intégration** : FAIBLE côté HTTP (API synchrone JSON), MOYEN côté modélisation : l'unité de facturation ('resultats') diffère de celle utilisée aujourd'hui ('requetes') dans api_pricing.yaml. Le mesureur passé à api_io.call(measure=...) devrait compter les résultats retournés et non les appels.
- **Justification** : Techniquement crédible et potentiellement le moins cher au résultat, mais deux chiffres contradictoires sur la page officielle, pas de palier gratuit récurrent, et une unité de facturation qui impose un ajustement du mesureur. Pas de raison de le préférer à Serper pour un pilote.

#### SearchApi.io — *a_considerer*

- **URL tarifs** : https://www.searchapi.io/pricing
- **Prix constaté** : SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à searchapi.io) : plan gratuit = 100 requêtes, sans carte bancaire ; plan Developer = 40 USD/mois pour 10 000 recherches ; plan Production = 100 USD/mois avec SLA 99,9%. ATTENTION : l'extrait officiel rattachait ces montants à la page 'Google AI Mode API' — il n'est PAS établi que la même grille s'applique à l'endpoint Google Search classique. À confirmer.
- **Coût unitaire** : 0,004 USD par recherche au plan Developer (40 USD / 10 000). Run type de 18 requêtes = 0,072 USD, mais avec un abonnement mensuel minimum de 40 USD engagé. Coût réel pour un run par mois : ~2,22 USD par recherche.
- **Palier gratuit** : 100 requêtes gratuites, sans carte bancaire (source officielle indirecte).
- **Couverture** : Paramètres gl/hl/location, gamme d'endpoints large (Search, Shopping, Autocomplete, AI Overview, AI Mode). NON VÉRIFIÉ : la qualité des résultats locaux sur le Québec et la Suisse romande.
- **Pertinence** : Format de réponse proche de celui de SerpApi, ce qui limiterait le travail de remappage vers Candidate. Mais le modèle par abonnement mensuel avec quota non reportable reproduit exactement le défaut économique de SerpApi, à un prix unitaire 6x moindre.
- **Conformité** : Même exposition CGU/Ryanair que les autres intermédiaires SERP. Aucun enjeu RGPD direct.
- **Intégration** : FAIBLE, probablement le plus faible du panel après SerpApi : la forme du JSON est largement calquée sur celle de SerpApi, donc le mapping vers Candidate dans discovery.py bougerait peu. NON VÉRIFIÉ : le degré exact de compatibilité de schéma.
- **Justification** : Alternative crédible et bon marché à SerpApi avec un effort de migration minimal, mais reproduit le mauvais modèle économique (abonnement mensuel non reportable) et le palier gratuit de 100 requêtes est trop maigre pour valider un pilote. De plus, la grille relevée pourrait ne concerner que l'API 'AI Mode'.

#### ValueSERP (Traject Data) — *ecarte*

- **URL tarifs** : https://trajectdata.com/serp/value-serp-api/pricing/
- **Prix constaté** : RAPPORTÉ PAR UN TIERS UNIQUEMENT (costbench, denebrixai, 2026-08-02 — aucune confirmation obtenue sur trajectdata.com) : 25 000 crédits à 50 USD/mois ; 200 000 crédits à 240 USD/mois ; 1 000 000 crédits à 1 000 USD/mois. Un tiers avance une fourchette de 0,50 à 1,50 USD par 1 000 recherches, ce qui est INCOHÉRENT avec 50 USD / 25 000 crédits (= 2,00 USD / 1 000). Palier gratuit sans carte bancaire mentionné, volume non précisé. Fiabilité globale de ces chiffres : FAIBLE.
- **Coût unitaire** : ~0,002 USD par recherche au premier palier (50 USD / 25 000), sous réserve que le chiffre tiers soit exact. Run type de 18 requêtes = 0,036 USD, avec 50 USD/mois engagés.
- **Palier gratuit** : Existe selon un tiers, sans carte bancaire — VOLUME NON TROUVÉ.
- **Couverture** : Ciblage par location et paramètres Google standards. NON VÉRIFIÉ pour Québec / Suisse / France.
- **Pertinence** : Positionné comme un clone bon marché de SerpApi, avec un schéma de réponse proche. Aucun avantage décisif sur Serper, et une documentation tarifaire nettement moins accessible.
- **Conformité** : Même exposition CGU/Ryanair. Aucun enjeu RGPD direct.
- **Intégration** : FAIBLE — schéma proche de SerpApi.
- **Justification** : Écarté pour insuffisance de sourçage : aucun tarif n'a pu être rattaché à une page officielle, et les chiffres tiers disponibles sont mutuellement incohérents (2,00 USD/1 000 calculé contre 0,50–1,50 USD/1 000 annoncé). Retenir un fournisseur dont on ne sait pas fiablement le prix contredit la règle de sourçage de cette étude.

#### Zenserp — *ecarte*

- **URL tarifs** : https://zenserp.com/pricing-plans/
- **Prix constaté** : RAPPORTÉ PAR UN TIERS (coldiq, lupagedigital, 2026-08-02 — page officielle non consultée) : plan gratuit 50 recherches/mois ; à partir de 49,99 USD/mois pour 5 000 recherches ; jusqu'à 1 000 000 de recherches à 1 599 USD/mois ; -20% en engagement annuel.
- **Coût unitaire** : ~0,010 USD par recherche au premier palier (49,99 USD / 5 000). Run type de 18 requêtes = 0,18 USD, avec 49,99 USD/mois engagés — soit ~2,78 USD par recherche réelle à raison d'un run mensuel.
- **Palier gratuit** : 50 recherches/mois (source tierce). Insuffisant pour un run complet de l'ICP persona1-quebec (18 requêtes) répété.
- **Couverture** : Paramètres de localisation standards. NON VÉRIFIÉ pour les marchés visés.
- **Pertinence** : Aucun avantage identifié sur Serper ou DataForSEO : 10x plus cher au crédit que Serper, palier gratuit 50x plus petit, abonnement mensuel obligatoire.
- **Conformité** : Même exposition CGU/Ryanair. Aucun enjeu RGPD direct.
- **Intégration** : FAIBLE — API HTTP JSON classique.
- **Justification** : Dominé sur tous les axes par Serper (10x plus cher, palier gratuit dérisoire, abonnement obligatoire) et par DataForSEO (17x plus cher au crédit). Aucune raison de le retenir.

#### ScraperAPI — *ecarte*

- **URL tarifs** : https://www.scraperapi.com/pricing/ — https://docs.scraperapi.com/getting-started/quick-start/credits-and-requests-costs
- **Prix constaté** : SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à scraperapi.com) : plan à 49 USD/mois pour 100 000 crédits API, soit 4 000 recherches Google (100 000 / 25). Plan gratuit : 1 000 crédits API, 5 connexions simultanées maximum. Les 7 premiers jours après inscription donnent accès à 5 000 requêtes d'essai. Les endpoints de données structurées (dont Google SERP) sont inclus dans tous les plans, y compris le gratuit, sans surcoût.
- **Coût unitaire** : 49 USD / 4 000 recherches Google = 0,0123 USD par recherche. Run type de 18 requêtes = 0,22 USD, avec 49 USD/mois engagés. Le multiplicateur x25 sur Google est le point à ne jamais oublier : le prix affiché 'par crédit' est trompeur d'un facteur 25 pour cet usage précis.
- **Palier gratuit** : 1 000 crédits API = seulement 40 recherches Google (multiplicateur 25). Plus 5 000 crédits d'essai sur 7 jours = 200 recherches Google. Très faible en pratique.
- **Couverture** : Géociblage disponible sur l'endpoint Google SERP (revendiqué sur le domaine officiel). Couverture Canada/Suisse/France attendue. NON VÉRIFIÉ.
- **Pertinence** : ScraperAPI est d'abord un service de proxy/scraping généraliste ; le SERP est un cas d'usage parmi d'autres. Le multiplicateur x25 sur Google révèle que ce n'est pas son terrain naturel. Un avantage marginal : il pourrait aussi servir au collecteur website.py (palier 0, fetch du site du prospect) — mais celui-ci fonctionne déjà en requests.get simple via api_io, sans besoin de proxy.
- **Conformité** : Même exposition CGU/Ryanair, aggravée par le positionnement explicite de contournement des mécanismes anti-scraping ('bypass any anti-scraping mechanism thrown your way' sur leur propre page) — formulation qui, dans le contexte du litige Google c/ SerpApi, est un aveu commercial peu confortable. Aucun enjeu RGPD direct.
- **Intégration** : FAIBLE — endpoint SERP structuré renvoyant du JSON.
- **Justification** : 12x plus cher que Serper à la recherche Google à cause du multiplicateur x25, palier gratuit de 40 recherches Google seulement, abonnement mensuel obligatoire. Le seul argument (mutualiser avec le fetch de website.py) ne tient pas : website.py n'a pas besoin de proxy.

#### Apify (place de marché d'acteurs, notamment Google Maps Scraper) — *ecarte*

- **URL tarifs** : https://apify.com/pricing — https://apify.com/compass/crawler-google-places
- **Prix constaté** : SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à apify.com) : plan gratuit = 5 USD de crédits d'usage chaque mois ; plan Starter = 29 USD/mois. Acteurs Google Maps : compass/crawler-google-places à 3,90 USD / 1 000 lieux (~0,004 USD par lieu) plus des frais de plateforme ; scraperlink/google-maps-scraper à 0,50 USD / 1 000 résultats ; microworlds/crawler-google-places affiché à 1,50 USD / 1 000 lieux avec emails. Les frais de compute s'ajoutent et ne sont pas chiffrables a priori.
- **Coût unitaire** : 0,0005 à 0,004 USD par établissement selon l'acteur, PLUS des frais de compute non déterministes. Le coût réel d'un run n'est pas prévisible à l'avance — ce qui est disqualifiant pour un système dont le garde-fou budgétaire (api_io._verifier_budget) fait un pre-check AVANT d'émettre l'appel.
- **Palier gratuit** : 5 USD de crédits d'usage par mois, renouvelés — soit 'plusieurs centaines de lieux' selon Apify. Suffisant pour tester, insuffisant pour cadencer un pilote de manière prévisible.
- **Couverture** : Bonne : scraping de Google Maps par zone géographique, donc Québec / Suisse / France couverts au même titre que Maps lui-même.
- **Pertinence** : Renvoie des ÉTABLISSEMENTS (nom, adresse, catégorie, site web, note, nombre d'avis) — donc formellement plus proche du besoin qu'un SERP. MAIS : dépendance à un acteur tiers non contrôlé, susceptible de casser ou de disparaître ; exécution asynchrone (lancement d'un run puis récupération du dataset) incompatible avec le contrat synchrone de api_io.call() sans couche d'attente ; coût non prévisible avant émission, ce qui casse le pre-check budgétaire.
- **Conformité** : Scraping de Google Maps — mêmes CGU Google, sans même la médiation contractuelle d'un fournisseur unique responsable : l'acteur est écrit par un tiers anonyme. Point RGPD AGGRAVANT : plusieurs acteurs annoncent l'extraction d'EMAILS ('with emails'), ce qui contredit frontalement l'invariant du projet (données 'personnes' exclusivement via API fournisseur, Contact à 6 champs, contact_email_source toujours renseigné). Utiliser un tel acteur casserait la piste d'audit RGPD.
- **Intégration** : ÉLEVÉ. Modèle asynchrone (run puis dataset), coût non prévisible avant appel, donc incompatible en l'état avec le pre-check budgétaire de api_io. Nécessiterait une exception dans le bus — exactement ce que l'architecture interdit.
- **Justification** : Écarté malgré un prix attractif : trois incompatibilités structurelles avec l'architecture (asynchrone vs api_io.call() synchrone ; coût non prévisible vs pre-check budgétaire ; acteurs à extraction d'emails vs minimisation RGPD à 6 champs). Dépendance à du code tiers non audité pour un maillon critique.

#### Google Custom Search JSON API / Programmable Search Engine — *ecarte*

- **URL tarifs** : https://developers.google.com/custom-search/v1/overview
- **Prix constaté** : SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à developers.google.com) : 100 requêtes/jour gratuites ; 5 USD par 1 000 requêtes au-delà ; plafond de 10 000 requêtes/jour. --- FAIT DÉCISIF, même source : l'API Custom Search JSON est FERMÉE AUX NOUVEAUX CLIENTS, et les clients existants ont jusqu'au 1er janvier 2027 pour migrer vers une autre solution.
- **Coût unitaire** : 0,005 USD par requête au-delà du quota gratuit. Sans objet : le projet n'a aucun compte existant, il ne peut donc plus souscrire.
- **Palier gratuit** : 100 requêtes/jour — mais inaccessible : l'API est fermée aux nouveaux clients.
- **Couverture** : Paramètres gl/cr/lr couvrant Canada, Suisse et France. Sans objet.
- **Pertinence** : C'était historiquement la seule route SERP juridiquement irréprochable (API officielle de Google, sous contrat). Cette option n'existe plus pour un nouvel entrant. C'est un point important pour l'analyse de risque : la voie légale 'propre' vers les résultats de recherche Google a été fermée par Google lui-même, ce qui explique la vitalité du marché gris des intermédiaires SERP.
- **Conformité** : Aurait été la seule option sans aucun risque CGU. Devenue inaccessible.
- **Intégration** : Sans objet — souscription impossible.
- **Justification** : ÉCARTÉ POUR CAUSE D'INDISPONIBILITÉ, pas pour cause de prix. L'API est fermée aux nouveaux clients et sa fin de vie est fixée au 2026-12-31 / 2027-01-01 pour les clients existants. Aucune souscription possible pour ce projet.

#### Bing Search API (Microsoft) — *ecarte*

- **URL tarifs** : https://learn.microsoft.com/en-us/lifecycle/announcements/bing-search-api-retirement
- **Prix constaté** : SOURCE OFFICIELLE (Microsoft Lifecycle, relevé 2026-08-02) : les API Bing Search ont été RETIRÉES le 11 août 2025. La création de nouvelles ressources Bing Search dans Azure était déjà désactivée depuis février 2025 ; l'annonce formelle date du 13 mai 2025 ; les endpoints publics renvoient HTTP 410 Gone depuis le 11 août 2025. Remplacement recommandé : 'Grounding with Bing Search' dans Azure AI Agents / Azure AI Foundry. Un tiers (ppc.land) rapporte que l'alternative coûte de 40% à 483% plus cher — RAPPORTÉ PAR UN TIERS, non vérifié.
- **Coût unitaire** : Sans objet.
- **Palier gratuit** : Aucun — service supprimé.
- **Couverture** : Sans objet.
- **Pertinence** : Aucune. Le remplacement (Grounding with Bing dans Azure AI Foundry) n'est pas une API de recherche mais un outil de grounding pour agents LLM : il exige un projet Azure complet, un groupe de ressources et un déploiement de modèle. C'est un engagement de plateforme, pas un endpoint HTTP. Cela contredit frontalement l'invariant du projet 'le LLM ne fetch JAMAIS' : Grounding with Bing fusionne précisément la collecte et le raisonnement, ce que l'architecture sépare délibérément.
- **Conformité** : Sans objet.
- **Intégration** : Sans objet / prohibitif pour le remplacement.
- **Justification** : Service mort depuis le 2025-08-11 (HTTP 410). Le remplacement proposé par Microsoft viole l'invariant architectural fondamental du projet (séparation collecte déterministe / raisonnement LLM) en plus d'imposer une adhérence à Azure. Sans objet.

#### Brave Search API — Web Search ET Place Search — *recommande*

- **URL tarifs** : https://api-dashboard.search.brave.com/documentation/pricing — https://brave.com/search/api/ — https://brave.com/blog/place-search-improved/
- **Prix constaté** : SOURCE OFFICIELLE INDIRECTE (relevé 2026-08-02, recherche restreinte à brave.com) : palier gratuit = 2 000 requêtes/mois, 1 requête/seconde, carte utilisée pour vérification d'identité uniquement, non débitée. Payant : 'à partir de 3 USD par 1 000 requêtes' selon une page, et 5 USD par 1 000 requêtes selon une page plus récente couvrant tous les types (Web, LLM Context, Images, News, Videos). PLACE SEARCH : 5 USD par 1 000 requêtes, TOUS LES CHAMPS INCLUS (pas de SKU par champ). Chaque plan inclut 5 USD de crédit gratuit chaque mois. DISCORDANCE 3 vs 5 USD/1 000 non tranchée — à confirmer sur le tableau de bord API.
- **Coût unitaire** : 0,003 à 0,005 USD par requête Web ; 0,005 USD par requête Place Search, tous champs inclus. Run type de 18 requêtes en Place Search = 0,09 USD — MAIS entièrement absorbé par le palier gratuit de 2 000 requêtes/mois. Coût réel pour le pilote envisagé : 0,00 USD.
- **Palier gratuit** : 2 000 requêtes/mois récurrentes (1 req/s) + 5 USD de crédit mensuel offert sur les plans payants. Le palier gratuit récurrent couvre environ 111 runs/mois de l'ICP persona1-quebec.
- **Couverture** : Index INDÉPENDANT (Brave n'interroge pas Google). Paramètres country/search_lang. POINT DE VIGILANCE MAJEUR ET NON VÉRIFIÉ : la profondeur d'un index indépendant sur des PME locales de Lévis, Trois-Rivières ou Sherbrooke est très probablement inférieure à celle de Google. C'est LE risque de ce fournisseur et il doit être testé empiriquement avant tout engagement, sur les 6 localités de l'ICP.
- **Pertinence** : Deux atouts décisifs. (1) Brave Place Search renvoie des ÉTABLISSEMENTS, pas des pages — c'est la bonne forme de donnée pour Candidate. Brave positionne explicitement ce produit comme l'alternative à Google Maps 'à un coût 6 à 7 fois moindre'. (2) Tarif forfaitaire tous champs inclus : pas de SKU à la carte comme chez Google Places, donc aucun risque de dérive budgétaire en ajoutant un champ. Le palier gratuit récurrent de 2 000 req/mois couvre intégralement le pilote.
- **Conformité** : MEILLEUR PROFIL DE CONFORMITÉ DU PANEL. Index propriétaire indépendant : aucune interrogation automatisée de Google, donc AUCUNE exposition aux CGU Google ni au raisonnement Ryanair/CJUE, et aucune exposition au contentieux Google c/ SerpApi. Brave a une politique de confidentialité publique forte et un positionnement 'privacy-first' — un argument de communication cohérent avec une consultante qui vend du conseil en marque sous CASL/nLPD/RGPD. Aucun enjeu RGPD direct sur les données d'entreprises.
- **Intégration** : FAIBLE. API HTTP GET simple avec en-tête X-Subscription-Token, réponse JSON — parfaitement compatible avec le contrat de api_io.call(). Il faudrait ajouter un fournisseur 'brave' dans api_pricing.yaml (la liste actuelle est anthropic, serp, google_places, apollo, http) et un mapping vers Candidate.
- **Justification** : RECOMMANDÉ COMME DEUXIÈME SOURCE, à tester en parallèle. Trois arguments : Place Search renvoie des établissements (bonne forme de donnée), tarif forfaitaire tous champs inclus à 5 USD/1 000 avec 2 000 requêtes/mois gratuites (pilote à coût nul), et surtout le SEUL fournisseur du panel totalement hors du risque juridique CGU Google. La réserve est sérieuse et non levée : la couverture d'un index indépendant sur les PME québécoises doit être mesurée avant de s'engager.

#### Google Places API (New) — Text Search / Nearby Search [ALTERNATIVE STRUCTURELLE, PAS UNE API SERP] — *recommande*

- **URL tarifs** : https://developers.google.com/maps/billing-and-pricing/pricing — https://developers.google.com/maps/documentation/places/web-service/usage-and-billing
- **Prix constaté** : Structure et quotas : SOURCE OFFICIELLE INDIRECTE (developers.google.com, relevé 2026-08-02) — depuis le 1er mars 2025, le crédit mensuel de 200 USD est remplacé par des quotas gratuits par SKU : 10 000 appels/mois gratuits pour les SKU Essentials, 5 000 pour Pro, 1 000 pour Enterprise. --- Montants unitaires : RAPPORTÉ PAR DES TIERS (safegraph, woosmap, openplacesapi, mapatlas, 2026-08-02 ; le tableau chiffré n'a PAS pu être lu sur la page officielle, WebFetch bloqué) — Text Search Pro = 32,00 USD / 1 000 appels ; Text Search Enterprise = 35,00 USD / 1 000 appels (l'ajout du champ 'rating' fait basculer de Pro à Enterprise) ; Text Search Essentials (IDs seuls) sans coût. Fourchette générale annoncée : 2 à 40 USD / 1 000 selon le SKU et le volume. CES MONTANTS DOIVENT ÊTRE RECONFIRMÉS SUR LA PAGE OFFICIELLE AVANT SAISIE dans api_pricing.yaml.
- **Coût unitaire** : 0,032 USD par appel Text Search Pro, 0,035 USD par appel Text Search Enterprise (note incluse). Run type de l'ICP (18 requêtes) = 0,63 USD en Enterprise — MAIS le quota de 1 000 appels Enterprise gratuits par mois couvre environ 55 runs complets par mois. POUR LE VOLUME RÉEL DE CE PROJET, LE COÛT EST DE 0,00 USD. C'est le prix unitaire le plus élevé du panel et, simultanément, le coût réel le plus bas à cette échelle. Attention : Text Search pagine par 20 résultats (jusqu'à 60 via next_page_token) et CHAQUE page est un appel facturé.
- **Palier gratuit** : 1 000 appels/mois gratuits sur le SKU Enterprise (celui requis pour obtenir la note et le nombre d'avis), 5 000 sur Pro, 10 000 sur Essentials. Renouvelé chaque mois. Une carte bancaire et un compte de facturation Google Cloud restent obligatoires.
- **Couverture** : La meilleure du panel, sans discussion. locationBias / locationRestriction par rectangle ou par cercle permettent de couvrir un TERRITOIRE de manière exhaustive plutôt que de dépendre d'un classement. includedType permet de filtrer par catégorie d'établissement. Couverture Québec, Suisse romande et France équivalente à celle de Google Maps — c'est-à-dire excellente pour des installateurs HVAC, qui sont typiquement des commerces avec fiche d'établissement.
- **Pertinence** : C'EST L'OPTION LA PLUS PERTINENTE DU PANEL, pour cinq raisons vérifiables dans le code. (1) La réponse EST déjà un Candidate : displayName, formattedAddress, location, types, websiteUri, rating, userRatingCount, businessStatus — là où un SERP renvoie une URL qu'il faut ensuite qualifier. (2) Toute la couche de filtres de l'ICP (domaines_exclus : pagesjaunes.ca, yelp, facebook, linkedin, 411.ca, houzz, kijiji, groupon + exiger_domaine_propre) devient LARGEMENT INUTILE : un annuaire n'est pas un établissement HVAC. Ces filtres n'existent que pour réparer l'inadéquation du SERP. (3) Le fournisseur google_places EST DÉJÀ CÂBLÉ : gbp.py:49 et reviews.py:89/99 appellent maps.googleapis.com via api_io, et api_pricing.yaml expose déjà google_places.text_search / place_details / nearby_search. Zéro nouveau fournisseur, zéro nouvelle clé, un seul budget. (4) La découverte ramènerait le place_id, que les collecteurs gbp.py et reviews.py pourraient réutiliser en J1 — économisant un text_search par prospect diagnostiqué. (5) rating et userRatingCount arrivent DÈS LA DÉCOUVERTE, ce qui alimente directement la dimension 'avis' de rubric_persona1 (20 points) et la dimension 'presence_locale' (25 points) : 45 des 100 points du score sont pré-alimentés avant même le diagnostic. DETTE À NOTER : le code actuel appelle maps.googleapis.com, c'est-à-dire l'API Places LEGACY, dont Google indique explicitement le statut 'Legacy' avec un guide de migration vers Places API (New) sur places.googleapis.com. Migrer maintenant évite de le faire deux fois.
- **Conformité** : API OFFICIELLE SOUS CONTRAT — aucune zone grise de scraping, aucune exposition aux CGU anti-requêtes-automatisées, aucune exposition au contentieux Google c/ SerpApi. C'est l'inverse exact du profil de risque de SerpApi. À respecter en revanche : les Google Maps Platform Terms interdisent la mise en cache prolongée de la plupart des champs (le place_id est l'exception, cachable sans limite) et interdisent la constitution d'une base concurrente de Google. Or le projet écrit des fiches Markdown persistantes dans le vault. POINT À FAIRE VALIDER : la durée de conservation des champs Places dans le vault et le TTL du cache disque de api_io doivent être alignés sur ces conditions. C'est le seul vrai point de conformité de cette option, et il est contractuel, pas pénal. Aucun enjeu RGPD (données d'établissements) tant qu'aucun nom de personne n'est collecté par cette voie.
- **Intégration** : MOYEN, mais entièrement dans le contrat existant. api_io.call() accepte une closure fn arbitraire (diagnostic/api_io.py:294-301) : elle est AGNOSTIQUE au verbe HTTP et aux en-têtes, donc le POST + X-Goog-FieldMask requis par Places API (New) passe sans modifier le bus. Travail réel : (a) un nouveau collecteur ou une variante de DiscoveryCollector dans discovery.py mappant la réponse Places vers Candidate ; (b) enrichir l'ICP YAML avec des zones géographiques (centre + rayon) au lieu de gabarits de requêtes textuelles — l'ICP est une DONNÉE, donc c'est de la configuration, pas du code ; (c) renseigner google_places.text_search dans api_pricing.yaml. Les invariants sont préservés : collecteur enfichable héritant de Collector, échec isolé via safe_collect, aucun import requests hors api_io.
- **Justification** : RECOMMANDATION PRINCIPALE. Seule option qui renvoie la bonne forme de donnée (un établissement, pas une page), qui réutilise un fournisseur DÉJÀ câblé derrière api_io, qui pré-alimente 45 des 100 points de la rubrique dès la découverte, qui offre un contrôle géographique réel du territoire, et qui est juridiquement propre (API officielle sous contrat). Coût réel pour le volume du projet : 0,00 USD grâce aux 1 000 appels Enterprise gratuits mensuels. Deux réserves à traiter : reconfirmer les montants 32/35 USD sur la page officielle, et cadrer la conservation des champs Places dans le vault au regard des Maps Platform Terms.

#### OpenStreetMap / Overpass API — *a_considerer*

- **URL tarifs** : https://wiki.openstreetmap.org/wiki/Overpass_API — https://operations.osmfoundation.org/policies/api/ — https://dev.overpass-api.de/overpass-doc/en/preface/commons.html
- **Prix constaté** : SOURCE OFFICIELLE INDIRECTE (wiki OSM + OSMF Operations, relevé 2026-08-02) : aucun frais d'usage sur les serveurs publics Overpass. Usage considéré comme sûr en dessous de 10 000 requêtes/jour ET 1 Go/jour. Un mécanisme de délestage automatique suit les requêtes par utilisateur anonymisé pour préserver l'accès des usagers modérés en cas de saturation. Données sous Open Database License (ODbL) 1.0.
- **Coût unitaire** : 0,00 USD. Le run type de 18 requêtes est très en deçà de toute limite. Coût réel : uniquement le temps d'ingénierie.
- **Palier gratuit** : Intégralement gratuit dans les limites de la politique d'usage (< 10 000 requêtes/jour, < 1 Go/jour). Aucune carte bancaire, aucun compte.
- **Couverture** : TRÈS INÉGALE, et c'est le problème. La couverture des commerces (POI) dans OSM est bonne en France et en Suisse (communautés OSM actives, imports d'annuaires) et nettement plus faible au Québec pour les PME de services — or le Québec est le PREMIER marché de la séquence. Le tag pertinent (craft=hvac ou trade=hvac) existe dans le schéma OSM, mais SON TAUX DE RENSEIGNEMENT RÉEL SUR LES 6 LOCALITÉS DE L'ICP N'A PAS ÉTÉ VÉRIFIÉ et constitue le facteur limitant. À mesurer empiriquement avant tout usage — c'est une requête gratuite, donc le test ne coûte rien.
- **Pertinence** : Renvoie des ÉLÉMENTS GÉOGRAPHIQUES avec tags — donc la bonne forme, comme une API de lieux. Mais deux manques rédhibitoires en tant que source primaire : le champ website est très inégalement renseigné (or le site web est l'entrée OBLIGATOIRE de tout le pipeline J1 : website.py, seo.py et social.py en dépendent), et il n'y a AUCUNE donnée d'avis ni de note — la dimension 'avis' de rubric_persona1 (20 points) resterait vide. Usage réaliste : recoupement gratuit et vérification de couverture, ou détection d'établissements ABSENTS de Google Maps (un signal de faible présence locale intéressant en soi pour l'argumentaire commercial de la consultante).
- **Conformité** : PROFIL EXCELLENT sur le plan de l'accès (données ouvertes, aucune CGU anti-scraping, aucun risque de litige), MAIS avec une contrainte de licence à ne pas sous-estimer : l'ODbL 1.0 impose l'attribution ET une clause de partage à l'identique sur les bases DÉRIVÉES. Constituer une liste de prospection à partir de données OSM peut, selon la manière dont elles sont combinées et redistribuées, faire tomber la base produite sous obligation de partage. Pour un export Kemana strictement interne et non redistribué, le risque est faible ; il devient réel si la liste est vendue ou transmise à un tiers. À faire trancher par le juriste, en même temps que le dossier J6. Aucun enjeu RGPD (données géographiques d'établissements).
- **Intégration** : FAIBLE côté HTTP (GET ou POST vers un endpoint Overpass, réponse JSON, compatible api_io.call()), MOYEN côté requêtage : Overpass QL est un langage de requête spécifique, et l'ICP YAML devrait porter des zones (bbox ou around) plutôt que des gabarits textuels. Ajouter un fournisseur 'osm' dans api_pricing.yaml à prix 0 — le bus fonctionne parfaitement avec un prix nul, il continuera de journaliser les appels, la latence et l'empreinte estimée.
- **Justification** : À retenir comme source de RECOUPEMENT gratuite, pas comme source primaire. Deux manques disqualifiants pour le pipeline : champ website très inégalement renseigné (or c'est l'entrée obligatoire de J1) et absence totale de données d'avis (dimension à 20 points). En revanche : coût nul, aucun risque CGU, et une utilité propre — repérer les établissements absents de Google Maps est en soi un signal de faible présence locale exploitable commercialement. Le test de couverture sur les 6 localités de l'ICP est gratuit : le faire avant de conclure.

#### Registres officiels d'entreprises — INSEE Sirene (FR), Données Québec / REQ (QC), Zefix (CH) — *recommande*

- **URL tarifs** : https://www.insee.fr/fr/information/6675111 — https://www.data.gouv.fr/dataservices/api-sirene-open-data — https://www.donneesquebec.ca/recherche/dataset/registre-des-entreprises — https://www.zefix.admin.ch/ZefixPublicREST/ — https://opendata.swiss/fr/dataset/zefix-zentraler-firmenindex
- **Prix constaté** : SOURCE OFFICIELLE INDIRECTE (insee.fr, economie.gouv.fr, data.gouv.fr, donneesquebec.ca, bj.admin.ch, opendata.swiss — relevé 2026-08-02) : gratuité confirmée pour les trois. INSEE Sirene : environ 25 millions d'entreprises et 36 millions d'établissements immatriculés depuis 1973, mise à jour quotidienne, recherche multicritère et phonétique, code NAF/APE disponible comme critère (4322B pour les travaux d'installation d'équipements thermiques et de climatisation). Données Québec / REQ : données publiques regroupées par secteur d'activité, mise à jour DEUX FOIS PAR MOIS, guide d'utilisation documentant la structure et les codes SCIAN, contact Groupe.EOS@req.gouv.qc.ca. Zefix : API REST publique officielle de l'Office fédéral du registre du commerce, données de base quotidiennes (raison sociale, siège, adresse) + publications FOSC.
- **Coût unitaire** : 0,00 USD. Pour le Québec, il ne s'agit même pas d'appels API mais d'un téléchargement de fichiers en masse, donc hors du périmètre de api_io et hors budget.
- **Palier gratuit** : Intégralement gratuit, sans limite tarifaire, sur les trois marchés de la séquence géographique.
- **Couverture** : EXHAUSTIVE ET FAISANT AUTORITÉ sur les trois marchés — par construction, ce sont les registres légaux. Aucune source commerciale ne peut égaler cette exhaustivité. Filtrage sectoriel : NAF 4322B en France, SCIAN au Québec (documenté dans le guide d'utilisation du REQ). LIMITE MAJEURE POUR LA SUISSE : Zefix ne fournit NI classification sectorielle NOGA, NI téléphone, NI email (confirmé par plusieurs sources, dont opendata.swiss et une analyse tierce). Le ciblage HVAC en Suisse romande via Zefix seul est donc IMPRATICABLE sans croiser avec une autre source.
- **Pertinence** : Complément de très haute valeur, mais PAS un moteur de découverte au sens du pipeline. Ce que les registres apportent : exhaustivité, autorité juridique, filtrage sectoriel fiable (FR/QC), forme juridique, date d'immatriculation (un signal de fraîcheur exploitable), et une base de dédoublonnage et de vérification bien plus solide que la normalisation de domaine actuelle. Ce qu'ils N'APPORTENT PAS et qui est bloquant : AUCUNE URL de site web (l'entrée obligatoire de J1), aucune note, aucun avis, aucune donnée de présence en ligne — c'est-à-dire précisément la matière du diagnostic de marque. Un registre dit qui EXISTE ; il ne dit rien de la présence numérique, qui est tout l'objet du produit.
- **Conformité** : MEILLEUR PROFIL DE CONFORMITÉ DE TOUTE L'ÉTUDE. Sources publiques officielles, réutilisation expressément prévue, aucune CGU anti-scraping, aucun risque de litige, aucune dépendance commerciale. Point RGPD à surveiller néanmoins : Sirene et le REQ exposent des données d'ENTREPRENEURS INDIVIDUELS, qui sont des données à caractère personnel — le régime n'est pas le même que pour une société. Sirene applique d'ailleurs un statut de diffusion restreinte pour les personnes physiques qui s'y sont opposées, et ce statut DOIT être respecté (c'est l'équivalent réglementaire d'un opt_out : il s'articule naturellement avec le champ opt_out déjà présent dans FicheProspect et son exclusion absolue à l'export). Un installateur HVAC en entreprise individuelle est un cas fréquent : ce n'est pas une hypothèse d'école.
- **Intégration** : VARIABLE. Sirene : API REST JSON après souscription — compatible api_io.call(), effort faible, à ajouter comme fournisseur 'sirene' à prix 0 dans api_pricing.yaml. Zefix : API REST publique — effort faible, mais utilité limitée sans classification sectorielle. Données Québec / REQ : ce n'est PAS une API mais un jeu de fichiers rafraîchi deux fois par mois — l'intégration naturelle n'est pas le bus réseau mais un import périodique hors ligne, ce qui sort du périmètre de api_io et n'a donc aucun coût ni budget à modéliser.
- **Justification** : RECOMMANDÉ EN COMPLÉMENT, jamais en source unique. Trois usages à forte valeur et à coût nul : (1) valider et dédoublonner les candidats découverts par Places sur une base faisant autorité ; (2) en France, cibler par NAF 4322B avec une exhaustivité qu'aucune source commerciale n'offre ; (3) exploiter la date d'immatriculation comme signal de fraîcheur. Le blocage reste le même partout : aucune URL de site web, aucune donnée d'avis — donc rien pour alimenter le diagnostic J1. Pour la Suisse romande, l'absence de classification NOGA dans Zefix rend le ciblage sectoriel impraticable en solo. À traiter comme une couche de VÉRIFICATION, pas de découverte.

### Incertitudes déclarées

- LIMITE MÉTHODOLOGIQUE MAJEURE À LIRE EN PREMIER — AUCUNE page tarifaire n'a pu être ouverte directement. L'outil WebFetch renvoie HTTP 403 pour TOUTES les URL de cet environnement (vérifié : le blocage touche même https://example.com), et curl direct est refusé par le proxy (CONNECT rejeté, 403). Tous les chiffres de cette étude proviennent donc de WebSearch. Deux niveaux de fiabilité en découlent : (a) SOURCE OFFICIELLE INDIRECTE = recherche restreinte au domaine officiel du fournisseur, le moteur a lu la page mais moi non — fiable mais non contrôlable ligne à ligne ; (b) RAPPORTÉ PAR UN TIERS = blog ou comparateur. AUCUN chiffre de cette étude ne peut être qualifié de 'vérifié sur la page officielle'. CONSÉQUENCE OPÉRATIONNELLE : ces montants suffisent à DÉCIDER d'une direction, ils ne suffisent PAS à renseigner knowledge/api_pricing.yaml. Chaque prix doit être reconfirmé sur la page du fournisseur retenu, avec la date, avant saisie.
- SERPAPI — CONTRADICTION NON RÉSOLUE sur deux points. Palier gratuit : 100 recherches/mois (recherche restreinte à serpapi.com) CONTRE 250 recherches/mois (trustradius, apiserpent, costbench). Plan Big Data : 250 USD/mois (domaine officiel) CONTRE 275 USD/mois (tiers). Il est possible que les sources tierces reflètent une grille périmée, ou que la grille ait changé. Non tranché.
- SERPER.DEV — la grille payante (50 USD / 50 000 crédits, etc.) provient EXCLUSIVEMENT de sources tierces (coldiq, apiserpent, serp.fast). La recherche restreinte à serper.dev n'a confirmé QUE le palier gratuit de 2 500 requêtes. La règle '11-100 résultats = 2 crédits' est également de source tierce uniquement. Or l'ICP fixe max_resultats_par_requete: 10, donc à la limite exacte du seuil de doublement — un réglage à 11 doublerait le coût. À vérifier impérativement.
- GOOGLE PLACES API — les montants unitaires (Text Search Pro 32,00 USD / 1 000 ; Enterprise 35,00 USD / 1 000) sont RAPPORTÉS PAR DES TIERS (safegraph, woosmap, openplacesapi, mapatlas). Le tableau chiffré officiel de developers.google.com n'a pas pu être lu. En revanche, la STRUCTURE (SKU Essentials / Pro / Enterprise, facturation au SKU le plus élevé, quotas gratuits mensuels de 10 000 / 5 000 / 1 000 depuis le 2025-03-01 en remplacement du crédit de 200 USD) est de source officielle indirecte et concordante. C'est la structure, pas le montant, qui fonde la recommandation — mais le montant doit être confirmé.
- GOOGLE PLACES — je n'ai PAS vérifié quel SKU exact est déclenché par la combinaison de champs dont le pipeline a besoin (displayName, formattedAddress, location, types, websiteUri, rating, userRatingCount). J'ai retenu Enterprise (35 USD / 1 000) par prudence, parce qu'une source tierce indique que l'ajout de 'rating' fait basculer de Pro à Enterprise. Le masque de champs exact détermine le SKU et donc le coût : à établir champ par champ sur la page officielle avant tout engagement. Le quota gratuit correspondant (1 000/mois en Enterprise contre 5 000 en Pro) change d'un facteur 5 selon la réponse.
- GOOGLE PLACES — pagination non chiffrée : Text Search renvoie environ 20 résultats par page, jusqu'à 60 via next_page_token, et CHAQUE page est un appel facturé. Le nombre réel d'appels par run dépend donc du nombre de résultats souhaité par zone, que je n'ai pas modélisé. Mes estimations 'coût par run' supposent un seul appel par requête et SOUS-ESTIMENT donc le coût si l'on pagine.
- BRAVE SEARCH — discordance 3 USD/1 000 contre 5 USD/1 000 entre deux pages du domaine brave.com, sans que je puisse déterminer laquelle est à jour. Le tarif Place Search de 5 USD/1 000 'tous champs inclus' est cohérent entre sources mais non contrôlé directement.
- BRAVE SEARCH — INCERTITUDE LA PLUS LOURDE DE CONSÉQUENCE : la couverture réelle d'un index INDÉPENDANT sur des PME de services au Québec (Lévis, Trois-Rivières, Sherbrooke) n'a PAS été mesurée. C'est le facteur qui décide de la viabilité de cette option, et aucune source ne le documente. Seul un test empirique tranche — il est gratuit (2 000 requêtes/mois).
- OPENSTREETMAP — le taux de renseignement réel des tags HVAC (craft=hvac ou trade=hvac) et surtout du champ website sur les 6 localités de l'ICP n'a PAS été mesuré. J'affirme que la couverture québécoise des PME de services est plus faible que la couverture européenne : c'est une appréciation générale sur les données OSM, PAS un relevé sur ces localités. À vérifier par une requête Overpass, qui ne coûte rien.
- OXYLABS — deux prix contradictoires dans les extraits du domaine officiel ('à partir de 1,6 USD / 1 000 résultats' et 'plan Micro à partir de 0,5 USD / 1 000 résultats'), sans montant d'abonnement mensuel minimum. Le prix d'entrée réel n'est PAS établi.
- BRIGHT DATA — le palier gratuit de '5K requests/month' ne provient QUE du TITRE de la page produit, pas de son contenu. Conditions, durée et obligation de carte bancaire : NON VÉRIFIÉES.
- VALUESERP — aucun tarif rattaché à une page officielle. Les chiffres tiers disponibles sont mutuellement INCOHÉRENTS (50 USD / 25 000 crédits = 2,00 USD par 1 000, contre une fourchette annoncée de 0,50 à 1,50 USD par 1 000). C'est le motif principal de sa mise à l'écart.
- ZENSERP — grille entièrement de source tierce (coldiq, lupagedigital). Page officielle non consultée.
- SEARCHAPI.IO — les montants relevés (Developer 40 USD / 10 000 ; Production 100 USD) étaient rattachés dans l'extrait officiel à la page 'Google AI Mode API'. Il n'est PAS établi que la même grille s'applique à l'endpoint Google Search classique, qui est celui dont le projet aurait besoin.
- DATAFORSEO — la page 'The cost of all additional SERP API parameters explained' n'a pas été consultée : des paramètres optionnels peuvent renchérir la requête au-delà des 0,0006 à 0,002 USD relevés. L'existence d'un bac à sable gratuit ou d'un crédit d'essai n'a pas été trouvée non plus.
- QUALITÉ DES RÉSULTATS LOCAUX — pour AUCUN fournisseur SERP je n'ai pu vérifier la granularité réelle du paramètre de localisation au niveau des villes de l'ICP (Québec, Lévis, Trois-Rivières, Sherbrooke, Laval, Longueuil) ni pour la Suisse romande. Toutes mes appréciations de 'couverture géographique' sont déduites de la documentation générale des fournisseurs, jamais mesurées. C'est un angle mort de cette étude que seul un test comparatif comble.
- APOLLO — hors mandat, donc non étudié. Signalé pour mémoire : APOLLO_API_KEY est bloquante au préflight (diagnostic/preflight.py:51) et apollo.people_enrichment / organization_search sont à 0,0 dans api_pricing.yaml. Le maillon contact du J4 reste donc non chiffré, et il porte le risque RGPD le plus élevé de la chaîne (données de personnes). Une étude distincte est nécessaire.
- GOOGLE c/ SERPAPI — le rejet des demandes DMCA de juillet 2026 est rapporté par des sources de presse spécialisée (androidheadlines, thenextweb, theregister, slashdot), pas par le document judiciaire lui-même. La juge citée est Yvonne Gonzalez Rogers. Google a annoncé amender sa plainte dans une fenêtre de 21 jours. L'état exact de la procédure au 2026-08-02 n'est PAS établi avec certitude, et l'issue est ouverte. Cette étude en tire une conclusion de RISQUE DE CONTINUITÉ, pas une conclusion juridique.
- CONFORMITÉ — les développements sur les CGU Google, l'arrêt CJUE Ryanair c/ PR Aviation (C-30/14) et hiQ c/ LinkedIn sont une synthèse de sources secondaires. Ce N'EST PAS un avis juridique. Le point le plus actionnable et le moins couvert reste la CONSERVATION DES DONNÉES GOOGLE PLACES DANS LE VAULT au regard des Maps Platform Terms : je sais que le place_id est cachable sans limite et que la plupart des autres champs ne le sont pas, mais je n'ai PAS lu le texte des conditions. À faire trancher par le juriste au même titre que le dossier J6.

---


<a id="s5"></a>

## 5. Marché — enrichissement contact B2B


**Recommandation.**

TRANCHE : NON, ne pas payer d enrichisseur pour la majorite des cas. Construire d abord le socle gratuit, garder l enrichisseur en recours strict, et ne rien souscrire avant d avoir MESURE le taux de succes reel sur le persona.

=== 1. LE RAISONNEMENT CHIFFRE ===

Hypothese de volume, tiree du CODE et non supposee : icp/persona1-quebec.yaml fixe max_enrichissements a 25 par run. Le plan de requetes produit 3 gabarits x 6 localites x 10 resultats = 180 resultats bruts par run, soit apres dedup par domaine normalise de l ordre de 60 a 90 domaines uniques (ESTIMATION, non mesuree : aucun run reel n a jamais eu lieu). A une cadence realiste pour une consultante solo de 2 runs par mois : 50 enrichissements par mois, 600 par an.

Cout annuel a 50 enrichissements/mois (tous chiffres RAPPORTES PAR DES TIERS, non verifies) :
- Cognism            : 16 500 a 27 500 USD/an  =>  27,50 a 45,80 USD / contact
- Apollo Organization : 1 428 USD/an           =>   2,38 USD / contact  (si l API exige bien ce palier)
- People Data Labs Pro: 1 176 USD/an           =>   1,96 USD / contact
- Dropcontact Business:   948 EUR/an           =>   1,58 EUR / contact
- Kaspr Business      :   948 EUR/an           =>   1,58 EUR / contact
- Clearbit / Breeze   :   900 USD/an           =>   1,50 USD / contact
- Apollo Basic        :   588 USD/an           =>   0,98 USD / contact
- Findymail Basic     :   492 USD/an           =>   0,82 USD / contact
- Lusha Starter       :   449 USD/an           =>   0,75 USD / contact
- Hunter Starter      :   408 USD/an           =>   0,68 USD / contact
- Snov.io Starter     :   351 USD/an           =>   0,59 USD / contact
- FullEnrich Start    :   348 USD/an           =>   0,58 USD / contact
- Dropcontact Starter :   288 EUR/an           =>   0,48 EUR / contact
- Anymailfinder 14$   :   168 USD/an           =>   0,28 USD / email VERIFIE, rien sur les echecs
- Prospeo Free        :     0 USD/an           =>   0,00 (75 credits/mois)
- Hunter Free         :     0 USD/an           =>   0,00 (50 credits/mois)
- SOCLE INTERNE       :     0 USD/an           =>   0,00 par contact, cout = developpement

Premier enseignement, contre-intuitif : le prix par CREDIT n a aucune importance a ce volume. Un credit Apollo coute nominalement moins de 0,02 USD, un credit PDL 0,28 USD — quatorze fois plus. Mais a 50 unites par mois, Apollo revient PLUS cher par contact utile qu Anymailfinder, parce que ce que l on paie n est pas la donnee, c est le PLANCHER D ABONNEMENT dimensionne pour une equipe de vente. Sur les paliers d entree, 86 a 95 pour cent de la dotation est perdue chaque mois. Toute grille saisie dans api_pricing.yaml sur la base du prix nominal du credit donnerait donc une image FAUSSE du cout reel du systeme, et ferait mentir le grand livre api_usage.log et l ecran GreenIT du cockpit.

Second enseignement, decisif : le seul modele economiquement sain a ce volume est celui qui ne facture QUE le succes (Anymailfinder, Findymail, FullEnrich) ou celui qui ne facture RIEN (paliers gratuits Prospeo 75/mois et Hunter 50/mois, qui couvrent a eux seuls le volume mensuel estime).

=== 2. LE VRAI ARGUMENT N EST PAS LE PRIX, C EST LA COUVERTURE — PUIS LE DROIT ===

Couverture. Toutes les sources concordent sur un point : ces bases sont excellentes sur le SaaS nord-americain et se degradent hors de ce perimetre. Des avis G2 rapportent en Europe des intitules perimes et des numeros invalides chez Apollo. Sur la Suisse, une source note que les bases globales captent bien les entreprises centralement indexees mais manquent la densite des PME hors grandes villes, produisant une bonne couverture grands comptes et une donnee PME mince. Les tests independants rapportes situent la precision reelle des emails entre 65 et 90 pour cent la ou les editeurs revendiquent 95 pour cent et plus, avec une deterioration annuelle de 20 a 30 pour cent.

Or notre cible est le pire cas possible pour ce type de base : un installateur de thermopompes de 5 a 30 personnes a Levis, Sherbrooke ou Bulle, dont le dirigeant n a souvent aucun profil LinkedIn exploitable. Il n existe AUCUNE mesure publique du taux de succes de ces outils sur ce segment precis — je n en ai trouve aucune, et je ne vais pas en inventer une. C est precisement pourquoi la decision doit etre precedee d une mesure, pas d un abonnement.

Droit. C est ici que l arbitrage bascule, et ce n est pas un argument de confort. Le consentement tacite CASL repose sur l article 10(9)(b) : la coordonnee doit etre CONSPICUOUSLY PUBLISHED, sans mention de refus de sollicitation, et le message doit etre pertinent pour la fonction de la personne. La charge de la preuve pese sur l expediteur. Les sanctions vont jusqu a 10 millions CAD par violation, avec responsabilite personnelle des dirigeants.

Une adresse extraite du site officiel FOURNIT SA PROPRE PREUVE : URL, date, extrait. Une adresse achetee a un enrichisseur ne prouve rien de tel — elle prouve qu un tiers la detenait, ce qui n est pas le meme fait juridique. Cote europeen, la collecte indirecte declenche l obligation d information renforcee de l art. 14 RGPD et ajoute un second responsable de traitement dans la chaine. Et l affaire KASPR — 240 000 EUR le 5 decembre 2024, pour aspiration de coordonnees LinkedIn a visibilite restreinte, duree de conservation disproportionnee, defaut d information et non-reponse aux droits d acces — montre exactement ou l autorite place la limite pour les bases de contacts agregees.

Il faut ajouter un point que le projet gagnerait a exploiter : une adresse generique de type contact@entreprise.ca n identifie pas une personne physique et sort largement du champ des donnees personnelles. Un email nominatif achete y entre pleinement. Preferer l adresse generique extraite du site n est donc pas un pis-aller — c est un cran entier de regime juridique en moins, parfaitement coherent avec la minimisation a 6 champs deja revendiquee par l objet Contact.

=== 3. CE QU IL FAUT CONSTRUIRE (ordre impose) ===

ETAGE 1 — Collecteur d extraction depuis le site officiel. Cout marginal ZERO : website.py fetch deja le site via api_io et en extrait meta, logo, formulaire, liens sociaux. On ajoute l extraction des adresses publiees (mailto:, page /contact, /a-propos, mentions legales, JSON-LD Organization). Nouveau module diagnostic/contact_site.py heritant de Collector, echec isole via safe_collect, fetch OBLIGATOIREMENT via api_io.call('http','get',...), et module A AJOUTER a la liste de _check_garde_fous_bus dans diagnostic/preflight.py conformement a la regle inscrite dans CLAUDE.md. Renseigner contact_email_source = 'site_officiel:<url>' — le champ existe deja et donne gratuitement la piste d audit. Detecter une mention de refus de prospection sur la page et la traduire en opt_out: true.

ETAGE 2 — Registres publics, gratuits, pour le NOM du dirigeant. REQ Quebec en import local de donnees ouvertes (mise a jour bimensuelle, donc pas un appel reseau par prospect : excellent cote GreenIT et cote budget), puis Zefix REST pour la Suisse et API Sirene INSEE pour la France, au rythme de la sequence geographique. Ces registres couvrent 100 pour cent des entreprises immatriculees — exhaustivite qu aucune base commerciale n atteindra jamais sur ce segment. Ils resolvent gratuitement la moitie du probleme que l on s appretait a payer.

Le couple etage 1 + etage 2 produit (nom du proprietaire issu du registre, adresse joignable issue du site) — c est-a-dire exactement ce qu on allait acheter, a cout marginal nul, avec une meilleure piste d audit.

ETAGE 3 — Enrichisseur en RECOURS uniquement, sur les fiches residuelles. Ordre de preference : Dropcontact d abord (recomposition algorithmique sans base, editeur francais, audit CNIL, indifferent a la notoriete de la cible — le seul dont la couverture ne s effondre pas sur une TPE francophone, et le seul dont la posture juridique est alignee sur trois marches dont deux europeens). Anymailfinder ensuite si le palier a 14 USD/mois pour 50 emails verifies est confirme, pour son modele au resultat qui transfere le risque de couverture au fournisseur. Hunter en troisieme, pour son moteur fonde sur le domaine et son palier gratuit de 50 credits.

APOLLO — verdict sur le statu quo : ne pas souscrire avant d avoir tranche la question de l acces API. Plusieurs sources tierces affirment que la cle API maitre est reservee au plan Organization a 119 USD/utilisateur/mois. Le systeme appelle api.apollo.io/v1/people/search en direct : si c est exact, le statu quo coute environ 1 428 USD/an et devient l une des options les plus cheres du panel pour l une des couvertures les plus faibles sur la cible. Le code reste en place — PersonEnrichment est proprement isole derriere api_io.call, le remplacer coute une trentaine de lignes.

=== 4. LE TEST QUI DOIT PRECEDER TOUTE DEPENSE ===

Aucune de ces decisions ne doit etre prise sur des chiffres d agregateurs, y compris les miens. Protocole, cout zero :
1. Constituer un echantillon de 50 domaines HVAC quebecois reels (le pipeline de decouverte sait deja les produire en --dry-run).
2. Mesurer le taux d extraction du socle interne : combien de ces 50 sites publient une adresse exploitable ? Cette mesure n existe nulle part dans la litterature — je n ai trouve aucune etude chiffrant la part des sites de TPE publiant une adresse email, et je refuse d en inventer une. Elle se mesure en une apres-midi.
3. En parallele, passer les memes 50 domaines dans les paliers GRATUITS : Prospeo 75 credits, Hunter 50 credits, Apollo free. Mesurer le taux de decouverte d un decideur nomme avec email verifie.
4. Comparer.

REGLE DE DECISION, posee a l avance pour ne pas etre rationalisee apres coup :
- Si le socle interne couvre plus de 60 pour cent des cibles : AUCUN abonnement. Recours au coup par coup, modele pay-per-verified uniquement.
- Entre 40 et 60 pour cent : socle + Dropcontact au palier le plus bas ouvrant l API, en recours sur le residuel.
- Sous 40 pour cent : reexaminer, mais examiner d abord POURQUOI — un taux d extraction faible sur des entreprises a domaine propre signalerait plus probablement un defaut du collecteur qu une absence reelle d adresse publiee.

Et symetriquement : si le taux de succes des enrichisseurs gratuits sur ces 50 domaines est inferieur a 40 pour cent, aucun abonnement paye n est justifiable, quel que soit son prix — on paierait un plancher mensuel pour un outil qui echoue plus d une fois sur deux sur la seule cible qui compte.

=== 5. CONSEQUENCE DIRECTE POUR knowledge/api_pricing.yaml ===

Ne rien y saisir aujourd hui a partir de cette etude. Aucun chiffre de ce rapport n a pu etre verifie sur une page officielle : le proxy de cet environnement a refuse toutes les connexions sortantes vers les sites des editeurs (HTTP 403 sur apollo.io, hunter.io, dropcontact.com, prospeo.io, findymail.com, peopledatalabs.com — trace dans recentRelayFailures du proxy). Saisir ces valeurs et renseigner releve_le reviendrait a transformer des chiffres de blogs comparatifs en verite budgetaire, et le preflight afficherait GO sur une base fausse — exactement le risque que le NO-GO structurel actuel protege.

Quand les tarifs auront ete releves sur les pages officielles, deux precautions de modelisation :
(a) Pour un fournisseur a abonnement, le prix_par_unite honnete n est PAS le prix nominal du credit mais le cout du plancher divise par les unites reellement consommees. Sinon le grand livre api_usage.log et l ecran GreenIT sous-estimeront le cout reel d un facteur 10 a 20 a ce volume. Cela merite un commentaire explicite dans le YAML, et probablement une entree de cout fixe mensuel distincte du cout a l unite.
(b) budgets.apollo.unites_max.credits doit etre cale sur max_enrichissements (25 par run) et non sur la dotation du plan — le garde-fou budgetaire doit refleter l intention d usage, pas la generosite du vendeur.

En resume : le systeme n a pas un probleme d enrichisseur, il a un probleme de SOURCE. La bonne source pour un installateur HVAC de 8 personnes a Levis, c est son propre site et le registre des entreprises du Quebec — pas une base agregee a San Francisco. L enrichisseur reste utile, mais comme filet, paye au resultat, sur le residuel. Construire le socle avant de signer quoi que ce soit.


### Comparatif des fournisseurs

| Verdict | Fournisseur | Modèle tarifaire | Prix constaté (statut de vérification) | Couverture QC/CH/FR |
|---|---|---|---|---|
| **recommande** | SOCLE INTERNE — Collecteur d extraction depuis le site officiel (conta | Aucun cout marginal par contact. Cout = developpement initial (un coll | 0,00 USD par contact (cout marginal reseau quasi nul, deja journalise par le fournisseur 'http' du bus). VERIFIE PAR LECTURE DU CODE : diagnostic/website.py effectue deja | Excellente et SYMETRIQUE sur les trois marches, parce qu elle ne depend d aucune base agregee : elle depend un |
| **recommande** | SOCLE INTERNE — Registres publics d entreprises (REQ Quebec, Zefix Sui | Donnees ouvertes gratuites (REQ, Zefix, Sirene). Pappers = freemium co | REQ Quebec : gratuit, telechargement de donnees ouvertes, mise a jour deux fois par mois (rapporte par Donnees Quebec — NON VERIFIE sur la page officielle). Zefix : regis | Couverture EXHAUSTIVE et officielle sur les trois marches — c est structurellement l inverse des bases america |
| **a_considerer** | Apollo.io (integration actuelle du systeme) | Abonnement par siege et par mois, avec une dotation de credits ; credi | RAPPORTE PAR DES TIERS (PhantomBuster, Warmly, Salesmotion, Hacking Demand — releve le 2026-08-02), NON VERIFIE sur la page officielle : Basic 49 USD/utilisateur/mois en  | C est le point faible decisif, et il faut le dire franchement. Les sources concordent : la couverture d Apollo |
| **a_considerer** | Hunter.io | Abonnement mensuel par volume de credits (pas par siege). 1 credit par | RAPPORTE PAR DES TIERS (rb2b, growthhacksuite, costbench, MarketBetter — releve le 2026-08-02), NON VERIFIE : Free 50 credits/mois ; Starter 49 USD/mois mensuel ou 34 USD | Meilleure que la moyenne des bases americaines sur l Europe francophone, parce que le moteur d Hunter part du  |
| **recommande** | Dropcontact | Abonnement mensuel par quota de credits, sans engagement, remise annue | RAPPORTE PAR DES TIERS, INCOHERENT ENTRE SOURCES — a traiter comme une fourchette et non comme un prix. Relevé le 2026-08-02 : Starter a partir de 24 EUR/mois pour 500 cr | La meilleure du panel sur la France, et significativement meilleure que les bases americaines sur la Suisse ro |
| **ecarte** | Lusha | Abonnement par siege et par utilisateur avec curseur de volume de cred | RAPPORTE PAR DES TIERS (UpLead, Cleanlist, Salesmotion, enrich.so, Amplemarket — releve le 2026-08-02), NON VERIFIE : Free 0 USD avec 40 credits/mois et 1 siege (une sour | Base agregee a dominante americaine et israelienne, orientee vers les personas commerciaux et technologiques.  |
| **ecarte** | Cognism | Devis annuel uniquement : frais de plateforme annuels + licences par u | RAPPORTE PAR DES TIERS et presente par eux comme des ESTIMATIONS (Landbase, Warmly, Amplemarket, derrick-app, Salesmotion — releve le 2026-08-02), NON VERIFIE et par natu | Paradoxe assume : c est probablement la MEILLEURE couverture europeenne du panel. Cognism revendique 180 pour  |
| **ecarte** | Kaspr (filiale de Cognism) | Abonnement mensuel par paliers, dotation separee en credits telephone  | RAPPORTE PAR DES TIERS (G2, derrick-app, leadhaste, xpay, prospeo — releve le 2026-08-02), NON VERIFIE : Free avec 15 credits email B2B, 5 credits telephone et 5 credits  | Base de contacts constituee a partir de LinkedIn et d autres sources, environ 160 millions de contacts selon l |
| **ecarte** | People Data Labs (PDL) | API a credits, abonnement mensuel ou contrat annuel volumique. 1 credi | RAPPORTE PAR DES TIERS (FullEnrich, prospeo, nubela, enrichlayer, syncgtm — releve le 2026-08-02), NON VERIFIE : Free a 0 USD/mois avec 100 recherches personne ou entrepr | Base d agregation americaine a tres large volume, orientee vers les cas d usage de data science et de resoluti |
| **ecarte** | Clearbit / HubSpot Breeze Intelligence | Module de credits adosse a un abonnement HubSpot. Plus de vente autono | RAPPORTE PAR DES TIERS (Landbase, derrick-app, Cleanlist, MarketBetter, getstealery — releve le 2026-08-02), NON VERIFIE : Breeze Intelligence a partir de 45 USD/mois en  | Historiquement forte sur les entreprises technologiques americaines, ce qui etait la marque de fabrique de Cle |
| **a_considerer** | Findymail | Abonnement mensuel par volume de credits, AVEC facturation uniquement  | RAPPORTE PAR DES TIERS (Capterra, derrick-app, syncgtm, usereviews, prospeo — releve le 2026-08-02), NON VERIFIE : Basic 49 USD/mois pour 1 000 credits ; Starter 99 USD/m | Aucune donnee de couverture specifique au Quebec, a la Suisse romande ou aux TPE artisanales francaises n a et |
| **ecarte** | Snov.io | Abonnement mensuel par volume de credits, avec remises a 3 mois et a 1 | RAPPORTE PAR DES TIERS (bookyourdata, Capterra, G2, UpLead, saleshandy, derrick-app — releve le 2026-08-02), NON VERIFIE : Trial gratuit avec 50 credits et 100 destinatai | Aucune donnee de couverture specifique aux trois marches vises. Editeur d origine ukrainienne, positionnement  |
| **a_considerer** | Anymailfinder | Abonnement mensuel avec facturation STRICTEMENT sur email verifie livr | RAPPORTE PAR DES TIERS ET INCOHERENT ENTRE SOURCES — a traiter comme une fourchette. Releve le 2026-08-02 (Capterra, UpLead, syncgtm, mentionagent, puzzleinbox), NON VERI | Aucune donnee de couverture specifique au Quebec, a la Suisse romande ou aux TPE francaises. Presomption de fa |
| **a_considerer** | Prospeo | Abonnement mensuel par volume de credits, tarif plat sans remise annue | RAPPORTE PAR DES TIERS (coldiq, satellyte, derrick-app, syncgtm — releve le 2026-08-02), NON VERIFIE : Free permanent avec 75 credits email par mois plus 100 credits d ex | Le produit est positionne autour de l identification d emails depuis LinkedIn, ce qui est le mauvais angle pou |
| **a_considerer** | FullEnrich (waterfall multi-fournisseurs, editeur francais) | Abonnement mensuel par credits, avec facturation UNIQUEMENT sur donnee | RAPPORTE PAR DES TIERS ET INCOHERENT ENTRE SOURCES. Releve le 2026-08-02 (coldiq, ZoomInfo pipeline, derrick-app, syncgtm, reviewnexa), NON VERIFIE : une source annonce u | C est l argument central du produit et il est structurellement pertinent ici : le waterfall interroge en casca |

### Détail par fournisseur


#### SOCLE INTERNE — Collecteur d extraction depuis le site officiel (contact@, page /contact, /a-propos, mentions legales, JSON-LD) — *recommande*

- **URL tarifs** : sans objet (developpement interne)
- **Prix constaté** : 0,00 USD par contact (cout marginal reseau quasi nul, deja journalise par le fournisseur 'http' du bus). VERIFIE PAR LECTURE DU CODE : diagnostic/website.py effectue deja un fetch HTTP du site via api_io et en extrait meta description, logo, formulaire de contact, liens sociaux — l infrastructure de fetch et de cache existe deja, il n y a rien a payer en plus.
- **Coût unitaire** : 0,00 USD par contact extrait. Le seul cout est le temps de developpement (estimation : un collecteur d environ 150 a 250 lignes, du meme ordre que seo.py ou social.py) et le temps humain de verification des cas ambigus.
- **Palier gratuit** : Sans objet — gratuit par construction.
- **Couverture** : Excellente et SYMETRIQUE sur les trois marches, parce qu elle ne depend d aucune base agregee : elle depend uniquement du site de l entreprise ciblee. Or l ICP persona1-quebec exige deja 'exiger_domaine_propre: true' et exclut pagesjaunes.ca, facebook.com, linkedin.com — donc TOUTE candidate qui entre dans le pipeline possede par construction un site propre. C est le seul mode de collecte dont la couverture ne s effondre pas entre un editeur SaaS de San Francisco et un chauffagiste de Levis ou de Vevey.
- **Pertinence** : Maximale. Le systeme fetch DEJA le site (website.py, palier 0) : extraire au passage les adresses de contact publiees ne coute pas une requete de plus dans la majorite des cas. Le collecteur respecte le contrat existant (heriter de Collector, exposer .name et .collect(company), echouer isolement via safe_collect). Limite honnete : renvoie majoritairement une adresse GENERIQUE (info@, contact@, administration@) et non l email nominatif du dirigeant. Pour ce persona, c est souvent suffisant : dans une entreprise HVAC de 5 a 30 personnes, l adresse generique est lue par le proprietaire ou son adjointe.
- **Conformité** : C est le regime le plus favorable des quinze options etudiees, pour trois raisons distinctes. (1) CASL : l article 10(9)(b) fait reposer le consentement tacite sur une coordonnee CONSPICUOUSLY PUBLISHED, sans mention de refus de sollicitation, et un message pertinent pour la fonction. Une adresse extraite du site officiel fournit sa propre preuve — URL, date, extrait — ce qu aucun enrichisseur ne fournit. (2) RGPD : une adresse generique de type contact@entreprise.ca n identifie pas une personne physique et sort largement du champ des donnees personnelles ; on descend d un cran entier de regime juridique par rapport a un email nominatif achete. (3) Art. 14 RGPD : la collecte indirecte via un tiers declenche une obligation d information renforcee et ajoute un second responsable de traitement dans la chaine ; la collecte directe a la source ne l ajoute pas. A implementer : respect de robots.txt, User-Agent honnete (deja la convention du projet), et detection d une mention de refus de prospection sur la page (qui doit produire opt_out: true).
- **Intégration** : FAIBLE et parfaitement aligne sur l architecture existante. Un nouveau module diagnostic/contact_site.py heritant de Collector ; aucun nouveau fournisseur a declarer dans api_pricing.yaml (reutilise le fournisseur 'http' deja present). ATTENTION A DEUX INVARIANTS : (a) tout fetch doit passer par api_io.call('http','get',...) — pas d import requests au niveau module ; (b) le module doit etre ajoute a la liste de _check_garde_fous_bus dans diagnostic/preflight.py, conformement a la regle 'tout nouveau module de ce type doit etre ajoute a cette liste' inscrite dans CLAUDE.md. Le mapping vers l objet Contact existant est direct : nom_personne (souvent absent), titre, email, email_source='site_officiel:<url>' — le champ email_source est deja prevu pour cela et donne gratuitement la piste d audit RGPD.
- **Justification** : C est le socle, pas l appoint. Cout marginal nul, couverture insensible a la faiblesse des bases sur les TPE francophones, et surtout la seule methode qui produit elle-meme sa preuve de publication conspicue — l element exact sur lequel repose le consentement tacite CASL. A construire AVANT de payer quoi que ce soit.

#### SOCLE INTERNE — Registres publics d entreprises (REQ Quebec, Zefix Suisse, API Sirene INSEE France) — *recommande*

- **URL tarifs** : https://www.donneesquebec.ca/recherche/fr/dataset/registre-des-entreprises (REQ, non consultee directement) ; https://www.zefix.admin.ch/ZefixPublicREST/ (API REST Zefix, non consultee directement) ; https://www.insee.fr/fr/information/3591226 (base Sirene, non consultee directement) ; https://www.pappers.fr/api (Pappers, alternative commerciale)
- **Prix constaté** : REQ Quebec : gratuit, telechargement de donnees ouvertes, mise a jour deux fois par mois (rapporte par Donnees Quebec — NON VERIFIE sur la page officielle). Zefix : registre du commerce public et consultable gratuitement, accessible par application web, API REST et application mobile ; une partie des donnees est publiee sur opendata.swiss avec mise a jour quotidienne (rapporte par des tiers — NON VERIFIE). API Sirene INSEE : gratuite, environ 25 millions d entreprises et 36 millions d etablissements, mise a jour quotidienne (rapporte par des tiers — NON VERIFIE). Pappers API : modele freemium, TARIFS NON TROUVES — les recherches n ont pas remonte de grille publique.
- **Coût unitaire** : 0,00 EUR / 0,00 CAD par entreprise. Cout reel = effort d integration et de rapprochement (matching entre le nom commercial trouve par le SERP et la denomination legale du registre), pas un cout par unite.
- **Palier gratuit** : Integralement gratuit pour REQ, Zefix et Sirene (donnees ouvertes publiques). Pappers : palier gratuit existant mais non chiffre.
- **Couverture** : Couverture EXHAUSTIVE et officielle sur les trois marches — c est structurellement l inverse des bases americaines : ces registres couvrent 100 pour cent des entreprises immatriculees, y compris l installateur de thermopompes de Trois-Rivieres que Apollo ou People Data Labs ne connaissent pas. Aucune base commerciale n atteindra jamais cette exhaustivite sur ce segment.
- **Pertinence** : Elevee mais PARTIELLE, et il faut etre precis sur ce qu ils donnent et ne donnent pas. Ils donnent : le NOM du ou des dirigeants, administrateurs ou actionnaires, la denomination legale, l adresse, la date d immatriculation, le code d activite. Ils ne donnent PAS d adresse email. Or pour ce systeme, la valeur du contact se decompose en deux : le NOM du decideur (pour personnaliser l accroche redigee par synthesis.py) et l EMAIL (pour joindre). Les registres reglent gratuitement la premiere moitie du probleme sur 100 pour cent des cibles. Combines a l adresse generique extraite du site, ils produisent le couple (nom du proprietaire, adresse joignable) — ce qui est exactement ce que l on cherchait a acheter.
- **Conformité** : Base legale solide : donnee publique legalement publiee, avec finalite de publicite legale. Attention nuancee : le nom d un dirigeant reste une donnee personnelle, et la reutilisation a des fins de prospection doit respecter la finalite et le droit d opposition (art. 21 RGPD, art. 6(1)(f) interet legitime). Le registre fournit une source citable et datee, ce qui satisfait l obligation d information sur l origine des donnees (art. 14 RGPD). Cote suisse, la nLPD accepte la meme logique. Cote Quebec, la Loi 25 n interdit pas la reutilisation d une donnee publique du REQ pour un contact professionnel. Ne JAMAIS croiser ces donnees pour reconstituer un profil au-dela du besoin : la minimisation a 6 champs deja en place dans l objet Contact protege le systeme de cette derive.
- **Intégration** : MOYEN, et c est le seul poste ou l effort est reel. Chaque registre a son format : REQ = fichiers de donnees ouvertes a telecharger et indexer localement (donc PAS un appel reseau par prospect — un import periodique, ce qui est excellent cote GreenIT et cote budget) ; Zefix = API REST publique appelable par entreprise ; Sirene = API INSEE avec inscription. Le point dur n est pas l acces mais le RAPPROCHEMENT : associer 'Climatisation Tremblay' trouve par le SERP a la bonne entite du registre, sans faux positif. Recommandation : commencer par le Quebec seul (REQ en import local, marche de la sequence en cours), et n ajouter Zefix puis Sirene qu au moment ou la sequence geographique y arrive. Un nouveau fournisseur 'registres' dans api_pricing.yaml a prix zero legitime, et un collecteur dedie ajoute a la liste _check_garde_fous_bus.
- **Justification** : Gratuit, exhaustif sur precisement le segment ou toutes les bases commerciales sont faibles, et il resout la moitie du probleme (le nom du dirigeant) que l on s appretait a payer 0,30 a 2,40 USD l unite. A traiter comme le second pilier du socle, apres l extraction site. Le seul cout est du developpement, pas de l abonnement.

#### Apollo.io (integration actuelle du systeme) — *a_considerer*

- **URL tarifs** : https://www.apollo.io/pricing — TENTATIVE DE CONSULTATION LE 2026-08-02, ECHEC : HTTP 403 (acces sortant bloque par la politique du proxy). Aucun chiffre officiel n a pu etre releve.
- **Prix constaté** : RAPPORTE PAR DES TIERS (PhantomBuster, Warmly, Salesmotion, Hacking Demand — releve le 2026-08-02), NON VERIFIE sur la page officielle : Basic 49 USD/utilisateur/mois en annuel, 59 USD en mensuel, avec 30 000 credits par an accordes d avance mais seulement 10 credits d EXPORT par mois ; Professional 79 USD/utilisateur/mois en annuel, 99 USD en mensuel, environ 48 000 credits ; Organization a partir de 119 USD/utilisateur/mois. Cout des credits rapporte : 1 credit par email professionnel trouve, 8 credits par mobile, 1 credit d export par enregistrement sorti vers un systeme externe. POINT CRITIQUE ET NON VERIFIE, mais decisif pour ce systeme : plusieurs sources tierces (galadon.com, datalane.com) affirment que l ACCES A LA CLE API MAITRE est reserve au plan Organization, les plans Free, Basic et Professional ne permettant que les integrations via marketplace (Zapier, Make, CRM natif) et non les appels API bruts. Le systeme appelle https://api.apollo.io/v1/people/search en direct : si cette affirmation est exacte, le statu quo coute au minimum 119 USD/utilisateur/mois, soit environ 1 428 USD/an, et non 49. A CONFIRMER EN PRIORITE ABSOLUE sur la documentation officielle avant tout engagement.
- **Coût unitaire** : Le prix par credit est trompeur ici ; ce qui compte est le prix par contact REELLEMENT utilise, car l abonnement est un plancher. Hypothese de volume EXPLICITE, tiree du code : l ICP persona1-quebec fixe max_enrichissements a 25 par run ; a une cadence realiste pour une consultante solo de 2 runs par mois, cela fait 50 enrichissements par mois, 600 par an. Sur cette base : Basic a 49 USD/mois = 588 USD/an = 0,98 USD par contact. Si l API exige Organization a 119 USD/mois = 1 428 USD/an = 2,38 USD par contact. Le prix nominal du credit (de l ordre de 0,001 a 0,02 USD) est economiquement sans objet a ce volume : on paie un abonnement dimensionne pour une equipe de vente, pour l usage d une personne seule.
- **Palier gratuit** : Rapporte par des tiers, NON VERIFIE : plan gratuit avec 100 credits par mois, porte a 10 000 credits par mois pour un compte avec domaine d entreprise valide et verifie. Le plan gratuit n ouvrirait PAS l acces API brute (voir ci-dessus).
- **Couverture** : C est le point faible decisif, et il faut le dire franchement. Les sources concordent : la couverture d Apollo est forte en Amerique du Nord sur les personas SaaS et mid-market, et se degrade nettement hors de ce perimetre. Des avis G2 rapportes signalent en Europe des intitules de poste perimes et des numeros invalides. Cognism revendique 250 pour cent de contacts en plus qu Apollo en France et en Allemagne (source interessee, a lire comme telle). Pour NOTRE cible precise — un installateur de thermopompes de 5 a 30 personnes a Levis, Sherbrooke ou dans le canton de Vaud — la probabilite qu Apollo detienne un decideur nomme avec email verifie est faible et n a jamais ete mesuree. C est exactement le profil d entreprise que ces bases, construites par agregation autour de l ecosysteme LinkedIn et SaaS, couvrent mal. Le Quebec francophone artisanal est le pire cas possible pour ce type de base.
- **Pertinence** : Le code diagnostic/enrichment.py est deja ecrit contre Apollo, avec cache par domaine, plafond max_enrichissements et extraction stricte des 6 champs. Techniquement, cela fonctionne. Economiquement, c est un mauvais ajustement : on paie un siege pense pour une equipe SDR pour un usage de 25 a 50 lookups par mois, sur un segment ou la base est faible. La question n est pas la qualite d Apollo dans l absolu, c est son adequation a CE persona et a CE volume.
- **Conformité** : Base americaine constituee par agregation de sources multiples. Points a verifier avant tout usage reel sur des personnes de l UE ou de Suisse : localisation des donnees (Etats-Unis, donc transfert hors UE a encadrer), existence et signature d un DPA, mecanisme d opposition et de suppression accessible aux personnes concernees, et surtout information au titre de l art. 14 RGPD lorsque la donnee ne vient pas de la personne. Le champ email_source deja implemente (valeurs Apollo de type 'verified', 'guessed', 'likely') est un bon debut de piste d audit — mais un statut 'guessed' signifie une adresse DEDUITE par algorithme, ce qui est fragile a la fois juridiquement et en delivrabilite : a exclure des exports. Aucun taux de delivrabilite officiel n a pu etre releve (page inaccessible).
- **Intégration** : NUL — c est deja integre et teste. C est le seul avantage restant du statu quo. Le retirer coute egalement peu : PersonEnrichment est isole derriere api_io.call('apollo','people_enrichment',...), et le remplacer revient a reecrire une methode privee d une trentaine de lignes.
- **Justification** : A conserver comme integration existante, mais NE PAS SOUSCRIRE avant deux verifications qui peuvent l ecarter d un coup : (1) l acces API brute exige-t-il vraiment le plan Organization a 119 USD/utilisateur/mois ? (2) quel est le taux de succes REEL sur 50 domaines HVAC quebecois ? Le plan gratuit permet de repondre a la question (2) sans depenser un dollar, si tant est qu il ouvre l API. Tant que ces deux reponses manquent, tout chiffre saisi dans api_pricing.yaml serait une decision prise a l aveugle.

#### Hunter.io — *a_considerer*

- **URL tarifs** : https://hunter.io/pricing — TENTATIVE DE CONSULTATION LE 2026-08-02, ECHEC : HTTP 403 (acces sortant bloque). Aucun chiffre officiel releve.
- **Prix constaté** : RAPPORTE PAR DES TIERS (rb2b, growthhacksuite, costbench, MarketBetter — releve le 2026-08-02), NON VERIFIE : Free 50 credits/mois ; Starter 49 USD/mois mensuel ou 34 USD/mois en annuel, 2 000 credits/mois ; Growth 149 USD/mois ou 104 USD en annuel, 10 000 credits/mois ; Scale 299 USD/mois ou 209 USD en annuel, 25 000 credits/mois ; Enterprise sur devis. Remise annuelle rapportee : 30 pour cent.
- **Coût unitaire** : A 50 enrichissements par mois : le palier GRATUIT couvre le besoin, soit 0,00 USD par contact. Si le volume double : Starter a 34 USD/mois en annuel = 408 USD/an = 0,68 USD par contact a 50/mois, 0,34 USD a 100/mois. Prix nominal du credit sur Starter : environ 0,017 USD, mais ce nominal n a de sens qu a partir de 2 000 credits consommes par mois — soit 40 fois le besoin.
- **Palier gratuit** : 50 credits par mois, gratuits et permanents (rapporte par des tiers, NON VERIFIE). C est un point important : 50 credits par mois correspondent presque exactement au volume mensuel d enrichissement de ce systeme selon l hypothese de cadence retenue.
- **Couverture** : Meilleure que la moyenne des bases americaines sur l Europe francophone, parce que le moteur d Hunter part du DOMAINE et pas d un profil de personne : il indexe les adresses publiquement visibles associees a un nom de domaine et infere les motifs d adressage. Ce mode de fonctionnement est structurellement plus robuste sur une TPE locale qu une base construite autour de LinkedIn — un chauffagiste vaudois n a pas de profil LinkedIn, mais son domaine existe et publie des adresses. Reserve honnete : aucun chiffre de couverture specifique au Quebec ou a la Suisse romande n a ete trouve ; c est une inference sur le mode de fonctionnement, pas une mesure.
- **Pertinence** : Bonne, et conceptuellement proche du socle interne recommande — ce qui est a la fois son merite et sa limite : Hunter fait, en service paye, une version industrialisee de ce que le collecteur d extraction ferait gratuitement, avec en plus la verification SMTP et l inference de motif d adressage (prenom.nom@). C est precisement le bon RECOURS : quand le site ne publie qu un formulaire sans adresse, Hunter peut deduire l adresse nominative du dirigeant dont le registre a donne le nom. Le couple 'registre pour le nom + Hunter pour le motif d adressage' est economiquement tres efficace.
- **Conformité** : Position juridique documentee et plutot serieuse : societe enregistree a Wilmington (Delaware) mais operee depuis la France ; DPA disponible pour les clients payants a partir du plan Starter ; Hunter declare avoir realise une evaluation d interet legitime (LIA) et une analyse d impact (DPIA) ; page de reclamation permettant a une personne de demander la suppression de ses donnees. Reserves : le DPA n est rapporte comme accessible qu a partir du plan payant — donc utiliser le palier gratuit en production sur des donnees de personnes UE laisse un trou contractuel ; et la localisation exacte des donnees n a pas pu etre verifiee (page sous-traitants inaccessible). L obligation d information art. 14 RGPD reste a la charge de l utilisatrice.
- **Intégration** : FAIBLE. Nouveau fournisseur 'hunter' dans api_pricing.yaml, unite 'credit', endpoints 'domain_search' et 'email_finder'. Une methode privee dans un module d enrichissement, sur le modele exact de _apollo_people_search : import requests en lazy, appel via api_io.call avec cache_key par domaine, mapping vers les 6 champs de Contact avec email_source renseigne depuis le score de confiance renvoye. Environ une demi-journee.
- **Justification** : Le meilleur candidat de recours parmi les enrichisseurs anglo-saxons pour ce cas d usage : facturation au volume et non au siege, palier gratuit de 50 credits/mois qui couvre le volume reel du systeme, moteur fonde sur le domaine plutot que sur LinkedIn (donc moins penalise sur les TPE francophones), et posture RGPD documentee. A tester en palier gratuit dans le meme lot de mesure qu Apollo avant tout paiement.

#### Dropcontact — *recommande*

- **URL tarifs** : https://www.dropcontact.com/pricing — TENTATIVE DE CONSULTATION LE 2026-08-02, ECHEC : HTTP 403 (acces sortant bloque). Aucun chiffre officiel releve.
- **Prix constaté** : RAPPORTE PAR DES TIERS, INCOHERENT ENTRE SOURCES — a traiter comme une fourchette et non comme un prix. Relevé le 2026-08-02 : Starter a partir de 24 EUR/mois pour 500 credits selon une source, pour 1 000 credits selon une autre ; Premium 69 EUR/mois pour 2 000 credits ; Growth 49 EUR/mois ; Business environ 79 EUR/mois pour 5 000 credits ; Enterprise sur devis a partir de 200 000 credits/mois. Remise annuelle rapportee d environ 20 pour cent. POINT A VERIFIER IMPERATIVEMENT : une source (derrick-app) affirme que l ACCES API est reserve au palier Business, autour de 74 a 79 EUR/mois. Comme ce systeme n utilise que l API et jamais l interface, cette contrainte, si elle est exacte, fixe le prix d entree reel a environ 79 EUR/mois et non 24. La divergence entre sources sur le nombre de credits du plan Starter (500 contre 1 000) montre a elle seule qu aucun de ces chiffres n est utilisable sans verification directe.
- **Coût unitaire** : A 50 enrichissements par mois, avec l hypothese haute (API gatee au Business a 79 EUR/mois) : 948 EUR/an = 1,58 EUR par contact. Avec l hypothese basse (Starter a 24 EUR/mois utilisable en API) : 288 EUR/an = 0,48 EUR par contact. Prix nominal du credit sur Business : environ 0,016 EUR — de nouveau sans portee pratique, puisque l on consommerait 50 credits sur 5 000.
- **Palier gratuit** : Aucun palier gratuit permanent trouve dans les resultats. Un essai est probable mais NON VERIFIE — a confirmer sur la page officielle.
- **Couverture** : La meilleure du panel sur la France, et significativement meilleure que les bases americaines sur la Suisse romande et le Quebec francophone — parce que l approche est algorithmique et non documentaire : Dropcontact ne cherche pas la fiche d une personne dans un stock, il recompose et teste l adresse a partir du nom et du domaine. Cette methode est indifferente a la notoriete de l entreprise : elle marche aussi bien pour un chauffagiste de Bulle que pour un editeur parisien. C est structurellement la bonne reponse au probleme du 'trou de couverture sur les TPE locales'. Reserve : elle exige de connaitre le NOM de la personne en entree — d ou la complementarite forte avec les registres publics (REQ, Zefix, Sirene) qui fournissent ce nom gratuitement.
- **Pertinence** : Tres bonne, mais avec un changement de posture a assumer : Dropcontact n est pas un moteur de decouverte de personnes, c est un verificateur et recomposeur. Le flux devient : registre ou site officiel donne le nom du dirigeant, puis Dropcontact recompose et verifie l adresse. Cela s articule parfaitement avec le socle recommande, et cela renforce la minimisation : on ne recoit pas un profil complet a filtrer, on recoit l adresse d une personne que l on avait deja identifiee par une source publique. C est plus propre que le modele Apollo, ou l on recoit une fiche riche dont on jette 90 pour cent des champs grace a extra='forbid'.
- **Conformité** : C est le point fort, et il est structurel. Dropcontact declare ne detenir AUCUNE base de donnees de contacts — ni achetee, ni construite a partir des donnees clients — et recomposer chaque adresse algorithmiquement en temps reel. Cela supprime a la racine plusieurs difficultes : pas de stock de donnees personnelles constitue a l insu des personnes, donc pas de probleme d art. 14 sur une collecte indirecte massive, pas de duree de conservation excessive (le grief exact retenu contre Kaspr), pas de transfert hors UE si l hebergement est europeen. La societe est francaise et a fait l objet d un audit de la CNIL — a noter que 'audite par la CNIL' n est PAS une certification ni un label, et ne vaut pas quitus : c est un element de serieux, pas un blanc-seing. Le positionnement RGPD-by-design reste, de loin, le meilleur du panel. Point non verifie : la localisation precise de l hebergement (la mention OVH/France n a pas pu etre confirmee).
- **Intégration** : FAIBLE a MOYEN. Nouveau fournisseur 'dropcontact' dans api_pricing.yaml, unite 'credit'. Particularite : l API Dropcontact est ASYNCHRONE sur les lots (on soumet, on interroge un identifiant de traitement). Cela demande une petite boucle d attente dans la methode privee, ce que le bus api_io absorbe sans probleme puisqu il enveloppe un simple callable — mais il faut prevoir un timeout franc pour ne pas bloquer le pipeline, et le mode degrade habituel (retourner None plutot que lever). Compter une journee plutot qu une demi-journee.
- **Justification** : Recommande comme UNIQUE enrichisseur paye du systeme, en RECOURS derriere le socle interne. C est le seul du panel dont le modele technique (recomposition sans base) et le modele juridique (RGPD-by-design, societe et audit francais) sont alignes avec les contraintes dures de ce projet — trois marches dont deux europeens, opt_out absolu, minimisation a 6 champs. Il est aussi le seul dont la couverture ne s effondre pas sur une TPE francophone, parce qu il ne depend pas d un stock. Condition prealable : verifier si l API exige le palier Business, ce qui triplerait le prix d entree.

#### Lusha — *ecarte*

- **URL tarifs** : https://www.lusha.com/pricing (URL officielle probable — NON CONSULTEE, acces sortant bloque)
- **Prix constaté** : RAPPORTE PAR DES TIERS (UpLead, Cleanlist, Salesmotion, enrich.so, Amplemarket — releve le 2026-08-02), NON VERIFIE : Free 0 USD avec 40 credits/mois et 1 siege (une source cite 70 credits — divergence non tranchee) ; Starter 37,45 USD/utilisateur/mois en annuel pour 4 800 credits par AN et 1 siege ; Pro de 52,45 a 174,95 USD/utilisateur/mois en annuel pour 7 200 a 24 000 credits par an et 2 sieges ; Premium de 299,95 a 659,95 USD/mois en annuel pour 40 800 a 98 400 credits par an et 5 sieges ; Scale sur devis. Cout en credits rapporte : 1 credit par email verifie revele, 5 credits par numero de telephone.
- **Coût unitaire** : Starter a 37,45 USD/mois = 449 USD/an pour 4 800 credits annuels, soit 400 credits par mois. A 50 enrichissements par mois : 0,75 USD par contact utile, avec 87 pour cent de la dotation perdue. Prix nominal du credit : environ 0,094 USD.
- **Palier gratuit** : 40 credits par mois selon la source principale, 70 selon une autre — DIVERGENCE NON TRANCHEE, NON VERIFIE.
- **Couverture** : Base agregee a dominante americaine et israelienne, orientee vers les personas commerciaux et technologiques. Aucune donnee de couverture specifique au Quebec, a la Suisse romande ou aux TPE artisanales francaises n a ete trouvee. L orientation produit — le telephone direct compte 5 fois plus cher que l email — revele la cible reelle : des equipes de vente sortante qui appellent des cadres d entreprises structurees. Ce n est pas notre cible.
- **Pertinence** : Faible. Le systeme ne collecte PAS de numeros de telephone et n en veut pas : l objet Contact a 6 champs n en comporte aucun, et en ajouter un casserait extra='forbid' et la minimisation revendiquee. Payer un produit dont la moitie de la valeur reside dans les numeros directs revient a financer une capacite que l architecture interdit deliberement d utiliser.
- **Conformité** : Base constituee par agregation, siege hors UE, avec une part de contribution communautaire (les utilisateurs alimentant la base) qui pose des questions de base legale pour les personnes dont les coordonnees sont ainsi versees. DPA et procedure d opposition a verifier. Pas d element positif specifique releve qui compenserait, pour ce projet, le desavantage face a une solution europeenne sans base.
- **Intégration** : MOYEN. Nouveau fournisseur, nouvelle methode privee, mapping vers Contact. Rien de bloquant techniquement — l effort n est pas le probleme, la pertinence l est.
- **Justification** : Ecarte pour trois raisons cumulatives : tarification par SIEGE avec dotation de credits annuelle largement surdimensionnee pour un usage solo (87 pour cent de gachis), valeur produit concentree sur le telephone direct que l architecture interdit deliberement de collecter, et aucune indication de couverture sur les TPE francophones ciblees. Rien ne le distingue positivement pour ce systeme.

#### Cognism — *ecarte*

- **URL tarifs** : https://www.cognism.com/pricing (URL officielle probable — NON CONSULTEE, acces sortant bloque ; Cognism ne publie de toute facon pas de grille publique)
- **Prix constaté** : RAPPORTE PAR DES TIERS et presente par eux comme des ESTIMATIONS (Landbase, Warmly, Amplemarket, derrick-app, Salesmotion — releve le 2026-08-02), NON VERIFIE et par nature invérifiable puisque l editeur ne publie pas ses prix : frais de plateforme estimes entre 15 000 et 25 000 USD/an, plus 1 500 a 2 500 USD par utilisateur et par an. Frais d integration estimes de 500 a 1 500 USD. Modules d intention (Bombora) de 75 a 400 USD par sujet. Augmentations au renouvellement rapportees de 10 a 15 pour cent. Exemple cite pour une equipe de 5 personnes : 22 500 a 37 500 USD/an avant options.
- **Coût unitaire** : Plancher estime a 16 500 USD/an (plateforme basse + une licence). A 600 enrichissements par an : environ 27,50 USD par contact. Avec l hypothese haute (27 500 USD/an) : environ 45,80 USD par contact. Rappel de contexte : la consultante est une micro-structure solo ; le seul frais de plateforme depasse tres probablement le budget annuel total de l ensemble de la chaine d outillage.
- **Palier gratuit** : Aucun. Pas d essai en libre-service au-dela d un echantillon limite de leads.
- **Couverture** : Paradoxe assume : c est probablement la MEILLEURE couverture europeenne du panel. Cognism revendique 180 pour cent de contacts en plus au Royaume-Uni et plus de 250 pour cent en France et en Allemagne par rapport aux concurrents (source : l editeur lui-meme, donc a lire comme un argument commercial et non comme une mesure independante). Il propose egalement un nettoyage des listes d opposition telephonique par marche. Sur le papier, c est l outil du marche europeen. Mais aucune de ces revendications ne porte specifiquement sur les TPE artisanales de 5 a 30 personnes, et rien n indique que la densite y soit meilleure qu ailleurs — l avantage europeen de Cognism se construit historiquement sur les entreprises structurees.
- **Pertinence** : Nulle a cette echelle. L outil est concu pour des equipes de vente sortante disposant d un budget d outillage annuel a cinq chiffres. L injecter derriere le bus api_io serait techniquement possible et economiquement absurde.
- **Conformité** : Posture de conformite serieuse et argumentee, avec nettoyage des listes d opposition. A noter cependant, et ce n est pas anodin : sa filiale Kaspr a ete sanctionnee de 240 000 EUR par la CNIL le 5 decembre 2024 pour aspiration de donnees LinkedIn (source : cnil.fr et edpb.europa.eu). Cela n implique pas mecaniquement un defaut chez Cognism, mais cela invite a examiner les pratiques de collecte du groupe plutot qu a se fier au discours de conformite.
- **Intégration** : Sans objet — la question ne se pose pas au prix constate.
- **Justification** : Ecarte sur le seul critere du prix : un plancher estime a 16 500 USD/an pour une consultante solo represente environ 27 a 46 USD par contact enrichi, soit deux ordres de grandeur au-dessus des alternatives. La qualite europeenne superieure est reelle mais sans rapport avec la structure de couts de ce projet. A ne reconsiderer que si le systeme passait un jour en multi-tenant avec plusieurs clients payants — c est-a-dire au palier 3, actuellement gele.

#### Kaspr (filiale de Cognism) — *ecarte*

- **URL tarifs** : https://www.kaspr.io/pricing (URL officielle probable — NON CONSULTEE, acces sortant bloque)
- **Prix constaté** : RAPPORTE PAR DES TIERS (G2, derrick-app, leadhaste, xpay, prospeo — releve le 2026-08-02), NON VERIFIE : Free avec 15 credits email B2B, 5 credits telephone et 5 credits email direct par mois ; Starter 45 EUR/mois en annuel ou 59 EUR/mois en mensuel, 100 credits telephone et 5 credits email direct ; Business 79 EUR/mois en annuel ou 99 EUR/mois en mensuel, 200 credits telephone et 200 credits email direct. Remise annuelle rapportee jusqu a 25 pour cent.
- **Coût unitaire** : Business a 79 EUR/mois = 948 EUR/an pour 200 emails directs par mois, soit environ 0,40 EUR par email direct a pleine consommation. A 50 enrichissements par mois : 1,58 EUR par contact utile. Sur Starter, avec 5 credits email direct par mois seulement, le systeme serait a court des le premier run — le plan est concu autour du telephone.
- **Palier gratuit** : 15 credits email B2B, 5 credits telephone, 5 credits email direct par mois (rapporte, NON VERIFIE).
- **Couverture** : Base de contacts constituee a partir de LinkedIn et d autres sources, environ 160 millions de contacts selon la CNIL. La couverture depend donc directement de la presence LinkedIn de la cible — ce qui est precisement le point de rupture pour un installateur HVAC quebecois ou un chauffagiste vaudois de 8 personnes, dont le dirigeant n a souvent aucun profil, ou un profil dormant sans coordonnees.
- **Pertinence** : Faible. Produit centre sur l extension navigateur et sur le telephone direct, avec une dotation email direct residuelle sur les paliers bas. L architecture de ce systeme est en appel API serveur-a-serveur, sans humain devant un navigateur — l usage principal de Kaspr n est pas accessible au pipeline.
- **Conformité** : REDHIBITOIRE POUR CE PROJET, et c est un fait etabli et non une opinion. La CNIL a inflige a KASPR une amende de 240 000 EUR le 5 decembre 2024 (sources : cnil.fr, edpb.europa.eu, next.ink), pour avoir collecte sur LinkedIn les coordonnees d utilisateurs qui avaient expressement limite leur visibilite a leurs relations de 1er et 2e degre. La CNIL a retenu que cette collecte excedait ce que les personnes pouvaient raisonnablement attendre, et a releve en outre une duree de conservation disproportionnee, un defaut de transparence et d information des personnes, et un manquement a l obligation de repondre aux demandes de droit d acces. Ce projet interdit explicitement tout scraping LinkedIn ou Facebook dans ses invariants d architecture : integrer un fournisseur sanctionne pour exactement cette pratique contredirait frontalement l invariant, et exposerait la consultante en tant que responsable de traitement en aval.
- **Intégration** : Sans objet.
- **Justification** : Ecarte pour non-conformite documentee. Sanction CNIL de 240 000 EUR du 5 decembre 2024 pour aspiration de donnees LinkedIn, incluant des coordonnees dont les personnes avaient restreint la visibilite — c est-a-dire la pratique exacte que les invariants de ce projet interdisent. Le produit est par ailleurs centre sur le telephone, que l architecture ne collecte pas. Aucun arbitrage a faire : c est une exclusion, pas un compromis.

#### People Data Labs (PDL) — *ecarte*

- **URL tarifs** : https://www.peopledatalabs.com/pricing — TENTATIVE DE CONSULTATION LE 2026-08-02, ECHEC : HTTP 403 (acces sortant bloque).
- **Prix constaté** : RAPPORTE PAR DES TIERS (FullEnrich, prospeo, nubela, enrichlayer, syncgtm — releve le 2026-08-02), NON VERIFIE : Free a 0 USD/mois avec 100 recherches personne ou entreprise par mois et 25 recherches IP, MAIS EXCLUANT les donnees de contact (emails et telephones) et les champs premium ; Pro a 98 USD/mois avec 350 credits d enrichissement personne et 1 000 recherches entreprise, soit environ 0,28 USD par credit en mensuel ; tarif degressif jusqu a environ 0,20 USD par credit sur contrat annuel volumique ; au-dela de 100 000 credits, bascule Enterprise avec une attente pratique de 20 000 a plus de 100 000 USD/an.
- **Coût unitaire** : Pro a 98 USD/mois = 1 176 USD/an pour 350 credits/mois. A 50 enrichissements par mois : 1,96 USD par contact utile, avec 86 pour cent de la dotation perdue. Le prix NOMINAL de 0,28 USD par credit est le plus transparent du panel, mais il n est atteint qu en consommant l integralite de la dotation — soit 7 fois le besoin.
- **Palier gratuit** : 100 recherches par mois, mais SANS les emails ni les telephones — donc strictement inutilisable pour le besoin de ce systeme. Le palier gratuit ne permet meme pas de mesurer le taux de succes sur l email, ce qui est le seul test qui nous interesse.
- **Couverture** : Base d agregation americaine a tres large volume, orientee vers les cas d usage de data science et de resolution d identite plutot que vers la prospection ciblee. La profondeur sur des TPE artisanales du Quebec ou de Suisse romande n est documentee nulle part et il n y a aucune raison de la supposer bonne : ce type de base tire sa densite de l empreinte numerique professionnelle des personnes, qui est faible chez un installateur de thermopompes de 8 salaries.
- **Pertinence** : Faible. PDL est un fournisseur de donnees en gros, pense pour alimenter un produit qui enrichit des millions d enregistrements. Ce systeme en enrichit 25 par run. Le decalage d echelle est de trois ordres de grandeur.
- **Conformité** : Base americaine constituee par agregation de sources multiples, avec un profil de risque parmi les plus eleves du panel du point de vue europeen : volume massif, sources multiples et pas toujours tracables par enregistrement, localisation aux Etats-Unis. L exercice concret de l information art. 14 RGPD et du droit d opposition sur une donnee issue d une telle agregation est difficile a documenter aupres d une autorite. Un DPA existe probablement mais n a pas pu etre verifie.
- **Intégration** : FAIBLE techniquement (API REST propre et bien documentee, mapping simple vers les 6 champs). L effort n est pas le sujet.
- **Justification** : Ecarte : palier gratuit inutilisable puisqu il exclut precisement les emails, plancher paye a 98 USD/mois pour un besoin de 50 unites (86 pour cent de gachis), echelle produit congue pour l enrichissement en masse, et profil de conformite le plus expose du panel sur des personnes europeennes. Le prix par credit affiche (0,28 USD) est honnete et lisible, mais sans rapport avec le cout reel a ce volume.

#### Clearbit / HubSpot Breeze Intelligence — *ecarte*

- **URL tarifs** : https://www.hubspot.com/products/breeze-intelligence (URL officielle probable — NON CONSULTEE, acces sortant bloque). L ancienne page clearbit.com/pricing n existe plus en tant que produit autonome.
- **Prix constaté** : RAPPORTE PAR DES TIERS (Landbase, derrick-app, Cleanlist, MarketBetter, getstealery — releve le 2026-08-02), NON VERIFIE : Breeze Intelligence a partir de 45 USD/mois en engagement annuel ou 50 USD/mois en mensuel pour 100 credits Breeze ; credits HubSpot additionnels a 10 USD pour 1 000 credits ; cout d entree REEL rapporte a 75 USD/mois minimum, soit 30 USD de HubSpot Starter plus 45 USD de credits Breeze — car le module n est pas vendu seul. Credits remis a zero chaque mois sans report.
- **Coût unitaire** : 75 USD/mois = 900 USD/an pour 100 credits/mois. A 50 enrichissements par mois : 1,50 USD par contact utile. Prix nominal du credit : 0,45 USD, l un des plus eleves du panel.
- **Palier gratuit** : Aucun. Tous les anciens outils gratuits Clearbit ont ete supprimes le 30 avril 2025 (rapporte par des tiers, NON VERIFIE).
- **Couverture** : Historiquement forte sur les entreprises technologiques americaines, ce qui etait la marque de fabrique de Clearbit — et faible partout ailleurs sur les petites structures. Aucune donnee sur le Quebec, la Suisse ou les TPE francaises. Clearbit n a jamais ete un outil de couverture des artisans locaux, y compris aux Etats-Unis.
- **Pertinence** : Nulle, pour une raison dirimante et independante du prix : l API Clearbit d origine, l extension Clearbit Connect et les points d entree d enrichissement autonomes sont en cours d extinction ou absorbes dans Breeze. Il n existe plus d acces autonome. Integrer Breeze derriere le bus api_io imposerait de souscrire a HubSpot et d y faire transiter les donnees — c est-a-dire d introduire un CRM entier dans une architecture dont la source de verite est deliberement un vault Obsidian local, avec porte humaine. C est une contradiction d architecture, pas un arbitrage de cout.
- **Conformité** : Base americaine agregee, desormais operee par HubSpot avec le DPA HubSpot. Le cadre contractuel est plutot mieux etabli que la moyenne (HubSpot est un acteur habitue aux exigences europeennes), mais cela ne change rien au fond : donnee constituee par agregation, hors UE, et l adoption imposerait un second responsable de traitement majeur dans la chaine.
- **Intégration** : ELEVE et structurellement mauvais : dependance a un abonnement HubSpot, disparition de l acces API autonome, et introduction d un CRM externe la ou l architecture a explicitement choisi un vault local comme source de verite.
- **Justification** : Ecarte : le produit autonome n existe plus. L API Clearbit historique est en extinction et l acces passe desormais par un abonnement HubSpot, ce qui reviendrait a plaquer un CRM entier sur une architecture qui a delibérement choisi un vault Obsidian local et une porte humaine. Prix par credit le plus eleve du panel (environ 0,45 USD) et zero couverture documentee sur les TPE francophones. La question ne se pose plus.

#### Findymail — *a_considerer*

- **URL tarifs** : https://www.findymail.com/pricing — TENTATIVE DE CONSULTATION LE 2026-08-02, ECHEC : HTTP 403 (acces sortant bloque).
- **Prix constaté** : RAPPORTE PAR DES TIERS (Capterra, derrick-app, syncgtm, usereviews, prospeo — releve le 2026-08-02), NON VERIFIE : Basic 49 USD/mois pour 1 000 credits ; Starter 99 USD/mois pour 5 000 credits ; Business 249 USD/mois pour 15 000 credits ; Enterprise sur devis. Remise annuelle d environ 17 pour cent, ramenant les mensualites effectives a environ 41, 83 et 208 USD. Cout en credits : 1 credit par email, 10 credits par telephone.
- **Coût unitaire** : Basic a 41 USD/mois en annuel = 492 USD/an. A 50 enrichissements par mois : 0,82 USD par contact utile, avec 95 pour cent de la dotation perdue. Prix nominal du credit : environ 0,041 USD. La facturation au resultat verifie et le report jusqu a 2x attenuent le gachis, mais ne le suppriment pas : le plancher d abonnement reste de 20 fois le besoin.
- **Palier gratuit** : Aucun palier gratuit permanent trouve dans les resultats. NON VERIFIE.
- **Couverture** : Aucune donnee de couverture specifique au Quebec, a la Suisse romande ou aux TPE artisanales francaises n a ete trouvee. Le produit est positionne sur l outbound B2B classique, majoritairement anglophone. Presomption de faiblesse sur le segment vise, non mesuree.
- **Pertinence** : Le MODELE de facturation est excellent pour ce cas d usage — et c est le point important, plus que le fournisseur lui-meme. Sur un segment ou l on s attend a un taux d echec eleve (TPE locales mal couvertes), ne payer que les succes deplace tout le risque de couverture du cote du fournisseur. C est exactement le modele qu il faut chercher quand on ne connait pas encore son taux de succes. Reserve : le plancher mensuel de 41 USD annule une partie de cet avantage a 50 unites par mois.
- **Conformité** : Peu d elements trouves. Editeur non europeen, base et methodes de collecte non documentees dans les sources consultees. L existence d un DPA, la localisation des donnees et la procedure d opposition n ont PAS pu etre verifiees. Pour un usage sur des personnes de l UE ou de Suisse, c est un angle mort a lever avant tout engagement.
- **Intégration** : FAIBLE. API REST simple, un fournisseur a declarer, une methode privee sur le modele d Apollo, cache_key par domaine.
- **Justification** : A considerer non pour sa couverture (inconnue et probablement faible sur ce segment) mais pour son MODELE : facturation au seul resultat verifie plus report des credits, ce qui est la bonne structure de risque quand le taux de succes sur la cible est inconnu. Handicape par un plancher d abonnement de 41 USD/mois pour un besoin de 50 unites et par une conformite non documentee. A garder en reserve derriere Dropcontact.

#### Snov.io — *ecarte*

- **URL tarifs** : https://snov.io/pricing (URL officielle probable — NON CONSULTEE, acces sortant bloque)
- **Prix constaté** : RAPPORTE PAR DES TIERS (bookyourdata, Capterra, G2, UpLead, saleshandy, derrick-app — releve le 2026-08-02), NON VERIFIE : Trial gratuit avec 50 credits et 100 destinataires par mois, sans carte bancaire ; Starter 39 USD/mois pour 1 000 credits et 5 000 destinataires (29,25 USD/mois en annuel) ; Pro S 99 USD/mois pour 5 000 credits, Pro M 189 USD/mois, Pro L 369 USD/mois, jusqu a 554 USD/mois pour 100 000 credits ; Custom Ultra sur devis. Remise annuelle de 25 pour cent.
- **Coût unitaire** : Starter a 29,25 USD/mois en annuel = 351 USD/an. A 50 enrichissements par mois : 0,59 USD par contact utile. Prix nominal du credit sur Starter : environ 0,029 USD. Le palier gratuit a 50 credits/mois couvrirait, comme chez Hunter, exactement le volume mensuel estime du systeme.
- **Palier gratuit** : 50 credits et 100 destinataires par mois, sans carte bancaire (rapporte, NON VERIFIE).
- **Couverture** : Aucune donnee de couverture specifique aux trois marches vises. Editeur d origine ukrainienne, positionnement international generaliste. Presomption de faiblesse sur les TPE artisanales francophones, non mesuree.
- **Pertinence** : PARTIELLEMENT INADAPTEE, et il faut le dire clairement. Une part importante de la valeur de Snov.io reside dans l envoi de sequences d emails et le rechauffement de boites — c est-a-dire J6 OUTREACH, qui n existe pas dans ce systeme, n est pas activable (double verrou : enabled: false dans dag_pipeline.yaml et runner renvoyant 'bloque'), et dont l activation est conditionnee a une validation juridique prealable par un juriste sur CASL, nLPD, art. 3 LCD, RGPD et transparence AI Act. Souscrire un outil d envoi alors que l envoi est verrouille par decision d architecture serait acheter la fonction que le projet a explicitement refuse d activer. Seule la brique de recherche d email est pertinente, et elle n est pas la meilleure du panel.
- **Conformité** : Elements de conformite non documentes dans les sources consultees : DPA, localisation des donnees, base legale de constitution de la base et procedure d opposition n ont PAS pu etre verifies. Risque supplementaire propre a ce fournisseur : la proximite entre la fonction d enrichissement et la fonction d envoi facilite un contournement accidentel de la porte humaine et du verrou J6.
- **Intégration** : FAIBLE pour la seule brique de recherche d email. Mais l integrer expose le systeme a une tentation d architecture — utiliser la fonction d envoi — que le projet a verrouillee a deux niveaux.
- **Justification** : Ecarte. Non parce que le produit est mauvais, mais parce que sa proposition de valeur est majoritairement l envoi de sequences — c est-a-dire exactement la fonction J6 que ce projet a delibérement rendue non activable en attendant une validation juridique. On paierait surtout pour une capacite interdite. Sur la seule recherche d email, Hunter et Dropcontact sont mieux places, et mieux documentes cote conformite.

#### Anymailfinder — *a_considerer*

- **URL tarifs** : https://anymailfinder.com/pricing (URL officielle probable — NON CONSULTEE, acces sortant bloque)
- **Prix constaté** : RAPPORTE PAR DES TIERS ET INCOHERENT ENTRE SOURCES — a traiter comme une fourchette. Releve le 2026-08-02 (Capterra, UpLead, syncgtm, mentionagent, puzzleinbox), NON VERIFIE : une source situe l entree de gamme publique a 14 USD/mois pour 50 emails verifies, avec une montee jusqu a 149 USD/mois pour 5 000 emails verifies ; une autre annonce Starter 49 USD/mois pour 1 000 emails verifies, Standard 99 USD/mois pour 5 000, Enterprise 299 USD/mois pour 50 000. Ces deux grilles sont INCOMPATIBLES (149 USD pour 5 000 contre 99 USD pour 5 000) : au moins une source est perimee. Remise annuelle rapportee d environ 33 pour cent. LE CHIFFRE DE 14 USD/MOIS POUR 50 EMAILS VERIFIES EST LE PLUS INTERESSANT DU PANEL POUR CE PROJET ET DOIT ETRE VERIFIE EN PRIORITE.
- **Coût unitaire** : Sur l hypothese 14 USD/mois pour 50 emails verifies : 0,28 USD par email EFFECTIVEMENT LIVRE ET VERIFIE, et zero paye sur les echecs. C est le seul point du panel ou le cout unitaire affiche correspond au cout unitaire REEL a notre volume, sans gachis de dotation : 168 USD/an pour exactement le volume estime du systeme. Sur l hypothese Starter a 49 USD/mois pour 1 000 : 588 USD/an, soit 0,98 USD par contact utile a 50/mois — quatre fois moins avantageux. L ecart entre les deux hypotheses justifie a lui seul de verifier la page officielle avant toute decision.
- **Palier gratuit** : Aucun palier gratuit permanent trouve. Le plancher a 14 USD/mois, s il est confirme, en tient pratiquement lieu.
- **Couverture** : Aucune donnee de couverture specifique au Quebec, a la Suisse romande ou aux TPE francaises. Presomption de faiblesse comme pour tout le panel anglo-saxon. MAIS — et c est l argument central — le modele de facturation rend cette faiblesse economiquement indolore : sur un segment ou l on echouerait 60 pour cent du temps, on ne paie que les 40 pour cent de succes. Chez Apollo ou PDL, on paie l abonnement quel que soit le taux d echec.
- **Pertinence** : Bonne comme RECOURS de dernier rang, precisement parce que le risque de couverture est porte par le fournisseur. C est le complement logique du socle interne : le collecteur d extraction et les registres traitent la majorite des cas a cout nul, et les cas residuels partent chez un fournisseur qui ne facture que s il reussit.
- **Conformité** : Elements non documentes dans les sources consultees : DPA, localisation des donnees, base legale de constitution et procedure d opposition n ont PAS pu etre verifies. Angle mort a lever avant tout usage sur des personnes de l UE ou de Suisse. C est ce qui l empeche d etre classe 'recommande' malgre l excellence de son modele economique.
- **Intégration** : FAIBLE. API REST simple, un fournisseur a declarer dans api_pricing.yaml avec unite 'credit', une methode privee sur le modele exact de _apollo_people_search. Le mode 'not found sans facturation' se marie particulierement bien avec le grand livre api_usage.log : une ligne a cout zero pour un echec, ce qui donne gratuitement la mesure du taux de succes reel sur le segment.
- **Justification** : Le meilleur ajustement economique du panel a ce volume SI le palier a 14 USD/mois pour 50 emails verifies est confirme : 0,28 USD par email reellement livre, zero paye sur les echecs, et le risque de couverture — qui est le risque principal sur ce segment — porte par le fournisseur. Deux reserves qui l empechent d etre recommande : divergence flagrante entre les grilles rapportees, et conformite non documentee. A verifier sur la page officielle en meme temps que Dropcontact.

#### Prospeo — *a_considerer*

- **URL tarifs** : https://prospeo.io/pricing (URL officielle identifiee dans les resultats de recherche — NON CONSULTEE DIRECTEMENT, HTTP 403, acces sortant bloque)
- **Prix constaté** : RAPPORTE PAR DES TIERS (coldiq, satellyte, derrick-app, syncgtm — releve le 2026-08-02), NON VERIFIE : Free permanent avec 75 credits email par mois plus 100 credits d extension Chrome par mois (une source cite 100 credits/mois — divergence non tranchee) ; Starter 39 USD/mois pour 1 000 credits ; Growth 99 USD/mois pour 5 000 credits ; Pro 199 USD/mois pour 20 000 credits ; Business 369 USD/mois pour 50 000 credits. Tarification plate : l annuel ne reduit pas le mensuel.
- **Coût unitaire** : 0,00 USD par contact tant que le volume reste sous 75 par mois — ce qui est le cas de l hypothese de cadence retenue (25 enrichissements par run, 2 runs par mois). Si le volume double : Starter a 39 USD/mois = 468 USD/an, soit 0,39 USD par contact a 100/mois. Prix nominal du credit sur Starter : 0,039 USD.
- **Palier gratuit** : 75 credits email par mois, permanent et sans limite de duree (rapporte, NON VERIFIE). C est le palier gratuit le plus genereux du panel, et il DEPASSE le volume mensuel estime du systeme (50 enrichissements/mois).
- **Couverture** : Le produit est positionne autour de l identification d emails depuis LinkedIn, ce qui est le mauvais angle pour ce persona : le dirigeant d une entreprise HVAC de 8 personnes a Trois-Rivieres n a souvent pas de profil LinkedIn exploitable. Aucune donnee de couverture specifique aux trois marches. Presomption de faiblesse marquee sur le segment vise.
- **Pertinence** : Interessante uniquement par le palier gratuit, qui permet de MESURER le taux de succes reel sur 75 domaines HVAC quebecois sans depenser un dollar. C est sa vraie valeur pour ce projet : un instrument de mesure gratuit, pas necessairement un fournisseur de production.
- **Conformité** : Elements non documentes dans les sources consultees : DPA, localisation, base legale, opposition — non verifies. L orientation LinkedIn du produit invite a la prudence au regard du precedent Kaspr : la ligne entre 'consulter un profil que l utilisateur a rendu public' et 'aspirer des coordonnees a visibilite restreinte' est precisement celle que la CNIL a sanctionnee. A instruire serieusement avant tout usage en production sur des personnes de l UE.
- **Intégration** : FAIBLE. API REST, un fournisseur, une methode privee.
- **Justification** : A considerer d abord comme instrument de MESURE : 75 credits gratuits par mois, en permanence, permettent d etablir le taux de succes reel sur le persona HVAC quebecois sans engagement — la donnee manquante qui bloque aujourd hui toute decision rationnelle. Comme fournisseur de production, il est moins bien place : orientation LinkedIn mal adaptee aux TPE artisanales, et conformite non documentee avec, en arriere-plan, le precedent Kaspr sur ce type d approche.

#### FullEnrich (waterfall multi-fournisseurs, editeur francais) — *a_considerer*

- **URL tarifs** : https://fullenrich.com/pricing (URL officielle probable — NON CONSULTEE, acces sortant bloque)
- **Prix constaté** : RAPPORTE PAR DES TIERS ET INCOHERENT ENTRE SOURCES. Releve le 2026-08-02 (coldiq, ZoomInfo pipeline, derrick-app, syncgtm, reviewnexa), NON VERIFIE : une source annonce un plan a partir de 26 USD/mois pour 6 000 credits en annuel, Pro a 49 USD/mois pour 12 000 credits, Scale a partir de 500 USD/mois sur devis ; une autre annonce Start a 29 USD/mois pour 500 credits/mois, Pro a 55 USD/mois pour 1 000 credits/mois, Scale a partir de 500 USD/mois. L ecart sur le nombre de credits (6 000 contre 500 pour un prix voisin) est d un facteur DOUZE : ces chiffres sont inutilisables en l etat et exigent une verification directe.
- **Coût unitaire** : Selon l hypothese basse en credits (500 credits pour 29 USD/mois) : 348 USD/an, soit 0,58 USD par contact utile a 50/mois, prix nominal du credit 0,058 USD. Selon l hypothese haute (6 000 credits pour 26 USD/mois) : 312 USD/an, prix nominal du credit 0,004 USD. L incertitude d un facteur douze rend tout calcul non engageant.
- **Palier gratuit** : Aucun palier gratuit permanent trouve. Une periode d essai est probable mais NON VERIFIEE.
- **Couverture** : C est l argument central du produit et il est structurellement pertinent ici : le waterfall interroge en cascade Apollo, Dropcontact, Hunter, Datagma, Findymail, RocketReach, BetterContact et une dizaine d autres, et revendique de depasser 80 pour cent de taux de decouverte en agregeant les sources. Un tiers rapporte que le waterfall ajoute 20 a 40 pour cent de couverture par rapport a n importe quelle base unique. Or notre probleme EST un probleme de couverture sur un segment mal couvert : c est exactement la faille que le waterfall adresse. L editeur est francais et son waterfall integre des fournisseurs orientes UE. Reserve honnete : les 80 pour cent revendiques sont un chiffre d editeur, mesure sur une population de contacts B2B generique et non sur des installateurs HVAC quebecois ; il n y a aucune raison de le transposer tel quel a notre cible.
- **Pertinence** : Bonne sur le principe, avec une reserve d architecture importante. Sur le principe : un seul appel derriere le bus api_io, une seule ligne au grand livre, une seule cle a gerer, et le meilleur taux de decouverte attendu du panel. La reserve : le waterfall introduit une OPACITE sur la provenance de chaque adresse — on ne sait pas toujours lequel des vingt fournisseurs a livre la donnee. Cela heurte directement le champ contact_email_source de l objet Contact, qui existe precisement pour constituer la piste d audit RGPD. Si l API ne renvoie pas le fournisseur d origine par enregistrement, la piste d audit se degrade en 'fullenrich', ce qui est une reponse insuffisante face a une demande de droit d acces. A verifier avant integration : l API expose-t-elle la source par enregistrement ?
- **Conformité** : Editeur francais, conformite RGPD et CCPA revendiquee, waterfall incluant des fournisseurs orientes UE. Mais le modele waterfall herite necessairement du profil de conformite du PLUS FAIBLE de ses vingt fournisseurs pour toute donnee livree par celui-ci. Passer par FullEnrich peut donc signifier consommer indirectement de la donnee issue d une base americaine agregee, sans le savoir. Pour ce projet, ou la conformite est une contrainte dure et non un critere de confort, cette opacite est un vrai probleme, pas une nuance. Elle est acceptable seulement si l API expose la source par enregistrement.
- **Intégration** : FAIBLE techniquement : un fournisseur, une methode privee, API asynchrone probable comme Dropcontact. L effort reel est de VERIFIER la restitution de la source par enregistrement, sans quoi le champ contact_email_source perd sa valeur d audit.
- **Justification** : A considerer serieusement si et seulement si deux points sont leves : la grille tarifaire reelle (les sources divergent d un facteur douze sur les credits, c est disqualifiant en l etat) et la restitution de la source par enregistrement. Le waterfall adresse exactement notre probleme — la couverture faible sur les TPE francophones — avec facturation au seul resultat verifie et editeur francais. Mais l opacite de provenance heurte frontalement le champ contact_email_source qui porte la piste d audit RGPD de ce systeme.

### Incertitudes déclarées

- BLOQUANT ET TRANSVERSAL — Aucune page tarifaire officielle n a pu etre consultee. Le proxy de cet environnement refuse les connexions sortantes vers les sites des editeurs : HTTP 403 sur https://www.apollo.io/pricing, https://hunter.io/pricing, https://www.dropcontact.com/pricing, https://prospeo.io/pricing, https://www.findymail.com/pricing, https://www.peopledatalabs.com/pricing (tentatives du 2026-08-02 ; le statut du proxy confirme un 'connect_rejected — gateway answered 403 to CONNECT'). TOUS les prix de ce rapport proviennent de recherches web sur des agregateurs, blogs comparatifs et G2/Capterra. AUCUN n est verifie a la source. Aucun ne doit etre saisi dans knowledge/api_pricing.yaml en l etat, et releve_le doit rester null jusqu a un relevé direct par l operatrice.
- CRITIQUE POUR LE STATU QUO — L acces a l API Apollo exige-t-il le plan Organization (119 USD/utilisateur/mois) ? Plusieurs sources tierces (galadon.com, datalane.com) l affirment, en indiquant que Free, Basic et Professional ne donnent acces qu aux integrations marketplace (Zapier, Make, CRM natif) et non aux appels API bruts. Le systeme appelle https://api.apollo.io/v1/people/search en direct. Si l affirmation est exacte, le cout du statu quo passe d environ 588 a environ 1 428 USD/an, ce qui inverse le classement economique. NON VERIFIE — a trancher sur la documentation officielle en priorite absolue.
- CRITIQUE POUR LA RECOMMANDATION — L acces a l API Dropcontact exige-t-il le palier Business (environ 74 a 79 EUR/mois) ? Une source (derrick-app) l affirme. Ce systeme n utilise QUE l API. Si c est exact, le prix d entree reel du fournisseur recommande est triple par rapport au Starter affiche a 24 EUR/mois. NON VERIFIE. Les sources divergent par ailleurs sur la dotation du plan Starter : 500 credits selon l une, 1 000 selon l autre.
- Anymailfinder — Grilles rapportees MUTUELLEMENT INCOMPATIBLES : une source annonce 14 USD/mois pour 50 emails verifies montant a 149 USD/mois pour 5 000 ; une autre annonce Starter 49 USD/mois pour 1 000, Standard 99 USD/mois pour 5 000. Le meme volume (5 000) est chiffre a 149 et a 99 USD. Au moins une source est perimee. Or le palier a 14 USD/mois est le meilleur ajustement economique de tout le panel a notre volume (0,28 USD par email verifie) : c est le chiffre le plus important a verifier apres les deux precedents.
- FullEnrich — Ecart d un facteur DOUZE entre sources sur les credits inclus : 6 000 credits pour 26 USD/mois selon l une, 500 credits pour 29 USD/mois selon l autre. Aucun calcul de cout unitaire n est engageant tant que ce point n est pas leve.
- Lusha — Divergence sur le palier gratuit : 40 credits/mois selon une source, 70 selon une autre. Non tranche.
- Prospeo — Divergence sur le palier gratuit : 75 credits email/mois selon une source, 100 credits/mois selon une autre. Non tranche.
- Cognism — Les montants (15 000 a 25 000 USD de frais de plateforme, 1 500 a 2 500 USD par siege) sont presentes par les sources elles-memes comme des ESTIMATIONS. L editeur ne publie aucune grille : ces chiffres sont par nature invérifiables sans passer par un devis commercial.
- Pappers API — TARIF NON TROUVE. Les recherches n ont remonte aucune grille publique. C est une information utile en soi : l alternative gratuite (API Sirene INSEE) doit etre privilegiee par defaut pour la France.
- AUCUNE MESURE DE COUVERTURE SUR LE SEGMENT REEL — Je n ai trouve aucune donnee chiffrant le taux de succes de l un quelconque de ces fournisseurs sur des TPE artisanales de 5 a 30 personnes au Quebec francophone, en Suisse romande ou en France. Les elements rassembles (couverture Apollo faible hors Amerique du Nord, donnee PME suisse mince, precision reelle mesuree entre 65 et 90 pour cent contre 95 revendiques, deterioration de 20 a 30 pour cent par an) sont des indications generales, pas des mesures sur ce persona. Toute la partie 'couverture' de ce rapport repose donc sur une inference argumentee, jamais sur une mesure. Seul le test sur 50 domaines reels peut trancher.
- AUCUNE STATISTIQUE SUR LA PUBLICATION D EMAIL PAR LES TPE — J ai cherche une etude chiffrant la part des sites de petites entreprises publiant une adresse email exploitable. Je n en ai trouve AUCUNE. Les seuls chiffres remontes portent sur le comportement des visiteurs (40 a 44 pour cent quittent un site sans coordonnees visibles), ce qui ne repond pas a la question. L hypothese centrale de ma recommandation — 'l email est souvent public sur le site d une TPE' — est donc PLAUSIBLE ET NON DEMONTREE. C est precisement pourquoi je propose de la mesurer sur 50 domaines reels avant toute depense, plutot que de l affirmer.
- Hypothese de cadence — Les 50 enrichissements par mois (2 runs de 25) sont une projection que je pose explicitement a partir de max_enrichissements: 25 lu dans icp/persona1-quebec.yaml. La cadence reelle de la consultante n est documentee nulle part. Tous les couts par contact varient lineairement avec ce chiffre : a 100 par mois ils sont divises par deux, a 25 par mois ils sont doubles.
- Estimation de dedup — Les 60 a 90 domaines uniques par run derivent de 3 gabarits x 6 localites x 10 resultats = 180 resultats bruts, avec un taux de recouvrement suppose. Aucun run reel n a jamais eu lieu (aucune cle API dans l environnement, preflight en NO-GO structurel) : ce chiffre n est pas mesure.
- Conformite non documentee pour cinq fournisseurs — Findymail, Anymailfinder, Prospeo, Snov.io et People Data Labs : je n ai trouve aucun element verifiable sur l existence d un DPA, la localisation des donnees, la base legale de constitution de la base ou la procedure d opposition. Pour Anymailfinder, dont le modele economique est le meilleur du panel, c est l angle mort qui l empeche d etre recommande plutot que simplement considere.
- Dropcontact — La mention d un hebergement en France (type OVH) n a PAS pu etre confirmee ; les recherches n ont pas remonte cette information. L audit CNIL est rapporte par la documentation de l editeur et par des tiers : a noter qu un audit n est ni une certification ni un label, et ne vaut pas quitus de conformite pour l utilisateur en aval.
- FullEnrich — Point a instruire avant toute integration : l API restitue-t-elle, PAR ENREGISTREMENT, lequel des vingt fournisseurs du waterfall a livre la donnee ? Si non, le champ contact_email_source de l objet Contact se degrade en 'fullenrich', ce qui est une reponse insuffisante face a une demande de droit d acces, et vide de sa substance la piste d audit RGPD que ce champ existe pour porter.
- REQ Quebec, Zefix, Sirene — La gratuite, la frequence de mise a jour et les modalites d acces sont rapportees par des tiers et par les portails de donnees ouvertes, mais aucune page officielle n a pu etre consultee directement. Les conditions de LICENCE de reutilisation (notamment pour un usage de prospection commerciale) n ont pas ete verifiees et doivent l etre avant integration — c est un point de conformite, pas un detail technique.

---


<a id="s6"></a>

## 6. Sources OSINT (registres, réputation, signaux web)


# ÉTUDE OSINT — Sources ouvertes et API pour un dossier de prospect TPE/PME HVAC (Québec, Suisse, France)

Relevé effectué le **2026-08-02**. Aucun chiffre ci-dessous n'a été écrit de mémoire.

---

## 0. Niveau de preuve — à lire avant tout usage budgétaire

**Avertissement d'exécution, à ne pas masquer :** dans cet environnement, `WebFetch` et `curl` ont reçu un **HTTP 403** sur toutes les pages tarifaires officielles à accès direct (`developers.google.com/maps/...`, `mapsplatform.google.com/pricing`, `pappers.fr/api`, `api.pappers.fr`, `business.yelp.com/data/resources/pricing`, `wappalyzer.com/pricing`, `zefix.admin.ch/ZefixPublicREST`). **Je n'ai donc pu vérifier aucune grille tarifaire par lecture directe de la page officielle.** Tout ce qui suit provient de résultats de recherche web. J'étiquette en conséquence :

| Étiquette | Signification |
|---|---|
| **[OFFICIEL-INDIRECT]** | Le contenu est attribué à une page du domaine officiel apparue dans les résultats, mais je n'ai pas ouvert la page moi-même (403). Fiable, à re-vérifier avant saisie en YAML. |
| **[TIERS]** | Chiffre rapporté par un blog / comparateur tiers. **Ne jamais saisir tel quel dans `api_pricing.yaml`.** |
| **[NON TROUVÉ]** | Recherche faite, information non trouvée. C'est un résultat, pas un trou à combler par estimation. |
| **[NON VÉRIFIÉ]** | Affirmation d'architecture ou de droit que je pose sans l'avoir sourcée ici. |

**Conséquence directe pour le projet :** aucune des valeurs de cette étude ne suffit à passer `releve_le: null` → `releve_le: 2026-08-02` dans `knowledge/api_pricing.yaml`. La Phase D exige une lecture humaine des pages tarifaires depuis un navigateur non bloqué. Cette étude fournit **la liste des pages à ouvrir et l'ordre de grandeur attendu**, pas la donnée engageante.

---

## 1. REGISTRES D'ENTREPRISES OFFICIELS

### 1.1 Québec / Canada

**Registraire des entreprises du Québec (REQ) — Données Québec**
- Données exposées : nom, autres noms, forme juridique, date d'immatriculation, statut, adresse du domicile et des établissements, **administrateurs et actionnaires**, codes d'activité économique (CAE), nombre de salariés déclaré (tranche). Schéma relationnel multi-fichiers documenté par un guide d'utilisation PDF. [OFFICIEL-INDIRECT]
- **Pas d'API REST métier du REQ.** Le portail Données Québec expose une **API de catalogue CKAN** pour récupérer les fichiers ; le mode d'usage réel est le **téléchargement de dumps**. Un client Go communautaire existe (`github.com/quebec/req`). [OFFICIEL-INDIRECT]
- Fraîcheur : **mise à jour deux fois par mois**. [OFFICIEL-INDIRECT]
- Coût : **gratuit**, données ouvertes.
- Valeur de qualification : **très haute**. C'est la seule source qui donne l'ancienneté légale, la forme juridique, l'effectif déclaré et les dirigeants pour une TPE québécoise. Contact officiel : `Groupe.EOS@req.gouv.qc.ca`.
- **Point d'architecture :** un dump bimensuel n'est pas un appel réseau par prospect. C'est une **ROM locale** (au sens de l'architecture J2), pas un collecteur palier 1. Coût marginal par prospect = **0**.

**Corporations Canada (ISED)**
- API `api.ised-isde.canada.ca` « Federal Corporation API » : statut, siège social, **administrateurs**, en temps réel ; interrogeable par `corporation_id` ou numéro d'entreprise à 9 chiffres. Dump XML complet : `ised-isde.canada.ca/cc/lgcy/download/OPEN_DATA_SPLIT.zip`. [OFFICIEL-INDIRECT]
- Coût : **gratuit** (compte sur l'API Store requis pour l'information sur les administrateurs). [OFFICIEL-INDIRECT]
- **Limite décisive pour le persona 1 :** ne couvre **que** les sociétés de régime fédéral (LCSA). Un installateur HVAC local québécois est très majoritairement constitué au provincial. → **Source secondaire**, ne pas en faire le socle. Le socle Québec est le REQ.

### 1.2 Suisse

**Zefix — Registre du commerce (Office fédéral du registre du commerce, OFRC)**
- API REST publique : `https://www.zefix.admin.ch/ZefixPublicREST/api/v1`, Swagger UI exposé à `/ZefixPublicREST/swagger-ui/index.html`. Retour JSON, interrogeable par **IDE/UID** ou par raison sociale. [OFFICIEL-INDIRECT]
- Données : raison sociale, IDE, siège, forme juridique, statut, date d'inscription, extraits, cantons. Les **personnes inscrites** (associés-gérants, administrateurs) figurent au registre du commerce cantonal.
- Coût : **gratuit**. Publié sur opendata.swiss. Deux versions coexistent dans les sources : « compte à demander par courriel à `zefix@bj.admin.ch` » (opendata.swiss) et « pas d'authentification pour les requêtes de base » (tiers). **À trancher avec l'OFRC avant industrialisation.** [OFFICIEL-INDIRECT / contradiction non résolue]
- Rate limit : **[NON TROUVÉ]** — non publié. Des clients tiers implémentent un « throttle » par prudence.

**Registre IDE / UID — Office fédéral de la statistique (OFS)**
- Web services UID (interface 5.0 documentée). Les **Public-Services sont limités à 20 requêtes par minute** ; au-delà, **blocage temporaire de l'appelant**. Disponibilité garantie hors 3 jours/an. Les **fonctions étendues sont réservées aux administrations publiques** ; la recherche publique et la vérification du numéro TVA restent ouvertes. [OFFICIEL-INDIRECT — bfs.admin.ch]
- Coût : **gratuit** (« Die UID-Webservices sind kostenlos »). [OFFICIEL-INDIRECT]
- Valeur : identifiant pivot IDE/CHE + **statut TVA** (signal de taille d'entreprise : assujettissement TVA = chiffre d'affaires ≥ seuil légal). Contact : `uid@bfs.admin.ch`, 0800 20 20 10.
- **20 req/min est le vrai plafond de débit du volet suisse.** À encoder comme budget dans `api_pricing.yaml`, même à coût nul.

### 1.3 France

**INSEE — API Sirene**
- Données : SIREN/SIRET, dénomination, **date de création**, code APE/NAF, **tranche d'effectif salarié**, adresse normalisée, état administratif, unités légales et établissements.
- Coût : **gratuite**. Quota : **30 interrogations par minute**, authentification **OAuth2** obligatoire, pas de SLA, pas de fuzzy matching. L'INSEE se réserve le droit de modifier cette limite. [OFFICIEL-INDIRECT — insee.fr, concordant sur 4 sources]
- **Alternative frugale majeure : les fichiers stock Sirene en open data.** Téléchargement complet, licence ouverte. Pour le persona HVAC français, le **code NAF 4322B** (« travaux d'installation d'équipements thermiques et de climatisation ») permet de **constituer localement l'univers entier du marché français sans un seul appel API**. [OFFICIEL-INDIRECT — insee.fr « Sirene Open Data »]

**API Recherche d'entreprises (`recherche-entreprises.api.gouv.fr`)**
- **Totalement ouverte : aucune authentification.** Rate limit **7 appels par seconde**, réductible en cas de charge. Gratuite. [OFFICIEL-INDIRECT — data.gouv.fr]
- C'est **la meilleure porte d'entrée France** : recherche plein texte (nom + commune) → SIREN, sans clé, sans OAuth, 7 req/s. À privilégier sur l'API Sirene pour la phase de découverte ; garder Sirene pour l'enrichissement fin.

**API Entreprise (`entreprise.api.gouv.fr`)**
- **Réservée aux administrations et collectivités.** [OFFICIEL-INDIRECT — data.gouv.fr]
- → **Inaccessible à une consultante indépendante.** Idem pour l'« API Certification RGE — Ademe » distribuée dans ce bouquet. Ne pas la faire figurer dans une roadmap : ce serait une hallucination de faisabilité.

**INPI — RNE (Registre national des entreprises)**
- API + **SFTP**, format JSON, **mise à jour quotidienne** pour les entreprises. Accès **gratuit**, compte INPI requis, activation dans l'espace personnel « Mes accès API/SFTP ». Toute personne peut consulter les données publiques du RNE. [OFFICIEL-INDIRECT — inpi.fr / economie.gouv.fr]
- Valeur ajoutée sur Sirene : **dirigeants, bénéficiaires effectifs (accès encadré), actes et comptes annuels**. C'est la source française la plus riche sur les personnes — donc **la plus sensible RGPD**.

**Pappers**
- Agrégateur commercial (RNE + BODACC + comptes). API par **crédits**, dégressive au volume ; crédits « Pay As You Go » reportables, crédits d'abonnement mensuel/annuel remis à zéro. [OFFICIEL-INDIRECT — pappers.fr/api, contenu résumé, page non ouvrable]
- Abonnement plateforme (non-API) : **29,90 €/mois** [TIERS]. Registres dématérialisés : **45 € HT par société** depuis février 2026 [OFFICIEL-INDIRECT — services.pappers.fr].
- **Grille tarifaire de l'API : [NON TROUVÉ] — page 403.** Ne pas inventer un prix par requête.
- Verdict frugalité : **Pappers n'apporte rien que RNE + Sirene + Recherche d'entreprises ne donnent gratuitement**, sauf le confort d'un seul endpoint. Pour un système dont le mandat est de minimiser la dépense : **à écarter en Phase D**, à reconsidérer seulement si le coût d'intégration de 3 API gratuites dépasse le coût d'une API payante.

---

## 2. ÉTABLISSEMENT ET RÉPUTATION

### 2.1 Google Places (déjà câblé en palier 1 : `gbp.py`, `reviews.py`)

- Tarifs rapportés : **Text Search Pro 32,00 $/1000 appels** (palier 0–100 k), puis 25,60 $/1000 (100 k–500 k), 19,20 $/1000 (500 k–1 M) ; **Place Details Pro 17 $/1000**. [TIERS — woosmap, mapatlas, safegraph ; concordants entre eux mais **non confirmés sur la page Google**]
- **Palier gratuit depuis le 1er mars 2025** : le crédit mensuel de 200 $ est supprimé et remplacé par **10 000 appels gratuits/mois par SKU Essentials, 5 000 par SKU Pro, 1 000 par SKU Enterprise**. **Le gratuit ne se mutualise plus entre API.** [OFFICIEL-INDIRECT — `developers.google.com/maps/billing-and-pricing/faq`]
- **Lecture pour ce projet :** à 5 000 appels Pro gratuits par mois et par SKU, un pilote de quelques centaines de prospects **coûte 0 $**. Le poste Places n'est un risque budgétaire qu'au-delà de ~2 500 prospects/mois (2 SKU consommés par prospect : `text_search` + `place_details`).
- ⚠️ **CONFLIT D'ARCHITECTURE À ARBITRER — le point le plus important de cette section.** Les CGU Google Maps Platform **interdisent de pré-charger, cacher ou stocker le contenu Places**. Exceptions : le **`place_id` est stockable indéfiniment** ; les **coordonnées lat/lng sont cachables 30 jours**. Noms, notes, avis, photos, téléphones sont censés être requêtés en direct et affichés avec attribution Google, **pas entreposés**. [OFFICIEL-INDIRECT — `cloud.google.com/maps-platform/terms/maps-service-terms` + `developers.google.com/maps/documentation/places/web-service/policies`]
  - Or `api_io.py` **cache sur disque** et le vault **persiste** `note`, `nb_avis`, `verified`. C'est une **non-conformité CGU probable**, pas une non-conformité RGPD.
  - **Recommandation :** ne persister au vault que (a) le `place_id`, (b) des **signaux dérivés non reconstituables** (`a_fiche_gbp: bool`, `avis_suffisants: bool`, `repond_aux_avis: bool`, `note_bucket: "3-4"`), et **purger la valeur brute** après scoring. Le TTL de cache Places doit être ramené **sous 30 jours** dans `greenit.yaml` (aujourd'hui 30 j globaux — à cloisonner par fournisseur). À faire valider juridiquement au même titre que J6.

### 2.2 OpenStreetMap / Overpass — l'alternative gratuite

- **Overpass API** : gratuit, politique d'usage **~10 000 requêtes/jour**. Les services **commerciaux doivent savoir que l'accès peut être retiré à tout moment** ; instance auto-hébergée recommandée au-delà (un serveur 32 Go absorbe des millions de requêtes/jour). Offre payante Geofabrik disponible. [OFFICIEL-INDIRECT — `operations.osmfoundation.org/policies/api/`, wiki OSM]
- **Nominatim** (géocodage) : **1 requête/seconde maximum**, **4 req/min** pour les scripts récurrents ou tournant plus d'un jour, **cache obligatoire côté client**, `User-Agent` ou `Referer` identifiant l'application obligatoire, **une seule machine, pas de script distribué**. [OFFICIEL-INDIRECT — `operations.osmfoundation.org/policies/nominatim/`]
- Données exploitables pour le HVAC : `shop=hvac`, `craft=hvac`, `craft=plumber`, `office=company`, plus `website`, `phone`, `opening_hours`, `operator`.
- ⚠️ **Licence ODbL** : attribution obligatoire et **clause de partage à l'identique sur les bases dérivées**. Mélanger OSM dans le vault peut « contaminer » la base. **Recommandation : n'utiliser OSM que comme signal booléen de présence/cohérence d'adresse, sans recopier les attributs dans le vault.** [NON VÉRIFIÉ — analyse juridique à confirmer]

### 2.3 Yelp

- **Le gratuit est terminé** : tous les comptes ont basculé en modèle payant. Plans rapportés : **Starter 7,99 $/1000 appels, Plus 9,99 $/1000, Enterprise 14,99 $/1000** ; essai 30 jours ; 5 000 appels/jour, 30 000/mois par défaut. [TIERS — appdevelopermagazine, docs.developer.yelp.com résumé ; page officielle 403]
- **Verdict : à écarter.** Couverture Yelp faible pour le HVAC au Québec, quasi nulle en Suisse romande et en France, à un prix supérieur à Google Places. Aucun apport marginal.

### 2.4 Annuaires sectoriels

- Pages Jaunes (QC/FR), local.ch / search.ch (CH) : **déjà exclus par filtre de domaine dans `DiscoveryCollector`** — décision correcte, ce sont des agrégateurs, pas des sites propres. Ils restent utiles comme **source de découverte** (et non de qualification), mais leurs CGU interdisent en général l'extraction automatisée. [NON VÉRIFIÉ — CGU à lire par marché]

---

## 3. CERTIFICATIONS ET ASSOCIATIONS MÉTIER HVAC — le signal de qualification le plus discriminant

C'est, à mon avis, **la découverte la plus rentable de cette étude** : ces registres sont gratuits, exhaustifs, sectoriels et légalement publics. Ils permettent de **construire l'univers de prospection sans SERP payante**.

### Québec

**RBQ — Liste des licences actives** (Données Québec)
- Jeu de données ouvert, **gratuit**, téléchargeable. Contient l'ensemble des détenteurs de licence RBQ actifs ; le registre en ligne couvre aussi les détenteurs des **5 dernières années**, avec depuis 2023 le **nombre de réclamations sur cautionnement et indemnités versées**. [OFFICIEL-INDIRECT — donneesquebec.ca, rbq.gouv.qc.ca]
- **Valeur exceptionnelle :** au Québec, exercer sans licence RBQ est illégal. Les **sous-catégories de licence** identifient précisément le métier (chauffage, ventilation, réfrigération). → **On peut générer l'univers complet des installateurs HVAC québécois, avec adresse et numéro d'entreprise, pour 0 $ et 0 appel API.**
- Le champ « réclamations / indemnités » est un **signal de risque** exploitable côté qualification.

**CMMTQ — Corporation des maîtres mécaniciens en tuyauterie du Québec**
- Répertoire public de **plus de 2 600 entrepreneurs** en mécanique du bâtiment (plomberie, chauffage). **Adhésion obligatoire par la loi** pour exercer ; la CMMTQ poursuit en justice l'exercice illégal. [OFFICIEL-INDIRECT — cmmtq.org]
- Pas d'API : **[NON TROUVÉ]**. Accès par répertoire web. **Lire les CGU avant toute extraction automatisée.**
- Signal : appartenance CMMTQ = entreprise structurée, non-appartenance sur un métier couvert = anomalie forte.

### Suisse

**Registre IDE + Zefix** (voir §1.2) pour la partie légale.

**GSP / FWS — Groupement promotionnel suisse pour les pompes à chaleur**
- **Plus de 440 entreprises membres.** Base de données publique des **installateurs et planificateurs qualifiés « PAC système-module »** (`wp-systemmodul.ch`, `fws.ch`). **Formation continue obligatoire depuis 2024** pour conserver la qualification. [OFFICIEL-INDIRECT — fws.ch, wp-systemmodul.ch]
- Signal : label PAC-SM = investissement de l'entreprise dans sa qualification → prospect qui prend sa marque au sérieux. Contact GSP : Route du Stand 11, 1880 Bex.

**suissetec** — Association suisse et liechtensteinoise de la technique du bâtiment, **~3 600 entreprises membres**, chauffage / ventilation / sanitaire, sections romandes (Genève, Fribourg, Valais, Neuchâtel, Jura). Répertoire consolidé en ligne : **[NON TROUVÉ]** — les annuaires sont fragmentés par section cantonale. [OFFICIEL-INDIRECT — suissetec.ch]

### France

**API Professionnels RGE / Liste des entreprises RGE — ADEME**
- **Open data, licence Etalab, gratuite, sans restriction d'accès.** Endpoint : `https://data.ademe.fr/data-fair/api/v1/datasets/liste-des-entreprises-rge-2`. **Données mises à jour quotidiennement** via l'API et les visualisations ; fichier téléchargeable hebdomadaire. Un jeu « Historique des entreprises RGE depuis 2014 » existe aussi. [OFFICIEL-INDIRECT — data.ademe.fr, data.gouv.fr]
- Contient : SIRET, raison sociale, **domaines de travaux** (dont pompes à chaleur), organisme de qualification, dates de validité.
- **Valeur exceptionnelle, symétrique de la RBQ :** univers complet des installateurs RGE français, avec SIRET (donc jointure directe sur Sirene), pour **0 €**.
- Le champ **historique** permet un signal rare : « qualification RGE **perdue** » = entreprise en difficulté ou en repositionnement → **accroche commerciale**.
- ⚠️ Ne pas confondre avec l'« API Certification RGE — Ademe » du bouquet API Entreprise, **réservée aux administrations**.

**Chaîne recommandée France, coût 0 €** : `RGE (ADEME) → SIRET → Sirene stock (NAF 4322B, effectif, date création) → site web → diagnostic`. Aucune SERP payante nécessaire pour le marché français.

---

## 4. SIGNAUX WEB ET TECHNIQUES — quasi tous gratuits

| Source | Ce qu'elle apporte | API | Coût | Limites / CGU |
|---|---|---|---|---|
| **RDAP** (remplace WHOIS depuis le 28/01/2025) | **Date de création du domaine** = ancienneté de la présence en ligne ; registrar ; statuts ; nameservers ; DNSSEC. JSON structuré. | Bootstrap IANA / `rdap.org`, **aucune clé** | **0** | Redaction RGPD du titulaire quasi systématique. Couverture RDAP de `.ch` et `.ca` : **[NON TROUVÉ]** — à tester avant de câbler. [OFFICIEL-INDIRECT — about.rdap.org, arin.net] |
| **DNS / MX** | Qui héberge la messagerie : `google.com` / `outlook.com` (structuré) vs MX du registrar mutualisé (amateur) vs **pas de MX** (signal très fort). Enregistrements SPF/DMARC = maturité. | `dnspython`, résolveur local | **0** | Aucune. [NON VÉRIFIÉ — pas de source externe nécessaire] |
| **Certificate Transparency (crt.sh)** | Historique des certificats TLS → **date du premier certificat**, sous-domaines oubliés, changements d'hébergeur. | `https://crt.sh/?q=%25.domaine&output=json`, **sans clé** | **0** | Endpoint **non documenté**, pas de limite officielle, blocages temporaires sur concurrence excessive. [TIERS + observation communautaire] |
| **Google PageSpeed Insights / Lighthouse API** | Performance, mobile, Core Web Vitals, accessibilité, **SEO technique** — chiffrable et opposable au prospect. | `developers.google.com/speed/docs/insights/v5` | **Gratuit — 25 000 requêtes/jour**, 400 requêtes/100 s | Augmentation de quota possible via Cloud Console. [OFFICIEL-INDIRECT — developers.google.com/speed] |
| **Wayback Machine / CDX Server API** | **Depuis quand le site n'a pas évolué.** Nombre de captures, date de la dernière modification substantielle, refonte ou absence de refonte sur 5 ans. | `web.archive.org/cdx/search/cdx`, sans clé | **0** | **Aucune limite publiée** ; consensus communautaire **~1 req/s**, throttling sur agressivité. [OFFICIEL-INDIRECT — archive.org/help/wayback_api.php + wiki] |
| **Sitemap.xml + `lastmod`** | Date de dernière publication réelle, volume de pages, présence d'un blog vivant ou mort. | Fetch direct | **0** | Respect `robots.txt`. |
| **BuiltWith** | Stack technique, CMS, pixels publicitaires, historique des technologies. | API à partir du plan Pro | **Basic 295 $/mois, Pro 495 $/mois, Team 995 $/an-mensualisé** [TIERS — hausse ~6× en 2026, ancien palier 50/200/400 $] | API **non incluse** dans le plan de base. **Rapporté par des tiers uniquement.** |
| **Wappalyzer** | Idem. | API par crédits | **Pro 250 $/mois, Business 450 $/mois (20 000 crédits API), Enterprise 850 $+/mois (200 000+ crédits)** ; **50 lookups gratuits/mois** ; crédits inclus expirent à 60 j, crédits achetés à 365 j [TIERS ; page officielle 403] | — |
| **Forks open source de Wappalyzer** | Même détection, 251 fingerprints dans le ruleset embarqué, ~6 000 technologies dans les rulesets communautaires. | `enthec/webappanalyzer`, `tunetheweb/wappalyzer`, `dochne/wappalyzer` — **licence MIT** | **0** | Wappalyzer est passé closed-source en août 2023 ; les forks maintiennent la lignée GPL→MIT et sont **actifs en 2026**. Angles morts hérités du jeu de signatures pré-2023. [TIERS, concordant sur 4 sources] |

**Recommandation frugalité, sans ambiguïté :** **ne pas payer BuiltWith ni Wappalyzer.** Un collecteur `stack.py` s'appuyant sur un fork MIT + le HTML déjà récupéré par `website.py` couvre le besoin à coût nul et **sans appel réseau supplémentaire** — il devient un **collecteur dérivé palier 0**, comme `seo.py` et `social.py`, alimenté par `_website_signals`. C'est exactement le patron que l'architecture prévoit déjà.

**Détection de pixels publicitaires** (Meta Pixel, Google Ads / gtag, GA4, TikTok, LinkedIn Insight) : purement locale, par regex sur le HTML déjà en mémoire. **Coût 0, aucun appel.** Signal d'investissement marketing extrêmement discriminant pour une consultante en branding : un prospect qui a un pixel Meta **dépense déjà** en acquisition — il a un budget et un problème de conversion, donc un besoin de marque.

---

## 5. SIGNAUX D'INTENTION ET D'ACTIVITÉ

| Source | Marché | API | Coût / quota | Note |
|---|---|---|---|---|
| **France Travail — API Offres d'emploi v2** | FR | `francetravail.io`, OAuth, compte gratuit | **Gratuit.** Quota **100 appels/s pour l'API**, **4 appels/s par application** | ~300 000 offres temps réel, JSON : titre, entreprise, contrat, salaire, compétences, lieu, code ROME. [OFFICIEL-INDIRECT — francetravail.io, data.gouv.fr] |
| **Guichet-Emplois / Job Bank Canada** | QC/CA | **API publique : [NON TROUVÉ]** | Jeux **CSV mensuels gratuits** sur `ouvert.canada.ca` | ~65 000 offres. Le mode d'accès industrialisable est le dump mensuel. [OFFICIEL-INDIRECT] |
| **Adzuna** | FR, CA (**pas la Suisse**) | `developer.adzuna.com`, `app_id`+`app_key` | **~1 000 appels/mois gratuits** [TIERS] ; au-delà, plans négociés, **pas de page tarifaire publiée** [TIERS] | 12 pays : GB, US, DE, FR, AU, NZ, CA, IN, PL, BR, AT, ZA. |
| **Meta Ad Library API** | FR (UE) surtout | Graph API, produit « Ad Library » | **Gratuit.** Vérification d'identité par pièce officielle, 1–3 jours ouvrés. **~200 appels/heure** [TIERS] | ⚠️ **Les annonces commerciales non politiques ne sont couvertes que dans l'UE**, et **seulement tant qu'elles sont actives** hors UE. Rétention 1 an après dernière impression pour l'UE. → **Utile pour la France, inutile pour le Québec et la Suisse.** [TIERS + OFFICIEL-INDIRECT] |
| **Google Ads Transparency Center** | 3 marchés | **API publique : [NON TROUVÉ]** | — | Consultation manuelle seulement, à ce que j'ai pu vérifier. |
| **Suisse — offres d'emploi** | CH | **[NON TROUVÉ]** | — | Ni France Travail ni Adzuna ne couvrent la Suisse. Piste non explorée ici : `job-room.ch` (SECO). **À investiguer en Phase D.** |

**Lecture métier :** une TPE HVAC qui **recrute un technicien** investit ; c'est la meilleure fenêtre de tir. C'est aussi le signal le plus asymétrique entre marchés — excellent en France (gratuit, temps réel, exhaustif), moyen au Canada (dump mensuel), **quasi inexistant en Suisse en l'état de cette recherche**.

---

## 6. COÛTS DES BRIQUES DÉJÀ CÂBLÉES (pour `api_pricing.yaml`)

⚠️ **Ces chiffres sont [TIERS]. Ils ne suffisent pas à lever le NO-GO structurel du préflight.** Ils indiquent seulement quelle page l'opératrice doit ouvrir en Phase D.

- **SerpApi** — Free **250 recherches/mois** ; Starter **25 $/mois pour 1 000** ; Developer **75 $ / 5 000** ; Production **150 $ / 15 000** ; Big Data **275 $ / 30 000** ; puis 725 $, 1 475 $, 2 750 $. Coût effectif **25 $ → 9,17 $ par 1 000 recherches** selon le palier. **Les recherches non consommées sont perdues au renouvellement.** [TIERS — trustradius, costbench, apiserpent]
- **Apollo.io** — Free (10 crédits export/mois) ; Basic **49 $/user/mois annuel (59 $ mensuel)**, 1 000 crédits export ; Professional **79 $ (99 $)**, 2 000 crédits ; Organization **119 $ (149 $)**, 4 000 crédits. Crédits supplémentaires **~0,20 $/crédit**. [TIERS — plusieurs comparateurs concordants]
- **Google Places** — voir §2.1.
- **Anthropic** — non recherché dans cette étude (hors mandat OSINT). À relever séparément.

**Observation stratégique :** au vu des §1 et §3, **SerpApi n'est indispensable qu'au Québec**, et encore. Les registres RBQ (QC) et RGE/ADEME + Sirene (FR) fournissent l'univers de prospection **gratuitement et plus proprement qu'une SERP** — sans le bruit des agrégateurs, sans filtre de domaines exclus, avec un identifiant légal en clé primaire. Un chemin de découverte « registre-first » réduirait le poste SERP de plusieurs centaines d'euros à **zéro** sur deux marchés sur trois. C'est un arbitrage produit à porter à `agent-produit`, pas une décision technique.

---

## 7. PROPOSITION DE DOSSIER OSINT — liste ordonnée des champs

Ordre = ordre de collecte recommandé. `€` = payant. `[P]` = **donnée personnelle, encadrée RGPD/nLPD/Loi 25**.

### Bloc A — Identité légale (gratuit, risque nul, ENTREPRISE)
1. `identifiant_legal` — NEQ (QC) / IDE-CHE (CH) / SIREN-SIRET (FR) — **clé primaire du dossier**
2. `raison_sociale` + `noms_commerciaux`
3. `forme_juridique`
4. `date_immatriculation` → **`anciennete_annees`** (dérivé)
5. `statut_administratif` (actif / radié / en liquidation) — **filtre d'exclusion dur**
6. `code_activite` (CAE / NOGA / NAF-APE)
7. `adresse_siege` normalisée
8. `nb_etablissements`
9. `tranche_effectif` — **proxy de taille**, seul critère de segmentation fiable et gratuit
10. `assujetti_tva` (CH, via UID) / `regime_fiscal`

### Bloc B — Certification métier (gratuit, ENTREPRISE) — **le plus discriminant**
11. `licence_rbq` + `sous_categories` + `nb_reclamations_cautionnement` (QC)
12. `membre_cmmtq` (QC)
13. `qualifications_rge` + `domaines_travaux` + `date_validite` (FR)
14. `rge_perdue_depuis` (FR, via l'historique ADEME) — **accroche commerciale directe**
15. `label_pac_systeme_module` / `membre_gsp` / `membre_suissetec` (CH)

### Bloc C — Établissement et réputation (gratuit ou quasi, ENTREPRISE)
16. `place_id` Google — **seul champ Places stockable indéfiniment** (voir §2.1)
17. `a_fiche_gbp` / `gbp_verified` (booléens dérivés)
18. `note_bucket` / `avis_suffisants` / `repond_aux_avis` (booléens **dérivés**, valeurs brutes non persistées)
19. `presence_osm` + `coherence_adresse_osm_vs_registre` — signal de sérieux à coût nul
20. `horaires_publies` (bool)

### Bloc D — Présence en ligne et marque (gratuit, ENTREPRISE) — cœur du scoring existant
21. `site_web` (domaine normalisé) — déjà en place
22. `https_actif`, `viewport_mobile`, `meta_description`, `logo_present`, `formulaire_contact` — déjà en place
23. `date_creation_domaine` (RDAP) → **`anciennete_presence_ligne`**
24. `ecart_anciennete_legale_vs_numerique` (dérivé A4 − D23) — **signal fort** : entreprise établie depuis 20 ans, domaine de 2 ans = retard numérique caractérisé
25. `derniere_maj_site` (copyright, sitemap `lastmod`)
26. `date_derniere_refonte` (Wayback) → **`annees_sans_refonte`** — le signal de négligence de marque le plus discriminant du lot
27. `nb_captures_wayback` (proxy d'activité éditoriale)
28. `liens_sociaux` + `plateformes_mentionnees` — déjà en place
29. `mots_cles_locaux` (SEO dérivé) — déjà en place

### Bloc E — Signaux techniques (gratuit, ENTREPRISE)
30. `cms` / `stack` (fork MIT, sur HTML déjà en mémoire — 0 appel)
31. `hebergeur_mail` (MX) → `messagerie_professionnelle: bool`
32. `spf_dmarc_present`
33. `pixels_publicitaires` (liste) → **`investit_en_acquisition: bool`**
34. `score_pagespeed_mobile` + `lcp` + `cls` (PSI, 25 000/jour gratuits) — **chiffres opposables au prospect dans le mini-audit**
35. `premier_certificat_tls` (crt.sh)

### Bloc F — Intention (gratuit, ENTREPRISE)
36. `recrute_actuellement` + `nb_offres_ouvertes` + `date_derniere_offre`
37. `annonces_publicitaires_actives` (FR uniquement, Meta Ad Library)

### Bloc G — Personne [P] — **PÉRIMÈTRE GELÉ**
38. `contact.nom` [P]
39. `contact.titre` [P]
40. `contact.email` [P]
41. `contact.email_source` [P] — piste d'audit RGPD
42. `contact.linkedin` [P] — référence, jamais scrapée
43. `contact.rattachement` [P]

**Sur le bloc G, ma recommandation est ferme : n'ajouter aucun champ.** Les blocs A→F sont, à une exception près, des **données d'entreprise** — objectivement publiques, publiées par des registres officiels, à faible risque. Dès qu'on touche à la personne, on entre dans un régime où le RGPD impose une obligation d'information de la personne concernée lorsque la donnée n'a pas été collectée auprès d'elle, la nLPD suisse impose un devoir d'information analogue, et la Loi 25 québécoise encadre la collecte indirecte [NON VÉRIFIÉ — je n'ai pas sourcé ces obligations dans cette étude ; **elles font partie du mandat du juriste, au même titre que J6**].

**Le contrat `Contact` à 6 champs avec `extra="forbid"` est un actif de conformité, pas une contrainte.** Deux dirigeants figurent pourtant nominativement dans les registres publics (REQ, RNE, Zefix). **Les extraire vers le vault transformerait un registre légal en fichier de prospection nominatif** — un basculement de finalité qui change le régime juridique applicable. **Recommandation : ne pas les collecter.** Si la consultante en a besoin, elle consulte le registre à la main, au cas par cas — c'est la porte humaine.

**Une exception à surveiller dans le bloc A :** pour une entreprise individuelle, la `raison_sociale` **est** le nom du dirigeant, et l'`adresse_siege` **est** souvent son domicile. Ces champs deviennent alors des données personnelles sans changer de nom. À traiter dans la politique `compliance/*.yaml` du Palier 2. [NON VÉRIFIÉ — qualification juridique à confirmer]

---

## 8. TRADUCTION EN COLLECTEURS ENFICHABLES

L'architecture existante absorbe tout cela sans modification structurelle. Proposition, du plus rentable au moins rentable :

| Collecteur | Palier | Coût/prospect | Rubrique alimentée | Effort |
|---|---|---|---|---|
| `registre.py` (REQ / Zefix+UID / Sirene) | 0 (dump local) ou 1 | **0** | nouvelle dimension `solidite_entreprise` | moyen |
| `certification.py` (RBQ / RGE / GSP) | 0 (dump local) | **0** | `solidite_entreprise` + filtre ICP | faible |
| `domaine.py` (RDAP + DNS/MX + crt.sh) | 1 | **0** | `site_web` | faible |
| `archive.py` (Wayback CDX) | 1 | **0** | `site_web` (négligence) | faible |
| `perf.py` (PageSpeed Insights) | 1 | **0** (25 k/j) | `seo_local` | faible |
| `stack.py` (fork MIT + pixels, dérivé de `_website_signals`) | 0 dérivé | **0** | `identite_visuelle` / intention | faible |
| `emploi.py` (France Travail, FR) | 1 | **0** | signal chaud | moyen |

**Sept collecteurs supplémentaires, tous à coût marginal nul, dont trois sans le moindre appel réseau.** Aucun ne touche aux autres : c'est précisément ce que garantit l'héritage `Collector` + `safe_collect`. Le seul travail d'architecture réel est **l'ajout d'une dimension à `rubric_persona1.yaml`** — donc de la donnée, pas du code — et la répartition des pondérations (les 5 dimensions actuelles totalisent 100).

**Trois points de vigilance sur les invariants du projet :**
1. Chaque nouveau module devra passer par `api_io.py` (bus unique) — y compris les collecteurs à coût nul : **coût nul n'est pas absence de comptabilité**. Les entrées ledger à `cout=0` restent nécessaires pour le suivi GreenIT (`octets_entrants`, `duree_ms`, `energie_wh`).
2. Chaque nouveau module `run_*.py` de ce type devra être **ajouté à la liste de `_check_garde_fous_bus`** — la dette technique n°2 déjà identifiée dans `CLAUDE.md` (absence de `greenit.py` dans cette liste) se reproduira mécaniquement sinon.
3. Les dumps de registres (REQ, RBQ, RGE, Sirene stock) sont des **fichiers volumineux hors vault** : leur place est `.cache/`, pas `vault/`, conformément à la contrainte G9. Ils relèvent du « disque », pas de la « RAM ».

---

## 9. CE QUI RESTE À VÉRIFIER AVANT TOUTE DÉCISION BUDGÉTAIRE

Liste des pages que l'opératrice doit ouvrir manuellement en Phase D — je n'ai pas pu les lire (403) :

1. `developers.google.com/maps/documentation/places/web-service/usage-and-billing` — prix exacts Text Search / Place Details par palier
2. `api.pappers.fr` — grille de crédits (ou décision d'écarter Pappers, cf. §1.3)
3. `serpapi.com/pricing` — paliers et politique de report
4. `apollo.io/pricing` — crédits API vs crédits export (distinction non résolue dans les sources tierces)
5. `business.yelp.com/data/resources/pricing` — sans objet si Yelp est écarté (recommandé)
6. `zefix.admin.ch` — obligation ou non d'un compte, et rate limit (contradiction non résolue)
7. Couverture RDAP effective de `.ch` et `.ca` — test empirique de 3 domaines suffit
8. CGU d'extraction automatisée : CMMTQ, suissetec, GSP/FWS
9. `job-room.ch` (SECO) — équivalent suisse de France Travail, non exploré
10. Arbitrage juridique du **conflit de cache Google Places** (§2.1) — à joindre au dossier du juriste, avec J6

---

## Sources

Registres : [Sirene Open Data INSEE](https://www.insee.fr/fr/information/9019311) · [API Sirene data.gouv](https://www.data.gouv.fr/dataservices/api-sirene-dont-unites-a-diffusion-partielle) · [API Recherche d'Entreprises](https://www.data.gouv.fr/dataservices/api-recherche-dentreprises) · [API Entreprise](https://api.gouv.fr/les-api/api-entreprise) · [Accès aux API Entreprises INPI](https://data.inpi.fr/content/editorial/Acces_API_Entreprises) · [RNE INPI](https://www.inpi.fr/ressources/formalites-dentreprises/registre-national-entreprises) · [Pappers API](https://www.pappers.fr/api) · [Pappers Services tarifs](https://services.pappers.fr/registres-dematerialises/tarifs) · [Zefix REST API i14y](https://www.i14y.admin.ch/en/catalog/dataservices/6ef8f5d2-3d6a-4d84-bf60-5e65fde98a87) · [Zefix Swagger UI](https://www.zefix.admin.ch/ZefixPublicREST/swagger-ui/index.html) · [Zefix opendata.swiss](https://opendata.swiss/en/dataset/zefix-zentraler-firmenindex) · [UID interfaces OFS](https://www.bfs.admin.ch/bfs/en/home/registers/enterprise-register/enterprise-identification/uid-register/uid-interfaces.html) · [UID-Webservice ChF](https://www.bk.admin.ch/bk/de/home/digitale-transformation-ikt-lenkung/e-services-bund/services/uid-webservice.html) · [Registre des entreprises Données Québec](https://www.donneesquebec.ca/recherche/fr/dataset/registre-des-entreprises) · [Guide d'utilisation REQ (PDF)](https://www.donneesquebec.ca/recherche/dataset/6f710997-b5f9-4347-893b-1a47ddb61437/resource/09008d3a-2e0e-4613-ab43-bd833f381929/download/guideutilisation.pdf) · [Federal Corporation API ISED](https://api.ised-isde.canada.ca/en/docs?api=corporations) · [Accessing federal corporation JSON datasets](https://ised-isde.canada.ca/site/corporations-canada/en/accessing-federal-corporation-json-datasets)

Certifications HVAC : [Licences actives RBQ — Données Québec](https://www.donneesquebec.ca/recherche/dataset/licencesactives) · [Registre des détenteurs de licence RBQ](https://www.rbq.gouv.qc.ca/salle-de-presse/les-nouvelles/nouvelles-detail/item/2023-04-12-registre-des-detenteurs-de-licence-validez-une-licence-plus-facilement/) · [Répertoire CMMTQ](https://www.cmmtq.org/liste_compagnies) · [API Professionnels RGE](https://www.data.gouv.fr/dataservices/api-professionnels-rge) · [Liste des entreprises RGE — ADEME](https://data.ademe.fr/datasets/liste-des-entreprises-rge-2) · [Historique RGE depuis 2014](https://data.ademe.fr/datasets/historique-rge) · [Installateurs qualifiés PAC-SM](https://www.wp-systemmodul.ch/fr/page/Proprietaires/Installateurs-et-planificateurs-qualifies-73353) · [Partenaires GSP certifiés — FWS](https://www.fws.ch/fr/partenaires-gsp-certifies-2/) · [Portrait suissetec](https://suissetec.ch/fr/portrait.html)

Places / cartographie / avis : [Places API Usage and Billing](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing) · [FAQ changements tarifaires Google Maps](https://developers.google.com/maps/billing-and-pricing/faq) · [10 000 appels gratuits par produit](https://mapsplatform.google.com/resources/blog/start-building-today-with-up-to-10-000-monthly-free-calls-per-product/) · [Maps Platform Service Specific Terms](https://cloud.google.com/maps-platform/terms/maps-service-terms) · [Policies and attributions for Places API](https://developers.google.com/maps/documentation/places/web-service/policies) · [OSMF API Usage Policy](https://operations.osmfoundation.org/policies/api/) · [Nominatim Usage Policy](https://operations.osmfoundation.org/policies/nominatim/) · [Overpass API status](https://wiki.openstreetmap.org/wiki/Overpass_API/status) · [Yelp Data Licensing pricing](https://business.yelp.com/data/resources/pricing/) · [Yelp Places API plans](https://docs.developer.yelp.com/docs/plans)

Signaux web : [RDAP.ORG](https://about.rdap.org/) · [ARIN RDAP](https://www.arin.net/resources/registry/whois/rdap/) · [crt.sh free API](https://dev.to/0012303/crtsh-has-a-free-api-find-every-ssl-certificate-for-any-domain-with-python-2nlk) · [PageSpeed Insights API get started](https://developers.google.com/speed/docs/insights/v5/get-started) · [Wayback Machine APIs](https://archive.org/help/wayback_api.php) · [Wayback CDX Server README](https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md) · [BuiltWith pricing 2026](https://derrick-app.com/tools/builtwith-pricing) · [Wappalyzer pricing (tiers)](https://prospeo.io/s/wappalyzer-pricing-reviews-pros-and-cons) · [Forks OSS de Wappalyzer](https://dev.to/nexgendata/wappalyzer-paywalled-itself-in-2023-heres-the-oss-powered-replacement-3i01)

Intention : [API Offres d'emploi France Travail](https://francetravail.io/data/api/offres-emploi) · [API Offres d'emploi data.gouv](https://www.data.gouv.fr/dataservices/api-offres-demploi) · [Guichet-Emplois — données ouvertes](https://ouvert.canada.ca/data/fr/dataset/ea639e28-c0fc-48bf-b5dd-b8899bd43072/resource/0de1da89-5aca-4178-b9f1-27fa4a18f8c1) · [Adzuna API field guide](https://jobspipe.dev/blog/adzuna-api) · [Meta Ad Library free API 2026](https://adlibrary.com/posts/meta-ad-library-free-api-2026)

Briques câblées : [SerpApi pricing (tiers)](https://costbench.com/software/web-scraping/serpapi/) · [Apollo.io pricing (tiers)](https://www.saleshandy.com/blog/apolloio-pricing/)

---


<a id="s7"></a>

## 7. Conformité & FinOps


# Analyse conformité + FinOps — Kemana‑Flow / Système Autonome de Diagnostic Marketing
**Date du relevé : 2026‑08‑02.** Tous les tarifs bougent : redater à chaque réutilisation.

---

## AVERTISSEMENT LIMINAIRE — 3 points, à lire avant tout le reste

1. **Ceci n'est pas un avis juridique.** C'est une analyse d'ingénierie de la conformité, destinée à produire des exigences implémentables. Les arbitrages CASL / Loi 25 / nLPD + art. 3 LCD / RGPD / AI Act doivent être validés par un juriste avant tout envoi (c'est déjà la pré‑condition dure de J6, elle est confirmée par cette analyse, pas levée).

2. **Limitation de sourçage rencontrée pendant cette étude.** Le proxy sortant de l'environnement a refusé (403 sur CONNECT) l'accès direct à `serpapi.com`, `developers.google.com`, `mapsplatform.google.com`, `anthropic.com`, `cnil.fr` et `artificialintelligenceact.eu`. Résultat : **seuls les tarifs Anthropic ont pu être lus sur une page officielle**. Tous les autres prix sont rapportés par des tiers via recherche web et sont étiquetés comme tels. Aucun chiffre n'a été écrit de mémoire ; là où je n'ai pas trouvé, j'écris « non trouvé ».

3. **`knowledge/api_pricing.yaml` est à zéro et `releve_le: null`.** `run_preflight.py` renvoie NO‑GO structurel. **Aucun coût réel n'existe encore dans ce système.** Tout ce qui suit en partie B est un modèle conditionnel, pas une facture.

---

# PARTIE A — CONFORMITÉ

## A.0 Ce que le système fait réellement (vérifié dans le code, base de l'analyse)

| Traitement | Module | Donnée personnelle ? |
|---|---|---|
| Requêtes SERP → URL + titre d'entreprise | `diagnostic/discovery.py` | Non (données d'entreprise) |
| Fetch du site public : https, viewport, meta, logo, formulaire, copyright, liens sociaux | `collectors/website.py` | Non en principe — **mais le HTML fetché peut contenir des données de personnes physiques** (page « équipe ») |
| Google Places : verified, photos, note, nb avis, réponses aux avis | `collectors/gbp.py`, `collectors/reviews.py` | Données d'établissement ; les avis contiennent des données de tiers |
| Apollo `/v1/people/search` → **un** décideur | `diagnostic/enrichment.py` | **Oui — cœur du sujet** |
| Rédaction du mini‑audit + accroche par LLM | `diagnostic/synthesis.py` | Contenu généré par IA → AI Act |
| Export CSV/JSONL 10 colonnes | `run_export.py` + `knowledge/export_kemana.yaml` | Oui (nom, titre, email) |

**Le point de conformité critique est un seul appel : Apollo.** Le reste de la chaîne traite majoritairement des données d'entreprise.

**Ce qui est déjà bon, et qui est rare** (vérifié) :
- `Contact` avec `extra="forbid"` et 6 champs — minimisation RGPD *par construction du schéma*, pas par discipline.
- Zéro scraping LinkedIn/Facebook : `contact_linkedin` est stocké comme référence, jamais comme cible de collecte ; `domaines_exclus` de l'ICP écarte `linkedin.com` et `facebook.com` en amont.
- `opt_out: true` → exclusion absolue de l'export, sans exception.
- Une seule requête par cible, User‑Agent honnête et identifiant (`DiagnosticMarque/0.1 (+prospection responsable ; contact@exemple.com)`), timeout, cache disque hors vault.
- J6 non activable par double verrou.

---

## A.1 Quelle base légale pour collecter un email professionnel nominatif sans consentement ?

### France / UE — **intérêt légitime, art. 6.1.f RGPD**, sous conditions

La CNIL admet que la prospection vers des professionnels peut reposer sur l'intérêt légitime **lorsque l'objet de la sollicitation est en rapport avec la profession de la personne contactée**. Une adresse email professionnelle nominative (`prenom.nom@entreprise.fr`) **reste une donnée personnelle** : elle identifie une personne physique. Une adresse fonctionnelle (`info@`, `contact@`) n'en est pas une — c'est une distinction opérationnelle à encoder.

L'intérêt légitime n'est pas une case à cocher : il exige le test en trois temps (intérêt légitime réel / nécessité / mise en balance avec les droits de la personne), **documenté**, et il tombe si la collecte dépasse les **attentes raisonnables** de la personne — c'est exactement le motif de la sanction Kaspr (voir A.3).

> ⚠️ Distinction à ne jamais confondre : **la base légale de la COLLECTE (art. 6 RGPD) et la règle d'ENVOI (ePrivacy / art. L34‑5 CPCE) sont deux régimes distincts.** Le système actuel ne fait que collecter. La règle d'envoi B2B (dérogation à l'opt‑in si le message est en rapport avec la fonction, avec information et droit d'opposition) ne concerne que J6, qui n'existe pas.

### Québec — deux lois qui se superposent

- **LPRPDE (fédérale), art. 4.01** : la loi **ne s'applique pas** aux « coordonnées d'affaires » (nom, titre, adresse, téléphone, courriel professionnels) collectées, utilisées ou communiquées **uniquement** pour communiquer avec la personne dans le cadre de son emploi ou de sa profession. *(source : OPC — voir A.6.)* Le mot « uniquement » est le verrou : dès que la donnée sert à autre chose (scoring d'une personne, revente, enrichissement croisé), l'exception tombe. **Le système est aujourd'hui du bon côté** : `Contact` ne porte pas de scoring personnel — le score est celui de l'entreprise.
- **Loi 25 / LPRPSP (Québec)** : régime de consentement plus strict, avec une exclusion analogue pour les renseignements relatifs à l'exercice de fonctions au sein d'une entreprise. **NON VÉRIFIÉ dans cette session** — à faire confirmer sur le texte (art. 1 LPRPSP) par le juriste. Ne pas s'appuyer dessus sans vérification.
- **CASL** régit l'envoi, pas la collecte (voir A.6).

### Suisse — la question ne se pose pas dans les mêmes termes

Depuis le 1er septembre 2023, **la nLPD ne protège plus les personnes morales** — seules les personnes physiques (VÉRIFIÉ par sources multiples). Et le droit suisse n'exige pas de « base légale » pour un traitement par un privé : le traitement est licite sauf atteinte illicite à la personnalité, justifiable notamment par un intérêt prépondérant. *Cette dernière construction (art. 30/31 LPD) n'a PAS été sourcée dans cette session — à faire confirmer.*
En revanche l'**art. 3 al. 1 let. o LCD** mord fort sur l'ENVOI : voir A.6.

### Règle d'ingénierie A.1
> Ajouter à `FicheProspect` un champ `base_legale: Literal["interet_legitime","coordonnees_affaires","consentement"] | None` renseigné par `run_discovery.py` **depuis l'ICP** (donc `icp/*.yaml` porte la base légale du marché). Une fiche sans base légale renseignée ne doit pas franchir la porte humaine.

---

## A.2 Obligations d'information (art. 14 RGPD, collecte indirecte) — **le système ne les remplit pas**

C'est le principal écart de conformité identifié, et il est structurel.

**Ce qui est exigé** (art. 14 RGPD) : quand les données ne sont pas collectées auprès de la personne — c'est exactement le cas d'Apollo — le responsable doit informer la personne (identité, finalités, base légale, catégories de données, **la source d'où proviennent les données** — art. 14.2.f, destinataires, durée, droits, droit d'opposition). Délai : **dans un délai raisonnable, au maximum un mois**, ou **au plus tard lors de la première communication** si les données servent à communiquer avec la personne.

**Ce que fait le système** (vérifié) :
- Aucun module n'envoie d'information aux personnes. `run_export.py` est en lecture seule, sans réseau. J6 n'existe pas.
- `contact_email_source` existe et est exporté (colonne « Source email »). ⚠️ **Nuance importante** : `CLAUDE.md` le décrit comme « piste d'audit RGPD », mais son contenu réel est le **statut de vérification Apollo** (`verified`, `guessed`…) — c'est un indicateur de qualité, **pas la source de collecte au sens de l'art. 14.2.f**. Le champ est utile, il ne répond pas à l'obligation.
- **Aucune durée de conservation, aucune purge** : `grep` sur `vault_io.py` / `vault_schema.py` ne remonte rien (`conservation|purge|retention|ttl`). Violation potentielle de l'art. 5.1.e à terme.
- Pas de registre des traitements (art. 30) dans le dépôt.

**Ce qui doit être fait (exigences implémentables) :**

| # | Exigence | Où |
|---|---|---|
| 1 | Renommer/dédoubler : `contact_email_source` (qualité Apollo) **+** nouveau `contact_source_collecte` (`"apollo:people_search"`) et `contact_date_collecte` | `vault_schema.py` |
| 2 | Nouveau champ `information_art14_transmise_le: date \| None` | `vault_schema.py` |
| 3 | Le gabarit du **premier** message J6 porte le bloc d'information art. 14 complet, y compris la source | templates J6 |
| 4 | Durée de conservation + purge : `duree_conservation_mois` dans l'ICP, tâche de purge des fiches `decouvert` non validées | `vault_io.py` + nouveau nœud DAG |
| 5 | `opt_out_source` + `opt_out_date` (prouver *quand* et *par quel canal* l'opposition a été exercée) | `vault_schema.py` |
| 6 | Registre des traitements art. 30, généré depuis les ICP + le DAG | `docs/conformite/` |

---

## A.3 Le scraping d'un site public est‑il licite pour un usage commercial ?

**Réponse courte : « public » ≠ « libre d'usage ». Il n'existe aucune exception « donnée publique » en RGPD.**

**Le précédent qui fait jurisprudence pratique — KASPR, 240 000 €, CNIL, 5 décembre 2024** (VÉRIFIÉ : CNIL + EDPB). Base de 160 M de contacts constituée par extraction depuis LinkedIn. Les griefs retenus, transposés en règles d'ingénierie :

| Grief CNIL | Règle d'ingénierie | État du projet |
|---|---|---|
| Collecte de coordonnées que les utilisateurs avaient **explicitement masquées** → dépasse les **attentes raisonnables** | Ne jamais contourner un choix de visibilité. Ne jamais dériver un email masqué. | ✅ Conforme : zéro scraping LinkedIn, données personnes via API fournisseur uniquement |
| **Défaut d'information** des personnes (aucune jusqu'en 2022, puis en anglais seulement) | Information dans la langue du marché ciblé (fr‑CA, fr‑CH, fr‑FR) | ❌ Non traité (cf. A.2) |
| Atteinte au droit d'accès | Procédure d'accès outillée sur le vault | ❌ Non traité |

**Conditions cumulatives pour qu'un fetch de site public reste défendable** :
1. Pas de contournement de mesure technique ni de choix de visibilité ;
2. Respect des CGU du site **et de `robots.txt`** ;
3. Minimisation stricte : ne collecter que les signaux nécessaires au scoring ;
4. Aucune donnée sensible, aucune donnée de personne physique non nécessaire ;
5. Information + droit d'opposition effectif ;
6. Politesse technique (fréquence, UA identifiant, timeout).

**Écart identifié — `robots.txt` n'est jamais consulté.** `grep -rn "robots" --include=*.py .` ne retourne **rien**. `website.py` fait `requests.get` sur la page d'accueil puis, le cas échéant, sur `sitemap.xml`, sans vérifier `robots.txt`. Ce n'est pas illégal en soi, mais c'est le premier argument qu'un contradicteur soulèvera, et c'est trivial à corriger.

> **Exigence A.3** : ajouter dans `website.py` une vérification `robots.txt` avant tout fetch (via `api_io`, comme tout le reste — donc `urllib.robotparser` alimenté par un `api_io.call("http","get",…)`, jamais un accès réseau direct, sous peine de casser l'invariant du bus testé par AST walk). Journaliser le verdict. Un refus `robots.txt` → collecteur en échec propre via `safe_collect`, pas d'exception.

**Second écart, plus subtil** : `reviews.py` récupère `repond_aux_avis`. Les avis Google contiennent des données de **tiers** (les auteurs d'avis), qui n'ont aucun lien avec le prospect. Vérifier que seul l'agrégat (note, compte, booléen de réponse) est persisté et qu'aucun texte d'avis ni auteur n'entre dans le vault. Le cache brut reste hors vault (contrainte G9) — c'est le bon design, à ne pas relâcher.

---

## A.4 Fournisseur hors UE = transfert international ?

**Oui, et le système en cumule quatre.** SerpAPI, Apollo, Google Places et Anthropic sont des entités américaines. Chaque appel `api_io.call()` vers ces fournisseurs qui embarque une donnée personnelle est un transfert au sens du chapitre V RGPD.

Précision utile pour cadrer le risque : **la majorité des appels ne transportent pas de données personnelles**. La requête SERP est `"installateur thermopompe Sherbrooke"`. L'appel Places est `"{nom} {région}"`. L'appel `website` est une URL publique. **Deux flux seulement sont concernés** :
- **Apollo** — flux sortant : un nom de domaine ; flux **entrant** : nom, titre, email d'une personne physique. C'est le transfert principal.
- **Anthropic** — le prompt de `synthesis.py` contient le nom de l'entreprise et ses failles. Vérifier qu'aucun `contact_nom`/`contact_email` n'y entre : le prompt est construit depuis `company`, `scores`, `gaps`, `knowledge` — pas depuis `Contact`. ✅ Bon design, à protéger par un test.

**Mécanismes exigibles par marché :**

| Marché | Exigence | Statut |
|---|---|---|
| **UE/FR** | Décision d'adéquation (EU‑US Data Privacy Framework si le fournisseur est certifié) **ou** clauses contractuelles types + analyse d'impact du transfert (TIA). *Le statut juridique actuel du DPF n'a pas été vérifié dans cette session — à confirmer, il fait l'objet de contestations.* | À faire |
| **Québec** | **EFVP (évaluation des facteurs relatifs à la vie privée) obligatoire AVANT toute communication hors Québec** (art. 17 LPRPSP), **plus** information à la personne au moment de la collecte que ses données peuvent être communiquées hors Québec (art. 8 al. 2). En vigueur depuis septembre 2023. (VÉRIFIÉ par sources juridiques concordantes.) | À faire — **bloquant pour le marché de départ** |
| **Suisse** | Équivalent nLPD (liste des États adéquats du Conseil fédéral, sinon CCT/garanties reconnues par le PFPDT). **NON VÉRIFIÉ dans cette session.** | À faire |

> ⚠️ **Point non‑évident et bloquant** : le Québec est le **premier** marché de la séquence, et l'EFVP transfert est une **pré‑condition documentaire**, pas une case à cocher a posteriori. Elle doit exister avant le premier appel Apollo réel.

**Exigence A.4** : ajouter un contrôle `run_preflight.py` — `transferts_documentes` — qui échoue si, pour l'ICP visé, il n'existe pas de fichier `compliance/<marche>.yaml` déclarant, par fournisseur, le mécanisme de transfert et la date de l'EFVP/TIA. Cela s'inscrit exactement dans le palier 2 déjà prévu par l'ADR 0001 (« conformité‑par‑donnée »), et respecte l'invariant « la conformité est une donnée, pas du code ».

---

## A.5 Clauses à exiger dans un DPA (fournisseur d'enrichissement)

Par ordre d'importance décroissante pour **ce** cas d'usage :

1. **Garantie de licéité de la source** — le fournisseur garantit qu'il dispose d'une base légale, qu'il n'obtient pas ses données par contournement d'un paramètre de visibilité, et qu'il **a informé les personnes** (art. 14). C'est la clause n°1 : après Kaspr, l'ignorance de la provenance n'est pas une défense. Exiger une description écrite des sources.
2. **Qualification des rôles** — sous‑traitant ou responsable conjoint ? Un fournisseur d'enrichissement qui constitue sa propre base est **responsable de traitement** pour cette base, et le client est responsable pour son usage. Un DPA « sous‑traitance » mal qualifié ne protège pas.
3. **Relais des droits en amont** — quand une personne s'oppose auprès de vous, le fournisseur s'engage à propager l'opposition à sa base (sinon le prospect réapparaît au run suivant). ➜ Contrepartie technique : votre `opt_out: true` doit alimenter une **liste de suppression persistante hors vault**, testée en amont de `PersonEnrichment`, sinon la ré‑exécution idempotente réintroduit un contact opposé.
4. **Localisation et transferts** — pays d'hébergement et de support, CCT (module 2 ou 3), TIA, sous‑traitants ultérieurs listés + droit d'opposition à tout ajout.
5. **Interdiction d'usage secondaire** — le fournisseur ne peut ni entraîner de modèle, ni enrichir sa base, ni établir de statistiques commercialisables à partir de vos requêtes. *(Applicable aussi au fournisseur SERP : vos requêtes révèlent votre stratégie de ciblage.)*
6. **Notification de violation** — délai exprimé en heures, pas « sans délai indu ».
7. **Suppression/restitution** en fin de contrat, avec attestation.
8. **Audit** — a minima documentaire annuel, certifications à jour.
9. **Assistance** aux art. 32 à 36 (sécurité, AIPD, notifications).
10. **Indemnisation** pour sanction résultant d'un défaut de licéité de la source.

---

## A.6 Le volet ENVOI (J6) — les trois régimes ne convergent pas

Non activable aujourd'hui, mais c'est **ici** que les trois marchés divergent le plus, et cela conditionne l'architecture de J6.

| | Québec (CASL) | Suisse (art. 3 al. 1 let. o LCD) | France/UE (ePrivacy B2B) |
|---|---|---|---|
| Régime | Opt‑in avec **consentement tacite** possible | **Opt‑in explicite** | Dérogation B2B à l'opt‑in |
| Voie praticable | Adresse **publiée bien en vue**, sans mention de refus des messages non sollicités, **et** message en rapport avec les fonctions ou l'entreprise (par. 10(9)b) | Consentement préalable exprès requis pour l'envoi de masse | Message en rapport avec la fonction + information + opposition |
| Émetteur | Doit être identifié, mécanisme d'exclusion fonctionnel | Expéditeur identifiable, adresse de contact valable, refus **simple et gratuit** | Identité claire + lien de désinscription fonctionnel (CNIL : recommande un clic) |
| Sanction | Administrative (CRTC) | **Pénale** (concurrence déloyale) | Administrative (CNIL) |

*(CASL et art. 3 LCD : VÉRIFIÉS par sources concordantes, dont CRTC et OFCOM/BAKOM. Régime français : rapporté par sources spécialisées reprenant la doctrine CNIL ; la page CNIL n'a pas été accessible directement.)*

**Conséquence d'architecture, non‑évidente :**
> Un email Apollo `guessed` (deviné) **ne peut pas** fonder un consentement tacite CASL, qui exige une adresse **publiée par la personne**. Et il ne satisfait certainement pas l'opt‑in explicite suisse. **`contact_email_source` n'est donc pas seulement un indicateur de qualité : c'est un discriminant juridique.** J6 doit refuser d'envoyer à tout contact dont `contact_email_source != "verified"` sur le marché Québec, et refuser tout envoi de masse en Suisse sans consentement préalable enregistré.
>
> Exigence : encoder cette matrice dans `compliance/<marche>.yaml` (`sources_email_autorisees`, `regime_envoi`), et faire du nœud « Conformité » un nœud **bloquant** en amont d'`export` et d'`outreach` — c'est déjà le palier 2 de l'ADR 0001, cette analyse en confirme la nécessité et en fournit le contenu.

---

## A.7 AI Act art. 50 — **applicable exactement aujourd'hui, 2 août 2026**

Les obligations de transparence de l'art. 50 s'appliquent **à compter du 2 août 2026** (VÉRIFIÉ, sources multiples concordantes ; la Commission a publié ses lignes directrices le 20 juillet 2026, et un accord « AI Omnibus » de mai 2026 accorde jusqu'au 2 décembre 2026 aux systèmes d'IA générative déjà sur le marché pour le marquage lisible par machine de l'art. 50(2) — **relayé par un tiers, à confirmer sur le texte définitif**).

**Ce que cela vise dans ce projet** : `synthesis.py` génère le **mini‑audit** et l'**accroche**. Ce sont des textes synthétiques produits par IA. Dès qu'ils sont diffusés à une personne dans l'UE (donc au marché France, et à la Suisse romande dans la mesure où des destinataires UE sont touchés), l'obligation de transparence s'active pour le déployeur.

**État du système (vérifié)** :
- `grep` sur `serializers.py` / `synthesis.py` : **aucune mention « généré par IA »** nulle part.
- Les rapports `30-Diagnostics/*.md` ne portent aucun marquage.
- ✅ **Bon point non intentionnel** : l'export Kemana (`export_kemana.yaml`, 10 colonnes) ne contient **pas** `accroche` — seulement `signal_chaud`, qui est calculé **déterministement** dans `serializers.py` depuis `diag.failles`. **Le CSV de sortie ne transporte donc aucun texte généré par LLM.** C'est une réduction d'exposition réelle, obtenue par la règle « `signal_chaud` dérivé, pas dans Diagnostic ».
- ⚠️ Le risque est donc **humain** : l'opératrice lit l'audit LLM dans Obsidian et le recopie dans un email. Le marquage doit être porté **là où elle le lit**.

**Exigences A.7 :**
1. `serializers.py::diagnostic_to_rapport_md` ajoute un en‑tête visible : *« Mini‑audit rédigé avec assistance IA (modèle : `<modele>`, profil : `<profil>`) à partir de signaux collectés automatiquement. Vérification humaine requise avant diffusion. »* — les champs `modele` et `profil` existent déjà dans `LedgerEntry`, la donnée est disponible.
2. Le repli déterministe (sans clé Anthropic) **ne doit pas** porter cette mention : ce n'est pas de l'IA générative. La mention doit être conditionnée à l'appel LLM effectif, pas au chemin de code.
3. Un futur gabarit J6 pour le marché UE porte la mention de transparence dans le corps du message.
4. `run_preflight.py` : nouveau contrôle `marquage_ia_present` (AST/regex sur le gabarit de rapport). Non bloquant tant que J6 est fermé, bloquant ensuite.

---

## A.8 Récapitulatif conformité — ce qu'il faut journaliser, prouver, et ne pas stocker

**JOURNALISER** (par contact, dans le frontmatter — le bus vault garantit l'atomicité et le journal append‑only, donc l'infrastructure de preuve existe déjà) :
`contact_source_collecte` · `contact_date_collecte` · `contact_email_source` (verified/guessed) · `base_legale` · `icp_id` (déjà) · `information_art14_transmise_le` · `opt_out` + `opt_out_date` + `opt_out_source` · référence de l'EFVP/TIA du marché.

**POUVOIR PROUVER** — le triptyque que réclamera une autorité :
1. **D'où vient cette adresse** → `runs.log` (écriture vault) ⇄ `api_usage.log` (appel fournisseur) corrélés **par intervalle temporel** via le manifeste `.cache/orchestrator/<run_id>.json`. **Ce mécanisme existe déjà et il est exactement ce qu'il faut.** Il n'a pas été conçu pour ça, mais c'est votre meilleur atout de conformité.
2. **Sur quelle base et avec quelle information** → `base_legale` + `information_art14_transmise_le`.
3. **Que l'opposition a été honorée** → `opt_out` + liste de suppression persistante testée **avant** l'enrichissement, pas seulement à l'export.

**NE PAS STOCKER** : téléphone personnel, adresse privée, données de tiers issues des avis Google, texte brut des pages scrapées dans le vault (déjà garanti — cache hors vault, contrainte G9), photo, tout attribut personnel non nécessaire au scoring (le score porte sur l'**entreprise**, jamais sur la personne — ne jamais faire glisser le scoring vers l'individu, cela ferait basculer le traitement vers un profilage et ferait tomber l'exception « coordonnées d'affaires » de la LPRPDE).

---

# PARTIE B — FINOPS : MODÈLE DE COÛT PAR PROSPECT QUALIFIÉ

## B.0 Rappel non négociable

`knowledge/api_pricing.yaml` : **tous les prix et budgets à `0`, `releve_le: null`**. `run_preflight.py` → NO‑GO (sortie 1). **Aucun coût affiché par ce système aujourd'hui n'est engageant, et aucun pourcentage d'économie n'est mesurable.** Tout ce qui suit est un modèle paramétrable destiné à être *rempli*, pas un résultat.

## B.1 Décompte des appels par fiche — **VÉRIFIÉ dans le code**

| Poste | Appels facturés | Preuve |
|---|---|---|
| **SERP** | `Q = |gabarits| × |localités|` **par run**, `num = max_resultats_par_requete` | `icp_schema.py::generer_requetes` = produit cartésien ; `discovery.py::_serp_search` |
| | persona1‑quebec : **3 × 6 = 18 requêtes**, 10 résultats → **180 résultats bruts max** | `icp/persona1-quebec.yaml` |
| **Places** | **2 par fiche** : 1 `text_search` + 1 `place_details` | `gbp.py` et `reviews.py` partagent `cache_key="places:{query}"` → le 2ᵉ `text_search` est un **cache‑hit à coût 0** |
| **Apollo** | **1 par domaine** (`cache_key="apollo:{domaine}"`) | `enrichment.py` |
| **HTTP** | 1 GET accueil **+ ≤1** GET `sitemap.xml` | `website.py::_fetch` + `_try_sitemap` — coût ~0, métré |
| **LLM** | **0** sans clé (repli déterministe) ; sinon **1**, ou **2** si la QA échoue **et** que l'escalade change réellement de modèle | `synthesis.py` : boucle `for quality_check_echoue in (False, True)` avec garde `if modele in modele_vu: break` |

**Bornes de frugalité appliquées avant émission — VÉRIFIÉ** (`knowledge/greenit.yaml`) : contexte tronqué à 4 000 car., prompt plafonné à 8 000 car., `max_tokens_sortie = 600` (écrase le profil), cache disque 30 j, `activer_prompt_caching: false`.

### ⚠️ Deux pièges FinOps trouvés dans le code

**1. Le plafond `max_enrichissements` ne plafonne pas les appels Apollo.**
`enrichment.py` incrémente `_nb_enrichissements` **uniquement si un contact est effectivement extrait**. Un appel qui ne renvoie aucun titre correspondant à `titres_cibles` consomme un appel fournisseur **sans consommer le quota interne**. Avec `max_enrichissements: 25` et un taux de correspondance de 40 %, on émet ~62 appels pour 25 contacts. **Le budget `api_io` est le seul vrai garde‑fou — d'où l'importance de le renseigner.**

**2. Le zéro silencieux.** `api_schema.py::compute_cout` retourne `0.0` sur `KeyError` (fournisseur ou endpoint absent de la grille). Un endpoint mal orthographié dans le YAML produit donc un coût de 0 **sans aucun signal**. Recommandation : logger un `WARN` dans ce cas (sans lever — le principe « ne jamais bloquer le pipeline » reste bon), et ajouter un contrôle préflight `tous_endpoints_tarifes` qui vérifie que chaque couple (fournisseur, endpoint) réellement appelé par le code a un prix non nul dans le YAML.

## B.2 La formule

```
C_fiche = C_serp + C_apollo + C_places + C_llm

C_serp   = p_serp / (n_res × ρ)
C_apollo = α × p_apollo
C_places = p_text_search + p_place_details          [ = 0 si cache-hit inter-runs, TTL 30 j ]
C_llm    = ε × (T_in × p_in + T_out × p_out)
```

| Paramètre | Valeur | Statut |
|---|---|---|
| `n_res` | 10 | **VÉRIFIÉ** (`max_resultats_par_requete`) |
| `ρ` | taux de survie filtres + dédup ∈ ]0;1] | **NON MESURÉ** — impossible sans clé. À instrumenter dès le premier `--dry-run` |
| `α` | ≈ 1 appel/fiche, **non borné** (cf. piège 1) | **VÉRIFIÉ** |
| `ε` | 1 ou 2 | **VÉRIFIÉ** |
| `T_out` | ≤ **600 tokens** | **VÉRIFIÉ** (borne dure) |
| `T_in` | ≤ ~2 300 tokens (dérivé de 8 000 car. FR ÷ ~3,5) | **ESTIMATION** — calibrer avec `client.messages.count_tokens()` sur 20 prompts réels |

## B.3 Prix — statut de chaque chiffre

### ✅ Anthropic — **VÉRIFIÉ sur page officielle**
Source : `https://platform.claude.com/docs/en/about-claude/pricing` — relevé le **2026‑08‑02**.

| Modèle (ceux routés par `greenit.yaml`) | Input | Output | Écriture cache 5 min | Lecture cache | Batch in/out |
|---|---|---|---|---|---|
| **Claude Haiku 4.5** (profils `frugal` + `standard`) | **$1 / MTok** | **$5 / MTok** | $1.25 | $0.10 | $0.50 / $2.50 |
| **Claude Sonnet 4.5** (profil `qualite`) | **$3 / MTok** | **$15 / MTok** | $3.75 | $0.30 | $1.50 / $7.50 |

Également vérifié : Batch API = **−50 %** sur input et output ; multiplicateurs cache = **1,25×** (5 min), **2×** (1 h), **0,1×** (lecture).
ℹ️ Note d'exploitation : `claude-sonnet-4-5` est classé **« legacy »** dans la doc officielle (toujours actif, mêmes tarifs). Le profil `qualite` de `greenit.yaml` devra migrer à terme — c'est une édition YAML, zéro code, exactement comme prévu par l'invariant GreenIT.

**Coût LLM par fiche, borne haute (les seuls chiffres pleinement sourcés de cette étude) :**
- Haiku seul : `2 300 × 1e‑6 + 600 × 5e‑6` = **$0,0053**
- Escalade (Haiku raté + Sonnet) : `0,0053 + (2 300 × 3e‑6 + 600 × 15e‑6)` = **$0,0212**
> **Le LLM coûte entre 0,5 et 2,1 cents par fiche.** Il n'est pas le problème. Le chantier GreenIT a raison sur le principe (frugalité, routage déterministe) et n'a **aucun** levier économique significatif ici. Le dire est plus honnête que de le vendre.

### ⚠️ Google Places — **RAPPORTÉ PAR UN TIERS, non vérifié sur page officielle** (proxy → 403 sur `developers.google.com` et `mapsplatform.google.com`)
- Text Search **Pro** : ~**$32 / 1 000** ; **Enterprise** : ~**$35 / 1 000** ; **Enterprise + Atmosphere** : ~**$40 / 1 000**.
- Paliers gratuits (changement de mars 2025 remplaçant le crédit de 200 $) : **10 000** appels/mois par SKU Essentials, **5 000** Pro, **1 000** Enterprise.
- **Place Details : prix NON TROUVÉ dans cette session.** Hypothèse de travail explicite ci‑dessous : `p_pd = p_ts`.

> 🎯 **Le point FinOps le plus important de toute l'étude.** Le SKU facturé dépend des **champs demandés**, et `reviews.py` demande la note, le nombre d'avis et les réponses aux avis → cela relève très probablement d'**Enterprise** ou **Enterprise + Atmosphere**, **pas** de Pro. Conséquence : le palier gratuit tombe de 5 000 à **1 000** appels/mois et le prix unitaire monte. **Une ligne de code (la liste `fields`) détermine votre facture Places et votre franchise mensuelle.** À vérifier en priorité absolue avant tout run réel.

### ⚠️ SerpAPI — **RAPPORTÉ, sources divergentes** (proxy → 403 sur `serpapi.com`)
Gratuit **250 recherches/mois** ; Developer **$75 / 5 000** (= $0,015/req) ; Production **$150 / 15 000** (= $0,010) ; **$275 / 30 000** (≈ $0,0092). Crédits **non reportables** d'un mois sur l'autre. Une source mentionne aussi **$25 / 1 000** ($0,025) — **incohérence non tranchée** : retenir une fourchette **$0,009 – $0,025 / requête**, ne pas fixer une valeur.

### 💡 Serper.dev — alternative SERP, **RAPPORTÉ**
**$50 / 50 000** crédits (= **$0,0010/req**), jusqu'à $0,00030/req sur les gros packs ; **2 500 requêtes d'essai** ; crédits valables 6 mois ; **>10 résultats = 2 crédits** (l'ICP demande `num=10` → 1 crédit).
➜ **Un ordre de grandeur (10× à 25×) moins cher que SerpAPI** pour ce cas d'usage. Coût de bascule : `discovery.py::_serp_search` lit `data["organic_results"]`, `link`, `title` (format SerpAPI) ; Serper renvoie `organic` avec `link`/`title`. **C'est un adaptateur de ~10 lignes dans une seule méthode**, l'architecture enfichable rend la bascule triviale. À évaluer avant de signer un abonnement.

### ⚠️ Apollo — **prix par crédit NON PUBLIÉ / NON TROUVÉ**
Rapporté : Basic **$49–59**/user/mois, Professional **$79–99**, Organization **$119–149** (min. 3 sièges) ; crédits d'export **1 000 / 2 000 / 4 000** par mois. **Le Basic n'inclut pas l'accès API** → Professional est le plancher praticable.
Prix par crédit **dérivé** (donc estimation) : ~**$0,040** (Pro) à ~**$0,030** (Org).
**Deux points explicitement non vérifiés, à confirmer avant de budgéter :**
1. Est‑ce que `/v1/people/search` consomme un crédit **d'export**, ou un compteur distinct ? Non trouvé.
2. `enrichment.py` appelle `https://api.apollo.io/v1/people/search`. Vérifier que ce chemin d'API est toujours servi — le versionnage des API Apollo n'a pas pu être confirmé dans cette session.

## B.4 Scénarios de volume

Hypothèses communes : ρ = 0,3 (**NON MESURÉ**, à remplacer par la vraie valeur au premier dry‑run) ; 2 appels Places/fiche ; 1 appel Apollo/fiche ; ε = 1 ; T_in = 2 300, T_out = 600.

### 🔴 Découverte structurelle préalable : le plafond de l'ICP

`Q = 3 gabarits × 6 localités = 18 requêtes × 10 résultats = **180 résultats bruts, plafond absolu**`. Après filtres et dédup, à ρ = 0,3 → **~54 fiches uniques atteignables au maximum avec l'ICP actuel**. Et **relancer le même ICP ne produit rien** : `cache_key = requete` avec TTL 30 j → cache‑hit, coût 0, **zéro nouvelle fiche**.

> **Le volume n'est pas limité par le budget, il est limité par la taille de l'ICP.**
> - 100 fiches/mois → ~**33 requêtes** → ICP × ~1,9
> - 500 fiches/mois → ~**167 requêtes** → ICP × ~9
> - 2 000 fiches/mois → ~**667 requêtes** → ICP × **~37** (p. ex. 20 gabarits × 34 localités)
>
> Or il n'existe qu'**un seul ICP** et **une seule rubrique**. **Le régime 2 000/mois n'est pas atteignable aujourd'hui, quel que soit le budget.** C'est une conclusion de capacité, pas de coût — et elle est décisive pour la feuille de route.

### Tableau des volumes (unités, VÉRIFIÉ) et coûts (conditionnels)

| | Pilote 100 | Régime 500/mois | Régime 2 000/mois |
|---|---|---|---|
| Requêtes SERP | ~33 | ~167 | ~667 |
| Appels Places facturés | 200 | 1 000 | 4 000 |
| Appels Apollo | ~100 (jusqu'à ~250, cf. piège 1) | ~500 | ~2 000 |
| Appels LLM | 100–200 | 500–1 000 | 2 000–4 000 |
| **SERP $** | **0** (palier gratuit 250) | **0** (palier gratuit 250) | Developer $75/mois **ou** Serper ≈ **$0,67** |
| **Places $** — hyp. SKU **Pro** (5 000 gratuits) | **0** | **0** | **0** |
| **Places $** — hyp. SKU **Enterprise+Atmo** (1 000 gratuits, $0,040) | **0** | **0** (pile au seuil) | (4 000 − 1 000) × 0,040 = **$120/mois** |
| **LLM $** (Haiku, borne haute) | **$0,53** | **$2,65** | **$10,60** |
| **LLM $** (100 % escalade Sonnet — pire cas) | $2,12 | $10,60 | $42,40 |
| **Apollo $** | abonnement Pro ~$79/mois | ~$79/mois (2 000 crédits) | Org : **3 × $119 = $357/mois** min. |

**Coût par prospect qualifié (calcul conditionnel, prix non vérifiés sauf LLM) :**
- Régime 2 000/mois, **hypothèse haute** (Places Enterprise+Atmo, SerpAPI, Apollo Organization) : `(120 + 42 + 75 + 357) / 2 000` ≈ **$0,30 / fiche**
- Régime 2 000/mois, **hypothèse basse** (Places Pro, Serper, Apollo Pro, Haiku) : `(0 + 10,6 + 0,67 + 79) / 2 000` ≈ **$0,045 / fiche**

### 🎯 Les trois conclusions FinOps

1. **Le système est en régime de coût FIXE, pas variable.** À ces volumes, 85–95 % de la dépense sont des abonnements (Apollo surtout, SerpAPI éventuellement). Le coût marginal d'une fiche supplémentaire est de l'ordre de **1 à 8 cents**. Corollaire brutal : **optimiser le cache, le routage de modèle ou les tokens ne déplace pas l'aiguille.** Ce qui la déplace : le **SKU Places**, le **fournisseur SERP**, et le **palier Apollo**.
2. **Le pilote de 100 prospects peut tourner à coût variable quasi nul** : SERP dans le palier gratuit (250/mois), Places dans le palier gratuit (200 ≪ 1 000), LLM à **$0,53**. La seule dépense réelle est l'abonnement Apollo. Un pilote à ~**$80** tout compris est plausible — sous réserve de vérification des tarifs.
3. **Le goulot est l'ICP, pas le budget.** Élargir `icp/persona1-quebec.yaml` (gabarits × localités) est **gratuit en code** et c'est le seul levier de volume. C'est la meilleure nouvelle de l'étude : le facteur limitant est éditable en YAML.

## B.5 Comment remplir `api_pricing.yaml` — ⚠️ piège d'unité

`compute_cout` calcule `somme(unites[k] × prix[k])` où `unites` porte le **compte brut** (tokens, requêtes, crédits). **`prix_par_unite` est donc un prix PAR UNITÉ INDIVIDUELLE, pas par 1 000, pas par million.** Erreur de facteur 10⁶ garantie si on recopie une page tarifaire telle quelle.

```yaml
releve_le: 2026-08-02   # ← remplir avec la date du VRAI relevé

anthropic:              # ✅ VÉRIFIÉ 2026-08-02 (platform.claude.com/docs/en/about-claude/pricing)
  endpoints:
    messages:
      prix_par_unite:
        input_tokens:              0.000001    # Haiku 4.5 : $1 / MTok
        output_tokens:             0.000005    # Haiku 4.5 : $5 / MTok
        cache_read_input_tokens:   0.0000001   # 0,1×
        cache_creation_input_tokens: 0.00000125 # 1,25× (5 min)
        # ⚠️ Sonnet 4.5 = $3 / $15 par MTok → 0.000003 / 0.000015.
        # La grille actuelle est mono-modèle : si l'escalade `qualite` est
        # activée, le coût Sonnet sera SOUS-ESTIMÉ d'un facteur 3.
        # ➜ Prévoir un endpoint `messages_qualite` ou une grille par modèle.

google_places:          # ⚠️ NON VÉRIFIÉ — confirmer sur la page officielle + le SKU réel
  endpoints:
    text_search:   { prix_par_unite: { requetes: 0.032 } }  # hyp. Pro ; 0.040 si Enterprise+Atmosphere
    place_details: { prix_par_unite: { requetes: 0.032 } }  # ⚠️ prix NON TROUVÉ — hypothèse

serp:                   # ⚠️ NON VÉRIFIÉ — fourchette 0.009 à 0.025 (SerpAPI) / 0.0010 (Serper)
  endpoints:
    search: { prix_par_unite: { requetes: 0.015 } }

apollo:                 # ⚠️ prix/crédit NON PUBLIÉ — valeur DÉRIVÉE d'un abonnement
  endpoints:
    people_enrichment: { prix_par_unite: { credits: 0.0395 } }

budgets:                # bornes de pilote, cohérentes avec le plafond structurel de l'ICP
  serp:   { unites_max: { requetes: 250 } }   # = palier gratuit SerpAPI, borne naturelle
  apollo: { unites_max: { credits: 150 } }    # 100 fiches + marge pour le piège 1
```

> 🔴 **Défaut de modélisation à corriger** : la grille `anthropic.messages` est **mono‑tarif**, alors que le routage GreenIT peut appeler Haiku **ou** Sonnet. Toute escalade vers `qualite` sera facturée au tarif Haiku dans `api_usage.log` → **sous‑estimation d'un facteur 3**. `LedgerEntry` porte déjà le champ `modele` : la correction propre est une grille indexée par modèle, ou un endpoint distinct par profil. À traiter **avant** le premier run avec clé Anthropic, sinon le grand livre ment.

---

# SYNTHÈSE — actions par priorité

**Bloquant avant tout run réel :**
1. Vérifier le **SKU Places réellement facturé** (champs demandés par `gbp.py`/`reviews.py`) — détermine à la fois le prix et la franchise mensuelle.
2. **EFVP transfert hors Québec (art. 17 LPRPSP)** — pré‑condition documentaire du marché de départ.
3. Corriger la grille `anthropic` **par modèle** (sinon le ledger sous‑estime Sonnet d'un facteur 3).
4. Relever les tarifs sur les pages officielles (les miennes sont majoritairement tierces) et dater `releve_le`.

**Haute valeur, faible coût :**
5. Vérification `robots.txt` dans `website.py` (via `api_io`, sans casser l'invariant du bus).
6. Marquage « assistance IA » dans `diagnostic_to_rapport_md` — **AI Act art. 50 applicable depuis aujourd'hui**.
7. Champs de preuve : `contact_source_collecte`, `contact_date_collecte`, `base_legale`, `information_art14_transmise_le`, `opt_out_date`/`opt_out_source`.
8. Liste de suppression persistante **hors vault**, testée **avant** `PersonEnrichment` (sinon l'idempotence réintroduit un opposé).
9. Évaluer Serper.dev (~10–25× moins cher, adaptateur de ~10 lignes).
10. Durée de conservation + purge (aucune aujourd'hui).

**Structurel :**
11. Élargir l'ICP — seul levier de volume, gratuit en code, et facteur limitant réel.
12. `compliance/<marche>.yaml` + nœud « Conformité » bloquant (palier 2 de l'ADR 0001) : cette étude en fournit le contenu (matrice CASL/LCD/ePrivacy, `sources_email_autorisees`, mécanismes de transfert).
13. Contrôles préflight : `tous_endpoints_tarifes`, `transferts_documentes`, `marquage_ia_present`.

**Fichiers concernés :** `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/knowledge/api_pricing.yaml`, `knowledge/greenit.yaml`, `knowledge/export_kemana.yaml`, `icp/persona1-quebec.yaml`, `diagnostic/enrichment.py`, `diagnostic/discovery.py`, `diagnostic/collectors/website.py`, `diagnostic/collectors/reviews.py`, `diagnostic/api_schema.py`, `diagnostic/serializers.py`, `diagnostic/vault_schema.py`, `diagnostic/preflight.py`.

---

## Sources

Officielles (lues directement) :
- [Anthropic — Pricing](https://platform.claude.com/docs/en/about-claude/pricing) · [Anthropic — Models overview](https://platform.claude.com/docs/en/about-claude/models/overview.md)

Autorités / institutions (via recherche web) :
- [CNIL — Data scraping: KASPR fined €240,000](https://www.cnil.fr/en/data-scraping-kaspr-fined-eu240000) · [EDPB — French SA fined KASPR €240 000](https://www.edpb.europa.eu/news/news/2025/data-scraping-french-supervisory-authority-fined-kaspr-eu240-000_en)
- [CNIL — Prospection commerciale par courrier électronique](https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique-sms-mms-et-automate-dappel) *(page inaccessible depuis cet environnement — reprise via sources secondaires)*
- [CRTC — Lignes directrices sur le consentement tacite (LCAP)](https://crtc.gc.ca/fra/com500/guide.htm) · [CRTC — FAQ LCAP](https://crtc.gc.ca/fra/com500/faq500.htm) · [Loi canadienne anti‑pourriel, texte](https://laws-lois.justice.gc.ca/fra/lois/E-1.6/page-2.html)
- [CPVP/OPC — Guidance for businesses doing e‑marketing](https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/r_o_p/canadas-anti-spam-legislation/casl-compliance-help-for-businesses/casl_guide/) · [OPC — Interpretation Bulletin: Personal Information](https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/pipeda-compliance-help/pipeda-interpretation-bulletins/interpretations_02/)
- [CAI Québec — Principaux changements apportés par la Loi 25](https://www.cai.gouv.qc.ca/protection-renseignements-personnels/sujets-et-domaines-dinteret/principaux-changements-loi-25) · [BLG — Transferts hors du Québec](https://www.blg.com/fr/insights/2022/12/cross-border-transfers-of-personal-information-outside-quebec)
- [OFCOM/BAKOM — Quand les envois en masse sont‑ils autorisés ?](https://www.bakom.admin.ch/fr/quand-les-envois-en-masse-sont-ils-autorises) · [PFPDT — Publicité et marketing](https://www.edoeb.admin.ch/edoeb/fr/home/datenschutz/arbeit_wirtschaft/werbung_marketing.html) · [KMU admin — nLPD](https://www.kmu.admin.ch/fr/nouvelle-loi-sur-la-protection-des-donnees-nlpd) · [swissprivacy.law — Prospection commerciale : France et Suisse](https://swissprivacy.law/412/)
- [Commission européenne — Transparency obligations under Article 50 AI Act](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act) · [EU AI Act — Article 50](https://artificialintelligenceact.eu/article/50/) · [EU AI Act — Practical guide to Article 50](https://artificialintelligenceact.eu/transparency-rules-article-50/)

Tarifs rapportés par des tiers (**non vérifiés sur page officielle** — accès proxy refusé) :
- [Google Maps Platform — March 2025 changes](https://developers.google.com/maps/billing-and-pricing/march-2025) · [Google — 10 000 free calls per product](https://mapsplatform.google.com/resources/blog/start-building-today-with-up-to-10-000-monthly-free-calls-per-product/) · [Woosmap — Places API pricing 2026](https://www.woosmap.com/blog/google-places-api-pricing) · [SafeGraph — Places API pricing](https://www.safegraph.com/guides/google-places-api-pricing/)
- [apiserpent — SerpApi pricing explained](https://apiserpent.com/blog/serpapi-pricing-explained) · [apiserpent — SERP API pricing comparison](https://apiserpent.com/blog/serp-api-pricing-comparison) · [costbench — SerpApi plans](https://costbench.com/software/web-scraping/serpapi/)
- [Serper.dev](https://serper.dev/) · [coldiq — Serper pricing 2026](https://coldiq.com/blog/serper-pricing) · [apiserpent — Serper credits explained](https://apiserpent.com/blog/serper-pricing-credits-explained)
- [Warmly — Apollo pricing 2026](https://www.warmly.ai/p/blog/apollo-pricing) · [Saleshandy — Apollo.io pricing](https://www.saleshandy.com/blog/apolloio-pricing/) · [G2 — Apollo.io pricing](https://www.g2.com/products/apollo-io/pricing)

---


<a id="s8"></a>

## 8. Challenge d'architecture (aval de revue REFUSÉ — voir §10)


J'ai lu le code plutôt que les rapports. Cinq faits vérifiés cette session commandent tout le reste.

**Vérification n°1 — le défaut A1 est pire que décrit.** Site parfait sur tous les signaux observables, sans clé Places :

```
SCORES: site_web 100 | presence_locale 0 | avis 0 | seo_local 100 | identite_visuelle 100 | global 55.0
GAPS:  haute | presence_locale | "Fiche Google Business non vérifiée (à confirmer en J3)"
       haute | presence_locale | "Pas de photos sur la fiche locale (à confirmer en J3)"
       haute | avis            | "Moins de 10 avis — preuve sociale faible (à confirmer en J3)"
       haute | avis            | "Note moyenne sous 4,0 (à confirmer en J3)"
SIGNAL_CHAUD -> "Fiche Google Business non vérifiée (à confirmer en J3)"
```
Le meilleur prospect possible plafonne à 55/100 et repart avec quatre affirmations fausses, dont une en tête d'export. Ce n'est pas un biais, c'est une fabrication.

**Vérification n°2 — le TTL de cache n'existe pas.** `knowledge/greenit.yaml:106` déclare `cache_ttl_jours: 30`, `greenit.py:61` le lit. `api_io._lire_cache` (l. 218-224) ne vérifie que `path.exists()`. **Aucune expiration n'est implémentée.** Trois conséquences : le levier GreenIT n°3 est inerte ; rejouer le même ICP ne produira jamais rien (cache éternel) ; et la limite contractuelle de 30 jours des Maps Platform Terms n'est pas techniquement tenue.

**Vérification n°3 — `max_enrichissements` ne plafonne pas les appels Apollo.** `enrichment.py:78-81` : `_nb_enrichissements` n'est incrémenté que si un contact est extrait. Un appel sans titre correspondant consomme le fournisseur sans consommer le quota.

**Vérification n°4 — l'export ne trie pas du tout.** `export.py:62-78` : `collect_fiches_exportables` retourne l'ordre de `vault_io.query()`. Le COO dit « trie sur score_global » — c'est pire, il n'y a aucun tri.

**Vérification n°5 — `_seo_text` fuit.** `website.py:94` place 2 000 caractères de la page du prospect dans `signaux`, donc dans `Diagnostic.signaux`, donc dans `run_diagnostic --json`. C'est du HTML brut hors du chemin prévu par G9.

---

# A. Le diagnostic d'architecture

Le système collecte correctement, écrit correctement, ordonnance correctement. **Il échoue en un seul point : il ne sait pas distinguer « j'ai observé une faille » de « je n'ai rien observé ».** Tout le reste — biais SERP, mono-axe, export pauvre — est une conséquence ou une aggravation de ça.

Corollaire d'architecture : le vrai actif est la couche de collecte *gratuite et déterministe*, et elle est sous-développée. Cinq collecteurs, dont deux produisent un booléen chacun, dont un (`social`) n'est câblé à aucune règle de la rubrique. Pendant ce temps 45 points sur 100 dépendent d'une clé absente. **Le déséquilibre est là : trop de score adossé au palier 1 payant, trop peu au palier 0 gratuit.** Toutes mes propositions vont dans ce sens : déplacer le poids du score vers ce qui s'observe sans clé.

---

# B. Réponses aux six questions

## B.1 — SERP vs API de lieux : les deux, priorité inversée

**Tranché : Places devient la source PRIMAIRE de découverte, le SERP est RÉTROGRADÉ en collecteur de signal. Aucun des deux n'est supprimé.**

L'argument décisif n'est ni le prix ni le litige Google, c'est l'anti-corrélation : un SERP renvoie ce que Google classe bien ; la consultante vend à ceux qui sont mal classés. Le gabarit `"installateur thermopompe {localite}"` sur-échantillonne mécaniquement le mauvais prospect. Aucun réglage tarifaire ne corrige ça.

Trois arguments secondaires, tous vérifiables dans le code :
- **Forme de donnée.** `icp/persona1-quebec.yaml` consacre 9 lignes à `domaines_exclus` + `exiger_domaine_propre`, et `discovery.py:20-34` 15 lignes de plateformes hébergées. Ces 24 lignes n'existent que pour réparer l'inadéquation de la source. Une API de lieux ne renvoie pas pagesjaunes.ca.
- **Fournisseur déjà câblé.** `google_places` existe dans `api_pricing.yaml:45-52` avec `text_search` / `place_details` / `nearby_search`, et `gbp.py:49` / `reviews.py:89` l'appellent déjà via le bus. Zéro nouvelle clé, zéro nouveau budget, un seul grand livre.
- **Pré-alimentation du score.** `rating` et `userRatingCount` arrivent dès la découverte → les 45 points aujourd'hui fabriqués à zéro deviennent connus **avant** de dépenser le moindre token. C'est un gain GreenIT non spéculatif : on priorise les fiches `decouvert` avant de les diagnostiquer.

**Ce que le SERP garde, et pourquoi ce n'est pas une consolation.** Une fois la découverte assurée par Places, la requête SERP change de nature : « cette entreprise ressort-elle sur `chauffagiste Lévis` ? » n'est plus un moyen de la trouver, c'est **la mesure directe de sa faiblesse SEO locale**, adossée à un fait vérifiable par le prospect en dix secondes. C'est exactement le type de preuve que le CMO réclame. Et c'est aussi ce qui alimente le benchmark de cohorte.

**Réserve que je porte contre les études.** Elles recommandent Places sans traiter le conflit qu'elles signalent par ailleurs : les Maps Platform Terms interdisent la persistance durable de la plupart des champs (`place_id` excepté). Or le vault persiste des fiches Markdown *par conception*. Ma position : **ne persister que `place_id` + des dérivés non reconstituables** (`a_fiche_gbp: bool`, `note_bucket: "4-4.5"`, `avis_bucket: "10-24"`, `repond_aux_avis: bool`), et implémenter le TTL réellement (vérification n°2). Le score n'a besoin que des dérivés ; la valeur brute ne sert à rien après le scoring. C'est une contrainte, pas un obstacle — mais elle doit être dans le design dès le départ, pas rattrapée après.

**OSM : non, sauf en recoupement.** Le champ `website` y est trop inégalement renseigné, et l'URL est l'entrée *obligatoire* de tout J1 (`website.py:54` : pas d'URL → `reachable: False` → tout s'effondre). En revanche, « absent d'OSM ET absent de Places » est en soi un signal de présence locale nulle, exploitable commercialement. Usage marginal, pas de priorité.

## B.2 — Apollo : rétrogradé en troisième rang, pas supprimé

**Tranché : cascade déterministe à trois étages, du gratuit vers le payant. Apollo reste câblé mais devient un recours conditionnel.**

Le raisonnement qui compte n'est pas le prix, c'est que **`contact_email_source` n'est pas un indicateur de qualité, c'est un discriminant juridique.** Le consentement tacite CASL repose sur une adresse *publiée bien en vue par la personne* (art. 10(9)b). Un email Apollo `guessed` est déduit par algorithme : il ne fonde rien. Aujourd'hui `enrichment.py:127` le stocke et `export_kemana.yaml:12` l'exporte comme une donnée neutre. Il doit devenir une **grille ordonnée** :

```
site_officiel:<url>#<date>   → CASL/nLPD/RGPD : utilisable, preuve auto-portée
apollo:verified              → utilisable sous réserve d'information art. 14
apollo:guessed | likely      → INUTILISABLE au Québec, à exclure de l'export
(absent)                     → fiche non actionnable
```

Une adresse extraite du site **fournit sa propre preuve** (URL + date + extrait). Une adresse achetée prouve seulement qu'un tiers la détenait — ce n'est pas le même fait juridique. Et une adresse générique `contact@` n'identifie pas une personne physique : on descend d'un cran entier de régime, ce qui est parfaitement cohérent avec le `Contact` à 6 champs déjà revendiqué.

**Ma divergence avec l'étude OSINT.** Elle recommande de ne *jamais* extraire le nom du dirigeant des registres publics (bascule de finalité : registre légal → fichier nominatif). **Je la suis, et je durcis :** `registre.py` ne persiste aucun nom de personne dans le vault. Il persiste `anciennete_annees`, `forme_juridique`, `tranche_effectif`, `statut_administratif` — de l'entreprise. Si la consultante veut le nom du dirigeant, elle ouvre le registre à la main, au cas par cas : c'est précisément à ça que sert la porte humaine. Cela coûte trente secondes par prospect réellement contacté (20 à 40 par mois, pas 400) et supprime la question juridique la plus lourde de la chaîne.

**Conséquence : l'étage 2 « registre pour le nom » que proposent les études tombe.** La cascade réelle est donc :

| Étage | Module | Ce qu'il produit | Coût |
|---|---|---|---|
| 1 | `contact_site.py` | adresse publiée + preuve (URL, date) | ~0 |
| 2 | *(porte humaine)* | nom du dirigeant, si nécessaire, à la main | 0 |
| 3 | `enrichment.py` (Apollo ou successeur) | email nominatif, sur résidu qualifié | payant |

Et l'étage 3 ne se déclenche que si la fiche passe un test de valeur : `score_capacite` suffisant **et** `score_faille` dans la bande utile. Payer un enrichissement pour un prospect qu'on ne contactera pas est du gaspillage pur — c'est ce que fait le système aujourd'hui (`run_discovery.py` enrichit tout ce qu'il découvre, dans la limite d'un compteur qui ne compte pas, cf. vérification n°3).

## B.3 — Les collecteurs gratuits à ajouter

Détaillés en section C. Classés par (gain × certitude) / effort :

1. `certification.py` — **0 appel réseau**, régex sur du HTML déjà en mémoire. Le plus discriminant du lot.
2. `contact_site.py` — ≤2 GET, souvent 0 (l'adresse est dans le HTML d'accueil déjà fetché).
3. `capacite.py` — **0 appel**, second axe calculé sur des signaux déjà collectés.
4. `cohorte.py` — **0 appel**, exploite les résultats de découverte déjà payés.
5. `archive.py` — 1 appel gratuit (Wayback CDX), fraîcheur *réelle* du site.
6. `domaine.py` — RDAP + DNS/MX, gratuit sans clé.
7. `perf.py` — PageSpeed Insights, 25 000/j gratuits, donne des **chiffres opposables** au prospect.
8. `registre.py` / `emploi.py` — reportés, gain réel mais hors goulot.

## B.4 — Modules à supprimer ou fusionner

**`seo.py` et `social.py` : ne pas supprimer. Les faire grossir.**

C'est la question piège du mandat et je réponds à contre-courant de sa formulation. Ces deux modules pèsent 72 lignes et `social.plateformes_mentionnees` n'est câblé à **aucune** règle de `rubric_persona1.yaml` — c'est du code mort côté scoring. La tentation de fusion est logique. Elle est mauvaise pour une raison structurelle : **ces deux modules sont l'implémentation de référence du patron « collecteur dérivé palier 0 », et je propose d'utiliser ce patron quatre fois de plus** (`certification`, `contact_site`, `cohorte`, et la lecture des signaux Places). Les fondre dans `website.py` en ferait un module-dieu couplant le fetch, le parsing, le SEO et le social — exactement la direction inverse de celle où le système doit aller. 72 lignes pour une couture démontrée et réutilisable, c'est bon marché.

Ce qu'il faut faire à la place : câbler `social.plateformes_mentionnees` dans la rubrique (il cesse d'être mort), et enrichir `seo.py` (aujourd'hui un seul booléen) avec `title_len`, H1, cohérence NAP, mention du programme de subvention.

**Trois vraies suppressions / fusions, elles :**

| Cible | Verdict | Motif |
|---|---|---|
| `website.py` l. 118-137 + 281-301 — cache autonome `.cache/website/` | **SUPPRIMER** | C'est une **seconde implémentation de cache hors du bus**, qui écrit un fichier et **n'écrit aucune ligne au grand livre**. Un appel réseau non journalisé est une érosion de l'invariant api_io, pas une rétrocompatibilité. L'orchestrateur injecte toujours `api_io` (`orchestrator.py:334-341`) ; les tests J1 autonomes doivent construire un `ApiIO` jetable, pas contourner le bus. |
| `gbp.py` + `reviews.py` | **CONSOLIDER, pas fusionner** | Les deux appellent le *même* `text_search` avec la *même* `cache_key` et parsent le *même* `results[0]`. Ils sont un collecteur coupé en deux, tenu par une coïncidence de clé de cache — un contrat implicite absent de l'interface `Collector`. Fusion en `places.py` = édition de rubrique + réécriture de tests. **Alternative moins risquée que je recommande :** `reviews.py` devient le seul à appeler, `gbp.py` dérive via l'injection `_places_payload` (patron `_website_signals` déjà en place). Les chemins de signaux `gbp.*` et `reviews.*` restent identiques → rubrique et tests intacts, coût à froid divisé par deux, couplage rendu explicite. |
| `_seo_text` et tout signal préfixé `_` | **STRIPPER de `Diagnostic`** | `pipeline.py:59-70` doit retirer les clés commençant par `_` de `signaux` **après** l'injection aux collecteurs dérivés et **avant** de construire `Diagnostic`. Aucun check de rubrique n'utilise de signal `_` → zéro régression. Corrige la vérification n°5 et ouvre la voie à `_html` (voir `contact_site.py`). |

## B.5 — Impact sur la rubrique et le DAG

### Rubrique — trois changements, dont un dans le moteur

**(a) `scoring.py` passe à trois états.** C'est le seul changement de moteur que je propose et il est inévitable. `_check_passes` renvoie aujourd'hui `bool` et `False` sur `None` (l. 29-30). Il doit renvoyer `"ok" | "echec" | "inconnu"`. Règles :
- `inconnu` → **aucun `Gap` émis** (c'est ça qui tue la fabrication),
- score de dimension renormalisé sur les seuls checks connus,
- dimension **sans aucun check connu** → exclue de la moyenne pondérée globale (`total_poids` recalculé),
- `Diagnostic.meta["dimensions_inconnues"]` et `meta["couverture"]` (somme des poids évalués / 100) tracent le taux de complétude.

Contrat préservé : `scores` reste `dict[str, float]` (une dimension inévaluée est **absente**, pas à `None`) ; `meta` est déjà `dict[str, Any]`. `diagnostic_to_rapport_md` itère `scores.items()` — il absorbe l'absence sans modification.

**(b) La gravité devient une donnée.** Aujourd'hui `_severity(points, max_points)` divise par le total de la dimension : « Site web inaccessible » (20/100 → 0.2) est classé **moyenne**, tandis que `gbp.verified` (60/100 → 0.6) est **toujours haute**. La faille la plus grave possible est mécaniquement dégradée parce qu'elle cohabite avec cinq autres checks. Ajouter un champ optionnel `gravite:` par check dans le YAML, avec repli sur `_severity` s'il est absent → **rétrocompatible, `test_j1_smoke` intact**.

**(c) Le second axe est une rubrique, pas une dimension.** C'est le geste le plus économique de tout le lot : `ScoringEngine` est générique et ne sait rien du HVAC. Donc `ScoringEngine(capacite_rubrique).score(signaux)` produit un **score de capacité** avec **zéro ligne de moteur nouvelle**. Deux fichiers de données, un seul moteur :

```
knowledge/rubric_persona1-quebec.yaml     → score_faille   (gravité du problème)
knowledge/capacite_persona1-quebec.yaml   → score_capacite (aptitude à payer)
```

Cela répond à l'objection centrale du COO (le mono-axe remonte les entreprises les plus cassées donc les moins solvables) sans introduire de concept nouveau dans l'architecture. La matrice de décision (faille × capacité) vit dans `export.py` comme clé de tri déclarée dans `export_kemana.yaml`.

Repondération cible de `rubric_persona1-quebec.yaml` (le fichier devient per-marché) :

| Dimension | Actuel | Cible | Signaux |
|---|---:|---:|---|
| `presence_locale` | 25 | 25 | `places.a_fiche`, `places.photos`, `places.horaires` |
| `avis` | 20 | 25 | + `reviews.date_dernier_avis`, `reviews.repond_aux_avis` *(déjà collectés, jetés)* |
| `site_web_conversion` | 25 | 20 | + `contact_site.tel_clicable`, `.formulaire_champs`, `.rdv_en_ligne` |
| `seo_local` | 15 | 15 | + `serp_rang.present_top10`, `seo.title_len` |
| `legitimite_conformite` | — | **10** | `certification.*` — **nouveau, gratuit, spécifique au marché** |
| `identite_marque` | 15 | **5** | rétrogradée tant que « a un logo + 3 images » n'est pas une mesure de marque |

Trois rubriques (`-quebec`, `-romandie`, `-france`) et trois ICP : ce n'est pas de la traduction, c'est un changement de **grammaire de légitimité** (RBQ 15.10 / suissetec / RGE), de **moteur de demande** (LogisVert / Programme Bâtiments / MaPrimeRénov') et de **régime de prospection**. L'invariant « la rubrique est une donnée » a été conçu exactement pour ça — il suffit de s'en servir.

### DAG — deux nouveaux nœuds, pas quatre

| Nœud | Verdict | Justification |
|---|---|---|
| Qualification / scoring capacité | **PAS de nœud** | Reste dans `diagnostic`. Le scoring y est déjà, ajouter un nœud pour une seconde passe du même moteur serait du bruit d'ordonnancement. |
| Calcul de cohorte | **PAS de nœud** | Post-traitement des résultats de découverte, déjà en mémoire dans `discovery`. Écrit un agrégat dans `.cache/cohortes/`. |
| `conformite` | **NOUVEAU, bloquant**, `depends_on: [diagnostic]`, précède `export` | Palier 2 de l'ADR 0001. Même patron que `preflight_gate` : **c'est une porte, pas un transformateur** — il lit `compliance/<marche>.yaml` et bloque la chaîne si le marché n'a pas de base légale déclarée, d'EFVP transfert (art. 17 LPRPSP — bloquant pour le Québec, marché de départ), ou de `sources_email_autorisees`. Il **ne touche aucune fiche, ne fait aucune transition** → machine à états intacte. |
| `registres_sync` | **NOUVEAU**, `enabled: false`, `depends_on: [preflight_gate]` | Rafraîchit les dumps gratuits (RBQ, RGE, Sirene) dans `.cache/registres/`. Cadence hebdomadaire, pas par prospect. |
| `purge` | **NOUVEAU** (palier 3), `depends_on: [usage_snapshot]` | Conservation RGPD — inexistante aujourd'hui (`grep conservation\|purge\|retention` sur `vault_io.py`/`vault_schema.py` : rien). **Anonymise les champs `contact_*` d'une fiche périmée ; ne transitionne pas et ne supprime pas** — `rejete` reste humain. Écriture via `vault_io` uniquement. Machine à états intacte. |

## B.6 — FicheProspect et export Kemana

**Le point que les deux briefs frôlent sans le nommer : la minimisation vit dans `Contact` (`extra="forbid"`, 6 champs, `enrichment.py:32-39`), pas dans `FicheProspect` (`extra="allow"`).** Ajouter des champs *entreprise* à `FicheProspect` ne touche **pas** au garde-fou RGPD. Ajouter des champs *personne* le touche. Cette ligne de partage tranche toute la question.

**À AJOUTER — entreprise, sans effet sur la minimisation :**
`place_id` · `localite` · `note_bucket` · `avis_bucket` · `score_capacite` · `anciennete_domaine_annees` · `annees_sans_refonte` · `certifications: list[str]` · `programme_subvention_mentionne: bool` · `rang_cohorte: str` · `motif_rejet: str | None` (liste fermée)

`motif_rejet` mérite un mot : c'est **le trou le plus coûteux du système**. Sans lui, un taux de rejet de 60 % ne dit pas s'il faut corriger l'ICP, les filtres, la rubrique ou l'enrichissement — la boucle d'apprentissage est ouverte. C'est un champ de frontmatter et une liste de six valeurs.

**À AJOUTER — conformité (servent l'audit, ne collectent rien de neuf) :**
`base_legale` (depuis l'ICP) · `contact_source_collecte` · `contact_date_collecte` · `opt_out_date` · `opt_out_source` · `information_art14_transmise_le` · `date_expiration_conservation`

**À AJOUTER — le champ qui change le produit :**
```yaml
preuves:
  - signal: reviews.date_dernier_avis
    constat: "Dernier avis Google du 14 mars 2025"
    valeur: "2025-03-14"
    observe_le: 2026-08-02
    source: google_places
    confiance: mesure        # mesure | derive | absent
```
« Une preuve non datée n'est pas utilisable » : si le constat a six semaines et que le site a été refait entretemps, l'accroche se retourne contre l'émettrice. `confiance: absent` rend structurellement impossible de promouvoir un signal non observé en accroche — c'est le verrou de crédibilité, en donnée plutôt qu'en discipline.

**À NE PAS AJOUTER, explicitement :** nom du dirigeant issu d'un registre (bascule de finalité) · téléphone personnel · tout attribut scorant la *personne*. **Le score porte sur l'entreprise ; le faire glisser vers l'individu ferait basculer le traitement en profilage et ferait tomber l'exception « coordonnées d'affaires » de la LPRPDE (art. 4.01).** Le `telephone_entreprise` est un cas limite : donnée d'entreprise en règle générale, donnée personnelle pour une entreprise individuelle — à traiter dans `compliance/<marche>.yaml`, pas dans le code.

**Export : 10 → 15 colonnes, plus un tri.** Édition de `export_kemana.yaml` seule pour les colonnes (`accroche`, `rapport`, `date_diagnostic`, `localite`, `score_capacite`, 2 colonnes de preuves datées, `qualite_email`). Trois de ces champs **existent déjà dans `FicheProspect` et ne sont simplement pas exportés** — on paie un LLM pour produire une `accroche` que la commerciale ne voit jamais.

Le tri, lui, est de la logique : il va dans `export.py`, avec la clé déclarée en YAML (`tri: [score_capacite desc, score_faille desc]`). Et `contact_email_source == "guessed"` doit être **exclu** de l'export sur le marché Québec, pas affiché en gris — un bounce dégrade la délivrabilité du domaine pour tous les prospects suivants.

---

# C. Les modules, un par un

Format imposé : fichier · palier · nature · scoring · coût/bus · mode dégradé · effort.

### C.1 — `diagnostic/collectors/certification.py`
- **Palier 0.** Hérite de `Collector`, dérivé pur : **zéro appel réseau**.
- **Nature :** collecteur dérivé, reçoit `_website_signals` (patron `seo.py`/`social.py`).
- **Scoring :** alimente la nouvelle dimension `legitimite_conformite` (10 pts). Signaux : `licence_rbq_affichee` (regex `RBQ\s*:?\s*\d{4}-\d{4}-\d{2}`), `mention_rge`, `membre_suissetec` / `membre_gsp`, `membre_cmmtq`, `programme_subvention_mentionne`. Motifs dans `knowledge/certifications.yaml` **par marché** → config = donnée.
- **Coût :** 0 $/fiche. Ne passe pas par `api_io` puisqu'il n'émet rien (le fetch a déjà été journalisé par `website.py`).
- **Dégradé :** `_website_signals` absent → tous signaux à `None`. Avec le scoring 3 états, `None` ⇒ `inconnu` ⇒ **aucune faille émise**. La suite tourne sans clé, inchangé.
- **Effort : faible** (~120 lignes + un YAML). Distinction importante à tenir : ce collecteur mesure **l'affichage** de la légitimité, pas sa validité. C'est le bon objet — la consultante vend du branding, et une licence RBQ valide mais invisible sur le site *est* une faille de marque.
- ⚠️ Un installateur français sans RGE affiché est coupé de MaPrimeRénov' : c'est le signal le plus discriminant du marché français, pour zéro appel.

### C.2 — `diagnostic/collectors/contact_site.py`
- **Palier 0** (réseau, mais gratuit).
- **Nature :** `Collector`. Lit `_website_html` en premier ; ne fetch `/contact`, `/nous-joindre`, `/mentions-legales` **que si** aucune adresse dans l'accueil.
- **Scoring :** `site_web_conversion` — `tel_clicable`, `formulaire_present`, `nb_champs_formulaire`, `rdv_en_ligne`, `whatsapp`, `horaires_publies`. Répond à la sous-pondération n°1 du CMO (la joignabilité pèse aujourd'hui 5 % du score total, via un unique booléen `has_contact`).
- **Sortie hors scoring :** `emails_publies: list[str]` + `preuve_publication: {url, date, extrait}` → alimente l'étage 1 de la cascade contact.
- **Coût :** 0 à 2 `api_io.call("http","get", …)` cachés, prix 0. **Passe par le bus, obligatoirement.**
- **Dégradé :** échec réseau → `safe_collect` isole ; signaux `None` ⇒ `inconnu` ⇒ pas de faille.
- **Effort : moyen** (~200 lignes). **Prérequis :** `website.py` doit exposer `_html` dans ses signaux **et** `pipeline.py` doit stripper les clés `_` avant de construire `Diagnostic` (sinon le HTML complet part dans le vault et viole G9). Ces deux changements se font ensemble.
- ⚠️ **Ajouter la vérification `robots.txt`** dans ce module et dans `website.py` (`grep -rn robots --include=*.py .` → **rien** aujourd'hui). Via `api_io.call("http","get", …)` alimentant `urllib.robotparser`, jamais un accès direct. Ce n'est pas illégal en soi, c'est le premier argument qu'un contradicteur soulèvera, et c'est trivial.

### C.3 — `diagnostic/capacite.py`
- **Palier 0.** **N'hérite pas de `Collector`** — c'est un module de service, appelé par `pipeline.py` après le scoring de faille.
- **Nature :** ~40 lignes. Charge `knowledge/capacite_<icp>.yaml` et appelle `ScoringEngine(capacite_rubrique).score(signaux)` — **le moteur existant, sans une ligne nouvelle**.
- **Scoring :** produit `score_capacite` (0-100) sur des signaux **déjà collectés** : `reviews.count` (proxy de taille), `website.fraicheur_mois` (quelqu'un est payé pour le site), `reviews.repond_aux_avis` (il y a un responsable marketing), `certification.*` (l'entreprise a investi dans sa qualification), `domaine.anciennete`, `stack.pixels_publicitaires` (elle achète déjà de l'acquisition).
- **Coût :** 0 $. Ne touche pas le réseau.
- **Dégradé :** signaux inconnus ⇒ dimensions exclues ⇒ `score_capacite` calculé sur ce qui est connu, avec `couverture` tracée. Jamais de zéro fabriqué.
- **Effort : faible** (~40 lignes + un YAML). **Meilleur rapport valeur/effort du lot après le correctif scoring**, parce qu'il corrige le biais qui remonte systématiquement les entreprises les plus petites et les moins solvables.

### C.4 — `diagnostic/cohorte.py` + `diagnostic/collectors/cohorte.py`
- **Palier 0.** Deux pièces : un module de service côté découverte, un `Collector` dérivé côté diagnostic.
- **Nature :** `discovery*.py` calcule, à la fin de chaque run, les médianes de la cohorte (même requête, même localité) sur `nb_avis`, `note`, `recence_avis`, et écrit `.cache/cohortes/<icp>-<localite>.json` (**hors vault**, `.gitignore`). Le collecteur lit ce fichier — aucun réseau.
- **Scoring :** ne modifie **aucun** score. Il produit du **positionnement relatif** : `rang_cohorte: "8e sur 10 sur la récence des avis"`. C'est ce qui transforme « 62/100 » (inintelligible pour le prospect) en une information qu'il ne peut obtenir nulle part.
- **Coût :** **0 appel supplémentaire** — les résultats sont déjà en mémoire et déjà payés.
- **Dégradé :** fichier de cohorte absent → `rang_cohorte: None`, aucun gap.
- **Effort : moyen** (~150 lignes, deux points d'insertion). Le CMO comme le COO le classent premier en valeur perçue par unité de coût, et ils ont raison : c'est de la donnée déjà achetée qu'on jette aujourd'hui.

### C.5 — `diagnostic/collectors/archive.py`
- **Palier 1**, mais **sans clé et gratuit** (Wayback CDX). Le système doit d'ailleurs distinguer « palier 1 » (réseau externe) de « payant » — ce sont deux axes que la doc actuelle confond.
- **Nature :** `Collector`, un `api_io.call("wayback","cdx", …)`.
- **Scoring :** `site_web` — `annees_sans_refonte`, `nb_captures`. Remplace `copyright_year` (qu'un thème WordPress met à jour automatiquement, donc non fiable) par la vraie date de refonte. Le signal de négligence de marque le plus discriminant du lot.
- **Coût :** 0 $, cadence ~1 req/s à respecter. Nouveau fournisseur `wayback` à prix 0 dans `api_pricing.yaml`.
- **Dégradé :** pas de réseau → `None` ⇒ `inconnu`. Tests verts sans clé.
- **Effort : faible** (~100 lignes).

### C.6 — `diagnostic/collectors/domaine.py`
- **Palier 1**, gratuit, sans clé (RDAP + DNS).
- **Scoring :** `date_creation_domaine` → `anciennete_presence_ligne` ; `messagerie_professionnelle` (MX Google/Microsoft vs MX du registrar vs **aucun MX** — signal très fort) ; `spf_dmarc_present`. Signal dérivé à forte valeur : **`ecart_anciennete_legale_vs_numerique`** (entreprise de 20 ans, domaine de 2 ans = retard numérique caractérisé) — il exige `registre.py`, donc il arrive plus tard.
- **Coût :** 0 $.
- ⚠️ **Alerte invariant.** Une résolution DNS n'utilise ni `requests` ni `anthropic` : **l'AST walk de `_check_garde_fous_bus` ne l'attraperait pas.** Deux corrections obligatoires si ce module est retenu : (a) tout passe par `api_io.call("dns","resolve", …)` ; (b) la liste `interdits = {"requests","anthropic"}` (`preflight.py:264`) est étendue à `{"dns","httpx","urllib3","socket","http.client","urllib.request"}`. Sans (b), le garde-fou est contournable par simple choix de bibliothèque.
- **Dégradé :** résolution impossible → `None`. **Effort : faible-moyen** (~120 lignes + durcissement du préflight).

### C.7 — `diagnostic/collectors/perf.py`
- **Palier 1**, 25 000 requêtes/jour gratuites. Réutilise `GOOGLE_PLACES_API_KEY` (même clé Google Cloud) ou tourne sans clé à débit réduit.
- **Scoring :** `seo_local` — `score_pagespeed_mobile`, `lcp`, `cls`. **Le seul collecteur qui produit des chiffres opposables** à mettre dans le mini-audit (« votre page met 6,2 s à s'afficher sur mobile » se vérifie ; « votre identité manque d'impact » ne se vérifie pas et se lit comme une insulte).
- **Coût :** 0 $ au volume du projet. **Dégradé :** sans clé et hors quota → `None`. **Effort : faible** (~100 lignes).

### C.8 — `diagnostic/collectors/serp_rang.py` *(le SERP rétrogradé)*
- **Palier 1 payant.**
- **Nature :** `Collector`. Une requête `"{métier} {localité}"` → l'entreprise ressort-elle dans le top 10 ?
- **Scoring :** `seo_local` — `present_top10`, `position`. Transforme la dépense SERP en **preuve directe et vérifiable**, au lieu d'un moyen de découverte biaisé.
- **Coût :** 1 requête/fiche. Réserve : à ce prix, ne le déclencher que sur les fiches ayant passé le filtre de capacité — le déclenchement conditionnel se déclare dans l'ICP.
- **Dégradé :** `SERP_API_KEY` absente → `None` ⇒ `inconnu`. **Effort : faible** (`_serp_search` de `discovery.py:85-103` est réutilisable tel quel).

### C.9 — `diagnostic/discovery_places.py`
- **Palier 1** (google_places, déjà câblé).
- **Nature :** **pas un `Collector`** — c'est une source de découverte, contrat `discover() -> list[Candidate]`, identique à `DiscoveryCollector`. `run_discovery.py` choisit la classe depuis un petit registre, **la source étant déclarée dans l'ICP** (`decouverte: {source: places|serp|registre}`) → config = donnée, zéro `if` métier dans le code appelant.
- **Scoring :** pré-alimente `places.*` dès la découverte → 45 points connus avant le diagnostic, donc priorisation des fiches `decouvert` avant toute dépense LLM.
- **Coût :** 1 `text_search` par zone (paginé par 20, **chaque page est un appel facturé**). Passe par `api_io`. Le `place_id` récupéré est **réutilisé** par `gbp`/`reviews` en J1 → un `text_search` économisé par prospect diagnostiqué.
- **Dégradé :** sans `GOOGLE_PLACES_API_KEY` → `discover()` retourne `[]` et journalise ; `run_discovery --dry-run` reste vert. Le faux serveur HTTP local des tests d'intégration (`PLACES_BASE_URL`) couvre le chemin nominal, comme il le fait déjà pour `SERP_BASE_URL`.
- **Effort : moyen.** Trois points seulement :
  1. `api_io.call` accepte une **closure arbitraire** (l. 294-307) — le `POST` + en-tête `X-Goog-FieldMask` de Places API (New) **passe sans toucher au bus**. L'invariant n'est pas menacé.
  2. `IcpConfig` (`extra="forbid"`) gagne un bloc optionnel `zones: [{centre, rayon_km, type}]` — `persona1-quebec.yaml` continue de valider inchangé.
  3. `Candidate` (`extra="forbid"`, 5 champs) gagne `place_id`, `note_bucket`, `avis_bucket`, `localite` — **entreprise uniquement**, la minimisation n'est pas touchée (elle vit dans `Contact`).
- ⚠️ **Dette à traiter au passage :** `gbp.py:49` et `reviews.py:89` appellent `maps.googleapis.com`, c'est-à-dire l'API Places **legacy**. Migrer maintenant vers `places.googleapis.com` évite de le faire deux fois.
- ⚠️ **Prérequis dur : implémenter le TTL de cache** (vérification n°2). Sans lui, la persistance des champs Places dans le vault **et** le cache éternel sont tous deux en tension avec les Maps Platform Terms.

### C.10 — `diagnostic/registres.py` + `diagnostic/collectors/registre.py`
- **Palier 0** en exploitation (dump local), **palier 1** pour la synchronisation.
- **Nature :** un module de service (téléchargement/indexation, appelé par le nœud `registres_sync`) + un `Collector` qui lit l'index local.
- **Scoring :** nouvelle dimension `solidite_entreprise` — `anciennete_annees`, `forme_juridique`, `tranche_effectif`, `statut_administratif` (filtre d'exclusion dur : radiée/en liquidation). Alimente surtout **`capacite.py`**, pas le score de faille.
- **Coût :** 0 $/fiche (dump bimensuel amorti). **Le rendement le plus élevé est ailleurs :** RBQ « licences actives » (Québec, dump gratuit, sous-catégorie 15.10) et RGE ADEME (France, API ouverte, SIRET) donnent **l'univers complet des installateurs HVAC sans aucun biais de sélection** — c'est la réponse de fond au problème du SERP sur deux marchés sur trois. D'où un `discovery_registre.py` en palier 3.
- ⚠️ **Alerte invariant, et je la lève avec la solution.** Télécharger un dump de plusieurs centaines de Mo via `api_io.call()` casserait le cache (qui fait `json.dumps` de la réponse, l. 234). **Conception conforme sans modifier le bus :** appeler avec `cache_key=None` et une closure qui écrit le fichier dans `.cache/registres/` puis retourne un petit dict `{"octets": N, "chemin": …}`. Le bus journalise durée et volume, le budget reste vérifié, rien ne transite par le cache JSON. **Zéro changement à `api_io.py`.**
- ⚠️ Sirene et le REQ exposent des **entrepreneurs individuels** — données personnelles. Sirene applique un statut de diffusion restreinte pour ceux qui s'y sont opposés : c'est un **opt-out réglementaire qui doit se propager dans `FicheProspect.opt_out`** et son exclusion absolue à l'export. Un installateur HVAC en entreprise individuelle est un cas fréquent, pas une hypothèse d'école.
- **Dégradé :** index absent → `None` partout, aucune faille. **Effort : élevé** — le point dur n'est pas l'accès, c'est le **rapprochement** (« Climatisation Tremblay » trouvé par Places ⇄ la bonne entité du registre) sans faux positif.

### C.11 — Modules NON retenus, et pourquoi
- **`emploi.py`** (France Travail) : gratuit et temps réel, mais **ne couvre que la France** — le 3ᵉ marché de la séquence. Aucun équivalent trouvé pour la Suisse. À reporter.
- **`stack.py` payant** (BuiltWith 295 $/mois, Wappalyzer 250 $/mois) : **écarté**. Un fork MIT + regex sur le HTML déjà en mémoire couvre le besoin à coût nul et **sans appel réseau supplémentaire** — c'est un collecteur dérivé palier 0. La détection de pixels publicitaires (Meta, GA4, gtag) est le meilleur signal de capacité gratuit du lot : un prospect qui a un pixel Meta **dépense déjà** en acquisition. À fusionner dans `certification.py` ou un `stack.py` gratuit.
- **Apify** : **écarté sur incompatibilité structurelle, pas sur le prix.** Asynchrone (incompatible avec le contrat synchrone de `call()`), coût non prévisible **avant** l'appel (casse le pre-check budgétaire `_verifier_budget`, l. 184-207), et plusieurs acteurs annoncent l'extraction d'emails — ce qui contredit frontalement l'invariant « données personnes via API fournisseur uniquement ». Trois violations, aucune rattrapable par un réglage.
- **Superviseur LLM de routage** : refusé par l'ADR 0001. Rien dans ce qui précède ne le réintroduit — `capacite.py`, `choisir_modele()` et le nœud `conformite` sont tous des comparaisons déterministes pilotées par YAML.

---

# D. Plan d'implémentation priorisé

Le classement suit une règle : **ce qui ne dépend d'aucune clé et ne coûte rien passe devant**, parce que le préflight est en NO-GO structurel et le restera jusqu'au relevé tarifaire.

## Palier 0 — Correctifs de moteur · aucune clé, aucun coût, **bloquant avant tout envoi**

| # | Action | Fichiers | Effort | Gain |
|---|---|---|---|---|
| 0.1 | **Scoring 3 états** + renormalisation + aucun gap sur `inconnu` | `scoring.py`, `models.py` (`Gap.signal`), tests | **M** | **Le plus élevé du projet.** Supprime la fabrication de failles. Sans lui, tout le reste décore un diagnostic faux. |
| 0.2 | **`gravite` explicite** dans la rubrique (repli sur `_severity`) | `scoring.py`, `rubric_*.yaml` | F | « Site inaccessible » cesse d'être classé *moyenne* |
| 0.3 | **Renommer `gbp.verified`** → `gbp.operationnel` + libellé honnête | `gbp.py:64`, rubrique | **F** | Supprime une affirmation fausse **même avec une clé valide** |
| 0.4 | **Strip des signaux `_`** avant `Diagnostic` | `pipeline.py` | F | Ferme la fuite `_seo_text` (vérif. n°5), prérequis de `contact_site` |
| 0.5 | **Corriger le compteur d'enrichissement** | `enrichment.py:78-81` | **F** | `max_enrichissements` plafonne enfin les appels (vérif. n°3) |
| 0.6 | **Implémenter le TTL de cache** (par fournisseur) | `api_io._lire_cache`, `greenit.yaml` | F | Rend le levier GreenIT n°3 réel ; prérequis Maps Terms (vérif. n°2) |
| 0.7 | **Supprimer le cache autonome** de `website.py` | `website.py` l. 118-137, 281-301 | F | Supprime les appels réseau non journalisés |

> **Rien de tout cela n'exige une clé.** Les 536 tests restent la preuve permanente : ils doivent être verts à chaque étape, et ils le peuvent, puisque `inconnu` est précisément l'état dans lequel tourne le système sans clé.

## Palier 1 — Collecteurs gratuits · aucune clé

| # | Action | Effort | Gain |
|---|---|---|---|
| 1.1 | Câbler les **5 signaux déjà collectés et jetés** (`repond_aux_avis`, `date_dernier_avis`, `fraicheur_mois`, `plateformes_mentionnees`, `title_len`) | **F — édition YAML pure** | Meilleur ratio absolu : déjà payés, jamais utilisés |
| 1.2 | `certification.py` + `knowledge/certifications.yaml` | F | Nouvelle dimension `legitimite_conformite`, 0 appel |
| 1.3 | `capacite.py` + `capacite_persona1-quebec.yaml` | **F** | Second axe, **zéro ligne de moteur** — corrige le biais mono-axe |
| 1.4 | `contact_site.py` + `_html` + **`robots.txt`** | M | Étage 1 de la cascade contact ; désamorce Apollo |
| 1.5 | `archive.py` (Wayback) | F | Fraîcheur réelle vs copyright non fiable |
| 1.6 | Tri de l'export + 15 colonnes + exclusion `guessed` | F | Export enfin actionnable sans rouvrir Obsidian |
| 1.7 | `motif_rejet` (liste fermée) | **F** | **Ouvre la boucle d'apprentissage** — inexistante aujourd'hui |
| 1.8 | Marquage « assistance IA » dans `diagnostic_to_rapport_md`, conditionné à un appel LLM réel | F | AI Act art. 50, **applicable depuis aujourd'hui** |

## Palier 2 — Bascule de découverte · exige une clé Places

| # | Action | Effort | Gain |
|---|---|---|---|
| 2.1 | `discovery_places.py` + `zones` ICP + `Candidate` élargie | M | Supprime le biais de sélection ; pré-alimente 45 pts |
| 2.2 | Migration Places legacy → New (`places.googleapis.com`) | F | À faire pendant 2.1, pas deux fois |
| 2.3 | `cohorte.py` (service + collecteur) | M | Positionnement relatif = l'accroche qui pique |
| 2.4 | `serp_rang.py` (SERP rétrogradé) | F | La dépense SERP devient une preuve |
| 2.5 | Consolidation `gbp` ⇄ `reviews` (un seul fetch, injection dérivée) | F | Supprime le couplage par clé de cache |
| 2.6 | `domaine.py`, `perf.py` + **durcissement de la liste `interdits`** du préflight | M | Chiffres opposables ; garde-fou bus non contournable |

## Palier 3 — Conformité et registres · structurel

| # | Action | Effort | Gain |
|---|---|---|---|
| 3.1 | `compliance/<marche>.yaml` + nœud `conformite` bloquant | M | Palier 2 de l'ADR 0001 ; **EFVP transfert art. 17 LPRPSP est une pré-condition du Québec**, marché de départ |
| 3.2 | `preuves[]` datées dans `FicheProspect` | M | « Une preuve non datée n'est pas utilisable » |
| 3.3 | Nœud `purge` + `date_expiration_conservation` | M | Conservation RGPD — **aucune aujourd'hui** |
| 3.4 | `registres_sync` + `registre.py` (RBQ d'abord) | **É** | Univers complet sans biais |
| 3.5 | `discovery_registre.py` (RBQ / RGE) | É | Endgame de la découverte, deux marchés sur trois à coût nul |
| 3.6 | Trois rubriques + trois ICP (`-romandie`, `-france`) | M | Grammaire de légitimité et régime de prospection distincts |

---

# E. Ce que je ne recommande pas, et pourquoi

- **Ne pas optimiser les tokens.** Borne haute vérifiable : ~600 tokens de sortie plafonnés (`greenit.yaml`), ~2 300 en entrée → de l'ordre de 0,5 à 2 cents par fiche. Le poste données représente ~95 % du coût variable, et les abonnements ~85-95 % de la dépense totale au volume visé. **Le chantier GreenIT a raison sur le principe et n'a aucun levier économique ici.** Le dire est plus honnête que de le vendre.
- **Ne pas augmenter le volume de découverte.** Le goulot n'est pas la production de fiches, c'est la capacité de validation humaine et d'exécution commerciale. Un run peut saturer la porte humaine. Produire plus, c'est brûler des crédits non reportables pour des fiches qui vieilliront dans le vault.
- **Ne pas activer J6.** Rien dans ce document ne le prépare autrement que par le nœud `conformite`, dont l'existence est justement de rendre l'activation *impossible* tant que le dossier juridique n'est pas fait.
- **Ne pas saisir de prix dans `api_pricing.yaml` depuis ces études.** Aucune page tarifaire n'a été lue directement dans aucune des quatre. Et un piège de modélisation attend au bout : `compute_cout` (`api_schema.py:63-80`) multiplie des **unités brutes** — `prix_par_unite` est un prix par unité individuelle, pas par 1 000, pas par million. Recopier une page tarifaire telle quelle garantit une erreur de facteur 10⁶. Second piège du même fichier : la grille `anthropic.messages` est **mono-tarif** alors que le routage GreenIT peut appeler Haiku *ou* Sonnet — toute escalade `qualite` serait facturée au tarif Haiku, soit une sous-estimation d'un facteur 3. `LedgerEntry` porte déjà le champ `modele` : la correction propre est une grille indexée par modèle. **À traiter avant le premier run avec clé Anthropic, sinon le grand livre ment.**

---

**Le geste unique, s'il ne devait y en avoir qu'un :** faire dire au moteur de scoring « je ne sais pas ». Tout le reste de ce plan — la bascule Places, la cascade contact, les collecteurs gratuits, l'axe capacité — n'a de valeur que si le système cesse d'affirmer ce qu'il n'a pas observé. C'est un correctif de code, pas de copywriting, et il tient en une trentaine de lignes dans `scoring.py`.

**Fichiers de référence :** `/home/user/01_Syst-me_Autonome_Diagnostic_Marketing/diagnostic/scoring.py` (l. 26-46) · `diagnostic/api_io.py` (l. 218-224 cache sans TTL ; l. 294-307 contrat de closure) · `diagnostic/enrichment.py` (l. 78-81) · `diagnostic/collectors/gbp.py` (l. 64) · `diagnostic/collectors/website.py` (l. 94, 118-137, 281-301) · `diagnostic/pipeline.py` (l. 39-70) · `diagnostic/export.py` (l. 62-78) · `diagnostic/preflight.py` (l. 249-282) · `diagnostic/orchestrator.py` (l. 334-341, 479-530) · `knowledge/greenit.yaml` (l. 106).

---


<a id="s9"></a>

## 9. Schéma du dossier OSINT (rejeté en l'état, réduit par le chef de projet)


# DOSSIER OSINT DE PROSPECT — SCHÉMA DE DONNÉES

Conception vérifiée par lecture directe du code (`vault_schema.py`, `enrichment.py`, `api_schema.py`, `serializers.py`, `icp_schema.py`, `vault_io.py`, `export.py`, `collectors/*.py`, `knowledge/*.yaml`, `icp/persona1-quebec.yaml`, `run_discovery.py`).

---

## 0. DÉCISIONS DE CONCEPTION (à valider avant implémentation)

| # | Décision | Justification vérifiable |
|---|---|---|
| D1 | **Blocs imbriqués**, pas 60 champs à plat | `FicheProspect` est aujourd'hui plate (23 champs). Passer à ~90 champs plats rend le frontmatter Obsidian illisible et mélange les natures juridiques. Un bloc = une nature + un TTL + une provenance. Un bloc non collecté vaut `None` (distinct d'un bloc vide). |
| D2 | **`Contact` reste figé à 6 champs**, `extra="forbid"` inchangé | `enrichment.py:32`. Toute donnée de conformité (base légale, art. 14, opt-out) va dans un bloc `conformite` **séparé** : c'est de la métadonnée de traitement (redevabilité art. 5.2), pas de la donnée sur la personne. La revendication « 6 champs » reste littéralement vraie. |
| D3 | **Les noms de dirigeants publics au registre ne sont PAS collectés** | REQ / RNE / Zefix les exposent. Les recopier dans le vault transforme un registre légal en fichier de prospection nominatif (changement de finalité). On stocke `dirigeant_registre_disponible: bool` + l'identifiant légal permettant la consultation manuelle. La consultation reste un geste humain. |
| D4 | **Google Places : seuls des dérivés sont persistés** | Maps Platform Terms : `place_id` stockable sans limite, lat/lng 30 j, le reste non entreposable. → on persiste `place_id`, des **buckets** (`note_bucket`, `nb_avis_bucket`) et des **booléens**, jamais `rating`/`user_ratings_total` bruts. Corollaire : `greenit.yaml:106 cache_ttl_jours: 30` est **global** — il doit devenir **par fournisseur**. |
| D5 | **`export.py` gagne le support des chemins pointés** | `export.py:84` fait `fiche_dict.get(col["champ"])` — plat uniquement. 3 lignes pour supporter `identite_legale.tranche_effectif`. Sinon il faut dupliquer les champs à plat : moins bien. La config reste une donnée. |
| D6 | **`contact_email_source` est dédoublé** | Vérifié `enrichment.py:128` : il porte `personne.get("email_status")` = **statut de vérification Apollo**, pas la provenance. Ce n'est donc pas une piste d'audit art. 14.2.f. On garde le champ (rétro-compat) mais on ajoute la vraie provenance dans le bloc `tracabilite`. |

**Légende des tableaux** — Palier : `G`=gratuit · `G€`=gratuit sous quota · `€`=payant · `D`=dérivé (0 appel). Nature : `E`=donnée d'entreprise · `E*`=donnée d'entreprise pouvant être personnelle (entreprise individuelle) · `P`=donnée personnelle · `M`=métadonnée système. Obl. : `O`=obligatoire pour `pret_a_contacter` · `o`=optionnel · `B`=bloquant (son absence ou sa valeur disqualifie).

---

## 1. SCHÉMA COMPLET, BLOC PAR BLOC

### Bloc 0 — Noyau existant (INCHANGÉ, ne pas toucher)

| Champ | Type | Source | Palier | Obl. | Nature |
|---|---|---|---|---|---|
| `type` | `Literal["prospect"]` | constante | — | O | M |
| `persona` | `Literal[1,2]` | ICP | — | O | M |
| `marche` | `Marche` (enum) | ICP | — | O | M |
| `statut` | `Statut` (enum) | machine à états | — | O | M |
| `nom` | `str` | SERP / Places | €/G€ | O | E* |
| `date_creation` | `date` | système | — | O | M |
| `site_web` | `str \| None` | SERP / Places | €/G€ | **B** | E |
| `score_global` | `int 0-100 \| None` | `scoring.py` | D | O | M |
| `gaps_majeurs` | `list[str]` | `serializers.py:26` | D | o | M |
| `source_decouverte` | `str` | `run_discovery.py:53` | — | O | M |
| `date_diagnostic` | `date \| None` | `serializers.py` | D | O | M |
| `rapport` | `str \| None` (wikilink) | `vault_io.write_rapport` | — | o | M |
| `contact_nom` `contact_titre` `contact_email` `contact_email_source` `contact_linkedin` | `str \| None` ×5 | Apollo | € | o | **P** |
| `icp_id` | `str \| None` | ICP | — | O | M |
| `opt_out` | `bool` = False | humain / site | — | **B** | M |
| `signal_chaud` `accroche` | `str \| None` | `serializers.py:30-39` | D | o | M |

---

### Bloc A — `identite_legale` — nature E/E*, palier G intégral

Aucune API payante. Deux marchés sur trois se traitent en **dump local** (pas d'appel réseau par prospect).

| Champ | Type | Source | Palier | Obl. | Nature |
|---|---|---|---|---|---|
| `identifiant_legal` | `str \| None` | REQ (NEQ) / Zefix+UID (IDE-CHE) / Sirene (SIREN) | G | O | E |
| `identifiant_type` | `Literal["neq","ide","siren","siret"] \| None` | idem | G | O | M |
| `raison_sociale` | `str \| None` | registre | G | O | **E\*** |
| `noms_commerciaux` | `list[str]` | REQ (« autres noms ») | G | o | E |
| `forme_juridique` | `str \| None` | registre | G | o | E |
| `entreprise_individuelle` | `bool \| None` | dérivé de `forme_juridique` | D | O | M |
| `date_immatriculation` | `date \| None` | registre | G | O | E |
| `anciennete_annees` | `int \| None` | dérivé | D | o | E |
| `statut_administratif` | `Literal["actif","radie","liquidation","inconnu"]` | registre | G | **B** | E |
| `code_activite` | `str \| None` | CAE (QC) / NOGA (CH) / NAF (FR) | G | o | E |
| `code_activite_systeme` | `Literal["cae","scian","noga","naf"] \| None` | idem | G | o | M |
| `adresse_siege` | `str \| None` | registre | G | o | **E\*** |
| `nb_etablissements` | `int \| None` | Sirene / REQ | G | o | E |
| `tranche_effectif` | `str \| None` (ex. `"5-9"`) | Sirene / REQ | G | O | E |
| `assujetti_tva` | `bool \| None` | UID/OFS (CH seul) | G | o | E |
| `dirigeant_registre_disponible` | `bool \| None` | présence au registre, **pas le nom** (D3) | G | o | M |

> ⚠️ `raison_sociale` et `adresse_siege` **deviennent des données personnelles** quand `entreprise_individuelle == True` (raison sociale = nom du dirigeant, siège = domicile). C'est pourquoi `entreprise_individuelle` est marqué obligatoire : il commande le régime applicable au reste du bloc. Cas fréquent en HVAC, pas une hypothèse d'école.

---

### Bloc B — `certification` — nature E, palier G intégral, **le plus discriminant**

| Champ | Type | Source | Palier | Obl. | Nature |
|---|---|---|---|---|---|
| `licence_rbq` | `str \| None` | RBQ « Licences actives » (Données Québec, dump) | G | o | E |
| `rbq_sous_categories` | `list[str]` | idem (15.10 = thermopompe résidentielle) | G | o | E |
| `rbq_actif` | `bool \| None` | idem | G | o | E |
| `rbq_nb_reclamations` | `int \| None` | registre RBQ (depuis 2023) | G | o | E |
| `membre_cmmtq` | `bool \| None` | répertoire CMMTQ ⚠️ CGU à lire | G | o | E |
| `rge_qualifications` | `list[str]` | ADEME open data (licence Etalab) | G | o | E |
| `rge_domaines_travaux` | `list[str]` | idem | G | o | E |
| `rge_valide_jusquau` | `date \| None` | idem | G | o | E |
| `rge_perdue_depuis` | `date \| None` | ADEME « Historique RGE depuis 2014 » | G | o | E |
| `membre_suissetec` / `membre_gsp` / `label_pac_systeme_module` | `bool \| None` ×3 | suissetec / FWS / wp-systemmodul | G | o | E |
| `certification_affichee_sur_site` | `bool \| None` | **regex sur le HTML déjà en mémoire** (`RBQ\s*:?\s*\d{4}-\d{4}-\d{2}`, `RGE`, logo suissetec) | D | o | E |
| `programmes_subvention_mentionnes` | `list[str]` | regex HTML (LogisVert, Rénoclimat, MaPrimeRénov', Programme Bâtiments, CEE) | D | o | E |

> Les deux derniers champs sont le cœur commercial du bloc : l'écart entre **détenir** une qualification (registre) et **l'afficher** (site) est une faille démontrable, datée, et gratuite à mesurer.

---

### Bloc C — `etablissement` — nature E, contrainte CGU Google (D4)

| Champ | Type | Source | Palier | Obl. | Nature |
|---|---|---|---|---|---|
| `place_id` | `str \| None` | Places Text Search — **seul champ stockable sans limite** | G€ | o | E |
| `a_fiche_gbp` | `bool \| None` | dérivé (résultat Places non vide) | D | O | E |
| `gbp_operationnel` | `bool \| None` | `business_status == "OPERATIONAL"` | G€ | o | E |
| `gbp_photos_presentes` | `bool \| None` | Places `photos` non vide | G€ | o | E |
| `horaires_publies` | `bool \| None` | Places / site | G€ | o | E |
| `telephone_public` | `str \| None` | **site officiel** (`tel:`) ou Places | G | O | E |
| `ville` / `region_precise` | `str \| None` ×2 | Places / registre / localité SERP | G€ | O | E |
| `coherence_nap` | `bool \| None` | dérivé (nom/adresse/tél site ⇄ GBP ⇄ registre) | D | o | E |
| `presence_osm` | `bool \| None` | Overpass (≤10 000 req/j) | G | o | E |
| `osm_website_renseigne` | `bool \| None` | Overpass | G | o | E |
| `places_rafraichi_le` | `date \| None` | système — **pilote la purge à 30 j** | — | O | M |

> 🔴 **Renommage obligatoire** : `gbp.py:64` produit `"verified": business_status == "OPERATIONAL"`. Ce n'est **pas** la vérification d'une fiche par son propriétaire. La rubrique émet pourtant « Fiche Google Business non vérifiée ». Le champ du dossier s'appelle `gbp_operationnel` et le libellé de faille doit suivre. Sinon le système affirme à un prospect un fait que le collecteur ne soutient pas.
>
> ⚠️ **`telephone_public` est ajouté sciemment** : c'est une donnée d'entreprise publiée par l'entreprise elle-même, c'est le meilleur canal en HVAC, et il échappe aux régimes CASL / art. 3 LCD qui ne visent que les **messages électroniques**. Absent du système aujourd'hui (vérifié : aucune occurrence de `telephone`/`phone` dans le code ni les YAML).

---

### Bloc D — `presence_numerique` — nature E, palier G/D

| Champ | Type | Source | Palier | Obl. | Nature |
|---|---|---|---|---|---|
| `domaine_normalise` | `str \| None` | dérivé de `site_web` (clé de dédup) | D | O | E |
| `https` `viewport_mobile` `meta_description` `has_title` `title_len` `has_logo` `image_count` `mentions_offre` | mixtes | `website.py` — **déjà collectés** | G | O | E |
| `formulaire_contact` | `bool \| None` | `website.py::_has_contact` | G | O | E |
| `tel_cliquable_mobile` | `bool \| None` | **nouveau** — présence `href="tel:"` | D | O | E |
| `rdv_en_ligne` / `chat_present` / `mention_urgence_24_7` | `bool \| None` ×3 | **nouveau** — regex HTML | D | o | E |
| `nb_champs_formulaire` | `int \| None` | **nouveau** — comptage `<input>` | D | o | E |
| `derniere_maj` `fraicheur_mois` `copyright_year` | `str/int \| None` | `website.py:92-93` — **collectés, jetés par la rubrique** | G | O | E |
| `date_creation_domaine` | `date \| None` | **RDAP** (bootstrap IANA, sans clé) | G | o | E |
| `anciennete_presence_ligne_annees` | `int \| None` | dérivé | D | o | E |
| `ecart_anciennete_legale_vs_numerique` | `int \| None` | dérivé (A.`anciennete_annees` − D.`anciennete_presence_ligne`) | D | o | E |
| `annees_sans_refonte` | `float \| None` | **Wayback CDX** (~1 req/s) | G | o | E |
| `nb_captures_wayback` | `int \| None` | idem | G | o | E |
| `sitemap_lastmod` | `date \| None` | `website.py::_try_sitemap` — déjà fetché | G | o | E |
| `plateformes_sociales` | `list[str]` | `social.py:29` — **collecté, jeté par la rubrique** | D | o | E |
| `mots_cles_locaux` | `bool \| None` | `seo.py` | D | o | E |

---

### Bloc E — `reputation` — nature E, **buckets uniquement** (D4)

| Champ | Type | Source | Palier | Obl. | Nature |
|---|---|---|---|---|---|
| `nb_avis_bucket` | `Literal["0","1-9","10-24","25-99","100+"] \| None` | Places (dérivé de `user_ratings_total`) | G€ | O | E |
| `note_bucket` | `Literal["<3","3-4","4-4.5","4.5+"] \| None` | Places (dérivé de `rating`) | G€ | o | E |
| `avis_suffisants` | `bool \| None` | dérivé (seuil ≥ 20-25, pas 10) | D | o | E |
| `repond_aux_avis` | `bool \| None` | `reviews.py:79` — **collecté, jeté** | G€ | O | E |
| `date_dernier_avis` | `date \| None` | `reviews.py:80` — **collecté, jeté** | G€ | O | E |
| `recence_dernier_avis_jours` | `int \| None` | dérivé | D | O | E |
| `rang_cohorte_recence` / `taille_cohorte` / `cohorte_requete` | `int/int/str \| None` | **résultats SERP déjà en mémoire** — 0 appel supplémentaire | D | o | E |
| `reputation_relevee_le` | `date \| None` | système — pilote la purge 30 j | — | O | M |

> ⚠️ Aucun **texte d'avis** ni **auteur d'avis** ne doit entrer dans le vault : ce sont des données de **tiers** sans lien avec le prospect. `reviews.py` ne persiste aujourd'hui que des agrégats — à protéger par un test.
>
> `rang_cohorte_recence` est le champ à plus fort levier commercial du schéma : « 8e sur 10 sur la récence des avis dans votre secteur » se calcule depuis les résultats SERP déjà payés.

---

### Bloc F — `signaux_techniques` — nature E, palier G/D intégral

| Champ | Type | Source | Palier | Obl. | Nature |
|---|---|---|---|---|---|
| `hebergeur_mail` | `Literal["google","microsoft","mutualise","aucun","autre"] \| None` | DNS MX (`dnspython`, résolveur local) | G | o | E |
| `messagerie_professionnelle` | `bool \| None` | dérivé | D | o | E |
| `spf_present` / `dmarc_present` | `bool \| None` ×2 | DNS TXT | G | o | E |
| `cms` | `str \| None` | fork MIT de Wappalyzer, sur HTML en mémoire | D | o | E |
| `stack` | `list[str]` | idem | D | o | E |
| `pixels_publicitaires` | `list[str]` | regex HTML (Meta Pixel, gtag, GA4, TikTok, LinkedIn Insight) | D | o | E |
| `investit_en_acquisition` | `bool \| None` | dérivé — **proxy de capacité n°1** | D | O | E |
| `pagespeed_mobile` / `lcp_ms` / `cls` | `int/float \| None` ×3 | PageSpeed Insights API (25 000 req/j gratuits) | G€ | o | E |
| `premier_certificat_tls` | `date \| None` | crt.sh (endpoint non documenté, throttling) | G | o | E |
| `robots_txt_autorise` | `bool \| None` | **`robots.txt` du prospect** | G | **B** | M |

> 🔴 `grep -rn "robots" --include=*.py .` ne retourne **rien**. `website.py` fetch sans consulter `robots.txt`. C'est le premier argument qu'un contradicteur soulèvera, et c'est trivial à corriger. `robots_txt_autorise == False` doit **bloquer** la collecte de tout le bloc D, pas seulement être journalisé.
>
> **Ne pas payer BuiltWith ni Wappalyzer** (295–495 $/mois) : `stack.py` en collecteur dérivé palier 0, alimenté par `_website_signals`, couvre le besoin à 0 appel — exactement le patron de `seo.py`/`social.py`.

---

### Bloc G — `signaux_intention` — nature E, palier G, **asymétrique par marché**

| Champ | Type | Source | Palier | Obl. | Nature |
|---|---|---|---|---|---|
| `recrute_actuellement` | `bool \| None` | France Travail API v2 (FR, 4 req/s/app) · Guichet-Emplois dump mensuel (QC) · **CH : aucune source trouvée** | G | o | E |
| `nb_offres_ouvertes` | `int \| None` | idem | G | o | E |
| `date_derniere_offre` | `date \| None` | idem | G | o | E |
| `page_carrieres_detectee` | `bool \| None` | regex HTML — **fonctionne sur les 3 marchés** | D | o | E |
| `annonces_publicitaires_actives` | `bool \| None` | Meta Ad Library (**UE seulement** pour le non-politique) | G | o | E |
| `badge_fabricant` | `list[str]` | regex HTML (Carrier FAD, Lennox Premier, Daikin Comfort Pro) | D | o | E |
| `intention_relevee_le` | `date \| None` | système | — | o | M |

> Couverture réelle : **excellente en France**, moyenne au Québec (dump mensuel), **quasi nulle en Suisse**. `page_carrieres_detectee` est le seul signal d'intention symétrique sur les trois marchés — et il coûte 0 appel.

---

### Bloc H — `contact` — **GELÉ, aucun champ ajouté** (D2)

| Champ | Type | Source | Palier | Obl. | Nature |
|---|---|---|---|---|---|
| `contact_nom` `contact_titre` `contact_email` `contact_linkedin` | `str \| None` ×4 | Apollo `/v1/people/search` **ou** site officiel | €/G | o | **P** |
| `contact_email_source` | `str \| None` | Apollo `email_status` (`verified`/`guessed`) | € | **B** | P |
| `contact_type` | `Literal["nominatif","fonctionnel"] \| None` | **dérivé** du localpart (`contact@`/`info@` → fonctionnel) | D | O | M |

> `contact_type` est le seul ajout, et il **réduit** l'exposition : une adresse fonctionnelle (`contact@entreprise.ca`) n'identifie pas une personne physique et sort largement du champ des données personnelles. Le système doit **préférer** le fonctionnel. C'est un cran entier de régime juridique en moins, obtenu par un champ dérivé.
>
> 🔴 `contact_email_source` est marqué **bloquant** : un email `guessed` ne peut pas fonder un consentement tacite CASL (par. 10(9)b exige une adresse **publiée**), ne satisfait pas l'opt-in suisse, et prédit un bounce qui dégrade la délivrabilité du domaine émetteur. Ce n'est pas un indicateur de qualité, c'est un **discriminant juridique**.

---

### Bloc I — `conformite` — nature M (métadonnée de traitement, pas donnée sur la personne)

| Champ | Type | Source | Obl. | Nature |
|---|---|---|---|---|
| `base_legale` | `Literal["interet_legitime","coordonnees_affaires","consentement"] \| None` | **ICP** (`icp/*.yaml` porte la base légale du marché) | **B** | M |
| `regime_marche` | `Literal["casl","nlpd_lcd","rgpd"] \| None` | `compliance/<marche>.yaml` | O | M |
| `information_art14_transmise_le` | `date \| None` | J6 (premier message) | o | M |
| `opt_out` | `bool` = False | *existe déjà* | **B** | M |
| `opt_out_date` | `date \| None` | humain / détection site | o | M |
| `opt_out_source` | `Literal["humain","site_mention_refus","fournisseur","destinataire"] \| None` | — | o | M |
| `transfert_documente_ref` | `str \| None` | réf. EFVP (art. 17 LPRPSP) / TIA | **B** (QC) | M |
| `conserve_jusquau` | `date \| None` | **calculé** (§4) | O | M |
| `ia_assistance` | `bool` = False | `synthesis.py` — True **seulement** si appel LLM effectif | O | M |
| `ia_modele` / `ia_profil` | `str \| None` ×2 | `LedgerEntry.modele/.profil` (champs existants) | o | M |

> `ia_assistance` doit être conditionné à l'**appel LLM réel**, pas au chemin de code : le repli déterministe (sans clé) n'est pas de l'IA générative et ne doit pas porter la mention art. 50.
>
> ✅ Point favorable non intentionnel : `export_kemana.yaml` n'exporte **pas** `accroche` — seul `signal_chaud`, calculé déterministement dans `serializers.py:30`. Le CSV ne transporte donc aucun texte LLM. Le risque art. 50 est **humain** (l'opératrice recopie l'audit lu dans Obsidian) → le marquage doit être dans `diagnostic_to_rapport_md`, là où elle le lit.

---

### Bloc J — `qualification` — nature M, 100 % dérivé

| Champ | Type | Calcul | Obl. |
|---|---|---|---|
| `score_besoin` | `int 0-100 \| None` | = `score_global` existant (sévérité du problème) | O |
| `score_capacite` | `int 0-100 \| None` | §3.2 — **axe orthogonal, nouveau** | O |
| `score_completude` | `int 0-100` | §3.1 | O |
| `completude_par_bloc` | `dict[str,int]` | §3.1 | o |
| `bande_besoin` | `Literal["trop_bas","utile","trop_haut"]` | `<35` / `35-75` / `>75` | O |
| `priorite` | `Literal["A","B","C","D"] \| None` | matrice besoin × capacité | O |
| `disqualifie` | `bool` = False | §3.3 | **B** |
| `motif_disqualification` | `Literal[...] \| None` | liste fermée §3.3 | o |
| `pret_a_contacter` | `bool` = False | **porte §3.4** | O |
| `motif_rejet` | `Literal[...] \| None` | **saisi par l'humain à `→ rejete`** | o |

> 🔴 `motif_rejet` est le champ le plus rentable du schéma. Aujourd'hui `transition(→ rejete)` n'enregistre **aucune raison** (`vault_io.py:256` journalise `"diagnostique→rejete acteur=humain"` et rien d'autre). Sans lui, un taux de rejet de 60 % ne dit pas s'il faut corriger l'ICP, les filtres, la rubrique ou l'enrichissement : **la boucle d'apprentissage est ouverte**.
> Liste fermée proposée : `hors_icp` · `trop_petit` · `deja_outille` · `contact_injoignable` · `deja_client_concurrent` · `zone_hors_perimetre` · `donnees_insuffisantes`.

---

### Bloc K — `tracabilite` — §2

---

## 2. TRACABILITÉ — généralisation du principe `contact_email_source`

### 2.1 Le modèle `Provenance` (un par champ ou par groupe de champs)

```python
class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str            # "req:donnees-quebec" | "ademe:rge-2" | "places:text_search"
                              #   | "site_officiel" | "apollo:people_search" | "derive:scoring"
    methode: Literal["api", "dump", "fetch_direct", "derive", "humain"]
    reference: str | None = None   # URL exacte, ou nom+date du dump, ou chemin du dérivé
    collecte_le: date
    confiance: Literal["officielle", "verifiee", "deduite", "declaree"]
    expire_le: date | None = None  # TTL par source (Places 30 j, registre 180 j…)
    run_id: str | None = None      # corrèle .cache/orchestrator/<run_id>.json
```

### 2.2 Rattachement

| Champ ajouté à `FicheProspect` | Type | Rôle |
|---|---|---|
| `sources` | `dict[str, Provenance]` | **clé = chemin pointé du champ ou du bloc** : `"identite_legale"`, `"certification.licence_rbq"`, `"contact.email"` |
| `run_ids` | `list[str]` | tous les runs ayant touché la fiche |
| `schema_version` | `int` = 1 | §5 |

Granularité : **une entrée par bloc** par défaut, **par champ** uniquement quand la provenance diffère à l'intérieur du bloc (typiquement `certification` : RBQ vient d'un dump, `certification_affichee_sur_site` d'un dérivé HTML).

### 2.3 La preuve à trois niveaux — ce qu'une autorité réclamera

| Question | Répondu par | Existe déjà ? |
|---|---|---|
| **D'où vient cette donnée ?** | `sources[chemin].source_id` + `.reference` + `.collecte_le` | ❌ à créer |
| **Quel appel l'a produite ?** | `api_usage.log` (`LedgerEntry.fiche`, `fournisseur`, `endpoint`, `ts`) ⇄ `runs.log` (`vault_io._journal`) corrélés **par intervalle temporel** via `.cache/orchestrator/<run_id>.json` | ✅ **existe et c'est exactement ce qu'il faut** |
| **L'opposition a-t-elle été honorée ?** | `opt_out` + `opt_out_date` + **liste de suppression persistante hors vault** testée **avant** `PersonEnrichment` | ⚠️ partiel |

> 🔴 **Défaut de jointure à corriger** : `api_usage.log` identifie une fiche par son **nom d'entreprise** (`"fiche": "Climatisation Test"`, cf. `enrichment.py:70` `fiche=candidate.nom`), `runs.log` par son **nom de fichier slugifié** (`vault_io._slugify`). La jointure est déterministe mais exige d'appliquer `_slugify` côté analyse. Correctif propre et rétro-compatible : ajouter `fiche_slug: str | None = None` à `LedgerEntry` — exactement le patron des 7 champs GreenIT (`api_schema.py:38-44`, tous optionnels avec défaut, `extra="forbid"` interdit les champs inconnus **pas** les champs manquants).

### 2.4 Provenance CASL — la seule qui fournit sa propre preuve

Pour le Québec, le consentement tacite repose sur une coordonnée **publiée bien en vue**. Une adresse extraite du site officiel produit sa preuve : `source_id="site_officiel"`, `reference="<URL de la page>"`, `collecte_le`, `confiance="officielle"`. Une adresse Apollo ne prouve que « un tiers la détenait » — ce n'est pas le même fait juridique. **`Provenance` n'est donc pas de la documentation : c'est la pièce du dossier.**

---

## 3. SCORING DE COMPLÉTUDE ET PORTE « PRÊT À CONTACTER »

### 3.1 Complétude — `knowledge/completude.yaml` (donnée, pas code)

```yaml
# Poids = 100 au total. Un bloc absent (None) score 0.
# `bloquants` : champs dont l'absence plafonne le bloc à 0, quel que soit le reste.
version: 1
blocs:
  identite_legale:
    poids: 20
    bloquants: [identifiant_legal, statut_administratif]
    champs: [raison_sociale, date_immatriculation, tranche_effectif, code_activite, entreprise_individuelle]
  presence_numerique:
    poids: 25
    bloquants: [domaine_normalise, https, viewport_mobile]
    champs: [formulaire_contact, tel_cliquable_mobile, derniere_maj, has_title, meta_description, mots_cles_locaux]
  reputation:
    poids: 20
    bloquants: [nb_avis_bucket]
    champs: [repond_aux_avis, recence_dernier_avis_jours, note_bucket, rang_cohorte_recence]
  etablissement:
    poids: 15
    bloquants: [a_fiche_gbp]
    champs: [telephone_public, ville, horaires_publies, coherence_nap]
  certification:
    poids: 10
    bloquants: []          # non bloquant : la non-détention EST une information
    champs: [certification_affichee_sur_site, programmes_subvention_mentionnes]
  contact:
    poids: 10
    bloquants: [contact_type]
    champs: [contact_email, contact_titre]
# Blocs hors score : signaux_techniques et signaux_intention sont des BONUS
# (ils alimentent score_capacite, pas la complétude du dossier).
```

**Calcul** — déterministe, aucun LLM :
```
completude_bloc = 0                              si un bloquant est None
                = 100 × (renseignés / total)     sinon   (bloquants + champs)
score_completude = Σ (completude_bloc × poids) / 100
```

⚠️ **`None` ≠ `False`.** C'est le défaut A1 du moteur de scoring (`scoring.py:29-30` : `if value is None: return False`), qui fabrique 45 % de la pondération à zéro sans clé Places. Le calcul de complétude doit distinguer trois états : **renseigné** / **absent** / **non applicable au marché** (ex. `licence_rbq` en France). Un champ non applicable sort du dénominateur, il ne pénalise pas.

### 3.2 Capacité à payer — second axe, `knowledge/capacite.yaml`

| Signal | Champ | Points | Disponible ? |
|---|---|---|---|
| Achète de la publicité | `investit_en_acquisition` | 30 | dérivé, 0 appel |
| Badge fabricant | `badge_fabricant` non vide | 20 | dérivé, 0 appel |
| Recrute | `recrute_actuellement` ∨ `page_carrieres_detectee` | 15 | G |
| Site frais (< 12 mois) | `fraicheur_mois <= 12` | 15 | **déjà collecté** |
| Volume d'avis | `nb_avis_bucket >= "25-99"` | 10 | dérivé |
| Effectif | `tranche_effectif >= "5-9"` | 10 | G |

### 3.3 Disqualification automatique — avant la porte humaine

| Motif | Règle |
|---|---|
| `opt_out` | `opt_out == True` — **absolu, déjà appliqué** |
| `hors_perimetre` | `statut_administratif != "actif"` ∨ ville hors ICP |
| `donnees_insuffisantes` | `score_completude < 40` |
| `injoignable` | `contact_email is None` ∧ `telephone_public is None` |
| `email_non_fiable` | `contact_type == "nominatif"` ∧ `contact_email_source != "verified"` ∧ marché ∈ {quebec, romandie} |
| `trop_petit` | `nb_avis_bucket == "0"` ∧ `a_fiche_gbp == False` ∧ `tranche_effectif` sous plancher |
| `non_collectable` | `robots_txt_autorise == False` |
| `conformite_absente` | `base_legale is None` ∨ (marché=quebec ∧ `transfert_documente_ref is None`) |

> Chaque disqualification automatisée est du temps rendu au goulot réel. **Ne pas faire arbitrer par un humain ce qu'une règle déterministe peut trancher.**

### 3.4 La porte `pret_a_contacter` — conjonction, pas moyenne

```
pret_a_contacter =
      disqualifie == False
  AND score_completude          >= 70
  AND completude_bloc(contact)  == 100
  AND bande_besoin              == "utile"        # 35 <= score_besoin <= 75
  AND score_capacite            >= 40
  AND base_legale               is not None
  AND opt_out                   == False
  AND (date_diagnostic est vieux de <= 30 jours)
  AND au moins UNE preuve datée à valeur non-None issue d'un collecteur ayant réellement répondu
```

> 🔴 La dernière clause est le correctif de crédibilité n°1. Aujourd'hui `serializers.py:30` prend `hautes[0].preuve` ; comme `site_web` (6 checks, max 0,25) ne produit jamais de gravité `haute` alors que `gbp.verified` (2 checks, 0,60) en produit toujours une, **chaque ligne de l'export part avec la même accroche non vérifiée**. Un `Gap` issu d'un signal `None` ne doit jamais pouvoir devenir `signal_chaud`.
>
> Un seuil unique sur `score_completude` ne suffit pas : un dossier à 85 % sans email n'est pas contactable. D'où la conjonction.

### 3.5 Priorité (tri de l'export — corrige le biais actuel)

| | Capacité ≥ 60 | Capacité 40-59 | Capacité < 40 |
|---|---|---|---|
| **Besoin 55-75** | **A** — cible prioritaire | B | D — puits de temps |
| **Besoin 35-54** | B | C | D |
| **Besoin < 35 ou > 75** | D | D | D |

`run_export.py` trie aujourd'hui sur `score_global` seul → il remonte **les entreprises les plus petites, les plus cassées et les moins solvables**. Trier sur `(priorite, score_capacite desc, recence_dernier_avis_jours desc)`.

---

## 4. RÉTENTION ET PURGE

### 4.1 TTL par bloc — `compliance/<marche>.yaml` (donnée)

| Bloc | TTL | Fondement | Action à expiration |
|---|---|---|---|
| `etablissement` (champs Places hors `place_id`) | **30 j** | Maps Platform Terms | purge des dérivés, **`place_id` conservé** |
| `reputation` | **30 j** | idem + pertinence commerciale (une preuve d'avis de 6 semaines se retourne contre l'émetteur) | purge, re-collecte au prochain diagnostic |
| `signaux_intention` | 90 j | pertinence | purge |
| `signaux_techniques` | 180 j | stabilité | re-collecte |
| `presence_numerique` | 180 j | stabilité | re-collecte |
| `identite_legale` / `certification` | 365 j | registres officiels, faible volatilité | re-collecte |
| `contact` (**P**) | **fiche `decouvert`/`diagnostique` non validée : 12 mois** · fiche `valide` non contactée : 24 mois · fiche `contacte` : 36 mois puis purge (alignement purge FR à 3 ans d'inactivité) | RGPD art. 5.1.e | **purge du bloc contact, fiche conservée** |
| `conformite` / `tracabilite` | **conservé après purge du contact** | redevabilité art. 5.2 — la preuve doit survivre à la donnée | — |

`conserve_jusquau` = `min(TTL de chaque bloc appliqué à sa date de collecte)`, recalculé à chaque écriture.

### 4.2 Opt-out — la règle non évidente

**Supprimer la fiche détruit la preuve de l'opposition et garantit sa réintroduction au run suivant** (la dédup inter-runs de `run_discovery.py` s'appuie sur `vault_io.exists()`, donc sur l'existence de la fiche).

Procédure :
1. `opt_out = True`, `opt_out_date`, `opt_out_source` renseignés ;
2. **purge immédiate** des blocs `contact` (P) et `signaux_intention` ;
3. la fiche est conservée en **tombstone** : `nom`, `domaine_normalise`, `identifiant_legal`, `opt_out*`, `tracabilite` ;
4. écriture d'une entrée dans une **liste de suppression persistante hors vault** (`.suppression/<marche>.jsonl`, gitignorée, clé = hash du domaine et hash de l'email) ;
5. **`PersonEnrichment.enrich()` teste cette liste AVANT tout appel Apollo** — pas seulement à l'export. Sinon la ré-exécution idempotente réintroduit un contact opposé et fait payer un crédit pour ça.

### 4.3 Purge — nouveau nœud DAG

`purge` déclaré dans `dag_pipeline.yaml`, exécuté après `usage_snapshot`. Il n'écrit que via `vault_io` (invariant : `os.replace()` reste l'exclusivité de `vault_io.py`), journalise chaque purge dans `runs.log` via `_journal`, et est **idempotent**. Une purge non journalisée n'est pas une purge : c'est une perte de données.

---

## 5. MIGRATION — étendre sans casser

### 5.1 Les six règles

| # | Règle | Pourquoi |
|---|---|---|
| **M1** | **Additif uniquement.** Aucun champ existant n'est renommé, retypé ou supprimé. | Les fiches antérieures se relisent. C'est le patron déjà validé deux fois : J4 (`contact_*`) et J5 (`signal_chaud`, `accroche`) — commentaire explicite `vault_schema.py:100`. |
| **M2** | **Tout nouveau bloc est `Bloc \| None = None`**, jamais `default_factory`. | `None` = « jamais collecté », bloc vide = « collecté, rien trouvé ». Cette distinction est la base du scoring de complétude (§3.1) et disparaît avec `default_factory`. |
| **M3** | **Tout champ dans un bloc est `T \| None = None`.** Les sous-modèles utilisent `extra="forbid"`. | Même mécanique que `LedgerEntry` (`api_schema.py:21` + champs GreenIT l. 38-44) : `extra="forbid"` interdit les champs **inconnus**, pas les champs **manquants**. Les anciennes lignes se relisent sans migration. |
| **M4** | **`FicheProspect` garde `extra="allow"`.** | Annotations humaines Obsidian préservées en round-trip. ⚠️ Contrepartie : un champ mal orthographié est silencieusement persisté — d'où M5. |
| **M5** | **`schema_version: int = 1`**, incrémenté à chaque extension. Absent d'une vieille fiche → vaut 1 par défaut. | Permet un backfill ciblé (`query(schema_version=1)`) et rend l'inventaire des fiches non migrées calculable. |
| **M6** | **Jamais de renommage : on ajoute à côté et on déprécie.** Ex. `gbp.verified` → nouveau `etablissement.gbp_operationnel`, l'ancien champ reste lisible et marqué déprécié dans le YAML de rubrique. | Un renommage casse `export_kemana.yaml` (validé contre `FicheProspect.model_fields` — `export.py:31`), les requêtes Dataview du dashboard, et les fiches en cours. |

### 5.2 Forme du modèle

```python
class BlocOsint(BaseModel):
    """Base de tous les blocs OSINT. extra='forbid' : la minimisation est
    garantie par le schéma, pas par la discipline (patron Contact)."""
    model_config = ConfigDict(extra="forbid")

class IdentiteLegale(BlocOsint):
    identifiant_legal: str | None = None
    identifiant_type: Literal["neq", "ide", "siren", "siret"] | None = None
    # … tous optionnels, tous None par défaut

class FicheProspect(BaseModel):
    model_config = ConfigDict(extra="allow", use_enum_values=True)   # INCHANGÉ

    # ... 23 champs existants, INCHANGÉS, dans le même ordre ...

    # --- Extension OSINT (schema_version 2) -----------------------------
    # Tous optionnels et None par défaut : les fiches v1 se relisent sans
    # migration, exactement comme les champs J4 puis J5 avant elles.
    schema_version: int = 1
    identite_legale:     IdentiteLegale     | None = None
    certification:       Certification      | None = None
    etablissement:       Etablissement      | None = None
    presence_numerique:  PresenceNumerique  | None = None
    reputation:          Reputation         | None = None
    signaux_techniques:  SignauxTechniques  | None = None
    signaux_intention:   SignauxIntention   | None = None
    conformite:          Conformite         | None = None
    qualification:       Qualification      | None = None
    sources:             dict[str, Provenance] = Field(default_factory=dict)
    run_ids:             list[str]             = Field(default_factory=list)
    contact_type:        Literal["nominatif", "fonctionnel"] | None = None
```

### 5.3 Séquence d'implémentation (chaque étape livrable et testable seule)

| Étape | Contenu | Risque | Prérequis clé API |
|---|---|---|---|
| 1 | `schema_version` + `Provenance` + `sources` + `run_ids`. Aucun collecteur. | nul | aucun |
| 2 | Test de rétro-compatibilité **golden files** : 5 fiches figées (une par génération : pré-J4, J4, J5, v1 complète, v1 avec annotations humaines) relues et re-sérialisées à l'identique. | nul | aucun |
| 3 | Blocs `conformite` + `qualification` + `motif_rejet` (aucun collecteur, tout dérivé ou humain). | nul | aucun |
| 4 | Blocs `presence_numerique` + `reputation` — **câblage des 5 signaux déjà collectés et jetés** (`repond_aux_avis`, `date_dernier_avis`, `derniere_maj`/`fraicheur_mois`, `plateformes_mentionnees`, `title_len`). | faible | **aucune** |
| 5 | Bloc `certification` + collecteur `certification.py` (dumps RBQ / ADEME, regex HTML). | faible | **aucune** |
| 6 | Bloc `signaux_techniques` + collecteurs `domaine.py` (RDAP/DNS/crt.sh), `stack.py` (fork MIT), `archive.py` (Wayback). | moyen | **aucune** |
| 7 | Bloc `identite_legale` + collecteur `registre.py` (dump REQ, puis Zefix/Sirene au rythme de la séquence géographique). | moyen | aucune |
| 8 | Bloc `etablissement` + refonte `gbp.py`/`reviews.py` en dérivés/buckets + TTL par fournisseur. | **élevé** — touche des collecteurs existants | Places |
| 9 | Bloc `signaux_intention`. | moyen | aucune |

**Les étapes 1 à 7 et 9 ne nécessitent aucune clé API et ne lèvent pas le NO-GO préflight.** Elles sont réalisables et testables aujourd'hui.

### 5.4 Ce qui doit être adapté en même temps

| Fichier | Modification | Impératif |
|---|---|---|
| `diagnostic/export.py:84` | support des chemins pointés dans `fiche_vers_ligne_kemana` **et** dans la validation `champs_fiche` (l. 31-37) | sinon toute colonne imbriquée lève `ValueError` à l'import |
| `knowledge/export_kemana.yaml` | 10 → 14-15 colonnes : ajouter `gaps_majeurs`, `accroche`, `rapport`, `date_diagnostic`, `etablissement.telephone_public`, `etablissement.ville`, `qualification.priorite`, `qualification.score_capacite`. **Ces 4 premiers existent déjà dans `FicheProspect` et ne sont pas exportés.** | pure édition YAML |
| `diagnostic/preflight.py:251` | ajouter à `_check_garde_fous_bus` **chaque** nouveau module (`registre.py`, `certification.py`, `domaine.py`, `archive.py`, `perf.py`, `stack.py`, `emploi.py`, `contact_site.py`) **et** `greenit.py` (dette technique n°2 déjà inscrite dans `CLAUDE.md`) | la règle « tout nouveau module de ce type doit y être ajouté » se reproduira mécaniquement sinon |
| `diagnostic/api_schema.py` | `fiche_slug: str \| None = None` sur `LedgerEntry` (patron GreenIT, rétro-compatible) | débloque le coût par prospect **qualifié** (§2.3) |
| `knowledge/greenit.yaml:106` | `cache_ttl_jours` **par fournisseur** (Places < 30 j) | conflit CGU Maps Platform (D4) |
| `tests/test_doc_coherence.py` | recompter tests, routes, écrans, invariants | garde-fou anti-hallucination du projet |
| `.gitignore` | `.suppression/` | §4.2 |

---

## 6. CE QUE CE SCHÉMA NE FAIT PAS (limites assumées)

- **Il ne mesure rien après `contacte`.** Pas d'état `rdv` ni `client`, pas de date ni de montant → aucun coût par rendez-vous, aucun ROI calculable. Ajouter ces deux états relève de la machine à états (`vault_schema.py:56`), pas de ce schéma.
- **Il ne lève pas le NO-GO préflight.** `api_pricing.yaml` reste à `0` / `releve_le: null` : tout coût affiché vaut 0,00 et n'est pas engageant.
- **Les blocs `identite_legale`, `certification` et `signaux_intention` supposent des dumps locaux** (REQ bimensuel, RBQ, ADEME hebdo, Sirene stock). Ce sont des fichiers volumineux : leur place est `.cache/`, **hors vault** (contrainte G9), et ils relèvent du « disque », pas de la « RAM ».
- **Le taux de renseignement réel de chaque champ sur les 6 localités de l'ICP n'est pas mesuré** — aucun run réel n'a jamais eu lieu. Les poids de `completude.yaml` sont un point de départ à recalibrer après le premier run borné, pas une vérité.
- **La qualification juridique des blocs `E*` (entreprise individuelle), la portée ODbL si OSM est retenu, la conservation des champs Places au regard des Maps Platform Terms, et l'EFVP art. 17 LPRPSP** relèvent du juriste, au même titre que J6. Le schéma les rend **traçables et purgeables** ; il ne les tranche pas.

---


<a id="s10"></a>

## 10. Revues anti-hallucination


Deux revues indépendantes ont audité les artefacts.

| Revue | Verdict | Aval | Chiffres non sourcés | Hallucinations |
|---|---|---|---|---|
| Chiffres / tarifs | approuve_avec_reserves | ✅ accordé | 8 | 3 |
| Architecture / invariants | approuve_avec_reserves | ❌ **REFUSÉ** | 8 | 4 |

### Revue des chiffres — approuve_avec_reserves

**Taux de fiabilité.** 94,2 % — 344 assertions chiffrées correctement sourcées ou correctement étiquetées / 365 assertions chiffrées distinctes recensées. Méthode de comptage : une « assertion chiffrée distincte » = un prix, un quota, un palier gratuit, un rate-limit, un coût unitaire dérivé, un taux de couverture ou un volume, compté une fois par fournisseur et par artefact. Répartition : SERP ~135 assertions / 7 défauts ; Enrichissement contact ~85 / 5 ; OSINT ~75 / 3 ; Conformité+FinOps ~70 / 6. Une assertion est comptée « correcte » si elle porte une étiquette de provenance explicite (SOURCE OFFICIELLE INDIRECTE / RAPPORTÉ PAR UN TIERS / NON VÉRIFIÉ / NON TROUVÉ), qu'elle n'est pas contredite par ma contre-vérification, et qu'elle n'est pas reprise ailleurs sans son avertissement. Le taux est élevé non parce que les prix sont justes, mais parce que la discipline d'étiquetage est réelle : les quatre artefacts déclarent en tête que WebFetch/curl renvoient 403 et qu'AUCUNE page tarifaire n'a été ouverte. Seuls les tarifs Anthropic sont pleinement vérifiés (contre-vérifiés OK par moi : Haiku 4.5 = 1 $/5 $ par MTok, Sonnet 4.5 = 3 $/15 $).


**Hallucinations détectées :**

- ⚠️ *« Google Places API — Coût réel pour le volume du projet : 0,00 USD grâce aux 1 000 appels Enterprise gratuits mensuels » (artefact SERP, justification du verdict RECOMMANDÉ, répété dans la recommandation finale §2)* → Ce n'est pas une hallucination de fait — le raisonnement est arithmétiquement juste (1 000 / 18 ≈ 55 runs) — mais une hallucination de CERTITUDE. Un coût de 0,00 USD est énoncé au présent de l'indicatif, dans un verdict, alors que : (a) les montants et les quotas sous-jacents sont RAPPORTÉS PAR DES TIERS de l'aveu même de l'étude ; (b) le SKU réellement déclenché n'a pas été établi (l'étude le dit dans ses incertitudes, puis retient Enterprise « par prudence » et conclut quand même à 0,00 USD) ; (c) le projet pose comme règle qu'aucun coût affiché n'est engageant tant que api_pricing.yaml est à zéro. C'est exactement le mécanisme par lequel un chiffre d'étude devient une décision budgétaire fausse.
- ⚠️ *Application de la grille tarifaire Places API (New) — SKU Essentials/Pro/Enterprise — au coût des appels actuellement émis par le code (artefacts SERP et Conformité+FinOps)* → Erreur de modélisation vérifiée dans le code : gbp.py et reviews.py appellent maps.googleapis.com/maps/api/place/textsearch/json et /details/json, c'est-à-dire l'API Places LEGACY, qui a sa propre grille et ses propres SKU — et non places.googleapis.com (Places API New) auquel s'applique le modèle Essentials/Pro/Enterprise. L'artefact SERP note la dette « legacy » mais chiffre quand même en SKU New ; l'artefact FinOps construit tout son point « le plus important de l'étude » (champs demandés → Enterprise+Atmosphere) sur la grille New appliquée à un appel legacy. Le point de fond reste juste (reviews.py demande fields=rating,user_ratings_total,reviews,photos — vérifié ligne à ligne — donc le SKU le plus cher), mais le prix qui en serait tiré pour api_pricing.yaml serait rattaché à la mauvaise grille.
- ⚠️ *« Places renvoie rating et userRatingCount dès le premier appel : 45 des 100 points de la rubrique (avis 20 + presence_locale 25) sont pré-alimentés AVANT le diagnostic »* → VÉRIFIÉ ET EXACT — je le consigne ici parce que c'était le candidat hallucination le plus probable et qu'il ne l'est pas. Contrôle effectué : rubric_persona1.yaml donne bien avis=20 et presence_locale=25 (total 45/100) ; gbp.py::_parse_place dérive verified de business_status == OPERATIONAL et has_photos de la liste photos, deux champs qu'un Text Search retourne ; reviews.py alimente count et avg. La chaîne d'inférence tient. Aucune correction requise.

**Chiffres non sourcés :**

- *Brave Search API — « palier gratuit = 2 000 requêtes/mois, carte utilisée pour vérification d'identité uniquement, non débitée » ; « couvre environ 111 runs/mois » ; « Coût réel pour le pilote envisagé : 0,00 USD » (artefact SERP, verdict RECOMMANDÉ)* → Étiqueté SOURCE OFFICIELLE INDIRECTE, donc présenté comme fiable — mais contredit par ma contre-vérification. Brave a supprimé son palier gratuit en février 2026 et l'a remplacé par 5 USD de crédit mensuel (≈ 1 000 requêtes à 5 USD/1 000), conditionné à l'attribution publique de Brave sur le site ; la carte enregistrée à l'inscription EST désormais débitée au-delà. Les trois chiffres dérivés (2 000/mois, 111 runs, pilote à coût nul) tombent avec la prémisse. C'est le défaut le plus grave du lot : il porte l'économie de l'un des deux verdicts « recommandé ». — **Action :** Corriger avant toute décision : Brave = 5 USD de crédit/mois ≈ 1 000 requêtes, sous condition d'attribution. Recalculer : 18 requêtes/run → ~55 runs/mois dans le crédit, et non 111. Le verdict « recommandé comme deuxième source » reste défendable sur l'argument juridique (index indépendant, hors CGU Google), pas sur l'argument « pilote à coût nul ».
- *Apollo — « Organization à 119 USD/utilisateur/mois = 1 428 USD/an = 2,38 USD par contact » (artefact Enrichissement contact, tableau de synthèse des coûts annuels)* → Le calcul 119 × 12 est arithmétiquement juste mais ignore le minimum de 3 sièges du plan Organization — minimum que l'artefact Conformité+FinOps mentionne pourtant explicitement (« Organization 119–149 $ (min. 3 sièges) ») et qu'il applique lui-même dans son scénario 2 000/mois (3 × 119 = 357 $/mois). Contradiction interne entre deux artefacts du même lot. Ma contre-vérification confirme le minimum de 3 utilisateurs. Le vrai plancher du statu quo est donc ≈ 4 284 USD/an, soit ≈ 7,14 USD par contact à 600 contacts/an — trois fois le chiffre annoncé, et cela change le classement économique du panel. — **Action :** Retenir 4 284 USD/an (3 sièges × 119 × 12) comme plancher du statu quo Apollo, et le reporter dans le tableau de synthèse. Cela renforce, sans l'inverser, la conclusion « ne pas souscrire Apollo ».
- *Apollo — « le Basic n'inclut pas l'accès API → Professional (79 USD/mois) est le plancher praticable » et, dérivé, « Un pilote à ~80 USD tout compris est plausible » (artefact Conformité+FinOps, §B.3 et §B.4)* → Contredit par ma contre-vérification et par l'artefact Enrichissement contact du même lot : l'accès à la clé API maître est réservé au plan Organization ; Free, Basic et Professional n'ouvrent que les intégrations marketplace (Zapier, Make, CRM natif), pas les appels REST bruts. Or diagnostic/enrichment.py appelle https://api.apollo.io/v1/people/search en direct. Le « pilote à ~80 USD » et l'hypothèse basse « 0,045 USD/fiche » reposent sur ce 79 USD. — **Action :** Trancher ce point sur docs.apollo.io AVANT toute saisie budgétaire. Si Organization est confirmé, le pilote passe de ~80 USD/mois à ~357 USD/mois et l'hypothèse basse du coût par fiche est invalide.
- *Anymailfinder — « 14 USD/mois pour 50 emails vérifiés = 0,28 USD par email livré = 168 USD/an », présenté comme « le meilleur ajustement économique de tout le panel »* → L'artefact signale lui-même l'incohérence entre grilles tierces (14 $ vs 49 $ pour l'entrée de gamme) et demande vérification — étiquetage correct. Ma contre-vérification pointe une page officielle intitulée « Plans from $29/mo · Pay Only for Verified Emails » : le palier à 14 USD paraît périmé. À 29 USD/mois, le coût passe à 348 USD/an et 0,58 USD par contact, ce qui le fait rétrograder derrière Dropcontact Starter et Snov.io dans son propre classement. — **Action :** Ne pas retenir 14 USD/mois. Recalculer sur 29 USD/mois tant que la page officielle n'a pas été ouverte par l'opératrice.
- *SerpApi — palier gratuit « 250 recherches/mois » (artefacts OSINT §6 et Conformité+FinOps §B.3), utilisé dans le tableau de scénarios FinOps pour conclure « SERP $ = 0 » sur le régime 500 fiches/mois (167 requêtes)* → L'artefact SERP relève la contradiction (100 selon une recherche restreinte au domaine officiel, 250 selon les tiers) et la déclare NON TRANCHÉE. Ma contre-vérification donne 100 recherches/mois. Les deux autres artefacts retiennent 250 sans mentionner la contradiction — et le scénario 500 fiches/mois (167 requêtes) ne tient QUE si le palier est à 250. À 100, ce régime devient payant. — **Action :** Retenir 100/mois comme hypothèse de travail. Marquer la cellule « Régime 500/mois → SERP $0 » du tableau FinOps comme invalidée en attente de vérification.
- *Google Places — « Text Search Pro 32,00 USD / 1 000 ; Enterprise 35,00 USD / 1 000 » et « quotas gratuits 10 000 Essentials / 5 000 Pro / 1 000 Enterprise depuis le 2025-03-01 »* → Correctement étiqueté RAPPORTÉ PAR DES TIERS dans les trois artefacts qui l'emploient, et ma contre-vérification concorde sur la structure (Text Search Pro 32 $/1 000 avec 5 000 appels gratuits inclus ; Place Details Pro 17 $/1 000, Enterprise 20 $/1 000 ; seuils gratuits par SKU 5 000 Pro / 1 000 Enterprise ; les champs rating/photos font basculer vers Enterprise, les avis vers Enterprise+Atmosphere à 40 $/1 000). MAIS : les trois artefacts divergent entre eux sur Place Details (17 $ chez OSINT, hypothèse 32 $ chez FinOps, non chiffré chez SERP), et FinOps pose explicitement p_place_details = p_text_search, soit une surestimation d'environ ×1,9. — **Action :** Ne saisir aucun de ces montants. Ouvrir developers.google.com/maps/documentation/places/web-service/usage-and-billing et relever le SKU réellement déclenché par le masque de champs utilisé, champ par champ.
- *« Un fork MIT de Wappalyzer embarque 251 fingerprints dans le ruleset embarqué et ~6 000 technologies dans les rulesets communautaires » (artefact OSINT §4)* → Fausse précision : « 251 » est un chiffre à trois chiffres significatifs pour un dépôt communautaire mouvant, étiqueté [TIERS] et concordant sur 4 sources non nommées individuellement. Le chiffre n'a aucune conséquence budgétaire, mais son niveau de précision est en décalage avec sa traçabilité. — **Action :** Arrondir ou supprimer. Ne pas en faire un critère de choix entre forks.
- *BuiltWith — « Basic 295 $/mois, Pro 495 $/mois, Team 995 $/an-mensualisé », avec la note « hausse ~6× en 2026, ancien palier 50/200/400 $ » (artefact OSINT §4)* → Trois paliers dont l'un est exprimé dans une unité différente des deux autres (« /an-mensualisé »), plus un facteur de hausse « ~6× » qui n'est cohérent avec aucun des couples de chiffres donnés (295/50 ≈ 5,9 ; 495/200 ≈ 2,5 ; 995/400 ≈ 2,5). Étiqueté [TIERS], donc non hallucinatoire, mais interne­ment incohérent. — **Action :** Sans conséquence : la recommandation « ne pas payer BuiltWith ni Wappalyzer, utiliser un fork MIT sur le HTML déjà en mémoire » est solide et indépendante de ces montants. Supprimer le « ~6× ».

**Violations / tensions d'invariants :**

- Aucune violation d'invariant d'architecture n'est proposée par les artefacts — contrôle explicite effectué. Les collecteurs suggérés (contact_site.py, registre.py, certification.py, domaine.py, archive.py, perf.py, stack.py, emploi.py) héritent tous de Collector, passent tous par api_io.call, sont tous à ajouter à _check_garde_fous_bus (la règle de CLAUDE.md est citée nommément), et les dumps de registres sont explicitement placés dans .cache/ hors vault. Apify et le mode Standard de DataForSEO sont écartés PRÉCISÉMENT parce qu'ils casseraient le contrat synchrone de api_io.call et le pre-check budgétaire — c'est un raisonnement d'invariant, pas de prix.
- TENSION NON RÉSOLUE, signalée par deux artefacts et non tranchée : les Google Maps Platform Terms interdisent la mise en cache prolongée de la plupart des champs Places (le place_id est l'exception, cachable sans limite), or api_io met en cache sur disque avec un TTL global de 30 jours et le vault persiste note, nb_avis et verified. Les deux artefacts qui recommandent d'ÉTENDRE l'usage de Places (découverte par Text Search) aggravent mécaniquement cette exposition sans la lever. La contre-mesure proposée par l'artefact OSINT est la bonne et doit conditionner la recommandation : ne persister que le place_id et des signaux dérivés non reconstituables (a_fiche_gbp, avis_suffisants, note_bucket), purger les valeurs brutes après scoring, et cloisonner le TTL de cache par fournisseur dans greenit.yaml. À joindre au dossier du juriste avec J6.
- RÈGLE PROJET ENTAMÉE, pas violée : « ne jamais avancer de gain chiffré ni de coût engageant avant la Phase D ». Les énoncés « Coût réel pour le volume du projet : 0,00 USD » (Places, artefact SERP) et « pilote à coût nul » (Brave) sont formulés à l'indicatif présent dans des verdicts, alors que api_pricing.yaml est à zéro et que run_preflight.py est en NO-GO structurel. À reformuler au conditionnel avant toute reprise en note de synthèse destinée à la consultante.

**Réserves :**

- PÉRIMÈTRE DE L'AVAL — il couvre l'usage DÉCISIONNEL (choisir une direction : découverte par établissements plutôt que par SERP, socle interne gratuit avant tout enrichisseur payant, registres publics en couche de vérification) et EXCLUT formellement l'usage de CONFIGURATION. Aucun chiffre de ce lot ne doit être saisi dans knowledge/api_pricing.yaml, et releve_le doit rester à null. Les quatre artefacts le disent eux-mêmes — c'est la raison principale pour laquelle je donne l'aval malgré des prix majoritairement non vérifiés.
- LIMITE MÉTHODOLOGIQUE ASSUMÉE ET CORRECTEMENT DÉCLARÉE — les quatre artefacts ouvrent sur le même constat : WebFetch et curl renvoient 403 sur toutes les pages tarifaires officielles ; tous les chiffres viennent de WebSearch. Cette déclaration est en tête de chaque livrable, avec une taxonomie de niveaux de preuve. C'est ce qui sauve le lot : les prix sont largement faux ou incertains, mais ils ne sont presque jamais présentés comme certains. Ma propre contre-vérification a subi la même contrainte (recherche web, pas lecture de page) — mes corrections ci-dessus ont donc le MÊME niveau de preuve que ce qu'elles corrigent, et ne doivent pas non plus être saisies telles quelles.
- LE POINT QUE LE MANDAT REDOUTAIT — la couverture des bases de contacts sur les TPE québécoises et suisses romandes — est le mieux traité du lot. L'artefact Enrichissement contact écrit explicitement : « Il n'existe AUCUNE mesure publique du taux de succès de ces outils sur ce segment précis — je n'en ai trouvé aucune, et je ne vais pas en inventer une », puis « toute la partie couverture de ce rapport repose sur une inférence argumentée, jamais sur une mesure ». Il pose en outre une règle de décision AVANT le test (>60 % → aucun abonnement ; 40-60 % → Dropcontact ; <40 % → réexaminer le collecteur avant de conclure). C'est la bonne discipline : la seule chose à exiger est que le test sur 50 domaines réels soit effectivement mené avant toute souscription.
- COÛTS D'EXPLOITATION RÉELS — contrôle demandé par le mandat : aucun artefact ne présente un coût d'exploitation constaté du système. Tous les coûts sont conditionnels et rattachés à des hypothèses nommées (ρ = 0,3 déclaré NON MESURÉ ; 50 enrichissements/mois déclaré comme projection tirée de max_enrichissements: 25 lu dans l'ICP ; T_in ≈ 2 300 tokens déclaré ESTIMATION). Une seule exception à surveiller : « Le LLM coûte entre 0,5 et 2,1 cents par fiche » (artefact FinOps) est énoncé au présent avec deux chiffres significatifs, alors que T_in est une estimation et qu'aucun appel LLM n'a jamais eu lieu (ANTHROPIC_API_KEY absente). Le calcul est exact (2 300 × 1e-6 + 600 × 5e-6 = 0,0053 ; escalade Sonnet = 0,0212) et les prix Anthropic sont les seuls vérifiés du lot — mais la formulation devrait rester « borne haute estimée ».
- CHIFFRES DÉRIVÉS DU CODE — j'ai revérifié un par un ceux qui portent des conclusions, tous exacts : 3 gabarits × 6 localités = 18 requêtes et 180 résultats bruts (icp/persona1-quebec.yaml) ; max_enrichissements = 25 ; rubrique 25/25/20/15/15 = 100 ; export Kemana = 10 colonnes sans le champ accroche (donc aucun texte LLM dans le CSV) ; 2 appels Places facturés par fiche, le second text_search étant un cache-hit via cache_key partagé « places:{query} » ; max_tokens_sortie = 600, troncatures 4 000/8 000, cache 30 j (greenit.yaml) ; api_io.call enveloppe bien une closure arbitraire, donc agnostique au verbe HTTP.
- DEUX DÉFAUTS DE CODE SIGNALÉS PAR L'ARTEFACT FINOPS SONT CONFIRMÉS PAR LECTURE DIRECTE, et ils comptent plus que les prix. (1) enrichment.py n'incrémente _nb_enrichissements que si un contact est effectivement extrait (ligne 79-80) : un appel Apollo infructueux consomme le fournisseur sans consommer le quota interne — max_enrichissements ne plafonne donc PAS les appels facturés ; seul le budget api_io le fait. (2) api_schema.py::compute_cout retourne 0.0 sur KeyError : un fournisseur ou un endpoint mal orthographié dans le YAML produit un coût nul silencieux. Ces deux points sont vérifiables, actionnables et indépendants de toute incertitude tarifaire.
- ÉCART DE CONFORMITÉ CONFIRMÉ — grep -rn "robots" --include=*.py ne retourne rien : robots.txt n'est jamais consulté avant le fetch de website.py. Et aucune notion de conservation/purge/rétention dans vault_io.py ni vault_schema.py. Les deux constats de l'artefact Conformité sont exacts. La sanction CNIL contre KASPR est également confirmée : 240 000 EUR, 5 décembre 2024, base d'environ 160 millions de contacts, grief central = collecte de coordonnées que les personnes avaient masquées.
- DATATIONS JURIDIQUES ET STRATÉGIQUES — contre-vérifiées et exactes : rejet par la juge Gonzalez Rogers des demandes DMCA de Google contre SerpApi le 20 juillet 2026, sans possibilité de refiler pour les résultats non protégés, avec 21 jours pour amender sur le périmètre étroit des Knowledge Panels, et intention d'amender confirmée par Google ; Custom Search JSON API fermée aux nouveaux clients avec fin de service au 1er janvier 2027. Ces éléments fondent solidement l'argument de RISQUE DE CONTINUITÉ, que les artefacts prennent soin de ne pas présenter comme une conclusion juridique.
- INCOHÉRENCE MINEURE HORS ARTEFACTS — le contexte de mission annonce « 14 contrôles bloquants en échec » au préflight, là où CLAUDE.md documente 9 contrôles. Aucun artefact ne reprend ce chiffre, donc il n'entre pas dans le taux ; à recompter avant toute reprise dans un livrable (python -c "from diagnostic.preflight import ...").

### Revue d'architecture — approuve_avec_reserves

**Taux de fiabilité.** Deux dénominateurs, parce que les deux artefacts mélangent deux natures d'affirmations. (1) Affirmations sur le code existant, vérifiables ici : 36 contrôlées, 32 exactes → 88,9 % (32/36). J'ai re-exécuté la vérification n°1 et obtenu une sortie identique au caractère près (site_web 100 | presence_locale 0 | avis 0 | seo_local 100 | identite_visuelle 100 | global 55.0, + les 4 mêmes gaps « haute »). (2) Affirmations chiffrées d'origine externe (tarifs, quotas, seuils, volumes, pondérations) : 22 relevées, 0 sourcée → 0 % (0/22). L'architecte le concède lui-même en section E (« Aucune page tarifaire n'a été lue directement dans aucune des quatre [études] ») — mais il s'en sert quand même pour conclure « ne pas optimiser les tokens ». Taux global sur l'ensemble des affirmations chiffrées : 32/58 = 55,2 %. Très en dessous de la porte 97 % du projet.


**Hallucinations détectées :**

- ⚠️ *Schéma OSINT §3.5 : « run_export.py trie aujourd'hui sur score_global seul → il remonte les entreprises les plus petites, les plus cassées et les moins solvables. »* → FAUX, et contredit par l'artefact qui l'accompagne. Vérifié : aucun sort/sorted/key= dans diagnostic/export.py ni dans run_export.py ; collect_fiches_exportables (l. 61-78) renvoie l'ordre brut de vault_io.query(). L'artefact 1 l'établit correctement en vérification n°4 (« c'est pire, il n'y a aucun tri »). Les deux documents livrés ensemble affirment donc deux choses incompatibles sur le même fichier. Conséquence : le §3.5 décrit un biais de tri qui n'existe pas et rate le vrai défaut (ordre non déterministe en sortie).
- ⚠️ *Schéma OSINT bloc I : « export_kemana.yaml n'exporte pas accroche — seul signal_chaud, calculé déterministement dans serializers.py:30. Le CSV ne transporte donc aucun texte LLM. »* → FAUX dans une branche atteignable, et c'est la branche qui compte. serializers.py l. 28-32 : signal_chaud = hautes[0].preuve si failles hautes, SINON failles[0].preuve, SINON diag.accroche. Quand un prospect n'a aucune faille (cas atteignable dès qu'une clé Places est présente et le prospect bon), signal_chaud vaut littéralement le texte LLM. Le CSV transporte alors du texte génératif non marqué. L'artefact en tire pourtant la conclusion « le risque art. 50 est humain » et place le marquage IA dans diagnostic_to_rapport_md seulement — conclusion de conformité fondée sur une prémisse fausse.
- ⚠️ *Schéma OSINT bloc C : « telephone_public est ajouté sciemment […] Absent du système aujourd'hui (vérifié : aucune occurrence de telephone/phone dans le code ni les YAML). »* → FAUX tel qu'écrit. website.py:261 fait soup.find("a", href=re.compile(r"^(tel:|mailto:)")) — le numéro de téléphone est bel et bien lu, il alimente website.has_contact. Les fixtures de test (tests/test_j1_smoke.py:36, tests/integration/faux_api.py:265) contiennent des href tel:. La bonne formulation est « détecté mais non extrait ni persisté », ce qui change l'effort annoncé : le sélecteur existe déjà.
- ⚠️ *Architecture, vérification n°5 : « website.py:94 place 2 000 caractères de la page du prospect dans signaux […] C'est du HTML brut hors du chemin prévu par G9. »* → Deux imprécisions dans une vérification présentée comme factuelle. (a) Ce n'est pas du HTML brut : website.py l. 67 fait text = soup.get_text(" ", strip=True).lower(), puis l. 72 seo_text = titre + meta + text[:2000] — c'est du texte extrait, minusculé. (b) « hors du chemin prévu par G9 » suggère une écriture disque non prévue : vérifié, serializers.py ne lit jamais diag.signaux, donc _seo_text n'atteint jamais le vault. L'exposition réelle se limite à la sortie run_diagnostic --json. Le correctif 0.4 reste souhaitable, mais sa gravité est surévaluée d'un cran.

**Chiffres non sourcés :**

- *« ~600 tokens de sortie plafonnés, ~2 300 en entrée → de l'ordre de 0,5 à 2 cents par fiche » (section E)* → Indérivable ici. api_pricing.yaml a anthropic.messages.prix_par_unite à 0.0 avec releve_le: null (vérifié l. 17 et 29-33), ANTHROPIC_API_KEY est absente, et aucun appel LLM réel n'a jamais eu lieu. Les 600 tokens sont bien dans greenit.yaml:102 ; les 2 300 tokens d'entrée et le coût en cents ne viennent d'aucune mesure ni d'aucune page tarifaire lue. — **Action :** Retirer le chiffre en cents, ou le remplacer par « non mesurable avant la Phase D ». La conclusion (ne pas optimiser les tokens) peut rester si elle s'appuie sur le plafond max_tokens_sortie=600, qui, lui, est vérifiable.
- *« Le poste données représente ~95 % du coût variable, et les abonnements ~85-95 % de la dépense totale au volume visé »* → Aucune source, aucune donnée. Tous les prix du grand livre valent 0 et aucun run réel n'a eu lieu. Ces deux pourcentages portent à eux seuls la recommandation « ne pas optimiser les tokens ». — **Action :** Supprimer les deux pourcentages. Reformuler en argument qualitatif (ordre de grandeur des postes) sans chiffre.
- *« BuiltWith 295 $/mois, Wappalyzer 250 $/mois » (archi C.11) vs « (295–495 $/mois) » (OSINT bloc F)* → Les deux artefacts se contredisent sur le même poste, et aucun ne cite de page tarifaire — ce que la section E de l'artefact 1 reconnaît explicitement pour les quatre études sources. — **Action :** Retirer les montants. La conclusion « ne pas payer, faire un collecteur dérivé palier 0 » tient sans eux.
- *« fork MIT de Wappalyzer » (archi C.11 et OSINT bloc F)* → Licence affirmée comme un fait, sans référence. Wappalyzer a changé de régime de licence en 2023 ; les forks communautaires ne sont pas tous sous MIT. C'est une affirmation juridique (licence) présentée comme acquise, dans un document qui fonde dessus le refus d'un budget outil. — **Action :** Nommer le fork précis et vérifier son fichier LICENSE avant de l'inscrire au plan. Sinon écrire « fork open source à identifier, licence à vérifier ».
- *Quotas gratuits : « PageSpeed Insights 25 000 req/j », « Overpass ≤10 000 req/j », « France Travail API v2, 4 req/s/app », « Wayback ~1 req/s »* → Quatre quotas fournisseurs cités sans source ni date de relevé. Ils dimensionnent directement la faisabilité de perf.py, du recoupement OSM, d'emploi.py et d'archive.py. — **Action :** Traiter ces quotas exactement comme api_pricing.yaml : une donnée YAML avec un champ releve_le, renseignée par l'opératrice, pas une constante de document.
- *Seuils opérationnels du schéma OSINT : score_completude >= 70, score_capacite >= 40, bande_besoin 35-75, matrice « Besoin 55-75 », « seuil avis ≥ 20-25, pas 10 », poids completude (20/25/20/15/10/10), points capacite (30/20/15/15/10/10), TTL 90/180/365 j, rétention 12/24/36 mois* → Une trentaine de seuils inventés. Le §6 concède que « les poids de completude.yaml sont un point de départ à recalibrer », mais le §3.4 les pose comme la porte pret_a_contacter et le §3.3 en fait des disqualifications automatiques — donc opérants, pas indicatifs. Pire : ils sont calibrés sur le score ACTUEL, celui que le correctif 0.1 va déplacer (mon site parfait passe de 55 à ~100 après renormalisation). — **Action :** Marquer tous ces seuils [À CALIBRER] et les sortir dans un YAML unique. Interdire toute disqualification automatique (§3.3) tant qu'aucun run borné n'a produit de distribution réelle.
- *« Cela coûte trente secondes par prospect réellement contacté (20 à 40 par mois, pas 400) »* → Volume de prospection et durée d'un geste manuel, tous deux inventés. Aucun run n'a eu lieu, le vault n'est même pas initialisé. Ce chiffre porte l'arbitrage « pas de nom de dirigeant automatisé » — arbitrage que j'approuve par ailleurs, mais qui doit tenir sur l'argument juridique, pas sur un volume fictif. — **Action :** Garder l'argument de bascule de finalité, supprimer le chiffrage.
- *« RBQ sous-catégorie 15.10 = thermopompe résidentielle » ; « toute escalade qualite serait facturée au tarif Haiku, soit une sous-estimation d'un facteur 3 »* → Le code de sous-catégorie RBQ est affirmé sans source. Le facteur 3 est asserté ; greenit.yaml:48 dit « ~3-5x » — l'artefact retient la borne basse sans le dire, alors qu'il s'agit d'un commentaire YAML, pas d'un relevé tarifaire. — **Action :** Sourcer le code RBQ. Remplacer « facteur 3 » par « facteur non déterminé tant que api_pricing.yaml est à 0 » — le défaut structurel (grille anthropic mono-tarif, vérifié l. 28-33) est réel et se démontre sans chiffre.

**Violations / tensions d'invariants :**

- CONTRADICTION ENTRE LES DEUX ARTEFACTS SUR LE BUS RÉSEAU (domaine.py). L'artefact 1 (C.6) impose « tout passe par api_io.call("dns","resolve", …) » et signale correctement que l'AST walk ne verrait pas dnspython. L'artefact 2 (bloc F) décrit les mêmes signaux comme « DNS MX (dnspython, résolveur local) », palier G, sans aucune mention du bus. Implémenté tel que rédigé dans l'artefact 2, c'est une sortie réseau directe, non journalisée au grand livre, non soumise au garde-fou budgétaire — violation frontale de l'invariant J3 « api_io.py est le bus réseau unique ». À trancher AVANT toute ligne de code.
- LE DURCISSEMENT PROPOSÉ DU PRÉFLIGHT REPRODUIT LA DETTE QU'IL PRÉTEND FERMER. Vérifié preflight.py l. 249-282 : _check_garde_fous_bus itère une LISTE EXPLICITE de 8 chemins de modules ; interdits = {"requests","anthropic"}. Les deux artefacts proposent d'y ajouter à la main 8 à 9 nouveaux modules (registre, certification, domaine, archive, perf, stack, emploi, contact_site, greenit). C'est exactement le mécanisme qui a déjà produit la dette technique n°2 de CLAUDE.md (greenit.py oublié). Le correctif durable existe déjà dans le dépôt et n'est proposé par aucun des deux : tests/test_api_io.py::test_requests_pas_importe_niveau_module_hors_api_io parcourt diagnostic/** en rglob. Généraliser le rglob dans le préflight ferme la classe de défaut ; ajouter des noms à la main la rouvre à chaque itération.
- LISTE DE SUPPRESSION : STOCKAGE PERSISTANT DE DONNÉES PERSONNELLES HORS DES DEUX BUS, ET NON SAUVEGARDÉ. Le §4.2 crée .suppression/<marche>.jsonl (hash de domaine + hash d'email) et le §5.4 demande de l'ajouter au .gitignore. Ce fichier n'est écrit ni par vault_io.py (donc pas d'écriture atomique, pas de ligne dans runs.log) ni par api_io.py. Aucun writer, aucun test, aucune journalisation ne sont spécifiés. Un hash d'email reste une donnée personnelle pseudonymisée au sens du RGPD. Et surtout : gitignoré = non versionné = perdu au premier reclonage, ce qui réactive silencieusement l'enrichissement Apollo de personnes qui se sont opposées — précisément le scénario que le §4.2 dit vouloir éviter. Il faut désigner un écrivain unique, journalisé, et un mécanisme de durabilité.
- LA PORTE pret_a_contacter EST ARITHMÉTIQUEMENT INATTEIGNABLE DANS L'ÉTAT DU SYSTÈME. Calcul sur les poids du §3.1 : identite_legale 20 (bloquants identifiant_legal + statut_administratif → exige registre.py, étape 7, effort « élevé ») ; reputation 20 (bloquant nb_avis_bucket → exige une clé Places) ; etablissement 15 (bloquant a_fiche_gbp → exige Places). Sans clé et sans registre.py, ces trois blocs valent 0 et le maximum atteignable est 25 + 10 + 10 = 45. Or le §3.4 exige score_completude >= 70. Aucune fiche ne peut donc jamais devenir pret_a_contacter, et le §3.3 disqualifie en plus automatiquement tout ce qui est sous 40 (donnees_insuffisantes). Livré tel quel, le schéma produit une porte fermée à 100 % et un taux de disqualification automatique proche de 1. Cette arithmétique n'est faite nulle part dans l'artefact.
- LE CORRECTIF PHARE 0.1 NE FERME PAS LA FABRICATION QU'IL VISE — website.py fabrique aussi. Vérifié website.py l. 64 : sur échec de fetch, le collecteur retourne {"reachable": False, "status": status, "https": False}. https vaut False, pas None. Avec le scoring 3 états, un timeout réseau continuera donc d'émettre la faille « Pas de HTTPS — signal de confiance manquant » sur un site qui est peut-être en HTTPS. Second chemin incohérent l. 54 : sans URL, le dict ne contient pas https du tout (→ None → inconnu). Les deux chemins d'échec du même collecteur ne se comportent pas pareil. La thèse finale de l'artefact 1 (« le geste unique […] tient en une trentaine de lignes dans scoring.py ») est donc fausse : sans un passage à None dans website.py, la fabrication survit au correctif.
- LE CORRECTIF 0.1 DÉPLACE LES ENTRÉES DU ROUTAGE GREENIT, SANS QUE NI L'UN NI L'AUTRE ARTEFACT NE LE SIGNALE. greenit.yaml (routage, mode « ou ») escalade vers le profil qualite (claude-sonnet-4-5, 900 tokens) si nb_failles >= 6 OU score_global >= 75. Or le correctif 0.1 fait exactement deux choses : il supprime des failles (les inconnues) et il renormalise le score à la hausse. Mon repro le montre : le site parfait passe de 55 à ~100, soit au-dessus du seuil 75. Effet net non anticipé : après 0.1, ce sont les MEILLEURS prospects qui basculent systématiquement sur le modèle cher. C'est un effet de coût direct, dans un document dont la section E affirme qu'aucun levier de coût LLM n'existe. À traiter dans le même lot que 0.1 (recalibrer les deux seuils de routage), sinon l'invariant GreenIT « escalade à déclencher, pas à subir » tombe.
- GRAVITÉ CONFIRMÉE, MAIS L'EFFET DE BORD SUR signal_chaud N'EST PAS TRAITÉ. Vérifié sur rubric_persona1.yaml : la dimension site_web a 6 checks pour max_points=100, ratio maximal 25/100 = 0,25 → aucun check de site_web ne peut jamais atteindre « haute » (seuil 0,4) ; gbp.verified vaut 60/100 = 0,6 → toujours « haute ». Les deux artefacts ont raison sur le diagnostic. Mais le correctif 0.2 (champ gravite dans le YAML) redistribue les gravités, donc redistribue hautes[0] dans serializers.py l. 28-32, donc change signal_chaud, donc change la colonne « Signal chaud » de tout export existant. Aucun des deux ne mentionne cette propagation ni le test de non-régression correspondant.

**Réserves :**

- MINIMISATION RGPD — verdict global : tenue, avec deux dérives à corriger. Le point de partage identifié par l'artefact 1 est juste et je l'ai vérifié : Contact (enrichment.py l. 32-39) a bien 6 champs sous extra="forbid", FicheProspect a bien extra="allow" (vault_schema.py:78). Ajouter des champs ENTREPRISE ne touche pas le garde-fou. D1/D2/D3 du schéma OSINT sont bien construits, et le refus de collecter le nom du dirigeant issu des registres (bascule de finalité) est le bon arbitrage. Deux réserves. (a) adresse_siege (bloc A) : le document le marque lui-même E* — donc adresse du DOMICILE dès que entreprise_individuelle == True, cas fréquent en HVAC. Aucun check de scoring ne l'utilise, aucune finalité n'est déclarée pour lui. Collecter une adresse personnelle sans usage est du gonflement pur : à retirer du schéma. (b) contact_type est présenté comme « le seul ajout, et il RÉDUIT l'exposition ». Non : il ajoute un champ personnel de plus au niveau fiche (5 champs contact_* deviennent 6). Il permet de PRÉFÉRER l'adresse fonctionnelle, ce qui est utile, mais ne réduit rien de ce qui est stocké. Corriger la formulation, garder le champ.
- RISQUE JURIDIQUE NON SIGNALÉ, LE PLUS SÉRIEUX DES DEUX ARTEFACTS — la grille de provenance email (B.2) écrit : « site_officiel:<url>#<date> → CASL/nLPD/RGPD : utilisable, preuve auto-portée ». Le raisonnement CASL est solide (adresse publiée sans avis contraire + message pertinent = consentement tacite). Mais l'extension aux TROIS régimes est une conclusion juridique non étayée, présentée comme acquise. En Suisse, l'art. 3 al. 1 let. o LCD vise la publicité de masse par voie électronique SANS égard au fait que l'adresse soit publiée : la publication sur un site n'y vaut pas consentement. Côté RGPD, l'extraction automatisée d'adresses depuis des sites tiers (contact_site.py, étage 1 de la cascade) est de la collecte indirecte au sens de l'art. 14, avec obligation d'information dans le mois — une obligation que le schéma prévoit (information_art14_transmise_le) mais qu'il rattache au premier message J6, donc potentiellement bien après la collecte. Dans un projet dont l'invariant est « J6 exige un juriste AVANT tout envoi », cette grille tranche par anticipation la question centrale. À reformuler en [À VALIDER PAR UN JURISTE] par marché, sans verdict d'utilisabilité.
- SOURCES À USAGE AUTOMATISÉ RISQUÉ, non ou mal signalées. (a) Meta Ad Library (bloc G, annonces_publicitaires_actives) : le document ne mentionne que la limite « UE seulement pour le non-politique ». Le vrai obstacle est l'accès : l'API exige une application approuvée et une identité vérifiée, et l'interrogation automatisée de l'interface web est contraire aux conditions de Meta. Aucune de ces deux contraintes n'est signalée. À classer non retenu ou [BLOQUÉ — accès à obtenir]. (b) crt.sh (bloc F, premier_certificat_tls) : correctement annoté « endpoint non documenté, throttling », mais bâtir un signal de scoring sur un endpoint non documenté d'un tiers est une dépendance instable pour une micro-structure sans astreinte. (c) Répertoire CMMTQ : le « ⚠️ CGU à lire » est le bon réflexe, à transformer en pré-condition bloquante. (d) OSM/Overpass : l'ODbL est renvoyée au juriste au §6 mais le bloc C liste presence_osm et osm_website_renseigne sans marquage. (e) Wayback CDX (archive.py, palier 1 du plan) : aucune mention de conditions d'usage. (f) Dumps Données Québec / RBQ / ADEME : licences (Etalab citée pour l'ADEME seulement) non vérifiées pour les autres.
- FAISABILITÉ — le plan cumulé n'est pas dimensionné pour une consultante solo + un développeur à temps partiel. Décompte de ce que les deux artefacts demandent ensemble : ~10 nouveaux collecteurs, 9 blocs Pydantic (~90 champs), un modèle Provenance à granularité par bloc/par champ, 3 nouveaux nœuds DAG, 4 pipelines d'ingestion de dumps (REQ bimensuel, RBQ, ADEME hebdo, Sirene stock), 3 marchés × (ICP + rubrique faille + rubrique capacité + compliance + certifications) = 15 fichiers de données à maintenir, plus completude.yaml, golden files, chemins pointés dans export.py, TTL par fournisseur, nœud purge, liste de suppression. Le tout sous une porte de cohérence à 97 % qui impose de RE-EXÉCUTER chaque assertion à chaque itération, avec 536 tests à garder verts et test_doc_coherence à recompter. Ce n'est pas un trimestre de travail à temps partiel. Le palier 0 (7 correctifs) est en revanche parfaitement calibré et doit partir seul.
- EFFORTS SOUS-ESTIMÉS, trois cas nommés. (a) 0.1 « scoring 3 états », noté M : change le type de retour de _check_passes, la sémantique de scores (dimension absente et non None), le calcul de total_poids, et — non mentionné — les entrées du routage GreenIT (voir violations). Bonne nouvelle vérifiée : le cockpit ne lit que score_global (webapp/backend/services.py:159, aucun accès par dimension), donc le front ne casse pas ; et les tests existants asservissent des plages (test_j1_smoke.py:74 : 0 <= score <= 100) plutôt que des valeurs. Le risque est donc réel mais contenu — à condition de traiter website.py et greenit.yaml dans le même lot. (b) 1.4 contact_site.py, noté M : ≤2 GET annoncés, mais le module doit aussi porter robots.txt (avec son propre cache et sa politesse par hôte), 3 chemins de repli d'URL, et l'extraction de preuve datée. Le projet pose « une requête par cible » en convention ; on passe à 4. (c) 3.6 « trois rubriques + trois ICP », noté M : trois régimes juridiques, trois vocabulaires de certification, trois cadences de dump. C'est de l'ordre du trimestre, pas de la semaine.
- COUPLAGE DE DÉPENDANCE DANGEREUX dans le schéma OSINT : la règle de disqualification automatique hors_perimetre (§3.3) repose sur statut_administratif != "actif", champ qui ne peut venir QUE de registre.py — le module que l'artefact classe lui-même effort « élevé », dont il reconnaît que le point dur (rapprochement d'entités sans faux positif) n'est pas résolu, et qui est relégué à l'étape 7 sur 9. Une porte bloquante ne doit jamais dépendre du module le plus incertain de la feuille de route. Même remarque pour identite_legale, bloc de poids 20 avec deux champs bloquants issus du même module.
- CE QUE JE VALIDE SANS RÉSERVE, et qui doit partir immédiatement : le palier 0 en entier (7 correctifs). J'ai re-vérifié chacun dans le code — 0.1 (scoring.py l. 29-30 : if value is None: return False), 0.2 (_severity divise par le total de dimension, l. 39-46), 0.3 (gbp.py:64 verified = business_status == "OPERATIONAL", qui n'est PAS la vérification d'une fiche par son propriétaire — le libellé de rubrique ment même avec une clé valide), 0.4 (website.py:94), 0.5 (enrichment.py l. 79-80, _nb_enrichissements incrémenté seulement si un contact est extrait — un appel Apollo sans titre correspondant consomme le fournisseur hors quota), 0.6 (api_io._lire_cache l. 218-224 : seul path.exists() est testé, cache_ttl_jours:30 de greenit.yaml:106 est lu mais jamais appliqué), 0.7 (website.py l. 118-137 et 281-301 : cache autonome qui écrit sur disque et n'émet AUCUNE LedgerEntry). Ces sept-là ne demandent aucune clé, ne coûtent rien, et sont tous reproductibles. Ils doivent être livrés en un lot, AVEC le correctif website.py https:False→None et la recalibration des seuils GreenIT.
- SUR L'INVARIANT MACHINE À ÉTATS — aucune violation trouvée, et c'est à porter au crédit des deux artefacts. Le nœud purge est explicitement conçu pour anonymiser sans transitionner ; j'ai vérifié que vault_io.update_frontmatter (l. 175) existe et est déjà le chemin qu'emprunte transition() (l. 255), donc la purge est implémentable via le bus vault sans toucher à la machine à états ni à l'exclusivité de os.replace(). Le nœud conformite est une porte (patron preflight_gate), pas un transformateur. La revendication « motif_rejet inexistant » est exacte : vault_io.py l. 256-259 journalise « ancien→nouveau acteur=X » et rien d'autre. Sur l'invariant collecte déterministe ≠ LLM, aucune des propositions ne réintroduit de décision LLM (capacite.py réutilise ScoringEngine, choisir_modele reste des comparaisons YAML). Sur le mode dégradé sans clé, la logique None→inconnu est cohérente avec le comportement réel des stubs vérifiés (gbp/reviews retournent None sans api_io, seo retourne None, social retourne []) — sous réserve du défaut website.py signalé plus haut.
- CONDITIONS DE LEVÉE DE L'AVAL — six items, tous vérifiables par exécution : (1) corriger les 4 affirmations fausses listées, dont les 2 qui portent une conclusion (tri de l'export, texte LLM dans le CSV / art. 50) ; (2) trancher la contradiction domaine.py entre les deux artefacts en faveur du bus api_io, par écrit ; (3) refaire l'arithmétique de completude.yaml pour que pret_a_contacter soit atteignable dans l'état sans clé, ou déclarer explicitement la porte inopérante jusqu'à l'étape 7 ; (4) ajouter website.py (https→None) et la recalibration des seuils GreenIT au lot 0.1, et retirer la thèse « trente lignes dans scoring.py » ; (5) retirer ou marquer [NON SOURCÉ] les 22 chiffres externes, en particulier les coûts en cents et les deux pourcentages de la section E ; (6) requalifier en [À VALIDER PAR UN JURISTE] la grille de provenance email pour la Suisse et la France, et reclasser Meta Ad Library et crt.sh. Une fois ces six points traités, le palier 0 et le palier 1 sont approuvables tels quels.

---
