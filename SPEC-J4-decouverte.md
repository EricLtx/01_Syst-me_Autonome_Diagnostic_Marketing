# SPEC — Module « J4 : agent de découverte (SERP + Apollo → fiches `decouvert`) »

> Document destiné à Claude Code. À placer à la racine, à côté de `SPEC-J2-bus-vault.md`,
> `SPEC-J3-api-io.md`, `ROADMAP.md` et `CLAUDE.md`.
>
> **Démarrer la session par** :
> « Lis `SPEC-J4-decouverte.md`, `SPEC-J3-api-io.md`, `SPEC-J2-bus-vault.md` et `CLAUDE.md`.
> Inventorie le repo réel et confirme l'état existant (§2). Signale toute divergence entre cette
> spec et le code AVANT d'écrire la moindre ligne. Puis propose un plan d'implémentation phase
> par phase. »

---

## 1. Contexte et objectif

Le système suit le modèle micro-ordinateur. Deux bus existent :

- **Bus de stockage** (J2) : `vault_io.py`, seul module à lire/écrire dans le vault, journalise dans `runs.log`.
- **Bus d'I/O périphérique** (J3) : `api_io.py`, seul module à toucher le réseau externe, journalise unités et coûts dans `api_usage.log`.

J4 ajoute le **premier agent amont** : la couche de découverte (temps 1 de `architecture.puml`).
Aujourd'hui, le vault est alimenté à la main (copie du template). Après J4 :

```
ICP (YAML) ──▶ DiscoveryCollector ──▶ boîtes candidates ──▶ PersonEnrichment ──▶ fiches `decouvert`
                  (requêtes SERP)        (nom, URL, ICP)         (Apollo)           dans le vault
```

Sortie phase 1a (cf. `architecture.puml`) : boîtes candidates (nom, URL, ICP).
Sortie phase 1b : + dirigeant / office manager, email à **source tracée**, URL LinkedIn.

L'agent de découverte est un **CPU** comme le pipeline diagnostic : il ne touche ni le vault ni le
réseau directement — il parle aux deux bus. Il ne change **rien** à la machine à états : il *crée*
des fiches `decouvert`, il ne fait aucune transition (le seul droit de transition d'un agent reste
`decouvert → diagnostique`, détenu par le pipeline diagnostic).

---

## 2. État attendu en entrée (post-J3) — à confirmer par Claude Code

Inventorier le repo et confirmer avant de coder :

- `api_io.py` existe : `call(fournisseur, endpoint, fn, *, fiche, cache_key, measure)`, ledger
  `api_usage.log`, budgets avec `BudgetExceeded`, cache hors vault, garde-fou AST « aucun réseau
  hors api_io ».
- `knowledge/api_pricing.yaml` existe avec les entrées `serp` et `apollo` (placeholders acceptés).
- `vault_io.exists(nom=..., site_web=...)` est fonctionnel (préparé en J2 pour la déduplication).
- `vault_io.write_fiche` est atomique, idempotent, journalisé ; `FicheProspect` porte
  `source_decouverte: str`.
- Les collecteurs réels J3 (GBP/avis/SEO/social) existent ; le pipeline `--out vault` est inchangé
  de l'extérieur.
- Le scaffold ne crée que 5 sous-dossiers persona×marché alors que le schéma autorise 10
  combinaisons — `_prospect_dir` crée le chemin à la volée, donc pas bloquant, mais à garder en
  tête (§5.4).

**Toute divergence (signatures, noms de modules, champs) : la signaler et s'aligner sur le code
réel, pas sur cette spec.**

---

## 3. Séquencement : faut-il le paramétrage J3 avant de construire J4 ?

**Non pour construire. Oui — une tranche mince — avant le premier run réel.**

