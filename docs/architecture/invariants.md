# Invariants d'architecture — règles non négociables et leur contrôle

> Un invariant qui n'est pas testé n'est pas un invariant : c'est un vœu.
> Chaque règle ci-dessous porte donc sa **preuve exécutable**. Les noms de
> tests cités ont été relevés dans le dépôt le **2026-08-01** (commit de tête
> `2ed8d93`) ; ils peuvent bouger, la commande de contrôle reste valable.
>
> Cadre général : `docs/architecture/README.md`.
> Protocole de vérification par itération : `docs/strategie/GOUVERNANCE-revue-iterative.md`.

## Comment lire ce document

| Colonne | Sens |
|---|---|
| **Invariant** | la règle, formulée de façon falsifiable |
| **Pourquoi** | ce qui casse si on la viole — jamais « parce que c'est propre » |
| **Comment c'est tenu** | le mécanisme dans le code |
| **Comment c'est testé** | la commande ou le test qui le prouve |

Un chantier qui casse un invariant est **échoué**, quel que soit son taux de
cohérence par ailleurs.

---

## I1 — Un seul écrivain du vault

**Invariant.** `diagnostic/vault_io.py` est le **seul** module autorisé à lire
et écrire sous `vault/`. Aucun autre module n'appelle `os.replace()`.

**Pourquoi.** Le vault est la source de vérité versionnée du système. S'il a
plusieurs écrivains, il n'a plus de journal fiable, plus de garantie
d'atomicité, et plus de validation de schéma — l'auditabilité disparaît.

**Comment c'est tenu.**
- Écriture atomique : `VaultIO._atomic_write()` écrit un `.tmp` **dans le même
  répertoire** (donc le même volume) puis appelle `os.replace()`. Un crash
  avant le `replace` ne laisse jamais une cible à moitié écrite.
- `os.replace()` n'apparaît nulle part ailleurs. L'orchestrateur, qui a besoin
  d'une création atomique pour son verrou, utilise délibérément
  `os.open(..., O_CREAT|O_EXCL)` **et non** `os.replace()` — le commentaire du
  code le dit explicitement.
- Toute écriture passe par une méthode publique de `VaultIO` : `write_fiche`,
  `update_frontmatter`, `transition`, `write_rapport`, `write_system_note`,
  `log_erreur`. Besoin d'écrire autre chose ? On ajoute une méthode, on n'ouvre
  pas de porte dérobée.

**Comment c'est testé.**
```bash
python -m pytest tests/test_vault_io.py -q          # test_os_replace_uniquement_dans_vault_io
python -m pytest tests/test_preflight.py -q         # test_modules_j5_pas_d_appel_os_replace_direct
grep -rn 'os\.replace' --include='*.py' .           # contrôle manuel : une seule occurrence utile
```
`tests/test_vault_io.py::test_crash_avant_replace_ne_cree_pas_la_cible` couvre
la propriété d'atomicité elle-même.

---

## I2 — Journal d'écritures append-only

**Invariant.** Toute opération d'écriture du vault produit **une ligne JSONL**
dans `runs.log`, écrite **exclusivement** par `VaultIO._journal()`. Aucun agent
n'écrit dans ce fichier.

**Pourquoi.** C'est la trace qui permet de répondre à « qui a modifié cette
fiche, quand, et pourquoi ». Si un agent peut y écrire directement, la trace
devient déclarative au lieu d'être constatée.

**Comment c'est tenu.** `_journal()` est privé et ouvre le fichier en mode `a`.
Les agents qui ont besoin de tracer une erreur passent par la méthode publique
`log_erreur()`, qui délègue à `_journal()`.

**Comment c'est testé.**
```bash
python -m pytest tests/test_vault_io.py -q          # test_journal_append_only
```

---

## I3 — Schéma validé à l'écriture

