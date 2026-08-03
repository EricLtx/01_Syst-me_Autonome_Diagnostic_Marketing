# ADR 0003 — `icp_id`/`secteur_id` comme clé de configuration multi-industrie

- **Statut** : **acceptée — implémentée** par le commit `356c361`
  (Lot 1). L'en-tête indiquait « proposée — aucune ligne de code livrée » ;
  c'était vrai à la rédaction, faux depuis l'implémentation. Corrigé après
  vérification : `secteur_id_for_fiche` existe (`vault_runner.py:35`),
  `persona: int | None`, `marche: str` validé par slug.
- **Date** : 2026-08-02
- **Remplace** : —
- **Remplacée par** : —
- **Se situe dans** : socle J1/J2/J4 (pas un palier de l'ADR 0001 — celle-ci ne
  touche pas l'orchestrateur ni le routage de modèle). Prépare la trajectoire
  SaaS « n'importe quelle industrie, n'importe quel marché » demandée par le
  commanditaire, en restant strictement dans le Palier 1 (données, zéro
  nouvelle dépendance, zéro superviseur LLM).

## Contexte

Cinq défauts, tous vérifiés par exécution, empêchent aujourd'hui de qualifier
une industrie autre que l'installation HVAC :

- **B1** — `FicheProspect.persona: Literal[1, 2]` (`diagnostic/vault_schema.py:86`)
  plafonne le système à deux personas *à jamais*. `persona=3` lève
  `ValidationError`.
- **B2** — `Marche` est un enum fermé à cinq valeurs
  (`diagnostic/vault_schema.py:37-42`). `marche="ontario"` lève `ValidationError`.
- **B3** — `knowledge/rubric_persona2.yaml` n'existe pas : `load_rubrique(2)`
  lève `FileNotFoundError`.
- **B4 (le plus grave)** — `diagnostic/vault_runner.py:36` et
  `run_diagnostic.py:55` appellent `load_rubrique()` **sans argument**, une
  seule fois, pour construire **un seul** `DiagnosticPipeline` appliqué à
  **toutes** les fiches du vault quel que soit leur persona. Écrire
  `rubric_persona2.yaml` n'aurait aucun effet : rien ne le chargerait par
  fiche.
- **B5** — `diagnostic/collectors/website.py:39-42` code en dur le vocabulaire
  HVAC (`OFFRE_KEYWORDS`) dans un collecteur générique. Pour toute industrie
  hors HVAC, `mentions_offre` vaut `False` de façon systématique : une
  **absence de vocabulaire configuré est lue comme un fait négatif observé**,
  alors que c'est une absence d'observation.

B5 est la troisième occurrence du même défaut de fond en une itération : de la
connaissance métier a fui dans le code et produit un faux négatif présenté
comme un fait. Les deux occurrences précédentes (moteur de scoring à trois
états ; distinction observation/échec technique dans `_places.py`) ont déjà
posé la règle : **tout signal doit pouvoir valoir `None` (inconnu)**. Cette
ADR applique la même règle à un cas qu'elles ne couvraient pas encore : le
**vocabulaire lexical**, qui n'est pas un signal réseau mais une donnée de
jugement métier au même titre que la rubrique.

## Décision

**`icp_id` devient la clé primaire de configuration métier.** Un `icp_id` se
décompose en `{secteur_id}-{marche}` — généralisation, pas remplacement, de la
convention actuelle `persona{N}-{marche}`. Trois changements portent cette
décision :

1. **`secteur_id: str`** (nouveau champ `IcpConfig`, optionnel avec défaut)
   remplace le `persona: int` numéroté comme clé de sélection de rubrique, de
   vocabulaire et de fiche de connaissance. Défaut si absent :
   `secteur_id = f"persona{persona}"` — ce qui fait que
   `icp/persona1-quebec.yaml` **n'a besoin d'aucune modification** : son
   `secteur_id` implicite est `"persona1"`, qui pointe exactement vers le
   fichier `rubric_persona1.yaml` déjà en place. `persona` devient un champ
   legacy, optionnel, sans rôle de configuration.
2. **`load_rubrique` / `load_knowledge` / nouveau `load_vocabulaire`** sont
   reparamétrés par `secteur_id` (type élargi `str | int`, nom de paramètre
   `persona` conservé pour compatibilité littérale des appels existants).
   `load_vocabulaire` suit le même contrat que `load_knowledge` : fichier
   absent → `{}`, jamais une exception.
3. **Résolution par fiche, pas par run.** `secteur_id_for_fiche(fiche)` résout
   la configuration à appliquer à CETTE fiche (`icp_id` → `IcpConfig.secteur_id`,
   ou repli `persona{fiche.persona}`). `run_vault_mode` construit (et met en
   cache) un pipeline par `secteur_id` rencontré dans le lot, au lieu d'un
   pipeline unique construit avant la boucle. C'est le geste qui corrige B4.

En corollaire, deux champs de schéma se desserrent sans se supprimer :
`FicheProspect.persona` passe de `Literal[1, 2]` à `int | None` (borné `ge=1`
si fourni) — lève B1 ; `FicheProspect.marche` passe de l'enum fermé `Marche` à
`str` validé par un motif de slug — lève B2. B3 (écrire une rubrique
manquante) et l'auteurship du vocabulaire par industrie restent des tâches de
**donnée**, hors du périmètre code : le mécanisme les rend possibles sans
ligne de code supplémentaire, il ne les exécute pas à la place de la
consultante.

**Anti-fuite de vocabulaire (généralisation du principe à trois états) :**
`WebsiteCollector` reçoit `vocabulaire_offre: list[str] | None` en paramètre
(injecté par le pipeline, comme `api_io`). Vocabulaire absent → `mentions_offre
= None` (inconnu, aucun point, aucune faille) — jamais `False`. Le paramètre
par défaut du constructeur conserve la liste HVAC actuelle **uniquement**
comme valeur par défaut d'instanciation nue (compatibilité des appels de test
existants) ; tout appel piloté par le pipeline passe le vocabulaire
explicitement, y compris `None` pour un secteur non encore documenté.

