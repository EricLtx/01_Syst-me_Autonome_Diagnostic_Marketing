# SPEC — Module « J5 : couche de sortie (liste Kemana) + préparation au premier run réel (préflight) »

> Document destiné à Claude Code. À placer à la racine, à côté de `SPEC-J2-bus-vault.md`,
> `SPEC-J3-api-io.md`, `SPEC-J4-decouverte.md`, `architecture.puml`, `ROADMAP.md` et `CLAUDE.md`.
>
> **Démarrer la session par** :
> « Lis `SPEC-J5-sortie-preflight.md`, `SPEC-J4-decouverte.md`, `SPEC-J3-api-io.md`,
> `SPEC-J2-bus-vault.md`, `architecture.puml` et `CLAUDE.md`. Inventorie le repo réel et confirme
> l'état existant (§2). Signale toute divergence entre cette spec et le code AVANT d'écrire la
> moindre ligne. Puis propose un plan d'implémentation phase par phase. »

---

## 1. Contexte et objectif

Le système suit le modèle micro-ordinateur. Trois sous-systèmes sont déjà livrés et testés :

- **Bus de stockage** (J2) : `vault_io.py`, seul module à lire/écrire dans le vault, journalise dans `runs.log`.
- **Bus d'I/O périphérique** (J3) : `api_io.py`, seul module à toucher le réseau externe, journalise unités et coûts dans `api_usage.log`.
- **Agent de découverte** (J4) : `run_discovery.py` (SERP → candidates → Apollo → fiches `decouvert`).

J5 ferme la chaîne de bout en bout du `architecture.puml` **jusqu'à la phase 4 incluse**
(« Liste de sortie — format Kemana »), et **prépare le premier vrai run du système**. Trois
objectifs, dans cet ordre :

1. **Couche de sortie** (`export.py` + `run_export.py`) : produire la **ligne au format Kemana**
   (cf. `architecture.puml`, sortie finale) à partir des fiches `valide` non `opt_out`. C'est la
   phase 4 de l'architecture : une liste exploitable par l'opératrice (CSV / JSONL hors vault).
   **L'export NE déclenche AUCUN envoi et NE fait AUCUNE transition d'état** — il lit le vault et
   écrit un fichier de sortie. C'est un agent en lecture seule sur le vault.

2. **Visualisation de l'usage** (`run_usage.py`) : agréger le grand livre `api_usage.log` (coût
   total, coût par fournisseur, coût par fiche, crédits par persona/ICP) en un rapport lisible —
   le « tableau de bord usage » attendu depuis J3. Sortie console + snapshot Markdown optionnel
   dans le vault via `vault_io`.

3. **Préflight — le garde-fou du premier run réel** (`preflight.py` + `run_preflight.py`) :
   une **vérification déterministe GO / NO-GO** qui contrôle, AVANT tout run réel, que tout ce qui
   doit être préparé l'est (clés, tarifs réels, budgets, vault initialisé, ICP valide, cache hors
   vault, suite de tests verte). C'est la pièce que tu demandes en dernier : implémenter d'abord
   l'export et la visualisation, puis le préflight qui vérifie l'ensemble.

> **Cadrage de périmètre (à confirmer avec l'opératrice).** L'**envoi réel d'emails** (séquence
> outreach, transition `valide → contacte`) reste **J6** : c'est l'action la plus risquée
> juridiquement (CASL au Québec, art. 3 LCD + nLPD en Suisse) et l'architecture impose qu'elle
> soit isolée. J5 produit la **matière** (liste de sortie) ; l'opératrice contacte hors système
> et fait elle-même la transition `valide → contacte` dans Obsidian. Le **premier vrai test du
> système** (découverte → diagnostic → validation → liste) ne nécessite donc aucun envoi.

---

## 2. État attendu en entrée (post-J4) — à confirmer par Claude Code

Inventorier le repo et confirmer avant de coder. **Toute divergence (signatures, noms de modules,
champs) : la signaler et s'aligner sur le code RÉEL, pas sur cette spec.**

- `vault_io.query(statut=..., persona=..., marche=...)` est fonctionnel et rapide (scan
  `10-Prospects/`, parse frontmatter seul).
- `FicheProspect` (Pydantic v2, `extra="allow"`) porte au moins : `statut`, `nom`, `site_web`,
  `score_global`, `gaps_majeurs`, `icp_id`, `opt_out`, `contact_nom`, `contact_titre`,
  `contact_email`, `contact_email_source`, `contact_linkedin`, `rapport`.
