# ADR 0002 — GreenIT : efficience des appels IA et observabilité de l'empreinte

- **Statut** : **en cours d'implémentation** — chantier GreenIT actif au moment
  de la rédaction (2026-08-01). Les éléments chiffrés et le détail
  d'implémentation sont **à compléter en seconde passe**, une fois le code
  vérifiable dans le dépôt.
- **Date** : 2026-08-01
- **Remplace** : —
- **Remplacée par** : —
- **Se situe dans** : Palier 2 de l'ADR 0001 (greffe « routeur de modèle piloté
  par YAML »), anticipé sur le socle du Palier 1.

> ⚠️ **Cette ADR documente une décision, pas un état livré.** Au moment de sa
> rédaction, le chantier était en cours et son arborescence encore mouvante :
> `knowledge/greenit.yaml` existait dans l'arbre de travail (non commité), et
> des artefacts GreenIT apparaissaient également côté cockpit
> (`webapp/backend/`, `webapp/frontend/`). **L'emplacement définitif des modules
> et le détail de leur API restent à constater en seconde passe.** Les valeurs
> citées ci-dessous décrivent l'**intention de conception** ; elles doivent être
> revérifiées avant d'être considérées comme vraies.

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

## À compléter en seconde passe

Cette section est un **contrat avec la prochaine passe documentaire**. Chaque
point exige une vérification dans le code, pas une reprise de cette ADR.

- [ ] **Emplacement définitif**, API publique et responsabilités des modules
      d'efficience (socle `diagnostic/` et/ou cockpit `webapp/`) : fonctions
      exportées, signatures, et qui appelle quoi. Vérifier notamment qu'aucune
      duplication de logique de calcul n'existe entre socle et cockpit — le
      cockpit doit rester en **lecture seule** et ne rien recalculer que le
      grand livre ne contienne déjà.
- [ ] **Valeurs finales** de `knowledge/greenit.yaml` : profils (modèles exacts,
      `max_tokens`), règles d'escalade (champs, opérateurs, seuils), bornes de
      frugalité, facteurs d'empreinte, table d'intensité carbone par région.
- [ ] Point d'intégration exact dans `diagnostic/synthesis.py` : quel contexte
      est fourni au routeur, à quel moment, et comment le repli déterministe est
      préservé.
- [ ] Champs ajoutés à `LedgerEntry` / `api_schema.py`, et rétro-compatibilité
      de lecture des anciennes lignes du grand livre.
- [ ] Colonnes ajoutées au rapport de `run_usage.py`, et **vérification que
      l'étiquette « estimation » apparaît effectivement** partout.
- [ ] Restitution dans le cockpit (`webapp/`), même exigence d'étiquetage.
- [ ] **Liste des tests** couvrant : déterminisme du routage (mêmes entrées →
      même profil), application effective des bornes, calcul d'empreinte,
      sélection de l'intensité carbone par région, absence de régression sur la
      suite existante.
- [ ] Ajout des nouveaux modules à la liste surveillée par le garde-fou AST
      `_check_garde_fous_bus` si l'un d'eux est susceptible d'importer
      `anthropic`.
- [ ] **Mesure avant / après** sur un jeu de données de test : taux de cache
      hit, tokens de sortie moyens, part d'escalades. Une optimisation sans
      mesure est une opinion.
- [ ] Mise à jour de `docs/architecture/flux-donnees.md` §4 (synthèse) et §7
      (usage), et de `docs/architecture/invariants.md` si un invariant naît de
      ce chantier.

---

## Vérification

À l'établissement de cette ADR, les contrôles applicables sont :

```bash
# Le fichier de stratégie d'efficience se charge et est bien formé
python -c "import yaml; d=yaml.safe_load(open('knowledge/greenit.yaml')); \
print(sorted(d)); print(sorted(d.get('profils', {})))"

# La suite reste verte (aucune régression introduite par le chantier)
python -m pytest tests/ -q

# Le repli déterministe fonctionne toujours sans clé LLM
python -m pytest tests/test_j1_smoke.py -q

# Aucun coût réel n'est engagé : la grille tarifaire est toujours à zéro
python run_usage.py
```

Les contrôles spécifiques au routage et au calcul d'empreinte seront ajoutés en
seconde passe, avec les noms de tests réels.