| Élément de paramétrage | Requis pour CODER J4 ? | Requis pour le 1er RUN RÉEL de J4 ? |
|---|---|---|
| Clés API (SERP, Apollo) | **Non** — tout est mocké | **Oui** |
| Tarifs réels dans `api_pricing.yaml` | **Non** — placeholders suffisent aux tests | **Oui** — la découverte est le principal poste de coût ; sans grille, le ledger ne quantifie rien |
| Budgets/plafonds `api_io` | **Non** | **Oui** — garde-fou indispensable : un run de découverte sans plafond peut consommer des crédits Apollo en masse |
| `ANTHROPIC_API_KEY` | **Non** | **Non** — la découverte n'utilise pas le LLM (§4, principe) |
| Rubrique persona 2, câblage des nouveaux signaux dans les rubriques | **Non** | **Non** — paramétrage indépendant, peut suivre |
| Rubriques ICP (`icp/*.yaml`) | **Oui, 1 seule** (le pilote `persona1-quebec`, livrée par cette spec) | Les autres suivent par config |

**Conclusion opérationnelle** : Claude Code peut enchaîner J3 → J4 sans interruption de
paramétrage. Le paramétrage minimal (clés SERP/Apollo + tarifs + budgets) se fait en une session
Cowork/manuelle **juste avant la Phase E** (run pilote réel, §10). Tout le reste du paramétrage
attend la fin de J4 sans rien bloquer.

---

## 4. Principes directeurs (non négociables)

- **Conformité d'abord.** Les données « personnes » viennent **exclusivement d'Apollo** (API
  licenciée). **Aucun scraping LinkedIn/Facebook, jamais** — même pas « juste la page publique ».
  La découverte d'entreprises passe par SERP API (fournisseur managé). Base légale : intérêt
  légitime B2B ; **minimisation** : on ne stocke que ce qui sert au diagnostic et au premier
  contact (nom, titre, email pro, URL entreprise) — pas de données superflues.
- **Traçabilité** : chaque donnée porte sa source et sa date (`source_decouverte`, champ `_source`
  des signaux, ledger). Exigence d'audit RGPD.
- **Découverte déterministe, zéro LLM.** La couche de découverte ne fait que requêter, filtrer,
  dédupliquer, écrire. Aucun appel Claude dans J4 : le raisonnement LLM reste confiné à la
  synthèse (J1) et, plus tard, à l'outreach (J6). Coût prévisible, comportement auditables.
- **Bus uniques** : tout réseau via `api_io` (métré, caché, budgété) ; toute écriture via
  `vault_io` (atomique, validée, journalisée). L'agent découverte n'importe ni `requests`, ni
  `anthropic`, ni n'ouvre de fichier sous `vault/`.
- **Config = données** : un ICP est un YAML. Nouveau profil Kemana ou nouveau marché = nouveau
  fichier, zéro code.
