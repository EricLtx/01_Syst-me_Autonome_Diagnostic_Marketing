# SPEC — Module « J3 : bus d'I/O périphérique (`api_io`) + activation des collecteurs réels »

> Document destiné à Claude Code. À placer à la racine du repo, à côté de `SPEC-J2-bus-vault.md` et `CLAUDE.md`.
>
> **Démarrer la session par** :
> « Lis `SPEC-J3-api-io.md`, `SPEC-J2-bus-vault.md` et `CLAUDE.md`. Fais d'abord l'inventaire du repo réel et confirme l'état existant (§2). Signale toute divergence entre cette spec et le code AVANT d'écrire la moindre ligne. Puis propose un plan d'implémentation phase par phase. »

---

## 1. Contexte et objectif

Le système suit le modèle d'une architecture micro-ordinateur (cf. `CLAUDE.md`). J2 a livré le **bus de stockage** : `vault_io.py`, seul module autorisé à lire/écrire dans le vault, qui journalise tout son trafic dans `runs.log`.

J3 ajoute le **bus d'I/O périphérique**. Dans l'analogie : un appel à une API externe est un transfert DMA vers un périphérique (réseau). On veut un **contrôleur unique** qui médie *tous* ces transferts — exactement comme `vault_io` médie le stockage — et qui les comptabilise.

Deux objectifs, dans cet ordre :

1. **`api_io.py`** : contrôleur de bus d'I/O. Authentification centralisée, cache idempotent, budgets/quotas, et un **grand livre d'usage** (`api_usage.log`, jumeau de `runs.log`) qui journalise chaque appel avec l'unité consommée et le coût estimé. C'est ce qui rend l'usage **quantifiable et suivi** (tokens par API, coût par fiche, crédits par persona).
2. **Activation des 4 collecteurs stubs** (GBP, avis, SEO, social) en les branchant — quand ils touchent le réseau — sur ce bus, pour produire les signaux fonctionnels demandés (cf. §8), sans rien casser de J1/J2.

**Contrainte structurante** : comme aucun module hors `vault_io.py` n'ouvre un fichier du vault, **aucun module hors `api_io.py` ne doit toucher le réseau externe** (pas de `requests` brut, pas de client `anthropic` direct ailleurs). C'est le même garde-fou, transposé.

---

## 2. État existant — à confirmer par Claude Code

Inventorier le repo réel et confirmer (ou infirmer) ces points avant de coder :

- `diagnostic/collectors/website.py` appelle **directement** `requests.get` dans `_fetch`. → à router via `api_io` (§6).
- `diagnostic/synthesis.py` instancie **directement** `anthropic.Anthropic()` et appelle `messages.create`. → à router via `api_io` pour métrer les tokens (§6).
- `gbp.py`, `reviews.py`, `seo.py`, `social.py` sont des stubs qui retournent des valeurs `None`. → à activer (§8).
- Le pipeline (`DiagnosticPipeline`) ne reçoit aujourd'hui aucune instance d'I/O. → injection de dépendance à ajouter (§6.3).
- **Doublons à la racine** : `pipeline.py`, `scoring.py`, `synthesis.py` et `rubric_persona1.yaml` existent en double (racine ET `diagnostic/` / `knowledge/`). Les imports passent tous par `diagnostic.*` et `config.py` charge `knowledge/` : les copies racine sont du **code mort** (la rubrique racine porte même un wording périmé « à confirmer en J2 »). → ménage en Phase 0.
- `scoring.py` lit `self.seuil_faille` mais ne l'utilise jamais : un `Gap` est émis pour *chaque* check échoué, indépendamment du seuil. → décision à prendre en Phase 0.

---

## 3. Principes directeurs (rappel — non négociables)

Ces principes priment sur toute optimisation. En cas de tension, on les respecte.