## Conséquences

**Positives**

- Nouveau persona/marché/secteur = nouveaux fichiers YAML
  (`icp/{secteur}-{marche}.yaml`, `knowledge/rubric_{secteur}.yaml`,
  `knowledge/vocabulaire_{secteur}.yaml`), **zéro ligne de code**.
- Les cinq blocages sont levés par un seul mécanisme cohérent (résolution par
  fiche), pas cinq rustines indépendantes.
- Rétro-compatibilité totale : `persona1-quebec` continue de se résoudre à
  l'identique (même `secteur_id` implicite, même fichier rubrique, même
  répertoire vault). Un seul test existant encode directement le défaut levé
  (`test_persona_invalide_leve_erreur` sur `persona=3`) et doit être remplacé
  par une assertion sur le nouvel invariant (`persona` positif ou absent) —
  documenté explicitement, ce n'est pas une régression silencieuse.
- Un lot de fiches multi-industrie peut être traité en un seul
  `run_vault_mode()` : chaque fiche reçoit SA rubrique et SON vocabulaire.

**Négatives / risques résiduels**

- `persona` et `Marche` (l'enum) deviennent des vestiges partiellement
  redondants avec `secteur_id`/`icp_id` — dette assumée pour ne pas casser le
  regroupement Dataview existant (`vault_init.py` `GROUP BY persona + marche`)
  ni les répertoires `10-Prospects/personaN-marche/` déjà écrits. Un nettoyage
  ultérieur (Lot 2+) pourra migrer l'affichage vers `icp_id` seul.
- Le vocabulaire par défaut du constructeur `WebsiteCollector` (liste HVAC)
  reste un cas particulier justifié uniquement par la compatibilité des tests
  qui instancient le collecteur nu ; tout appelant piloté par la configuration
  doit explicitement passer `vocabulaire_offre=`, sans quoi il hériterait
  silencieusement du biais HVAC. Documenté et testé, mais reste un piège pour
  un futur appelant négligent — à surveiller en revue.
- Écrire une rubrique et un vocabulaire pour une industrie réelle (dentaire,
  immobilier…) reste un travail humain de jugement métier, non automatisable
  par cette ADR — c'est voulu (invariant I4), pas une limitation à corriger.

## Alternatives écartées

1. **Renommer `persona`/`marche` en un identifiant libre unique, migration de
   schéma complète.** Rejeté : casse le regroupement Dataview existant, les
   répertoires vault déjà écrits, et huit sites d'appel de test qui
   construisent des fiches avec `persona=1/2`. Coût de migration disproportionné
   par rapport au gain (le même résultat est atteint en gardant `persona` comme
   champ vestige).
2. **Système de plugins par industrie** (modules Python découverts par
   `entry_points`, un module par secteur). Rejeté : sur-ingénierie pour une
   consultante solo (bus factor 1) ; le mécanisme YAML + injection existant
   (déjà utilisé pour `api_io`, `_website_signals`) couvre le besoin sans
   nouvelle pièce mobile.
3. **Classification automatique du vocabulaire métier par LLM ou NLP.**
   Rejeté explicitement : réintroduirait un raisonnement non déterministe dans
   la couche de collecte (violerait l'invariant « le LLM rédige, il ne collecte
   jamais » et l'esprit du refus du superviseur-planificateur de l'ADR 0001).
   Le vocabulaire reste écrit par un humain, dans un YAML.
4. **Construire dès maintenant un collecteur de registre légal
   multi-marché** (SIRENE, registre du commerce, REQ…). Rejeté pour ce lot :
   c'est un nouveau point de contact réseau (touche `api_io.py`, budgets,
   cache) pour un rendement non prouvé sur le premier pilote. Conservé comme
   piste documentée (voir corps du rapport), pas construit.

## Comment cette ADR sera vérifiée

- Suite existante : `pytest tests/ -v` doit rester verte à l'exception du seul
  test explicitement réécrit et documenté ci-dessus.
- Nouvelle preuve positive : un test de bout en bout qui traite, dans **un
  seul** appel `run_vault_mode()`, un lot mixte contenant une fiche
  `persona1-quebec` (HVAC) et une fiche d'un secteur fictif non-HVAC, et vérifie
  que chacune reçoit sa propre rubrique, son propre vocabulaire, et un
  `mentions_offre` cohérent avec SON texte — pas celui de l'autre.
- Garde-fous bus (AST `os.replace`, `import requests`/`anthropic`) inchangés :
  aucun fichier touché par cette ADR n'ajoute d'import réseau de niveau module.