**Invariant.** Tout frontmatter est validé par `FicheProspect` (Pydantic v2)
**avant** persistance. Une fiche invalide n'est jamais écrasée silencieusement.

**Pourquoi.** Le vault est édité à la main dans Obsidian. Sans validation, une
faute de frappe humaine se propage silencieusement dans tout le pipeline.

**Comment c'est tenu.** `update_frontmatter()` valide (`model_validate`) **avant**
d'appeler `_atomic_write`. `read_fiche()` valide à la lecture. `query()` ignore
silencieusement les fichiers non conformes plutôt que de planter la boucle.
`FicheProspect` utilise `extra="allow"` : les annotations humaines survivent au
round-trip au lieu d'être effacées.

**Comment c'est testé.**
```bash
python -m pytest tests/test_vault_schema.py tests/test_vault_io.py -q
```

---

## I4 — Un seul chemin vers le réseau

**Invariant.** `diagnostic/api_io.py` est le **seul** module dont les fonctions
touchent le réseau sortant. Aucun `import requests` ni `import anthropic` **au
niveau module** hors de lui.

**Pourquoi.** C'est ce qui rend les coûts intégralement traçables et les budgets
réellement bloquants. Un seul appel direct hors bus, et le grand livre ment.

**Comment c'est tenu.**
- Tout appel passe par `ApiIO.call(fournisseur, endpoint, fn, ...)`, qui
  enchaîne : lecture de cache → pré-contrôle budgétaire → exécution → mesure des
  unités → calcul du coût → journalisation → mise en cache.
- Les collecteurs qui ont besoin de `requests` l'importent **à l'intérieur des
  fonctions** (import paresseux), jamais au niveau module.
- Un garde-fou AST (`diagnostic/preflight.py::_check_garde_fous_bus`) parcourt
  une liste **nominative** de modules surveillés et refuse tout import de niveau
  module de `requests` ou `anthropic`. Elle couvre `export.py`, `usage.py`,
  `preflight.py`, `run_export.py`, `run_usage.py`, `run_preflight.py`, **et
  depuis l'itération 1** `orchestrator.py` et `run_pipeline.py`.
- **Second filet, générique** : `tests/test_api_io.py` parcourt **tout
  `diagnostic/**` en `rglob`** et applique la même règle à chaque fichier sauf
  `api_io.py`. C'est ce filet qui rattrape les modules absents de la liste
  nominative.

**Comment c'est testé.**
```bash
python -m pytest tests/test_api_io.py -q      # test_requests_pas_importe_niveau_module_hors_api_io
                                              # test_anthropic_pas_importe_niveau_module_hors_api_io
python -m pytest tests/test_preflight.py -q   # contrôles du garde-fou AST
python -c "from diagnostic.preflight import _check_garde_fous_bus; \
[print(c.ok, c.message) for c in _check_garde_fous_bus()]"
```

> **Dette constatée (2026-08-01, non bloquante).**
> `diagnostic/greenit.py` — module introduit à l'itération 2 et susceptible
> d'importer `anthropic` — **n'est pas** dans la liste nominative de
> `_check_garde_fous_bus`, alors que la règle ci-dessus impose de l'y ajouter.
> **L'invariant tient malgré tout** : il est couvert *de fait* par le test
> générique en `rglob` sur `diagnostic/**`. Mais il tient par le filet de
> sécurité, pas par le mécanisme annoncé — et le préflight, lui, ne le signale
> pas. → Ajouter le module à la liste (correctif côté code, hors périmètre de
> la passe documentaire).
> Contrôle : `sed -n '/modules_j5 = \[/,/\]/p' diagnostic/preflight.py | grep -c greenit` → `0`.

---

## I5 — Grand livre des coûts, registres recalculés

**Invariant.** Chaque appel réseau produit **une ligne JSONL** dans
`api_usage.log` (`LedgerEntry`). Les registres de consommation sont
**recalculés depuis le fichier** au démarrage — jamais maintenus en double état.