- **Conformité** (RGPD / CASL / nLPD + LCD) : **aucun scraping de LinkedIn ou Facebook**. Les données « personnes » passent par l'API licenciée **Apollo** ; les données Google (Maps / avis) par l'**API Google Places** ou un **SERP API** managé. Le palier navigateur (§7) ne s'applique **qu'au site propre de l'entreprise**, dans le respect de son `robots.txt`. Chaque donnée collectée porte sa **source et sa date** (audit RGPD).
- **Collecte déterministe ≠ raisonnement LLM** : le LLM rédige à partir de faits déjà établis, il ne va jamais chercher de données. Inchangé.
- **Config = données** : la grille tarifaire (§5.2) et les rubriques sont des YAML, jamais du code. Changer un tarif = éditer un fichier, pas le contrôleur.
- **Bus unique** : `api_io.py` est le seul point de contact avec le réseau externe. Imposé par convention + test (§9, garde-fou).
- **Échec gracieux isolé** : un appel API qui échoue (réseau, quota, budget dépassé) ne fait pas tomber le pipeline ; la fiche concernée reste `decouvert`, l'erreur est journalisée, les autres fiches continuent.
- **Cache hors vault** : le cache d'appels API reste hors du vault (même esprit que la contrainte G9 de J2).
- **Gouvernance humaine** : rien ne change côté machine à états. L'agent ne fait toujours que `decouvert → diagnostique`.

---

## 4. Phase 0 — Ménage préalable (petit, isolé, à valider en premier)

But : assainir la base avant d'empiler une nouvelle couche. Aucune nouvelle fonctionnalité.

| # | Tâche | Détail |
|---|---|---|
| H1 | Supprimer les doublons racine | Retirer `pipeline.py`, `scoring.py`, `synthesis.py`, `rubric_persona1.yaml` de la **racine** après avoir confirmé qu'aucun import ne les référence. Les versions sous `diagnostic/` et `knowledge/` font foi. |
| H2 | Trancher `seuil_faille` | Soit l'implémenter (une dimension dont le score < `seuil_faille` est signalée comme faille, en plus ou à la place des gaps par check), soit le retirer de la rubrique et du commentaire. Documenter le choix dans `CLAUDE.md`. **Recommandation : conserver le comportement actuel** (un gap par check échoué, plus fin) et retirer la mention trompeuse. |
| H3 | Corriger un nom de test trompeur | `test_fiche_sans_url_reste_decouvert_avec_erreur_journal` affirme « reste decouvert » mais teste `statut == "diagnostique"`. Renommer le test et corriger sa docstring pour refléter le comportement réel. |

Critère d'acceptation Phase 0 : la suite existante (101 tests) passe toujours, sans copie racine.

---

## 5. Spécification `api_io.py` (contrôleur de bus d'I/O)

### 5.1 Principe

- ~200–350 lignes. Dépendances : stdlib + `requests` + `pydantic` + `PyYAML`. Le client `anthropic` reste un import **paresseux interne** à `api_io` (jamais ailleurs).
- Aucun autre module n'a le droit de faire un appel réseau sortant. Imposé par convention + test garde-fou (§9).
- Chemins (ledger, cache) et clés injectés par config / variables d'environnement, jamais codés en dur.

### 5.2 Grille tarifaire — `knowledge/api_pricing.yaml` (config = données)

Le contrôleur ne connaît aucun prix en dur : il lit cette table au moment de journaliser. **Chaque fournisseur facture dans une unité différente** ; la table porte donc, par fournisseur et par endpoint, le type d'unité et le prix unitaire.

> **Note pour le paramétrage (étape ultérieure, hors de cette spec)** : les valeurs ci-dessous sont des **placeholders**. Les vrais tarifs devront être renseignés à partir des pages officielles des fournisseurs au moment de la mise en service — les prix changent régulièrement, ne pas les figer ici de mémoire. Devise pivot suggérée : `USD` (conversion EUR/CAD/CHF en option, table séparée).