- **À vérifier — point structurant pour l'export** : le **signal chaud** et l'**accroche**
  (sortie phase 2 de `architecture.puml`) sont aujourd'hui dans le **corps du rapport**
  (`30-Diagnostics/…`), PAS dans le frontmatter. L'export en a besoin → voir Phase 0 (§4).
- `api_usage.log` existe à la racine, JSONL append-only, une ligne par appel (`LedgerEntry` :
  fournisseur, endpoint, unité, quantité, coût estimé, `fiche`, `cache_hit`, `ts`). Confirmer les
  noms de champs réels de `LedgerEntry`.
- `knowledge/api_pricing.yaml` existe (entrées `serp`, `apollo`, et selon J3 `places`,
  `anthropic`), possiblement avec des **placeholders** (à détecter en préflight).
- `ApiIO` expose ses budgets/plafonds (confirmer comment ils sont configurés : constructeur,
  `config.yaml`, ou env) et lève `BudgetExceeded`.
- Le scaffold (`init_vault.py`) crée les dossiers `10-Prospects/`, `20-Rubrics/`,
  `30-Diagnostics/`, `90-Systeme/`, `_templates/` et `00-Dashboard.md`.
- ICP pilote `icp/persona1-quebec.yaml` présent et valide (`IcpConfig`).

---

## 3. Principes directeurs (rappel — non négociables)

Ces principes priment sur toute optimisation.

- **Gouvernance humaine d'abord.** J5 n'envoie rien et ne déclenche rien automatiquement.
  L'export est en **lecture seule sur le vault**. Aucune transition d'état n'est faite par un
  agent J5. La transition `valide → contacte` reste un geste **humain** dans Obsidian (préparation
  J6).
- **Bus uniques.** Tout réseau via `api_io` (J5 n'en fait aucun : export, usage et préflight sont
  hors-ligne). Toute écriture **dans le vault** via `vault_io`. Les fichiers de **sortie** (CSV /
  JSONL / rapports d'export) sont écrits **hors du vault** (ce ne sont pas des données système, et
  le vault ne doit pas être pollué par des artefacts régénérables — même esprit que la contrainte
  cache G9).
- **Conformité & minimisation.** L'export ne contient **que** les champs nécessaires au premier
  contact (format Kemana, §5.2). Toute fiche `opt_out: true` est **exclue** de tout export, sans
  exception. Chaque ligne exportée porte la **source** de l'email (`contact_email_source`) pour
  l'audit RGPD.
- **Config = données.** Le format de sortie (colonnes Kemana) et la grille tarifaire sont des
  données YAML, jamais codées en dur dans la logique.
- **Échec gracieux isolé.** Une fiche incomplète (email manquant, rapport illisible) ne fait pas
  tomber l'export : elle est listée dans un rapport d'anomalies et l'export continue.
- **Déterminisme, zéro LLM.** J5 ne fait aucun appel Claude. Export, agrégation d'usage et
  préflight sont purement déterministes et auditables.

---

## 4. Phase 0 — Persister le signal chaud et l'accroche (petit, isolé, à valider en premier)

But : rendre l'export possible sans parser le corps Markdown des rapports (fragile). On promeut
deux sorties de la synthèse au rang de **registres du frontmatter**.

| # | Tâche | Détail |
|---|---|---|
| H1 | Étendre `FicheProspect` | Ajouter `signal_chaud: str \| null = None` et `accroche: str \| null = None` (optionnels → rétro-compatibles avec toutes les fiches existantes). Documenter : écrits **par l'agent diagnostic**, comme `score_global`. |
| H2 | Alimenter au diagnostic | Dans `serializers.py` / `vault_runner.py` : lors du passage `decouvert → diagnostique`, `update_frontmatter(signal_chaud=…, accroche=…)` à partir de l'objet `Diagnostic` (champs déjà produits par `synthesis.py` — confirmer leurs noms réels). |
| H3 | Mettre à jour le memory-map | `vault_init.py` génère `memory-map.md` depuis le schéma : vérifier par test que les deux nouveaux champs y apparaissent automatiquement. |

> Si le `Diagnostic` n'expose pas distinctement « signal chaud » et « accroche », **le signaler**
> et proposer la plus petite extension de `synthesis.py` qui les rende disponibles, sans toucher
> à la sortie JSON existante (harnais de test J1).

---

## 5. Spécification — couche de sortie

### 5.1 `export.py` (logique, hors I/O réseau, hors écriture vault)