**Pourquoi.** Un compteur en mémoire qui diverge du fichier rend les budgets
inopérants après un crash ou un run concurrent. La source de vérité doit être
le fichier.

**Comment c'est tenu.** `ApiIO._charger_registres()` relit le ledger à
l'instanciation. Les entrées en cache hit et les interruptions
`budget_depasse` sont exclues des totaux (elles n'ont rien consommé).
Le fichier est ouvert en mode `a` : append-only, gitignoré.

**Extension GreenIT (itération 2).** Sept champs optionnels ont été ajoutés à
`LedgerEntry` : `octets_entrants`, `octets_sortants`, `duree_ms`, `energie_wh`,
`co2e_g`, `modele`, `profil`. Tous ont une valeur par défaut, donc **les lignes
antérieures se relisent sans migration** — `extra="forbid"` interdit les champs
*inconnus*, pas les champs *manquants*.

**Comment c'est testé.**
```bash
python -m pytest tests/test_api_io.py tests/test_api_schema.py tests/test_usage.py -q
python -m pytest tests/test_greenit.py -q -k "RetroCompatLedger or LedgerGreenIT"
python -m pytest tests/integration/test_e2e_bus.py -q -k "grand_livre"
```
`test_e2e_bus.py::test_grand_livre_est_du_jsonl_append_only` vérifie la
propriété sur un **vrai flux d'appels** contre un serveur HTTP local.

**Deux implémentations, une convergence garantie.** Le coût est calculé à deux
endroits depuis le **même** grand livre : `diagnostic/usage.py::agreger` (typée,
via `LedgerEntry`) et `webapp/backend/greenit.py::agreger` (JSONL brut, parsing
défensif — justifié pour une vue de consultation, cf. ADR 0002). Deux sources de
vérité pour un chiffre financier seraient une dette dangereuse ; elle est
**tenue par un test de non-régression croisé** (`611eb74`) :

```bash
python -m pytest webapp/backend/tests/test_greenit_usage_convergence.py -q   # 7 tests
```
Il compare les deux agrégations sur un ledger panaché — coût total, comptages,
par fournisseur, filtre `depuis`, ledger vide, endpoints HTTP — et **échoue si
elles divergent**. Reste une duplication de *code* (refactor souhaitable à
terme), mais plus de risque de divergence *silencieuse*.

---

## I6 — Budget bloquant *avant* l'appel

**Invariant.** `ApiIO` lève `BudgetExceeded` **avant** d'exécuter la fonction
réseau, jamais après. L'orchestrateur transforme cette exception en arrêt propre.

**Pourquoi.** Un budget contrôlé après coup n'est pas un budget, c'est un
constat de dépassement.

**Comment c'est tenu.** `call()` fait un pré-contrôle sur des unités estimées
(`_unites_precheck`) et journalise l'interruption avant de propager
l'exception ; `fn()` n'est jamais appelée. Côté orchestrateur,
`_executer_noeud()` capture `BudgetExceeded` → statut `budget_depasse` → la
chaîne s'arrête, ce qui a déjà été écrit reste valide, la reprise est idempotente.

**Limite connue et documentée.** Pour les API facturées au token, le pré-contrôle
est un **minorant** (une unité par unité tarifée) : il protège du dépassement
grossier, pas du token près.

**Comment c'est testé.**
```bash
python -m pytest tests/test_api_io.py -q
python -m pytest tests/test_orchestrator.py -q      # test_budget_exceeded_arret_propre
python -m pytest tests/integration/test_e2e_bus.py -q -k "budget"
```
Depuis l'itération 2, l'invariant est prouvé **par le réseau réel** (faux serveur
HTTP local, aucune clé) et non plus seulement par mock :
`test_budget_interrompt_avant_lappel_reseau` constate qu'**aucune requête
n'atteint le serveur** une fois le plafond atteint ;
`test_budget_apollo_epuise_ne_corrompt_pas_le_vault` et
`test_reprise_apres_budget_est_idempotente` couvrent l'arrêt propre et la reprise.

---

## I7 — Machine à états intangible

**Invariant.**
`decouvert → diagnostique → valide → contacte`, et `* → rejete` (état final).
**Un agent ne peut déclencher que `decouvert → diagnostique`.** Toutes les
autres transitions sont réservées à l'humain, dans Obsidian.

**Pourquoi.** C'est la porte humaine du système. Elle garantit qu'aucune fiche
n'est exportée — et *a fortiori* contactée — sans qu'une personne l'ait
regardée. C'est aussi la pièce maîtresse de la conformité : le jour où J6
existera, un envoi automatique sans validation serait un risque juridique direct.

**Comment c'est tenu.** `diagnostic/vault_schema.py` déclare deux registres :
`TRANSITIONS_LEGALES` (agent + humain) et `TRANSITIONS_AGENT` (uniquement
`decouvert → {diagnostique}`). `VaultIO.transition()` refuse par `ValueError`
toute transition hors registre, puis toute transition légale mais non autorisée
pour `acteur="agent"`.

**Comment c'est testé.**
```bash
python -m pytest tests/test_vault_schema.py -q      # test_transitions_agent_sous_ensemble_legales
python -m pytest tests/test_vault_io.py -q          # test_transition_agent_reservee_a_humain
python -m pytest tests/test_orchestrator.py -q      # test_transition_agent_vers_valide_interdite
                                                    # test_chaine_complete_ne_valide_aucune_fiche
python -m pytest tests/integration/test_e2e_bus.py -q -k "GardeFousVault"
```
`test_chaine_complete_ne_valide_aucune_fiche` est le plus important du lot : il
vérifie qu'une **exécution complète** de la chaîne ne fait passer aucune fiche
en `valide`. Depuis l'itération 2, `tests/integration/test_e2e_bus.py` le double
sur un flux réel : `test_agent_ne_peut_pas_valider_une_fiche` et
`test_transitions_illegales_refusees` (paramétré sur les couples départ/cible
interdits) rendent la machine à états **inviolable de bout en bout**, et
`test_journal_vault_append_only` confirme que la trace suit.

---

## I8 — Le graphe est une donnée

**Invariant.** L'ordre des étapes vit dans `dag_pipeline.yaml`. Ajouter,
désactiver ou réordonner une étape = éditer ce YAML, **jamais** le code de
`diagnostic/orchestrator.py`.

**Pourquoi.** Même raison que pour les rubriques et les ICP : le comportement
métier doit être modifiable sans toucher au code, donc sans re-tester le code.

**Comment c'est tenu.** `charger_dag()` lit et **valide** le YAML : nœud
dupliqué, dépendance inconnue, champ mal typé → `DagInvalide`.
`tri_topologique()` détecte les cycles → `CycleDetecte`. Les runners sont un
registre `{nom: callable}` — un nœud sans runner échoue explicitement.

**Comment c'est testé.**
```bash
python -m pytest tests/test_orchestrator.py -q      # test_dag_reel_charge, test_noeud_duplique,
                                                    # test_dependance_inconnue, test_cycle_detecte, …
python -c "from diagnostic.orchestrator import charger_dag, tri_topologique; \
print([n.nom for n in tri_topologique(charger_dag())])"
```

---

## I9 — Ordonnancement déterministe

**Invariant.** Deux exécutions du même DAG produisent **exactement** la même
séquence de nœuds.

**Pourquoi.** Le déterminisme est la propriété qui rend le système auditable et
reproductible — c'est le cœur de la décision d'architecture (ADR 0001), et ce
qui le distingue d'un superviseur LLM.

**Comment c'est tenu.** `tri_topologique()` implémente l'algorithme de Kahn avec
un **départage alphabétique** : quand plusieurs nœuds sont simultanément prêts,
c'est toujours le plus petit nom qui part. L'ordre ne dépend donc ni de l'ordre
d'écriture dans le YAML, ni du hasard d'un dictionnaire.

**Comment c'est testé.**
```bash
python -m pytest tests/test_orchestrator.py -q      # test_determinisme_independant_de_l_ordre_source
                                                    # test_departage_alphabetique_apres_liberation
```

---

## I10 — Verrou de run exclusif

**Invariant.** Deux runs ne peuvent pas s'exécuter simultanément sur le même
vault. Le verrou est libéré **en toute circonstance**, y compris sur exception.

**Pourquoi.** Le cron J7 et un lancement manuel se marcheraient dessus : double
écriture de fiches, double consommation de budget, journal incohérent.

**Comment c'est tenu.** `RunLock` crée le fichier verrou par
`os.open(path, O_CREAT|O_EXCL|O_WRONLY)` — atomique au niveau système de
fichiers. Il y inscrit `run_id`, `pid` et horodatage pour le diagnostic. Une
seconde acquisition lève `VerrouExiste`. La libération passe par `__exit__`
du context manager, donc par un `try/finally` implicite. Le verrou vit **hors du
vault** et est gitignoré.

**Comment c'est testé.**
```bash
python -m pytest tests/test_orchestrator.py -q      # test_second_acquisition_refusee
                                                    # test_context_manager_libere_sur_exception
                                                    # test_orchestrateur_refuse_demarrage_concurrent
                                                    # test_verrou_libere_apres_run_normal
```

---

## I11 — Une seule instance `ApiIO` par run, injectée

**Invariant.** L'orchestrateur crée **une** instance `ApiIO` et l'**injecte**
dans tous les nœuds qui touchent au réseau. Aucun nœud n'en fabrique une.

**Pourquoi.** C'est le geste architectural qui corrige le défaut historique où
chaque `run_*.py` créait son propre `ApiIO` : budgets non partagés, garde-fous
inopérants à l'échelle de la chaîne. Un seul grand livre, un seul budget.

**Comment c'est tenu.** `Orchestrateur.__init__` construit l'instance (budgets
chargés depuis `api_pricing.yaml`) ; `ContexteRun.api_io` la porte ; les
adaptateurs la passent explicitement (`run_discovery.run(..., api_io=ctx.api_io)`,
`run_diagnostic._build_pipeline(api_io=ctx.api_io)`).

**Comment c'est testé.**
```bash
python -m pytest tests/test_orchestrator.py -q      # test_meme_instance_injectee_discovery_et_diagnostic
                                                    # test_construction_apiio_avec_budgets_depuis_pricing
```
Le test vérifie l'**identité** de l'objet (`is`), pas seulement sa présence —
c'est la seule vérification qui a du sens ici.

---

## I12 — Zéro logique métier dans l'orchestrateur

**Invariant.** `diagnostic/orchestrator.py` branche, ordonne, journalise,
s'arrête. Chaque nœud est un **adaptateur mince** autour d'un entrypoint
existant.

**Pourquoi.** Si la logique métier migre vers l'ordonnanceur, les `run_*.py`
divergent, la rétro-compatibilité casse, et la couche « mince » devient un
second système à maintenir.

**Comment c'est tenu.** Chaque `_run_*` délègue : `diagnostic.preflight` pour la
porte, `run_discovery.run` pour la découverte, `run_diagnostic._build_pipeline`
+ `vault_runner.run_vault_mode` pour le diagnostic, `diagnostic.export` et
`diagnostic.usage` pour la sortie. Les imports sont faits **dans** les fonctions,
ce qui limite aussi le coût de démarrage.

**Comment c'est testé.** Rétro-compatibilité : les `run_*.py` historiques
fonctionnent toujours seuls (assertion C12 du protocole de revue), et la suite
J1-J5 antérieure reste verte.
```bash
python -m pytest tests/ -q
python run_pipeline.py --help
```

---

## I13 — Reprise idempotente

**Invariant.** Relancer la chaîne après une interruption ne refait pas le
travail déjà accompli et ne consomme pas deux fois le budget.

**Pourquoi.** Un budget dépassé ou une coupure doivent pouvoir être suivis d'une
relance sans surcoût ni doublon.

**Comment c'est tenu.** `_est_satisfait()` saute le nœud `diagnostic` s'il ne
reste aucune fiche `decouvert`. La découverte est idempotente par déduplication
(domaine normalisé intra-lot, `vault_io.exists()` inter-runs). L'export est en
lecture seule, donc rejouable sans effet de bord sur le vault.

**Comment c'est testé.**
```bash
python -m pytest tests/test_orchestrator.py -q      # test_diagnostic_saute_si_aucune_fiche_decouvert
                                                    # test_diagnostic_non_satisfait_avec_fiche_decouvert
python -m pytest tests/test_discovery_vault.py -q   # déduplication inter-runs
```

---

## I14 — Le cockpit est en lecture seule

**Invariant.** `webapp/` n'écrit rien dans le vault, ne déclenche aucune
transition, n'appelle jamais `api_io`, n'émet aucune requête réseau sortante.

**Pourquoi.** La décision appartient à l'humain dans Obsidian. Un bouton
« Valider » dans une interface web contournerait la porte humaine — c'est-à-dire
l'invariant I7, et avec lui la garantie de conformité.

**Comment c'est tenu.** Backend FastAPI exposant uniquement des routes `GET`,
CORS restreint (`allow_methods=["GET"]`), accès au vault via `VaultIO` en
lecture, aucune dépendance `requests`/`anthropic`. Frontend sans mutation.

**Comment c'est testé.**
```bash
python -m pytest webapp/backend/tests -q
grep -rn 'write_fiche\|write_rapport\|write_system_note\|\.transition(\|api_io' webapp/
```
Le second contrôle doit ne rien renvoyer d'exécutable (assertion B3 du protocole
de revue).

