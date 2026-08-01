# ADR 0002 — GreenIT : efficience des appels IA et observabilité de l'empreinte

- **Statut** : **acceptée — implémentée** (commit `6055e14` pour le socle,
  `d5b14d1` pour l'observabilité cockpit). Vérifiée par exécution le 2026-08-01.
- **Date** : 2026-08-01 · **Implémentation constatée** : 2026-08-01
- **Remplace** : —
- **Remplacée par** : —
- **Se situe dans** : Palier 2 de l'ADR 0001 (greffe « routeur de modèle piloté
  par YAML »), anticipé sur le socle du Palier 1. **Le superviseur-planificateur
  LLM de B reste refusé** — le routage retenu ici est purement déterministe.

> ⚠️ **Ce qui est implémenté est le mécanisme, pas une économie démontrée.**
> Aucun pourcentage de gain n'est mesurable aujourd'hui : `api_pricing.yaml` est
> intégralement à `0.0`, donc **tous les coûts valent 0,00**. Les facteurs
> d'empreinte n'ont jamais été étalonnés (`releve_le: null`). Toute affirmation
> du type « X % d'économie » serait une invention. Voir §« Ce qui n'est pas
> mesurable ».

---

## Contexte

Le système consomme trois ressources externes payantes et énergivores :

1. **SERP** (par requête) et **Apollo** (par crédit) — le poste **dominant** du
   coût variable ;
2. **Google Places** (par requête, deux endpoints par fiche) ;
3. **l'inférence LLM** (par token, en entrée et en sortie) — un appel court par
   fiche, avec repli déterministe.

Trois problèmes se posent simultanément :

- **Économique.** L'utilisatrice est une consultante solo. L'OPEX plancher est
  un critère cardinal de l'ADR 0001 (noté 5/5). Chaque appel évité compte.
- **Écologique.** Le projet veut pouvoir démontrer sa sobriété, pas seulement
  l'affirmer. Or **aucun fournisseur ne publie la consommation réelle par
  requête** : il n'existe aucune mesure certifiée à laquelle se raccrocher.
- **De pilotage.** Le choix du modèle était jusqu'ici implicite dans le code de
  `synthesis.py`. Un choix implicite ne se pilote pas, ne se compare pas, et ne
  se change pas sans toucher au code — ce qui contredit l'invariant I16
  (la connaissance est une donnée).

Contrainte forte héritée de l'ADR 0001 : **le superviseur-planificateur LLM a
été explicitement refusé**. Toute solution de routage qui ferait décider un
modèle par un modèle réintroduirait par la porte de service exactement ce qui a
été rejeté par la porte d'entrée.

---

## Décision

Trois leviers, dans leur ordre de rentabilité, **tous pilotés par une donnée
YAML** (`knowledge/greenit.yaml`) et **aucun par un LLM**.

### 1. Routage de modèle déterministe piloté par YAML

- Le fichier déclare des **profils** — un profil = (modèle, budget de sortie,
  description). Un profil **frugal** par défaut, un profil **d'escalade** pour
  les cas où le petit modèle a démontré son insuffisance.
- La sélection se fait par des **règles de comparaison explicites** évaluées sur
  un contexte fourni par l'appelant (nombre de failles à rédiger, score global,
  échec d'un contrôle qualité précédent, taille du prompt assemblé).
  Opérateurs simples (`>=`, `>`, `<=`, `<`, `==`, `!=`, `in`), combinaison
  déclarée (`ou` / `et`).
- **Mêmes entrées → même sortie.** C'est un `if/else` dont les seuils vivent
  dans un YAML. **Aucun LLM ne décide du routage** — conformité stricte au refus
  posé par l'ADR 0001.
- Chaque règle porte un **motif** rédigé : le fichier explique *pourquoi* on
  escalade, pas seulement *quand*.

### 2. Frugalité — bornes dures appliquées avant l'appel

- **Borner l'entrée** : troncature du contexte assemblé. Le prompt croît avec le
  nombre de failles ; sans borne, une fiche pathologique multiplie le coût.
  Un second plafond couvre le prompt complet — c'est un garde-fou de dernier
  recours, pas un réglage de régime normal.
- **Borner la sortie** : plafond de `max_tokens` qui **écrase** celui du profil
  s'il est plus permissif. La génération de sortie coûte nettement plus cher que
  le pré-remplissage de l'entrée : c'est le levier le plus efficace.
- **Cacher agressivement** : durée de vie du cache disque d'`api_io`.
  **Un cache hit coûte 0 en argent, ~0 en énergie et ~0 en CO₂e** — c'est
  l'économie la plus facile à démontrer, et donc la première à mesurer.