- **Échec gracieux isolé** : une candidate qui échoue à l'enrichissement n'interrompt pas le lot ;
  elle est journalisée et — décision de cette spec — **écrite quand même** sans contact (le
  diagnostic ne dépend pas du contact ; l'enrichissement pourra être rejoué).
- **Gouvernance humaine inchangée** : J4 crée des `decouvert` ; il ne valide rien, ne contacte
  rien, ne transitionne rien.

---

## 5. Spécifications

### 5.1 Rubriques ICP — `icp/*.yaml` (config = données)

Un fichier par couple persona×marché. Livrer le **pilote** `icp/persona1-quebec.yaml` ; les autres
sont du paramétrage. Structure :

```yaml
# icp/persona1-quebec.yaml — DONNÉE, pas du code.
# Un nouvel ICP (profil Kemana, nouveau marché) = un nouveau fichier. Zéro code.
icp_id: persona1-quebec
persona: 1
marche: quebec
description: "Détaillant / installateur HVAC (climatisation, chauffage, PAC) — Québec"

# Génération des requêtes SERP : produit cartésien gabarits × localites (borné).
requetes:
  gabarits:
    - "installateur thermopompe {localite}"
    - "entreprise climatisation chauffage {localite}"
    - "chauffagiste {localite}"
  localites: ["Québec", "Lévis", "Trois-Rivières", "Sherbrooke", "Laval", "Longueuil"]
  max_resultats_par_requete: 10        # plafond dur côté agent (en plus du budget api_io)

# Filtres déterministes sur les candidates (anti-bruit) :
filtres:
  domaines_exclus:                      # annuaires/agrégateurs — pas des prospects
    - "pagesjaunes.ca"
    - "yelp."
    - "facebook.com"
    - "linkedin.com"
    - "411.ca"
    - "houzz."
  exiger_domaine_propre: true           # rejeter les pages hébergées (ex. site.wix.com/x)

# Enrichissement Apollo :
enrichissement:
  titres_cibles: ["propriétaire", "président", "directeur général", "office manager", "owner", "president"]
  max_enrichissements: 25               # plafond dur par run (en plus du budget api_io)
```

Validation pydantic du fichier ICP à la lecture (`icp_schema.py`, modèle `IcpConfig`) : un YAML
mal formé lève une erreur explicite — même philosophie que `FicheProspect`.

### 5.2 `discovery.py` — DiscoveryCollector (phase 1a)

```python
class DiscoveryCollector:
    def __init__(self, api_io: ApiIO, icp: IcpConfig): ...
    def discover(self) -> list[Candidate]:
        """ICP → requêtes SERP → candidates filtrées et dédupliquées (intra-lot).
        Chaque appel SERP : api_io.call("serp", "search", ..., cache_key=requete).
        Le cache rend les re-runs gratuits (idempotence, principe n°5)."""
```

- `Candidate` (pydantic, en mémoire) : `nom`, `site_web`, `icp_id`, `source` (ex.
  `"serp:<requete>"`), `date_decouverte`.
- Normalisation d'URL avant dédup (schéma, `www.`, slash final, casse du domaine) pour que
  `https://exemple.ca/` et `http://www.exemple.ca` soient la même entreprise.
- Extraction du nom : depuis le titre du résultat SERP, nettoyé de façon déterministe (séparateurs
  `|`, `—`, suffixes de localité). Pas de LLM.
- Application des `filtres` ICP (domaines exclus, domaine propre).

### 5.3 `enrichment.py` — PersonEnrichment (phase 1b)

```python
class PersonEnrichment:
    def __init__(self, api_io: ApiIO, icp: IcpConfig): ...
    def enrich(self, candidate: Candidate) -> Contact | None:
        """Apollo (people_enrichment via api_io) → meilleur contact selon titres_cibles.
        Retourne None si aucun contact pertinent — la candidate reste valable sans contact."""
```

- `Contact` (pydantic) : `nom_personne`, `titre`, `email`, `email_source` (ce qu'Apollo déclare
  comme provenance/statut de l'email), `linkedin_url`, `date_enrichissement`.
- **Minimisation** : ne mapper que ces champs, ignorer le reste de la réponse Apollo.
- `cache_key` = domaine de l'entreprise (ne jamais payer deux fois le même enrichissement).
- Respecter `max_enrichissements` de l'ICP ; au-delà, les candidates sont écrites sans contact et
  marquées pour enrichissement ultérieur (§5.4).

### 5.4 Écriture vault + extension minimale du schéma

**Extension de `FicheProspect`** (champs optionnels, rétro-compatibles — aucune fiche existante
n'est invalidée) :

```yaml
# Ajouts au frontmatter (tous optionnels, null par défaut) :
contact_nom: null          # str | null
contact_titre: null        # str | null
contact_email: null        # str | null
contact_email_source: null # str | null  — provenance déclarée (audit RGPD)
contact_linkedin: null     # str | null  — URL (référence, jamais scrapée)
icp_id: null               # str | null  — ex. "persona1-quebec"
opt_out: false             # bool — fondation : si true, EXCLU de tout export/outreach futur
```

Règles d'écriture :
- `source_decouverte` = `"serp:<fournisseur>"` (vs `"manuel"` existant — valeur par défaut
  inchangée).
- **Déduplication inter-runs** via `vault_io.exists(site_web=...)` puis `exists(nom=...)` :
  une fiche existante n'est **jamais** recréée ni écrasée par la découverte (les annotations
  humaines priment). La collision est journalisée comme « doublon ignoré ».
- Création via `vault_io.write_fiche` uniquement (atomique, validée, journalisée dans `runs.log`).
- `_prospect_dir` route la fiche dans `10-Prospects/personaN-marche/` ; si le sous-dossier
  manque (combinaisons non scaffoldées), il est créé par le bus — comportement existant, à
  documenter dans `memory-map.md`.
- Mettre à jour `vault_init.py` : le `memory-map.md` généré doit refléter les nouveaux champs
  (il est généré depuis le schéma, donc cela suit automatiquement — vérifier par test).

### 5.5 `run_discovery.py` — point d'entrée CLI

```bash
python run_discovery.py --icp persona1-quebec                  # run complet (1a + 1b)
python run_discovery.py --icp persona1-quebec --sans-contact   # 1a seulement (zéro crédit Apollo)
python run_discovery.py --icp persona1-quebec --dry-run        # affiche les candidates, n'écrit RIEN
python run_discovery.py --enrichir-existants --icp ...         # rejoue 1b sur les fiches sans contact
```

- `--dry-run` est **essentiel** pour la gouvernance : il permet de juger la qualité des requêtes
  ICP avant de dépenser un crédit ou d'écrire une fiche. (Les appels SERP du dry-run passent
  quand même par `api_io` — donc métrés et cachés ; le run réel qui suit est alors quasi gratuit
  côté SERP grâce au cache.)
- Sortie console : N candidates trouvées, M doublons ignorés, K fiches créées, E enrichies,
  erreurs isolées — même style que `run_diagnostic.py --out vault`.
- `BudgetExceeded` (levée par `api_io`) : arrêt **propre** du lot — tout ce qui est déjà écrit
  reste valide, le message indique le plafond atteint, et le run est reprenable (dédup + cache
  rendent la reprise idempotente).

---

## 6. Ce que J4 ne fait PAS (hors périmètre)

- **Aucun appel LLM** (pas de reformulation de requêtes, pas de scoring de pertinence par Claude).
- **Aucun scraping** de LinkedIn, Facebook, Google Maps — ni direct ni « via navigateur ».
- **Aucune transition d'état**, aucun déclenchement automatique du diagnostic (l'opératrice lance
  `--out vault` quand elle veut ; le chaînage automatique est J7).