- `collect_fiches_exportables(vault_io, *, persona=None, marche=None, icp_id=None) -> list[FicheProspect]`
  - Lit via `vault_io.query(statut="valide")`, **filtre `opt_out is False`**, applique les filtres
    optionnels. Aucune autre lecture de fichier.
- `fiche_vers_ligne_kemana(fiche: FicheProspect) -> dict` : mappe une fiche vers les colonnes §5.2.
- `valider_ligne(ligne: dict) -> list[str]` : retourne la liste des anomalies (email absent,
  signal chaud absent, etc.) — **n'exclut pas** la ligne, sert au rapport d'anomalies.

### 5.2 Format de sortie « Kemana » = donnée (`knowledge/export_kemana.yaml`)

Colonnes par défaut, dans l'ordre, conformes à la sortie finale de `architecture.puml`
(`Nom, Titre, Boîte, ICP, Email, Site, Signal chaud, Statut`) :

```yaml
# knowledge/export_kemana.yaml — schéma de la liste de sortie (config = données)
colonnes:
  - {entete: "Nom",          champ: contact_nom}
  - {entete: "Titre",        champ: contact_titre}
  - {entete: "Boîte",        champ: nom}
  - {entete: "ICP",          champ: icp_id}
  - {entete: "Email",        champ: contact_email}
  - {entete: "Source email", champ: contact_email_source}   # audit RGPD — non optionnel
  - {entete: "Site",         champ: site_web}
  - {entete: "Score",        champ: score_global}
  - {entete: "Signal chaud", champ: signal_chaud}
  - {entete: "Statut",       champ: statut}
encodage: utf-8-sig            # BOM pour ouverture propre dans Excel FR
```

> Ajouter / réordonner une colonne = éditer ce YAML, pas le code. `run_export.py` lève une erreur
> explicite si un `champ` référencé n'existe pas dans `FicheProspect`.

### 5.3 `run_export.py` — point d'entrée CLI

```bash
python run_export.py                                  # toutes les fiches 'valide' non opt_out → CSV
python run_export.py --icp persona1-quebec            # filtré par ICP
python run_export.py --format jsonl                   # JSONL au lieu de CSV
python run_export.py --out exports/cible-qc.csv       # chemin de sortie explicite (hors vault)
python run_export.py --dry-run                         # affiche le compte et les anomalies, n'écrit RIEN
```

- Sortie par défaut : `exports/kemana_<icp|tous>_<date>.csv`. Le dossier `exports/` est **hors du
  vault** ; l'ajouter au `.gitignore` du vault et/ou du repo (artefact régénérable).
- Refuse d'écrire dans un chemin situé **sous** `vault/` (erreur fatale explicite, même garde-fou
  d'esprit que G9). Test dédié.
- Console : `N fiches valides, M exclues (opt_out), K exportées, A anomalies`. Les anomalies
  (email manquant, signal chaud absent…) sont listées et écrites dans un rapport voisin
  `exports/<nom>.anomalies.txt`, **sans bloquer** l'export des lignes valides.
- **Aucune transition d'état, aucun envoi.** Re-exécuter l'export est idempotent côté vault
  (lecture seule) ; le fichier de sortie est réécrit.

---

## 6. Spécification — visualisation de l'usage

### 6.1 `usage.py` (agrégation pure, hors I/O réseau)

- `charger_ledger(path: Path) -> list[LedgerEntry]` : lit `api_usage.log` (JSONL). Lignes
  illisibles → ignorées + comptées (le ledger est append-only et peut contenir une ligne tronquée
  après un crash). Ne lève pas.
- `agreger(entries) -> Usage` : totaux et ventilations — coût total, par fournisseur, par
  `endpoint`, par `fiche`, par persona/ICP (déduit de `fiche`/`source`), part de `cache_hit`
  (économies). Tout en pur Python, déterministe.

### 6.2 `run_usage.py` — point d'entrée CLI

```bash
python run_usage.py                       # résumé console (totaux + ventilations)
python run_usage.py --depuis 2026-06-01   # filtre temporel
python run_usage.py --snapshot            # écrit aussi vault/90-Systeme/usage-report.md via vault_io
```

- `--snapshot` écrit un Markdown **dans le vault** — donc **via `vault_io`** (jamais `open()`
  direct). C'est une note système (`90-Systeme/usage-report.md`), régénérable, marquée « généré,
  ne pas éditer ». Permet de consulter l'usage dans Obsidian à côté du reste.