---

## I15 — Cache et exports hors du vault (contrainte G9)

**Invariant.** Le cache de scraping / d'appels API et les fichiers d'export
vivent **hors** de `vault/`, et hors du versionnement.

**Pourquoi.** Le vault est synchronisé, versionné et ouvert dans Obsidian.
Y déverser des artefacts binaires ou volumineux le rend inutilisable et pollue
l'historique.

**Comment c'est tenu.** Triple garde :
- `VaultIO.__init__` lève `RuntimeError` si le `cache_path` fourni est sous le
  vault ;
- `ApiIO.__init__` fait la même vérification ;
- côté export, `verifier_chemin_hors_vault()` refuse une destination sous le
  vault ; le préflight embarque un contrôle `cache_hors_vault`.

`.gitignore` exclut `.cache/`, `exports/`, `api_usage.log`, `runs.log`,
`.run.lock`.

**Comment c'est testé.**
```bash
python -m pytest tests/test_vault_io.py tests/test_api_io.py tests/test_export.py tests/test_preflight.py -q
python -m pytest tests/integration/test_e2e_bus.py -q -k "cache_refuse"
python -m pytest tests/integration/test_e2e_export.py -q -k "refuse_decrire"
```
Doublé à l'itération 2 par `test_cache_refuse_de_sinstaller_dans_le_vault` et
`test_refuse_decrire_dans_le_vault` sur un flux réel.