- **Aucun export** (J5), **aucun outreach** (J6), **aucun cron** (J7).
- Pas de scoring de candidates au-delà des filtres déterministes de l'ICP.

---

## 7. Tests et critères d'acceptation

Tout mocké (SERP, Apollo via `api_io` mock ou réponses simulées). **Aucun réseau réel, aucune clé.**

1. **Schéma ICP** : YAML valide accepté ; `icp_id` incohérent avec persona/marche, gabarit sans
   `{localite}`, ou champ manquant ⇒ erreur explicite.
2. **Génération de requêtes** : produit cartésien gabarits×localites correct, borné par
   `max_resultats_par_requete`.
3. **Filtrage** : un résultat `pagesjaunes.ca` est exclu ; un domaine hébergé est exclu si
   `exiger_domaine_propre` ; un domaine propre passe.
4. **Normalisation/dédup intra-lot** : `https://exemple.ca/` et `http://www.exemple.ca` ⇒ une
   seule candidate.
5. **Dédup inter-runs** : une fiche existante dans le vault (même `site_web`, ou même `nom`) ⇒
   non recréée, non modifiée, collision journalisée. Une fiche annotée à la main survit
   intégralement à un re-run de découverte.
6. **Enrichissement** : réponse Apollo mockée ⇒ `Contact` correctement mappé (titres_cibles
   respectés, minimisation : aucun champ hors liste) ; réponse vide ⇒ fiche créée **sans**
   contact ; `max_enrichissements` respecté.
7. **Écriture conforme** : la fiche créée valide `FicheProspect`, `statut="decouvert"`,
   `source_decouverte` tracée, `icp_id` renseigné, `opt_out=false`, rangée dans le bon
   sous-dossier ; `runs.log` porte les `write_fiche`.