- **Prompt caching fournisseur : désactivé par défaut.** Il n'est rentable que
  si un préfixe stable de plus d'un millier de tokens est réutilisé, ce qui
  n'est pas le cas aujourd'hui (un prompt par prospect). À réévaluer si un
  prompt système long apparaît. Décision documentée plutôt qu'omise.

### 3. Observabilité — empreinte estimée, tracée au grand livre

- **Facteurs d'empreinte paramétrables** : Wh pour mille tokens d'entrée, de
  sortie et de lecture de cache ; Wh par requête HTTP et par mégaoctet
  transféré ; **intensité carbone du mix électrique en g CO₂e/kWh, par région**.
- La régionalisation est structurante et non cosmétique : entre un mix
  hydroélectrique et une moyenne mondiale, l'écart d'intensité carbone est de
  **deux ordres de grandeur**. Ignorer la région produirait un chiffre sans
  aucun sens.
- L'estimation est **tracée au grand livre `api_usage.log`** et agrégée par
  `run_usage.py`, à côté des coûts monétaires. La sobriété devient un indicateur
  suivi, pas une intention.
- Le fichier porte un champ `releve_le` : la date du dernier réétalonnage des
  facteurs. Il vaut `null` tant qu'aucun étalonnage n'a eu lieu.

---

## Règle de véracité (non négociable)

> **Les chiffres d'énergie et de CO₂e produits par ce dispositif sont des
> ESTIMATIONS PARAMÉTRABLES, jamais des mesures certifiées.**

Aucun fournisseur — ni Anthropic, ni Google, ni un fournisseur SERP — ne publie
la consommation réelle par requête. Les facteurs retenus sont des **ordres de
grandeur** dont l'utilité est de **comparer des scénarios entre eux** :
avec cache contre sans cache, profil frugal contre profil qualité, 300 contre
900 tokens de sortie. Ils donnent une **tendance**, jamais un bilan carbone
opposable.

En conséquence, et sans exception :

- **toute valeur affichée porte la mention « estimation »** — dans
  `run_usage.py`, dans le cockpit, dans toute documentation ;
- **les facteurs vivent en YAML** avec une date de relevé : un réétalonnage doit
  être une **édition de donnée**, zéro ligne de code touchée (les noms de clés ne
  changent pas) ;
- **un chiffrage opposable exigerait une ACV réalisée par un tiers**, dont les
  valeurs remplaceraient les facteurs actuels ;
- la même règle s'applique aux **coûts monétaires** : tant que
  `knowledge/api_pricing.yaml` est intégralement à `0.0` avec `releve_le: null`,
  **tout total vaut 0,00 et n'est pas une prévision de facture**.

Cette règle est formalisée comme invariant **I19** dans
`docs/architecture/invariants.md`.

---

## Conséquences

### Positives

- **Le coût devient pilotable par la donnée** : changer de modèle, de seuil
  d'escalade ou de plafond de sortie = éditer un YAML. Cohérent avec l'invariant
  I16 et avec le traitement déjà réservé aux rubriques, ICP, tarifs et au graphe
  du DAG.
- **Le déterminisme est préservé** : le routage est reproductible, donc
  auditable, donc testable. La propriété cardinale de l'ADR 0001 n'est pas
  entamée.
- **L'escalade devient explicite et motivée** : on ne subit pas le modèle cher,
  on le déclenche pour une raison écrite dans le fichier.
- **La sobriété devient démontrable** : le taux de cache hit et l'empreinte
  estimée sont des indicateurs suivis, pas des affirmations.
- **Effet de bord vertueux** : borner l'entrée réduit aussi la surface
  d'injection de prompt via du contenu scrapé.

### Négatives — assumées

- **Une pièce mobile de plus.** Un fichier de configuration supplémentaire à
  comprendre et à maintenir, pour une opératrice solo. Mitigation : le fichier
  est abondamment commenté et fonctionne avec ses valeurs par défaut.
- **Risque de fausse précision.** Un chiffre de CO₂e affiché à deux décimales
  **paraît** mesuré. C'est précisément le risque que la règle de véracité et
  l'étiquetage systématique doivent neutraliser. Le risque est réel et doit
  rester sous surveillance à chaque itération.
- **Facteurs à réétalonner.** Ils vieilliront ; sans discipline sur `releve_le`,
  ils deviendront silencieusement faux.
- **Le levier porte sur le poste minoritaire.** Le coût variable est dominé par
  SERP et Apollo, pas par le LLM. Le routage de modèle est utile mais **ne doit
  pas détourner l'attention** de la déduplication et du cache, qui pèsent
  davantage. À vérifier sur données réelles après la Phase D.