---

## I16 — La connaissance métier est une donnée

**Invariant.** Rubriques (`knowledge/rubric_*.yaml`), ICP (`icp/*.yaml`), tarifs
et budgets (`knowledge/api_pricing.yaml`), colonnes d'export
(`knowledge/export_kemana.yaml`), stratégie d'efficience
(`knowledge/greenit.yaml`), graphe du pipeline (`dag_pipeline.yaml`).
**Nouveau persona, marché, fournisseur ou étape = nouveau YAML, zéro code.**

**Pourquoi.** L'opératrice doit pouvoir faire évoluer le métier sans faire
appel à un développeur, et sans re-tester le moteur.

**Comment c'est tenu.** `scoring.py` est un moteur générique piloté par la
rubrique ; `IcpConfig` (Pydantic) valide les ICP ; `charger_schema_kemana()` lit
les colonnes ; `compute_cout()` lit la grille tarifaire. Aucun seuil métier n'est
codé en dur.

**Comment c'est testé.**
```bash
python -m pytest tests/test_icp_schema.py tests/test_export.py tests/test_api_schema.py -q
```

---

## I17 — Le LLM rédige, il ne collecte jamais

**Invariant.** La collecte de faits est **déterministe**. Le LLM
(`diagnostic/synthesis.py`) met en forme des faits **déjà établis**. Sans
`ANTHROPIC_API_KEY`, un **repli déterministe** produit la synthèse : le système
tourne entièrement hors ligne.