8. **Ledger** : un run mocké produit dans `api_usage.log` les lignes SERP et Apollo attendues,
   avec `fiche` renseignée pour les enrichissements ; un re-run identique ⇒ `cache_hit=True`,
   coût 0.
9. **Budget** : plafond Apollo atteint en milieu de lot ⇒ arrêt propre, fiches déjà écrites
   intactes, message explicite ; reprise idempotente.
10. **Dry-run** : `--dry-run` n'écrit **rien** dans le vault (aucun `write_fiche` dans
    `runs.log`).
11. **Garde-fous bus** : par AST/grep, `discovery.py` / `enrichment.py` / `run_discovery.py`
    n'importent ni `requests` ni `anthropic` et n'ouvrent aucun fichier sous `vault/`
    (extension des tests garde-fous J2/J3 existants).
12. **Régression** : la suite J1/J2/J3 complète passe sans modification ; le schéma étendu lit
    toutes les fiches existantes (champs nouveaux optionnels).

---

## 8. Conformité — checklist intégrée (à vérifier en revue, pas seulement en code)

- [ ] Personnes : Apollo uniquement ; `contact_email_source` rempli pour chaque email.
- [ ] Minimisation : seuls les champs §5.4 sont persistés ; rien d'autre de la réponse Apollo.
- [ ] Traçabilité : `source_decouverte` + dates sur chaque fiche ; ledger complet.
- [ ] `opt_out` présent dans le schéma et documenté dans `memory-map.md` (consommé par J5/J6 :
      toute fiche `opt_out: true` est exclue d'export et d'outreach).
- [ ] Aucun contournement technique (pas de navigateur furtif, pas de bypass anti-bot).

---

## 9. Ordre d'implémentation (phases — une session Claude Code par phase)

1. **Phase A** — `icp_schema.py` + `icp/persona1-quebec.yaml` (pilote) + extension
   `FicheProspect` (champs optionnels) + tests 1, 12. Petit, fonde tout.
2. **Phase B** — `discovery.py` (requêtes, filtres, normalisation, dédup intra-lot) + tests 2–4.
3. **Phase C** — `enrichment.py` (Apollo via bus, minimisation, plafonds) + tests 6, 8 (partiel).
4. **Phase D** — Écriture vault (dédup inter-runs) + `run_discovery.py` (CLI, dry-run, reprise)
   + tests 5, 7–11.
5. **⏸ Paramétrage minimal** (hors Claude Code — opératrice/Cowork) : clés SERP + Apollo,
   tarifs réels dans `api_pricing.yaml`, budgets `api_io`. **Bloquant pour la phase suivante
   uniquement.**
6. **Phase E** — Run pilote réel : `--dry-run` sur `persona1-quebec`, revue des candidates par
   l'opératrice, puis run réel borné (ex. `max_enrichissements: 5`), lecture du ledger, revue
   des fiches dans Obsidian.

**Revue de diff par l'opératrice entre chaque phase.** Fin de Phase D : mettre à jour `CLAUDE.md`
(architecture : agent découverte + nouveaux champs ; commandes `run_discovery.py` ; table des
tests) et `README.md`.

---

## 10. Tâches délégables à Claude Cowork (hors code)

- **E1 — Rubriques ICP** : décliner les six profils Kemana en `icp/*.yaml` (gabarits de requêtes,
  localités par marché, titres cibles) — pur paramétrage après la Phase A.
- **E2 — Paramétrage minimal pré-Phase E** : tarifs SERP/Apollo vérifiés sur pages officielles
  (date de relevé notée), budgets prudents pour le pilote.
- **E3 — Revue du pilote** : juger la qualité des candidates du dry-run (pertinence, bruit) →
  ajuster gabarits/filtres de l'ICP (config, pas code).
- **E4 — Revue conformité** : vérifier la checklist §8 sur les premières fiches réelles
  (notamment `contact_email_source`).