### Neutres

- Aucune de ces décisions ne lève le **NO-GO structurel** du préflight, ni ne
  rend un run réel possible : aucune clé API n'est disponible.
- Le schéma de `LedgerEntry` est un contrat lu par `diagnostic/usage.py` et par
  le cockpit. Y ajouter des champs d'empreinte impose de vérifier les deux, et
  de **rester tolérant à la lecture des anciennes lignes**.

---

## Alternatives écartées

| Alternative | Motif du rejet |
|---|---|
| **Routage confié à un LLM** (« demander au modèle quel modèle utiliser ») | Réintroduit le superviseur-planificateur LLM explicitement refusé par l'ADR 0001 : coût, non-déterminisme, charge cognitive. Et un appel pour décider d'un appel est absurde sur le plan de la frugalité. |
| **Seuils codés en dur dans `synthesis.py`** | Viole l'invariant I16. Rend tout ajustement dépendant d'un développeur et d'une re-passe de tests. |
| **Toujours le modèle le moins cher** | La qualité prime sur l'économie : le contrôle QA (« aucune affirmation non adossée aux failles réelles ») n'est pas négociable. Un modèle qui hallucine n'est pas une économie, c'est une dette de crédibilité. |
| **Toujours le modèle le plus fort** | Coût multiplié pour un bénéfice nul sur la majorité des fiches, où le LLM ne fait que mettre en forme des faits déjà établis. |
| **Ne pas estimer l'empreinte du tout** | Renonce à un indicateur utile au pilotage et à un différenciateur défendable, alors que le coût de l'estimation est faible. L'absence de mesure certifiée est un argument pour **étiqueter**, pas pour se taire. |
| **Publier un bilan carbone chiffré comme un engagement** | Malhonnête en l'absence d'ACV tierce. Risque réputationnel et juridique (allégation environnementale non étayée) sans commune mesure avec le bénéfice. |
| **Prompt caching fournisseur activé par défaut** | Non rentable dans le profil d'usage actuel (un prompt par prospect, aucun préfixe long réutilisé). Activable par la donnée le jour où un prompt système long apparaît. |

---

## Implémentation constatée (vérifiée par exécution le 2026-08-01)

Les dix points laissés ouverts à la rédaction initiale, relevés dans le code.

### 1. Emplacement et responsabilités — `[x]`

| Module | Rôle |
|---|---|
| `diagnostic/greenit.py` | socle : routage, bornes, estimation d'empreinte |
| `knowledge/greenit.yaml` | la donnée : profils, règles, bornes, facteurs |
| `diagnostic/synthesis.py` | consommateur du routage |
| `diagnostic/api_schema.py` | 7 champs GreenIT sur `LedgerEntry` |
| `webapp/backend/greenit.py` | lecture/agrégation du grand livre + tail SSE, **lecture seule** |
| `webapp/frontend/src/pages/GreenIT.tsx` | écran `/greenit` |

API publique du socle : `charger_config()`, `evaluer_escalade()`,
`choisir_modele()`, `max_tokens_du_profil()`, `tronquer_contexte()`,
`intensite_carbone()`, `estimer_empreinte()`.

> **Duplication assumée, convergence garantie.** `diagnostic/usage.py::agreger`
> et `webapp/backend/greenit.py::agreger` calculent tous deux le coût depuis le
> **même** grand livre. Depuis `611eb74`, un **test de non-régression croisé**
> (`webapp/backend/tests/test_greenit_usage_convergence.py`, 7 tests) échoue si
> les deux divergent. Voir §« Dette technique ».

### 2. Valeurs finales de `knowledge/greenit.yaml` — `[x]`

| Profil | Modèle | `max_tokens` |
|---|---|---|
| `frugal` | `claude-haiku-4-5-20251001` | 400 |
| `standard` (défaut) | `claude-haiku-4-5-20251001` | 600 |
| `qualite` (escalade) | `claude-sonnet-4-5` | 900 |

Routage : `profil_defaut: standard`, `profil_escalade: qualite`, `mode: ou`
(une seule règle vraie suffit).

| Règle | Champ | Opérateur | Valeur |
|---|---|---|---|
| `quality_check_echoue` | `quality_check_echoue` | `==` | `true` |
| `failles_nombreuses` | `nb_failles` | `>=` | `6` |
| `prospect_a_fort_score` | `score_global` | `>=` | `75` |

Frugalité : `troncature_contexte_caracteres: 4000`,
`troncature_prompt_caracteres: 8000`, `max_tokens_sortie: 600`,
`cache_ttl_jours: 30`, `activer_prompt_caching: false`.
`releve_le: null` — **les facteurs d'empreinte n'ont jamais été étalonnés.**

