# Tests d'intégration bout-en-bout

Ces tests exercent la **vraie** chaîne du système — le bus `api_io`, son cache
disque, ses budgets, son grand livre, le bus vault, la machine à états, le SDK
Anthropic — **sans aucune clé réelle et sans une seule dépense**.

Le principe est simple : on ne remplace pas le réseau par des mocks Python, on
remplace seulement la **destination**. Un serveur HTTP local
(`tests/integration/faux_api.py`) émule SerpAPI, Apollo, Google Places, l'API
Messages d'Anthropic et les sites web des prospects. Les variables
`*_BASE_URL` pointent dessus. Tout le reste du code s'exécute tel quel.

```bash
python -m pytest tests/integration -q        # 46 tests, ~10 s, zéro réseau externe
```

Dépendance optionnelle : le SDK `anthropic` (`pip install anthropic`). Sans
lui, le test qui exerce le POST `/v1/messages` est *skippé* et le système
retombe sur son repli déterministe — 45 tests passent, 1 skip.

---

## 1. Tableau des clés API

| Variable | Fournisseur | Endpoint appelé | Obligatoire ? | Sans la clé |
|---|---|---|---|---|
| `SERP_API_KEY` | SERP managé (SerpAPI ou équivalent) | `GET {SERP_BASE_URL}/search` | **Oui** pour la découverte J4 (préflight *bloquant*) | `run_discovery` ne trouve aucune candidate ; préflight NO-GO |
| `APOLLO_API_KEY` | Apollo.io | `POST {APOLLO_BASE_URL}/v1/people/search` | **Oui** pour l'enrichissement J4 (préflight *bloquant*) | Fiches écrites **sans contact** (le run continue) |
| `GOOGLE_PLACES_API_KEY` | Google Places | `GET {PLACES_BASE_URL}/maps/api/place/textsearch/json`<br>`GET {PLACES_BASE_URL}/maps/api/place/details/json` | Optionnelle (préflight *warn*) | Collecteurs `gbp` et `reviews` en mode stub (`None`) ; les dimensions *présence locale* et *avis* ne sont pas notées |
| `ANTHROPIC_API_KEY` | Anthropic | `POST {ANTHROPIC_BASE_URL}/v1/messages` | Optionnelle (préflight *warn*) | **Repli déterministe** : `synthesis.py` rédige le mini-audit hors-ligne. Le système tourne intégralement sans clé |

> Aucune clé n'est nécessaire pour faire tourner le projet : sans clé, le
> diagnostic fonctionne en palier 0 (site web seul) avec synthèse déterministe.
> Les clés achètent de la **profondeur de signal**, pas la capacité à tourner.

### Variables de redirection (nouveauté)

| Variable | Défaut (= production, comportement inchangé) |
|---|---|
| `SERP_BASE_URL` | `https://serpapi.com` |
| `APOLLO_BASE_URL` | `https://api.apollo.io` |
| `PLACES_BASE_URL` | `https://maps.googleapis.com` |
| `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` (honorée nativement par le SDK Anthropic) |

Elles ne sont **jamais** posées en exploitation. Le défaut étant l'URL de
production, ne rien faire = comportement d'origine, à l'octet près.

---

## 2. Basculer du faux serveur vers les vraies APIs