**Pourquoi.** C'est la barrière anti-hallucination du produit : le modèle ne
peut pas inventer un fait qu'il n'a pas le droit d'aller chercher. Et c'est
aussi ce qui maintient l'OPEX au plancher.

**Comment c'est tenu.** Les collecteurs (`diagnostic/collectors/`) héritent de
`Collector` et échouent isolément via `safe_collect`. Les collecteurs dérivés
(`seo`, `social`) n'ont **aucun accès réseau propre** : ils lisent
`_website_signals`, injecté par le pipeline après la collecte du site.
Un contrôle QA vérifie qu'aucune affirmation n'est produite sans faille réelle
correspondante.

**Comment c'est testé.**
```bash
python -m pytest tests/test_j1_smoke.py tests/test_collectors_phase_d.py -q
```
Toute la suite tourne **sans aucune clé API** : c'est la preuve permanente que
le repli fonctionne.

---

## I18 — J6 / outreach non activable

**Invariant.** Aucun email ne peut partir. `outreach` est déclaré
`enabled: false` dans `dag_pipeline.yaml`, et son runner **refuse de s'exécuter**
même si quelqu'un force l'activation.

**Pourquoi.** L'envoi d'emails à froid est encadré par CASL (Québec),
la nLPD + art. 3 LCD (Suisse), le RGPD (France), et par les obligations de
transparence de l'AI Act. Une **validation juridique par un juriste** est une
pré-condition dure, pas une formalité.