### 3. Intégration dans `synthesis.py` — `[x]`

`from diagnostic import greenit` ; `charger_config()` puis
`choisir_modele(contexte, config)` → `(modele, profil)` ;
`max_tokens_du_profil(profil, config)` ; double troncature —
`tronquer_contexte(faits, config)` puis
`tronquer_contexte(prompt, config, cle="troncature_prompt_caracteres")` avant
émission. Le modèle est passé à l'appel (`model=modele, max_tokens=max_tokens`).
**Le modèle n'est nulle part en dur.** Le repli déterministe sans
`ANTHROPIC_API_KEY` est préservé (couvert par
`tests/integration/test_e2e_diagnostic.py::test_sans_cle_anthropic_repli_deterministe_et_zero_appel`).

### 4. Champs ajoutés à `LedgerEntry` et rétro-compatibilité — `[x]`

Sept champs, tous optionnels avec valeur par défaut : `octets_entrants`,
`octets_sortants`, `duree_ms`, `energie_wh`, `co2e_g`, `modele`, `profil`.

Rétro-compatibilité **vérifiée par exécution** : une ligne antérieure à
l'extension se relit sans migration (`energie_wh` → `0.0`), une ligne enrichie
se relit intégralement. `extra="forbid"` interdit les champs **inconnus**, pas
les champs **manquants** — c'est ce qui rend la migration inutile.
Couvert par `tests/test_greenit.py::TestRetroCompatLedger`.

### 5-6. Restitution — `[x]` partiellement

Rapport `run_usage.py` et écran cockpit `/greenit` (+ flux SSE
`/api/greenit/stream`). L'étiquetage « estimation » est présent dans les
docstrings du socle et du module cockpit.
**Reste à vérifier finement** : que l'étiquette apparaît sur **chaque valeur
affichée** de l'interface, pas seulement en en-tête d'écran.

### 7. Tests — `[x]`

`tests/test_greenit.py` : **78 tests** (compté, pas recopié — le message du
commit annonçait 77, écart corrigé par la revue), répartis en
`TestChargerConfig`, `TestChoisirModele`, `TestMaxTokens`,
`TestEstimerEmpreinte`, `TestTronquerContexte`, `TestLedgerGreenIT`,
`TestEstimerOctets`, `TestRetroCompatLedger`, `TestSynthesisGreenIT`.

### 8. Garde-fou AST — `[!]` **dette**

`diagnostic/greenit.py` **n'est pas** dans la liste `modules_j5` de
`_check_garde_fous_bus`. L'invariant tient malgré tout : le test générique
`tests/test_api_io.py::test_requests_pas_importe_niveau_module_hors_api_io`
parcourt `diagnostic/**` en `rglob`. Mais il tient **par le filet générique, pas
par le mécanisme annoncé**. Voir §« Dette technique ».

### 9. Mesure avant / après — `[ ]` **impossible à ce stade**

Voir §« Ce qui n'est pas mesurable » ci-dessous.

### 10. Documentation — `[x]`

`docs/architecture/README.md` §7, `flux-donnees.md` §4 et §7,
`docs/CHANGELOG.md` itération 2, `CLAUDE.md` section GreenIT.

---

## Ce qui n'est PAS mesurable aujourd'hui

Le mécanisme est livré. **L'économie ne l'est pas** — et il serait malhonnête de
la chiffrer :

- **Aucun gain monétaire mesurable.** `knowledge/api_pricing.yaml` est
  intégralement à `0.0` avec `releve_le: null` : tous les coûts du grand livre
  valent 0,00. Un pourcentage d'économie calculé sur zéro n'a aucun sens.
- **Aucun gain énergétique mesuré.** Les facteurs d'empreinte n'ont jamais été
  étalonnés (`releve_le: null`) et restent des ordres de grandeur. Ils
  permettent de **comparer deux scénarios entre eux**, pas de produire une
  valeur absolue défendable.
- **Aucune donnée de production.** Aucune clé API n'est disponible, aucun run
  réel n'a eu lieu : il n'existe pas de jeu de mesures « avant » auquel comparer
  un « après ».