- Le résumé met en avant : **coût par fiche** et **coût par persona** (la découverte Apollo est le
  principal poste), et le **taux de cache** (combien le cache idempotent fait économiser).

> Choix assumé : pas de tableau de bord web ni de dépendance graphique. Le ledger est hors vault
> (Dataview ne peut pas le lire), donc l'agrégation se fait en Python et le résultat est rendu en
> texte / Markdown. Cohérent avec « dépendance-light, zéro coût récurrent ». Si un visuel riche
> est souhaité plus tard, il se branchera sur la même fonction `agreger()`.

---

## 7. Spécification — préflight (le garde-fou du premier run réel)

### 7.1 Principe

`preflight.py` exécute une **batterie de contrôles déterministes** et retourne un verdict
**GO / NO-GO** avec, pour chaque contrôle, un statut `ok | warn | bloquant` et un message
actionnable. **Aucun réseau, aucune clé réellement utilisée** (on vérifie la *présence* d'une clé,
on ne l'appelle pas). C'est le filet de sécurité avant de dépenser le moindre crédit.

### 7.2 Contrôles (un par ligne — `Check(nom, niveau, ok, message)`)

| Contrôle | Niveau si échec | Vérifie |
|---|---|---|
| `cles_api` | bloquant (SERP, Apollo) / warn (Places, Anthropic) | `SERP_API_KEY` et `APOLLO_API_KEY` présentes en env. `GOOGLE_PLACES_API_KEY` et `ANTHROPIC_API_KEY` absentes ⇒ **warn** (mode dégradé : palier 1 désactivé / repli déterministe). |
| `tarifs_reels` | bloquant | `api_pricing.yaml` ne contient **plus de placeholder** pour les fournisseurs qui seront appelés ; un champ `releve_le` (date) est présent. Détecter les valeurs sentinelles (0, `null`, `"TODO"`, `"placeholder"`). |
| `budgets` | bloquant | Les budgets `ApiIO` (au moins SERP et Apollo) sont définis, > 0 et raisonnables (plafonds prudents pour un pilote). Sans budget ⇒ un run de découverte peut vider les crédits Apollo. |
| `vault_initialise` | bloquant | Les dossiers attendus existent (sinon : « lance `python init_vault.py` »). |
| `cache_hors_vault` | bloquant | Le `cache_dir` d'`api_io` est bien **hors** du vault (ré-assertion G9). |
| `icp_valide` | bloquant | Au moins un `icp/*.yaml` charge sans erreur via `IcpConfig` ; l'ICP visé par le run pilote existe. |
| `schema_export` | bloquant | `knowledge/export_kemana.yaml` charge et tous ses `champ` existent dans `FicheProspect`. |
| `tests_verts` | warn (par défaut) / bloquant (`--strict`) | Lance `pytest -q` ; un échec est un avertissement (ou bloquant en mode strict). |
| `garde_fous_bus` | bloquant | Les tests AST « aucun réseau hors `api_io` » et « aucune écriture vault hors `vault_io` » passent (inclut les nouveaux modules J5 : `export.py`, `usage.py`, `run_export.py`, `run_usage.py`, `preflight.py`). |

### 7.3 `run_preflight.py` — point d'entrée CLI

```bash
python run_preflight.py                         # rapport complet GO / NO-GO
python run_preflight.py --icp persona1-quebec   # vérifie aussi l'ICP visé par le pilote
python run_preflight.py --strict                # tests verts deviennent bloquants
```

- Sortie : un tableau lisible (un symbole par contrôle), puis un verdict final.
  **Code de sortie 0 si GO, non-zéro si NO-GO** (utilisable en pré-condition de script / cron J7).
- Le verdict liste explicitement **ce qu'il reste à préparer** et **comment** (commande ou
  fichier à éditer), pour que la mise en route soit auto-documentée.

---

## 8. Tests et critères d'acceptation

Tout mocké. **Aucun réseau réel, aucune clé.** Fixtures de fiches en `tmp_path`.

1. **Export — sélection** : 3 fiches (`valide` non opt_out, `valide` opt_out, `diagnostique`)
   ⇒ seule la première est exportée ; l'opt_out est exclue ; la `diagnostique` ignorée.
2. **Export — mapping Kemana** : une fiche complète ⇒ ligne avec toutes les colonnes du YAML, dans
   l'ordre, valeurs correctes ; `champ` inexistant dans le YAML ⇒ erreur explicite au chargement.
3. **Export — anomalies non bloquantes** : fiche `valide` sans `contact_email` ⇒ exportée +
   signalée dans le rapport d'anomalies ; l'export ne lève pas.