**Comment c'est tenu.** Double verrou : le YAML (`enabled: false` → statut
`desactive`) **et** le code (`_run_outreach()` renvoie systématiquement `bloque`
avec un message explicite).

**Comment c'est testé.**
```bash
python -m pytest tests/test_orchestrator.py -q      # test_dag_reel_outreach_desactive
                                                    # test_outreach_runner_refuse_si_force
```

---

## I19 — Aucun chiffre non mesuré présenté comme mesuré

**Invariant.** Les coûts monétaires et les estimations d'énergie / CO₂e sont
étiquetés comme **estimations paramétrables** tant qu'ils dérivent de facteurs
YAML non étalonnés.

**Pourquoi.** `knowledge/api_pricing.yaml` est intégralement à `0.0` avec
`releve_le: null` : **tout total de coût vaut actuellement 0,00 et n'est pas
engageant**. Côté empreinte, aucun fournisseur ne publie de consommation réelle
par requête : les facteurs servent à **comparer des scénarios**, jamais à
produire un bilan carbone opposable.

**Comment c'est tenu.** Les grilles portent une date de relevé (`releve_le`) qui
vaut `null` tant qu'aucun relevé n'a eu lieu ; le préflight bloque sur ce champ
et sur les prix à zéro. Un chiffrage opposable exigerait une ACV par un tiers.

