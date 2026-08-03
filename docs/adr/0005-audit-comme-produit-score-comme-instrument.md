# ADR 0005 — L'audit est le produit ; le score est un instrument interne

- **Statut** : acceptée
- **Date** : 2026-08-03
- **Remplace partiellement** : rien. **Complète** : ADR 0003 (multi-industrie),
  ADR 0004 (axe intention).
- **Portée du présent commit** : Lot A uniquement (l'artefact d'audit).
  Les lots B et suivants sont listés en fin de document et **ne sont pas
  implémentés**.

---

## Contexte

Le système a été construit pour répondre à une question **comparative** :
« parmi ces N entreprises, lesquelles ont le plus besoin d'un accompagnement
marketing ? » Cette question suppose un ordre total sur une cohorte.

Le banc d'essai du 2026-08-03 (ADR 0004, 9 entreprises HVAC) a montré que cet
ordre ne se forme pas : **7 prospects sur 9 sortent à exactement 36,9 avec une
accroche identique**. Une partie de cet effondrement est un artefact de la
fixture (le faux serveur n'expose que deux gabarits de site : 7 « pauvres »,
2 « corrects ») — vérifié dans `tests/integration/faux_api.py`. Le banc ne peut
donc pas trancher la question du pouvoir de classement.

Mais une seconde cause n'est pas un artefact, et elle est **structurelle**.

### La cause structurelle : un score renormalisé ne classe pas

Depuis la règle des trois états (invariant I22, paradigme §P4), un score global
est renormalisé sur les **seules dimensions observées**, et `scores["_couverture"]`
publie la part réellement évaluée.

Conséquence non anticipée à l'époque : **deux entreprises couvertes
différemment ne passent pas le même examen.** Un prospect noté sur 65 % de la
rubrique et un autre noté sur 90 % produisent deux nombres sur la même échelle
sans que ces nombres soient comparables. Les classer l'un par rapport à l'autre
revient à classer un élève interrogé sur six chapitres à côté d'un élève
interrogé sur neuf.

Dans le banc actuel l'effet est invisible : aucune clé API n'étant disponible,
Places est également non observé pour tout le monde et la couverture est
uniforme à 0,65. **En production ce sera pire, pas mieux** — site injoignable,
entreprise sans fiche d'établissement, domaine qui bloque le fetch : la
couverture variera d'un prospect à l'autre, et le classement se dégradera à
mesure que les données deviendront réelles.

Le correctif d'honnêteté a donc rendu chaque score **individuellement juste** et
**collectivement non ordonnable**. Ce n'est pas un défaut du correctif : c'est
la révélation d'une propriété qui était déjà vraie et que le bug masquait.

---

## Décision

**Le livrable du système devient le dossier d'audit d'une entreprise. Le score
cesse d'être le produit et devient un instrument de lecture interne.**

Quatre règles, dont trois sont des règles d'honnêteté.

### D1 — « Complet » est vérifiable, jamais décoratif

Le document se déclare lui-même `audit complet`, `**audit PARTIEL**` ou
`complétude inconnue`, selon `scores["_couverture"]` comparée à
`SEUIL_AUDIT_COMPLET` (0,80, `[À CALIBRER]`). Promettre un « audit marketing
express complet » sans mécanisme de vérification serait une formule
commerciale ; ici la promesse est calculée.

Conséquence assumée : **le pivot rehausse la dépendance à la Phase D.** Un
audit qui ne regarde jamais les avis Google ni la fiche d'établissement — faute
de `GOOGLE_PLACES_API_KEY` — se déclarera PARTIEL, et il aura raison.

### D2 — Une dimension non observée est une question d'entretien

C'est le retournement central. Une dimension à `None` n'apparaît ni comme un
zéro, ni comme un point fort, ni comme un écart : elle alimente la section
**« À vérifier en entretien »**, qui est la liste de questions de l'opératrice.

La plus grande faiblesse du système — sa couverture partielle — devient une
matière de conversation. C'est la règle des trois états (I22) appliquée au
livrable plutôt qu'au moteur.

### D3 — Le score est déclaré non comparable, dans le document lui-même

La section « Scores par dimension » porte la mention explicite
« non comparable d'une entreprise à l'autre », avec sa raison. Le score global
n'est plus le titre du document : il est relégué en fin de section, assorti de
sa couverture.

Le document reste un **document de travail interne** (choix de l'opératrice,
2026-08-03) : il prépare l'entretien, il n'est pas remis tel quel. La porte
humaine absorbe le résidu de rédaction.

### D4 — La priorisation est déterministe