Les tests sont hermétiques par construction ; pour vérifier une intégration
réelle (à faire **une fois**, en connaissance de cause — cela coûte de l'argent) :

```bash
# 1. NE PAS poser les *_BASE_URL : les défauts pointent la production.
unset SERP_BASE_URL APOLLO_BASE_URL PLACES_BASE_URL ANTHROPIC_BASE_URL REQUESTS_CA_BUNDLE

# 2. Poser les vraies clés.
export SERP_API_KEY=...        APOLLO_API_KEY=...
export GOOGLE_PLACES_API_KEY=... ANTHROPIC_API_KEY=...

# 3. Renseigner les vrais tarifs ET des budgets bornés dans
#    knowledge/api_pricing.yaml  (releve_le + prix_par_unite + budgets),
#    faute de quoi le préflight refuse le départ.

# 4. Vérifier la porte avant toute dépense.
python run_preflight.py --icp persona1-quebec     # 0 = GO, 1 = NO-GO

# 5. Commencer par un dry-run (SERP métré, aucune écriture vault).
python run_discovery.py --icp persona1-quebec --dry-run
```

Garde-fous à ne pas contourner : les budgets `budgets.serp.unites_max.requetes`
et `budgets.apollo.unites_max.credits` d'`api_pricing.yaml` interrompent le run
**avant** l'appel réseau dès le plafond atteint.

---

## 3. Lancer le faux serveur seul

```bash
python scripts/faux_api_serveur.py --port 8899
```

Il affiche les `export ...` à copier, la liste des entreprises servies et les
sondes. Mode script :

```bash
python scripts/faux_api_serveur.py --shell > /tmp/faux.sh && source /tmp/faux.sh
```

Options : `--port`, `--port-https`, `--sans-tls`, `--shell`.

### Endpoints émulés

| Route | Émule | Notes |
|---|---|---|
| `GET /search` | SerpAPI | Résultats organiques crédibles d'installateurs HVAC québécois + 3 résultats à exclure (`pagesjaunes.ca`, `facebook.com`, `*.wixsite.com`) |
| `POST /v1/people/search` | Apollo | Personnes avec titres cibles, `email`, `email_status` ; renvoie volontairement des champs en trop (téléphone, ville, organisation) pour prouver la minimisation RGPD |
| `GET /maps/api/place/textsearch/json` | Google Places | `rating`, `user_ratings_total`, `business_status`, `photos` |
| `GET /maps/api/place/details/json` | Google Places | Avis, `owner_answer`, horodatages |
| `POST /v1/messages` | API Messages Anthropic | Format exact (`content:[{type:"text",…}]`, `usage:{input_tokens,output_tokens}`). Le faux modèle rédige **uniquement** à partir des failles du prompt : il passe le `quality_check` sans rien inventer |
| `GET /sites/<slug>` | Site web du prospect | 6 sites « pauvres » (ni viewport, ni meta-description, ni logo, ni contact, © 2017) et 2 « corrects » |
| `GET /sitemap.xml` | Sitemap | Servi seulement pour les sites « corrects » |
| `GET /__sante`, `GET /__journal` | Sondes | Vie du serveur ; journal des requêtes reçues (base des assertions) |

Détail d'implémentation utile : les liens SERP pointent sur des **IP de
bouclage distinctes** (`127.0.0.2` … `127.0.0.9`). `discovery._normaliser_url()`
force le schéma `https` et déduplique par domaine — une IP par entreprise donne
donc une clé de dédup réaliste **et** un site réellement joignable en HTTPS
(certificat auto-signé généré par `openssl`, `REQUESTS_CA_BUNDLE` posée par les
fixtures). Sans `openssl`, le serveur reste en HTTP seul et rien ne casse.

---

## 4. Dataset de démonstration

```bash
python scripts/seed_dataset.py --vault /tmp/vault_demo
python scripts/seed_dataset.py --vault /tmp/vault_demo --base-url http://127.0.0.1:8899
```

Idempotent : une fiche existante n'est jamais récrite (`--forcer` pour outrepasser).
Sans `--base-url`, les sites pointent sur des domaines `.test` (RFC 6761),
jamais résolvables — impossible de taper un vrai site par accident.

Fiches semées : 2 `decouvert`, 1 `diagnostique`, 2 `valide`, 1 `valide` +
`opt_out: true` (doit être exclue de tout export), 1 `rejete`.

`tests/integration/fixtures/api_pricing_test.yaml` est une grille tarifaire de
**test** (prix et budgets non nuls) — elle ne remplace jamais
`knowledge/api_pricing.yaml`, dont le relevé réel reste une tâche Phase D.

---

## 5. Ce que couvre chaque fichier de test

| Fichier | Couverture |
|---|---|
| `test_e2e_decouverte.py` | SERP HTTP → filtres ICP → dédup intra-lot et inter-runs → Apollo → fiches `decouvert` ; minimisation RGPD ; lignes `serp`/`apollo` au grand livre avec coût non nul ; dry-run et `--sans-contact` |
| `test_e2e_diagnostic.py` | Collecte réelle d'un site pauvre et de son contre-exemple ; cache Places partagé entre `gbp` et `reviews` ; pipeline vault complet → rapport + frontmatter + transition `decouvert → diagnostique` ; synthèse par le faux endpoint Anthropic (tokens métrés) ; repli déterministe sans clé |
| `test_e2e_export.py` | `run_export.main()` réel → CSV/JSONL Kemana ; **exclusion absolue des `opt_out`** ; colonnes, anomalies, lecture seule, refus d'écrire dans le vault |
| `test_e2e_bus.py` | Cache : 2 appels identiques = 1 requête réseau ; budget interrompu **avant** le réseau ; budget Apollo épuisé sans corruption du vault ; machine à états inviolable ; journaux append-only |
| `test_e2e_orchestrateur.py` | Préflight GO avec la grille de test / NO-GO sans clé ou avec la grille de production à zéro ; chaîne DAG complète → état cohérent ; ré-exécution idempotente ; dry-run ; verrou anti-concurrence |

## 6. Hermétisme — les règles respectées

- Port dynamique, boucle locale uniquement, **aucune** sortie réseau.
- Vault, `api_usage.log`, cache disque et exports : tous dans `tmp_path`.
- Clés factices : aucun test ne dépend d'une vraie clé.
- Les assertions sur le grand livre ne comparent **jamais** un dict entier :
  `LedgerEntry` peut gagner des champs optionnels sans casser un seul test.
- `preflight._check_tests_verts` est neutralisé dans le test d'orchestrateur —
  il relance `pytest tests/` en sous-processus et se relancerait à l'infini.
  Les 8 autres contrôles du préflight restent réels.