**Comment c'est testé.**
```bash
python -m pytest tests/test_j5_phase0.py tests/test_preflight.py -q
python run_preflight.py; echo "code de sortie : $?"   # 1 = NO-GO attendu aujourd'hui
```

---

## I20 — Le routage de modèle est déterministe et piloté par la donnée

**Invariant.** Le choix du modèle LLM résulte de règles **explicites** évaluées
sur un contexte. Mêmes entrées → même profil. **Aucun LLM ne décide du routage**,
et aucun nom de modèle n'est codé en dur.

**Pourquoi.** Le superviseur-planificateur LLM a été explicitement refusé par
l'ADR 0001 (coût, non-déterminisme, charge cognitive). Faire décider un modèle
par un modèle le réintroduirait par la porte de service. Par ailleurs, un
routage déterministe est reproductible, donc auditable, donc testable.

**Comment c'est tenu.** `diagnostic/greenit.py::choisir_modele(contexte, config)`
évalue les règles de `knowledge/greenit.yaml` (opérateurs de comparaison simples,
combinaison `ou`/`et`). Profil par défaut `standard`, escalade `qualite`.
`synthesis.py` consomme le résultat ; le modèle n'apparaît nulle part en dur.

**Comment c'est testé.**
```bash
python -m pytest tests/test_greenit.py -q -k "ChoisirModele or MaxTokens"
grep -n "greenit\|choisir_modele" diagnostic/synthesis.py
```

---

## I21 — Frugalité : les bornes s'appliquent avant l'émission

**Invariant.** Le contexte et le prompt assemblé sont tronqués, et `max_tokens`
est plafonné, **avant** tout appel réseau.

**Pourquoi.** Le prompt croît avec le nombre de failles : sans borne, une fiche
pathologique multiplie le coût. Un plafond appliqué après coup ne plafonne rien.
Effet de bord vertueux : borner l'entrée réduit la surface d'injection de prompt
via du contenu scrapé.

**Comment c'est tenu.** `tronquer_contexte()` est appelé deux fois dans
`synthesis.py` — sur les faits, puis sur le prompt complet (garde-fou de dernier
recours). `max_tokens_du_profil()` applique `frugalite.max_tokens_sortie` s'il
est plus restrictif que le profil.

**Comment c'est testé.**
```bash
python -m pytest tests/test_greenit.py -q -k "TronquerContexte or MaxTokens"
```

---

## Contrôle global — le préflight

`diagnostic/preflight.py` regroupe neuf familles de contrôles GO/NO-GO :
clés API · tarifs réels · budgets · vault initialisé · cache hors vault · ICP
valide · schéma d'export · tests verts · garde-fous de bus (AST).

```bash
python run_preflight.py                      # tous les contrôles
python run_preflight.py --icp persona1-quebec
python run_preflight.py --strict             # « tests verts » devient bloquant
```

Code de sortie : `0` = GO, `1` = NO-GO. C'est la **pré-condition du cron J7** et
le premier nœud du DAG.

> **Verdict actuel : NO-GO structurel.** Aucune clé API dans l'environnement,
> tarifs et budgets à `0`, `releve_le: null`, vault non initialisé.
> Ce n'est pas un défaut : c'est le garde-fou qui remplit son office. Le lever
> relève de la **Phase D** (paramétrage par l'opératrice), pas du développement.

---

## Ajouter un invariant

1. Le formuler de façon **falsifiable** (une commande peut dire vrai ou faux).
2. Écrire le **test** qui le prouve, avant ou avec le code qui le tient.
3. L'ajouter à ce document avec les quatre colonnes.
4. L'ajouter à la table d'assertions du chantier dans
   `docs/strategie/GOUVERNANCE-revue-iterative.md` (via le chef de projet).
5. Le refléter dans le prompt système des agents concernés
   (`.claude/agents/`) — un invariant que les agents ignorent sera cassé.