Ce qui est **réellement établi** : le routage est déterministe et testé, les
bornes sont appliquées avant émission, l'empreinte est calculée et tracée, et
le cache réduit démontrablement le nombre d'appels réseau
(`tests/integration/test_e2e_bus.py::test_deux_appels_identiques_une_seule_requete_reseau`
prouve qu'un second appel identique ne produit **aucune** requête réseau).

La mesure avant/après devient possible **après la Phase D**, sur données réelles.

---

## Dette technique inscrite

1. **Deux implémentations du calcul de coût** — `diagnostic/usage.py::agreger`
   (typée, via `LedgerEntry`) et `webapp/backend/greenit.py::agreger` (JSONL
   brut, défensive).
   **Statut : risque fermé** (`611eb74`). Un test de non-régression croisé,
   `webapp/backend/tests/test_greenit_usage_convergence.py` (7 tests), compare
   les deux agrégations sur un ledger panaché et **échoue si elles divergent**.
   Reste une duplication de *code* — refactor souhaitable à terme (une seule
   fonction de calcul, deux vues), **non urgent**.
   *Note de méthode* : ce test a été créé **après** que la passe documentaire a
   signalé que le docstring l'annonçait sans qu'il existe. Un filet de sécurité
   documenté mais absent est plus dangereux qu'un manque assumé — le signaler a
   suffi à le faire combler.
2. **`diagnostic/greenit.py` hors de la liste `_check_garde_fous_bus`**
   (cf. §8). **Statut : ouvert** — vérifié le 2026-08-01,
   `sed -n '/modules_j5 = \[/,/\]/p' diagnostic/preflight.py | grep -c greenit`
   → `0`. L'invariant tient via le test générique en `rglob`, mais le préflight
   ne le signale pas. → L'ajouter à `diagnostic/preflight.py`.

Le point 2 est **non bloquant** (l'invariant tient) mais doit être traité côté
code — hors périmètre de cette passe documentaire.

---

## Note sur la justification du parsing défensif (cockpit)

Le choix de lire le JSONL brut dans `webapp/backend/greenit.py` plutôt que via
`LedgerEntry` est **correct**, mais l'argument initialement avancé (« `extra="forbid"`
rejetterait les lignes enrichies ») était **faux** : `LedgerEntry` relit
parfaitement les lignes enrichies depuis `6055e14` — vérifié par exécution.

Le **bon** argument, celui que porte aujourd'hui le docstring du module :
`LedgerEntry` est un schéma d'**écriture**, strict par construction. Une vue de
**consultation** a le devoir inverse — ne jamais tomber sur ce qu'elle lit. Or
`LedgerEntry.model_validate` lève sur :

- un **champ futur** — vérifié : ajouter un champ inconnu déclenche une
  `ValidationError`. Enrichir le ledger demain ferait passer le cockpit en 500
  tant que `webapp/` n'a pas rattrapé le schéma, pour un champ qui ne le
  concerne même pas ;
- une **ligne dégradée** — `ts` malformé, `unites: null`, `resultat` hors
  énumération : cas normaux pour un journal append-only lu **à chaud** pendant
  qu'un autre processus écrit.

La tolérance au schéma futur et aux lignes corrompues est donc la vraie
justification. Elle est documentée comme telle dans le module.

---

## Vérification

```bash
# Tests GreenIT — 78 collectés
python -m pytest tests/test_greenit.py --collect-only -q | tail -2

# Déterminisme du routage : mêmes entrées → même profil
python -m pytest tests/test_greenit.py -q -k "ChoisirModele"

# Configuration : profils, règles, bornes
python -c "import yaml; d=yaml.safe_load(open('knowledge/greenit.yaml')); \
print({k: (v['modele'], v['max_tokens']) for k, v in d['profils'].items()}); \
print(d['routage']['profil_defaut'], d['routage']['mode']); \
print([r['nom'] for r in d['routage']['regles_escalade']])"

# Rétro-compatibilité du grand livre : ancienne ligne relue sans migration
python -m pytest tests/test_greenit.py -q -k "RetroCompatLedger"

# Le modèle n'est jamais en dur dans synthesis.py
grep -n "greenit\|choisir_modele\|max_tokens_du_profil" diagnostic/synthesis.py

# Le cache évite réellement un appel réseau (test e2e contre serveur local)
python -m pytest tests/integration/test_e2e_bus.py -q -k "cache"

# Suite complète — aucune régression
python -m pytest tests/ -q

# Aucun coût réel engagé : la grille tarifaire est toujours à zéro
python run_usage.py
```

**Convergence socle ⇄ cockpit (créée par `611eb74`) :**

```bash
python -m pytest webapp/backend/tests/test_greenit_usage_convergence.py -q   # 7 tests
```

**Contrôle de dette restante (rend `0`, c'est le défaut à corriger) :**

```bash
# diagnostic/greenit.py absent de la liste du garde-fou AST du préflight
sed -n '/modules_j5 = \[/,/\]/p' diagnostic/preflight.py | grep -c greenit   # → 0
```