4. **Export — refus d'écrire dans le vault** : `--out` sous `vault/` ⇒ erreur fatale, rien écrit.
5. **Export — lecture seule sur le vault** : après export, aucune fiche n'a changé de `statut`,
   `runs.log` ne contient **aucune** opération d'écriture vault imputable à l'export.
6. **Export — dry-run** : `--dry-run` n'écrit aucun fichier de sortie ; le compte est correct.
7. **Usage — agrégation** : ledger mocké (SERP + Apollo + cache_hit) ⇒ totaux, coût par
   fournisseur, coût par fiche, taux de cache corrects ; ligne tronquée ⇒ ignorée et comptée, pas
   d'exception.
8. **Usage — snapshot via bus** : `--snapshot` écrit `90-Systeme/usage-report.md` **via
   `vault_io`** (vérifier l'opération dans `runs.log`) et nulle part en `open()` direct.
9. **Préflight — NO-GO** : clés absentes / tarifs placeholder / budget nul ⇒ contrôles `bloquant`,
   verdict NO-GO, code de sortie non-zéro, messages actionnables présents.
10. **Préflight — GO** : environnement mocké complet (clés présentes, tarifs datés, budgets > 0,
    vault initialisé, ICP valide, cache hors vault) ⇒ verdict GO, code de sortie 0.
11. **Préflight — Places/Anthropic absents = warn** : ces deux clés manquantes ⇒ `warn` (pas
    `bloquant`), verdict GO possible (mode dégradé documenté dans le message).
12. **Garde-fous bus étendus** : par AST/grep, `export.py` / `usage.py` / `run_export.py` /
    `run_usage.py` / `preflight.py` n'importent ni `requests` ni `anthropic`, et n'ouvrent aucun
    fichier sous `vault/` (seul `usage.py --snapshot` y écrit, et uniquement via `vault_io`).
13. **Phase 0** : `FicheProspect` accepte `signal_chaud`/`accroche` optionnels ; une fiche
    antérieure (sans ces champs) se lit toujours ; `memory-map.md` régénéré les mentionne.
14. **Régression** : la suite J1/J2/J3/J4 complète passe **sans modification** ; `--out json` et
    `--out vault` inchangés de l'extérieur.

---

## 9. Conformité — checklist intégrée (à vérifier en revue, pas seulement en code)

- [ ] **Opt-out absolu** : aucune fiche `opt_out: true` n'apparaît dans un export (test 1).
- [ ] **Minimisation** : l'export ne contient que les colonnes du format Kemana ; aucune donnée
      Apollo superflue.
- [ ] **Traçabilité** : `Source email` (`contact_email_source`) présent pour chaque ligne portant
      un email ; sinon anomalie signalée.
- [ ] **Pas d'envoi en J5** : aucune transition `valide → contacte`, aucun appel réseau.
- [ ] **Avant J6 (envoi)** : faire valider par un juriste le cadre CASL (QC) / nLPD + art. 3 LCD
      (CH) / RGPD (FR) — identification claire, base légale intérêt légitime B2B, mécanisme de
      désinscription. **À documenter dans `journal-decisions.md` avant tout premier envoi.**

---

## 10. Ordre d'implémentation (phases — une session Claude Code par phase)

1. **Phase 0** — Persistance `signal_chaud`/`accroche` (§4) + tests 13. Petit, fonde l'export.
2. **Phase A** — `export.py` + `knowledge/export_kemana.yaml` + `run_export.py` + tests 1–6.
3. **Phase B** — `usage.py` + `run_usage.py` (+ snapshot via `vault_io`) + tests 7–8.
4. **Phase C** — **Préflight (le garde-fou, en dernier)** : `preflight.py` + `run_preflight.py`
   + extension des garde-fous bus aux modules J5 + tests 9–12, 14.
5. **⏸ Paramétrage minimal** (hors Claude Code — opératrice / Cowork, cf. §11) : clés, tarifs
   réels, budgets. **Bloquant pour la phase suivante uniquement.**
6. **Phase D** — **Premier vrai run du système** (pilote borné) :
   `python run_preflight.py --icp persona1-quebec` ⇒ doit être **GO** ; puis
   `run_discovery.py --dry-run`, revue des candidates, run réel borné (`max_enrichissements: 5`),
   `run_diagnostic.py --out vault`, validation humaine dans Obsidian, `run_export.py`,
   `run_usage.py --snapshot`. Lecture du ledger, revue des fiches et de la liste de sortie.

**Revue de diff par l'opératrice entre chaque phase.** Fin de Phase C : mettre à jour `CLAUDE.md`
(architecture : couche de sortie + usage + préflight ; commandes `run_export.py` / `run_usage.py`
/ `run_preflight.py` ; table des tests) et `README.md` (le réaligner — il est resté à « prochaine
étape J3 / 101 tests »).

---

## 11. Ce qui manquera avant le premier vrai test — à préparer hors code (Cowork / opératrice)

> Le **préflight (§7)** automatise la vérification de cette liste : viser un verdict **GO**.

### 11.1 Clés API (variables d'environnement, jamais en dur)

| Clé | Requise pour le 1er test ? | Effet si absente |
|---|---|---|
| `SERP_API_KEY` | **Oui** | Découverte impossible (NO-GO préflight). |
| `APOLLO_API_KEY` | **Oui** | Enrichissement contact impossible ; `--sans-contact` reste possible mais la liste Kemana n'aura ni nom ni email (NO-GO si on veut une vraie liste). |
| `GOOGLE_PLACES_API_KEY` | Optionnelle (warn) | Collecteurs palier 1 (GBP, avis) en stub. Diagnostic dégradé mais fonctionnel. |
| `ANTHROPIC_API_KEY` | Optionnelle (warn) | Synthèse LLM remplacée par le repli déterministe. Tourne hors-ligne. |

### 11.2 Tarifs réels (`knowledge/api_pricing.yaml`)

- Remplacer les **placeholders** par les vrais tarifs SERP et Apollo (et Places/Anthropic si
  utilisés), relevés sur les pages officielles. Ajouter un champ `releve_le: AAAA-MM-JJ`.
- Sans tarifs réels, le ledger « compte » mais ne **chiffre** rien — le contrôle `tarifs_reels` du
  préflight est **bloquant**.

### 11.3 Budgets (`ApiIO`)

- Définir des plafonds **prudents** pour le pilote (ex. plafond Apollo correspondant à ~quelques
  dizaines d'enrichissements, plafond SERP idem). Garde-fou indispensable : un run non borné peut
  consommer des crédits Apollo en masse. Contrôle `budgets` **bloquant**.

### 11.4 Vault et ICP

- Lancer `python init_vault.py` (idempotent).
- Confirmer l'ICP pilote `icp/persona1-quebec.yaml` (déjà livré J4). Les autres ICP (les six
  profils Kemana, persona 2 cabinets d'avocats) sont du **paramétrage** ultérieur, non bloquant
  pour le premier test.

### 11.5 Visualisation

- La visualisation d'usage est livrée **dans J5** (`run_usage.py`, §6) — rien à préparer côté
  opératrice, sinon ouvrir le snapshot dans Obsidian après le run.

### 11.6 Juridique (uniquement pour J6 — l'envoi, pas pour le test J5)

- La validation CASL / nLPD / RGPD du cadre d'**envoi** est requise **avant J6**, pas avant le
  premier test du système (qui s'arrête à la liste de sortie). À acter dans
  `journal-decisions.md`.

---

## 12. Tâches délégables à Claude Cowork (hors code)

- **F1 — Paramétrage pré-pilote** : renseigner clés, tarifs réels datés, budgets prudents (§11) ;
  faire passer `run_preflight.py` au vert.
- **F2 — Revue de la liste de sortie** : juger la qualité du CSV Kemana du run pilote (colonnes
  utiles ? signal chaud parlant ? anomalies récurrentes ?) → ajuster `export_kemana.yaml` (config)
  ou la synthèse (rubric).
- **F3 — `rubric_persona2.yaml`** (cabinets d'avocats) + câblage des signaux `derniere_maj`,
  `repond_aux_avis`, `seo.local_keywords` dans les rubriques — pur paramétrage (config = données).
- **F4 — Revue conformité** : repasser la checklist §9 sur la première liste réelle (opt-out,
  minimisation, source des emails).

---

## 13. Hors périmètre de ce livrable

- **Envoi d'emails / séquence outreach / transition `valide → contacte` automatique** → **J6**.
- **Orchestrateur cron** (chaînage automatique découverte → diagnostic → export) → **J7**.
  (`run_preflight.py` est conçu pour servir de pré-condition à ce cron : code de sortie 0 = GO.)
- **Tableau de bord web** de l'usage : non — agrégation Python + Markdown suffit.
- **Nouveaux ICP / persona 2 / nouveaux signaux dans les rubriques** : paramétrage (config), pas
  ce livrable.