```yaml
# knowledge/api_pricing.yaml — DONNÉE, pas du code.
# Prix unitaires. Renseigner au paramétrage à partir des docs officielles.
devise: USD

fournisseurs:

  anthropic:
    # Facturation au token (entrée / sortie séparés).
    # L'objet `message.usage` expose input_tokens / output_tokens
    # (+ cache_creation_input_tokens / cache_read_input_tokens).
    unite: token
    endpoints:
      messages:
        prix_par_unite:
          input_tokens:  0.0      # USD / token — À RENSEIGNER
          output_tokens: 0.0      # USD / token — À RENSEIGNER
          cache_read_input_tokens: 0.0      # optionnel
          cache_creation_input_tokens: 0.0  # optionnel

  serp:
    # Facturation à la requête (crédit/recherche).
    unite: requete
    endpoints:
      search:  { prix_par_unite: { requetes: 0.0 } }   # À RENSEIGNER
      maps:    { prix_par_unite: { requetes: 0.0 } }
      reviews: { prix_par_unite: { requetes: 0.0 } }

  google_places:
    # Facturation à la requête, mais le PRIX DÉPEND DU SKU (endpoint).
    # → journaliser l'endpoint précis, pas un générique "1 appel".
    unite: requete
    endpoints:
      text_search:   { prix_par_unite: { requetes: 0.0 } }   # À RENSEIGNER
      place_details: { prix_par_unite: { requetes: 0.0 } }
      nearby_search: { prix_par_unite: { requetes: 0.0 } }

  apollo:
    # Facturation au crédit (par enrichissement / enregistrement).
    unite: credit
    endpoints:
      people_enrichment:    { prix_par_unite: { credits: 0.0 } }   # À RENSEIGNER
      organization_search:  { prix_par_unite: { credits: 0.0 } }

  http:
    # Fetch statique (palier 0). Coût ~nul mais on journalise le volume/la latence.
    unite: requete
    endpoints:
      get: { prix_par_unite: { requetes: 0.0 } }
```

### 5.3 Schéma du grand livre — `api_schema.py` (pydantic) + `api_usage.log`

Modèle pydantic `LedgerEntry`, source unique de vérité de ce qu'on journalise. Une ligne JSONL par appel, append-only, à la **racine du repo** (pas dans le vault), fichier `api_usage.log`.

```python
class LedgerEntry(BaseModel):
    ts: datetime                 # horodatage UTC ISO
    fournisseur: str             # "anthropic", "serp", "google_places", "apollo", "http"
    endpoint: str                # "messages", "place_details", ...
    unites: dict[str, float]     # {"input_tokens": 1200, "output_tokens": 350} | {"requetes": 1}
    cout_estime: float           # somme(unites[k] * prix[k]) selon api_pricing.yaml
    devise: str                  # "USD"
    fiche: str | None = None     # nom de fiche concernée, si applicable
    cache_hit: bool = False      # True → cout_estime = 0, aucun appel réseau
    resultat: str                # "ok" | "erreur" | "budget_depasse"
    detail: str = ""             # message d'erreur éventuel
```

À partir de ce journal, n'importe quelle agrégation devient triviale (un petit script ou une requête Dataview sur un export) : « tokens Claude ce mois-ci », « coût total par fiche diagnostiquée », « crédits Apollo par persona/marché », « taux de cache_hit ».

### 5.4 API publique

```python
class ApiIO:
    def __init__(
        self,
        pricing: dict,                 # chargé depuis api_pricing.yaml
        ledger_path: Path,             # api_usage.log (hors vault)
        cache_dir: Path | None = None, # cache hors vault (cf. 5.6)
        budgets: dict | None = None,   # cf. 5.5
        vault_path: Path | None = None,# si fourni, vérifie cache hors vault
    ) -> None: ...

    def call(
        self,
        fournisseur: str,
        endpoint: str,
        fn: Callable[[], Any],         # exécute l'appel réel, retourne la réponse brute
        *,
        fiche: str | None = None,
        cache_key: str | None = None,  # si fourni, active le cache idempotent
        measure: Callable[[Any], dict[str, float]] | None = None,
    ) -> Any:
        """
        1. Si cache_key fourni et présent → retourne la valeur cachée,
           journalise cache_hit=True, cout_estime=0, AUCUN appel réseau.
        2. Vérifie le budget du fournisseur (5.5) ; si dépassement → BudgetExceeded.
        3. Exécute fn().
        4. Extrait les unités via measure(reponse) (ou {endpoint_par_defaut: 1}).
        5. Calcule le coût depuis pricing, journalise une LedgerEntry.
        6. Met en cache si cache_key fourni.
        Retourne la réponse brute de fn().
        """
```