`_plan_action()` ordonne les écarts par **gravité déclarée**, puis par **score
de la dimension croissant** (la plus faible d'abord). Aucun LLM ne réordonne ce
tableau. Une gravité inconnue passe en **dernier** : on ne fait pas remonter en
tête ce qu'on n'a pas su qualifier.

Les **poids de rubrique ne sont volontairement pas utilisés** : ils ne figurent
pas dans `Diagnostic`, et les y faire entrer élargirait un contrat que l'ADR
0004 vient de stabiliser. Le score de la dimension est un proxy suffisant et
déjà disponible.

---

## Ce que cette décision ne change pas

- **`diagnostic/scoring.py` n'est pas modifié.** Le moteur continue de produire
  des scores renormalisés à trois états ; c'est leur *usage* qui change, pas
  leur calcul. L'invariant dur de l'ADR 0004 tient.
- **Le contrat JSON de `Diagnostic` n'est pas touché.** Aucun champ ajouté,
  aucun supprimé. Tout le Lot A vit dans `serializers.py`.
- **L'axe intention reste orthogonal** : il alimente la section « pourquoi
  maintenant », pas le classement.
- **La porte humaine reste la seule voie de transition** vers `valide`.

---

## Conséquences

### Positives

- Le système délivre de la valeur **sans avoir à résoudre le classement**, qui
  est le problème dur — et qu'il ne peut pas prouver avoir résolu.
- Le pivot consomme l'existant à ~80 % : entrée directe (`run_diagnostic.py
  --nom --url`), génération de rapport, `Gap` avec preuve, `_couverture`,
  `quality_check()`, trois états. Ce n'est pas une refonte, c'est un changement
  de livrable.
- Les deux branches (prospection sortante, lead entrante) produisent **le même
  artefact** ; elles ne diffèrent que par le point d'entrée.

### Négatives, assumées

- **`SEUIL_AUDIT_COMPLET` et `SEUIL_POINT_FORT` sont `[À CALIBRER]`.** Aucun n'a
  été validé par la consultante.
- **Le seuil de complétude rend visible une dette existante** : aujourd'hui,
  sans clé API, tous les audits se déclarent PARTIEL. C'est exact, et
  inconfortable.
- **Le classement n'est pas réparé, il est déclassé.** Si un besoin de
  priorisation inter-prospects revient, il faudra le traiter à couverture
  égale — pas en comparant des scores renormalisés.

---

## Alternatives écartées

- **Calibrer davantage la rubrique pour faire émerger un ordre.** Utile
  (`fraicheur_mois ≤ 18` reste binaire, Lot 0bis), mais ne corrige pas le
  problème de comparabilité : deux couvertures différentes resteront deux
  examens différents, quelle que soit la finesse des checks.
- **Comparer à couverture égale** (ne classer que les prospects couverts sur
  les mêmes dimensions). Théoriquement correct, mais réduit la cohorte
  comparable à peu de chose et complique le produit sans bénéfice immédiat.
  Reste disponible si le besoin revient.
- **Publier le score au client.** Écarté : un score renormalisé sur une
  couverture partielle n'a pas de sens pour son destinataire, et
  « vous obtenez 36,9/100 » est commercialement hostile.

---

## Lots — état réel

- **Lot A — l'artefact d'audit** : **LIVRÉ** par le présent commit.
  `serializers.py` (`SEUIL_AUDIT_COMPLET`, `SEUIL_POINT_FORT`, `_plan_action`,
  gabarit restructuré), `tests/test_audit_dossier.py` (19 tests).
- **Lot B — entrée lead entrante** : **NON FAIT.** `run_diagnostic.py --nom
  --url` exécute déjà le pipeline mais n'écrit pas le dossier. Il manque
  l'écriture de l'artefact hors flux de découverte et un `source_decouverte`
  distinguant une lead entrante.
- **Lot C — porte de grounding déterministe** : **NON FAIT.** Déjà prévue au
  Palier 2 de l'ADR 0001. Devient nécessaire si le document doit un jour sortir
  tel quel — ce n'est pas le choix retenu aujourd'hui.
- **Lot D — rendu client distinct** : **NON FAIT**, et hors décision : le
  document est interne par choix explicite de l'opératrice.

---

## Références

- Banc d'essai : `scripts/benchmark_intention.py`, exécuté le 2026-08-03.
- Invariant I22 (trois états) : `docs/architecture/invariants.md`.
- Paradigme §P4 (renormalisation et couverture) :
  `docs/architecture/PARADIGMES.md`.
- ADR 0004 (axe intention, orthogonalité besoin/intention).