- `fn` est une *closure* fournie par l'appelant qui réalise l'appel concret (`lambda: requests.get(...)`, `lambda: client.messages.create(...)`). C'est `api_io` qui possède le client `anthropic` et `requests` ; l'appelant ne fait que décrire l'intention.
- `measure` traduit la réponse brute en unités. Mesureurs fournis par défaut (§5.7). Si absent, on compte `1` requête de l'unité par défaut de l'endpoint.
- Le contrôleur **ne lève jamais** pour une erreur réseau ordinaire : il journalise `resultat="erreur"` et propage proprement (l'appelant/collecteur applique son `safe_collect`). Il **lève** `BudgetExceeded` (interruption volontaire) si un plafond est atteint.

### 5.5 Registres, budgets et interruptions

Dans l'analogie : les compteurs d'usage courants sont des **registres** ; un dépassement de plafond est une **interruption** qui stoppe le transfert.

- `budgets` (optionnel) : `{ "anthropic": {"cout_max": 5.0}, "apollo": {"unites_max": {"credits": 100}} }`, par période (jour/mois — au choix, documenter).
- Les registres (totaux courants par fournisseur sur la période) sont **recalculés depuis le ledger** (pas de second état à maintenir : le journal est la vérité). Mettre en cache en mémoire pour la session.
- Si un appel *ferait* dépasser le plafond → lever `BudgetExceeded` AVANT d'exécuter `fn` ; journaliser `resultat="budget_depasse"`. Le `vault_runner` traite ça comme un échec de fiche isolé.

### 5.6 Cache idempotent — hors vault

- Cache disque, hors du vault (réutiliser la logique de garde de la contrainte G9 : si `cache_dir` est sous `vault_path`, erreur fatale au démarrage).
- Clé = hash de `(fournisseur, endpoint, cache_key)`. Un `cache_key` stable (ex. l'URL pour `http`, le `nom+marche` pour Places) garantit qu'on ne re-paie jamais un appel identique (principe n°5).
- Le cache de scraping brut existant de `website.py` (`.cache/website`) peut être unifié ici ou laissé tel quel — au choix de Claude Code, mais **documenter** la décision.

### 5.7 Mesureurs par fournisseur

Fonctions pures `reponse → dict[str, float]` :

- **anthropic** : `{"input_tokens": r.usage.input_tokens, "output_tokens": r.usage.output_tokens}` (+ cache tokens si présents). Lit l'objet `usage` de la réponse Messages.
- **serp / google_places / http** : `{"requetes": 1}` (facturation à la requête ; le SKU est porté par `endpoint`).
- **apollo** : `{"credits": <crédits consommés>}` selon ce que renvoie l'API (à confirmer à l'intégration ; fallback `{"credits": 1}`).

---

## 6. Câblage des collecteurs et de la synthèse sur le bus

### 6.1 `website.py` (palier 0)
Remplacer l'appel `requests.get` direct de `_fetch` par :
`api_io.call("http", "get", lambda: requests.get(url, ...), cache_key=url)`.
Le collecteur ne fait plus d'I/O réseau lui-même.

### 6.2 `synthesis.py` (LLM métré)
Router l'appel LLM via `api_io.call("anthropic", "messages", lambda: client.messages.create(...), fiche=company.nom, measure=mesureur_anthropic)`. **C'est ce qui fait que les tokens Claude apparaissent dans `api_usage.log`.** Le `quality_check` et le repli déterministe restent inchangés.

### 6.3 Injection de dépendance
- `DiagnosticPipeline.__init__` reçoit un `api_io: ApiIO` (optionnel ; si `None`, comportement dégradé documenté — utile pour les tests unitaires hors réseau).
- `run_diagnostic.py` et `vault_runner.py` instancient **un seul** `ApiIO` (pricing chargé depuis `knowledge/api_pricing.yaml`, ledger à la racine) et l'injectent dans le pipeline. Une instance par run, comme une seule instance de `VaultIO`.

---

## 7. Collecte étagée (paliers) — efficacité sans alourdir

Trois paliers, **du moins cher au plus cher**. Chaque palier reste un collecteur déterministe ; le scoring ne change pas.

- **Palier 0 — fetch statique** (`requests`, existant) : défaut, quasi gratuit, rapide, caché. Couvre la majorité des sites de l'ICP (WordPress / Wix / Squarespace, rendus côté serveur).
- **Palier 1 — API managée** (Places, SERP, Apollo via `api_io`) : pour les données structurées et les signaux dynamiques (avis, réponses aux avis). On délègue scraping et risque au fournisseur ; on récupère du JSON daté et traçable.
- **Palier 2 — navigateur headless** (Playwright **ou** SeleniumBase, choix déféré) : **escalade rare, optionnelle, hors défaut.** Déclenchée *uniquement* quand le palier 0 renvoie une page vide/gated, et **seulement sur le site propre de l'entreprise**, `robots.txt` respecté. **Jamais** sur LinkedIn/Facebook. À implémenter en dernier (Phase E) ou à reporter en J4 ; derrière un flag explicite (`--escalade-navigateur`), désactivé par défaut pour préserver la contrainte de coût.

---

## 8. Activation des collecteurs réels — les signaux fonctionnels demandés

Quatre familles de signaux, conduisant au diagnostic et donc aux fiches à valider. **Important** : on *produit* les signaux ici ; les **brancher dans la rubrique** (nouveaux checks) relève du **paramétrage ultérieur**, pas de cette spec. Les signaux déjà attendus par `rubric_persona1.yaml` (`gbp.verified`, `gbp.has_photos`, `reviews.count`, `reviews.avg`, `seo.local_keywords`) reçoivent en revanche enfin de vraies valeurs.

### 8.1 Site web — palier 0 enrichi : « dernière mise à jour / date la plus récente »
Sans navigateur, ajouter au `WebsiteCollector` un signal `derniere_maj` agrégeant le plus récent de : `lastmod` du `sitemap.xml`, en-tête HTTP `Last-Modified`, dates visibles d'un blog/actu, et `copyright_year` (déjà capté). Signal : `website.derniere_maj` (date ou année) + `website.fraicheur_mois` (ancienneté en mois) si datable.

### 8.2 Réseaux sociaux mentionnés — DÉRIVÉ, aucun scraping
`website.py` extrait déjà `social_links` depuis les liens sortants du site. **C'est la source.** Détecter qu'une entreprise *lie* Facebook / Instagram / LinkedIn (présence) est gratuit et déjà fait — radicalement plus défendable que de *lire le contenu* de ces pages. → Repurposer `social.py` en collecteur **passif** qui normalise/expose `social.plateformes_mentionnees` à partir du signal website (ou retirer `social.py` et laisser la rubrique pointer directement `website.social_links`). **Aucun appel réseau, aucune API.** C'est suffisant pour le diagnostic de maturité de marque (« aucune présence sociale liée » est déjà une faille exploitable).

### 8.3 Présence locale (GBP) — palier 1, Google Places
`gbp.py` via `api_io.call("google_places", "place_details", ...)` : présence/vérification (proxy via existence de la fiche), nombre de photos, et — si l'endpoint le permet — posts récents. Remplit `gbp.verified`, `gbp.has_photos`. `cache_key` = `nom+marche` pour ne pas re-payer.

### 8.4 Avis + « réponse aux avis » — palier 1, Places (+ SERP si besoin)
`reviews.py` via Places : `reviews.count`, `reviews.avg`, **`reviews.repond_aux_avis`** (le propriétaire répond-il ? — signal demandé, détectable via la présence de réponses du propriétaire dans les avis retournés), et `reviews.date_dernier_avis` (alimente aussi « date la plus récente »). Si Places ne suffit pas pour les réponses, escalade vers un SERP API `reviews` (toujours via `api_io`).

### 8.5 SEO local — palier 0, déterministe sur le texte du site
`seo.py` analyse le texte déjà récupéré par website (mots-clés géolocalisés : ville/région de l'ICP présents dans le contenu, le `title`, les `meta`). Remplit `seo.local_keywords`. Pas de réseau supplémentaire.

> Source + date : chaque signal issu d'une API porte sa provenance et son horodatage (via le ledger et/ou un champ `_source` dans les signaux), pour l'audit RGPD.

---

## 9. Tests et critères d'acceptation

Même esprit que `SPEC-J2-bus-vault.md` §8. À mocker : `requests.get`, le client `anthropic`, les API Places/SERP/Apollo. **Aucun réseau réel, aucune clé requise** pour faire passer la suite.

1. **Ledger** : un appel via `api_io.call` produit exactement une ligne JSONL dans `api_usage.log`, avec `ts`, `fournisseur`, `endpoint`, `unites`, `cout_estime`, `resultat="ok"`.
2. **Coût depuis YAML** : avec une `api_pricing.yaml` de test, le `cout_estime` est calculé correctement pour (a) un appel anthropic (input/output tokens) et (b) un appel serp (1 requête).
3. **Cache idempotent** : deux appels identiques avec le même `cache_key` ⇒ un seul appel réseau (mock appelé une fois), 2ᵉ ligne `cache_hit=True` et `cout_estime=0`.
4. **Budget / interruption** : un plafond fournisseur dépassé ⇒ `BudgetExceeded` levée AVANT l'appel, ligne `resultat="budget_depasse"`, et le `vault_runner` isole l'échec (fiche reste `decouvert`, autres fiches traitées).
5. **Mesureur anthropic** : sur une réponse mockée portant `usage.input_tokens`/`usage.output_tokens`, les unités journalisées sont exactes.
6. **Garde-fou imports (le test clé)** : par AST/grep, ni `requests` ni le client `anthropic` ne sont importés/appelés en dehors de `api_io.py`. (Transposition directe du test §8.7 de J2 sur `os.replace`.)
7. **Cache hors vault** : `cache_dir` sous `vault_path` ⇒ erreur fatale explicite au démarrage.
8. **Câblage** : `website.py` et `synthesis.py` passent par `api_io.call` (vérifié en injectant un `ApiIO` mock et en comptant les appels).
9. **Signaux réels** (mockés) : `reviews.repond_aux_avis` correctement déduit d'avis contenant/non une réponse propriétaire ; `website.derniere_maj` renseignée depuis un `sitemap.xml`/`Last-Modified` mockés ; `social.plateformes_mentionnees` dérivé de `website.social_links` sans aucun appel réseau.
10. **Régression** : la suite J1/J2 existante (101 tests) passe **sans modification** ; le mode `--out json` et le mode `--out vault` restent identiques de l'extérieur (le ledger est un ajout, pas une rupture de contrat).

---

## 10. Ordre d'implémentation (phases — une session Claude Code par phase)

1. **Phase 0** — Ménage (§4). Petit, fonde une base propre.
2. **Phase A** — `knowledge/api_pricing.yaml` (placeholders) + `api_schema.py` (`LedgerEntry`) + tests 1–2.
3. **Phase B** — `api_io.py` : `call`, cache, ledger, budgets, mesureurs, garde-fou imports + tests 3–7.
4. **Phase C** — Câblage `website.py` + `synthesis.py` sur le bus, injection de dépendance dans le pipeline + tests 8, 10 (régression). **À ce stade, les tokens Claude et les fetchs sont déjà métrés**, même avant d'activer les autres collecteurs.
5. **Phase D** — Activation des collecteurs réels : `seo.py` (palier 0), `social.py` (dérivé), `gbp.py`/`reviews.py` (Places via bus), signaux `derniere_maj` + `repond_aux_avis` + tests 9.
6. **Phase E** *(optionnelle / reportable J4)* — Palier 2 navigateur, derrière flag, site propre uniquement, `robots.txt`.

**Revue de diff par l'opératrice entre chaque phase.** Mettre à jour `CLAUDE.md` (section architecture : ajouter le bus d'I/O et le garde-fou réseau ; section commandes ; table des tests) en fin de Phase D.

---

## 11. Hors périmètre de ce livrable (→ J4 et paramétrage)

- **Agent de découverte** : Apollo (`organization_search` / `people_enrichment`) et SERP de découverte alimentant automatiquement le vault en fiches `decouvert`. Le mesureur/cache Apollo est posé ici, mais l'agent qui crée les fiches est J4.
- **`rubric_persona2.yaml`** (cabinet d'avocats) et **wiring des nouveaux signaux** (`derniere_maj`, `repond_aux_avis`) dans les rubriques : c'est du **paramétrage** (config = données), à faire une fois les tests verts.
- **Renseigner les vrais tarifs** dans `api_pricing.yaml` (paramétrage).
- **Orchestrateur cron** (traitement batch planifié).
- Palier 2 si reporté.

---

## 12. Tâches délégables à Claude Cowork (hors code)

À exécuter dans Cowork, pas dans Claude Code :

- **D1 — Tarifs** : remplir `api_pricing.yaml` avec les tarifs vérifiés sur les pages officielles (Anthropic, SERP API retenu, Google Places, Apollo) au moment de la mise en service. Noter la date de relevé.
- **D2 — Tableau de bord usage** : concevoir une requête Dataview (ou un petit export) qui lit `api_usage.log` et affiche coût par fiche / par fournisseur / par mois, et le taux de cache_hit.
- **D3 — Revue de conformité** : relire la matrice « quel signal vient de quelle source » et confirmer qu'aucune donnée ne provient d'un scraping LinkedIn/Facebook ; vérifier la traçabilité source+date.
- **D4 — Jeu d'essai** : compléter les fixtures de fiches prospects pour tester le mode vault de bout en bout avec les nouveaux signaux.
