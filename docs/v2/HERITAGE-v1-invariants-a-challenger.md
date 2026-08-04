# Héritage v1 — les 24 invariants, et la question à leur poser en v2

> Document d'entrée de la refonte. Il n'est pas une défense de l'existant.
> Il sert à ce que la v2 **paie une deuxième fois** uniquement les leçons
> qu'elle choisit sciemment de repayer.
>
> Rédigé le 2026-08-04, avant toute décision d'architecture v2.

---

## Pourquoi ce document existe

La v1 est un système de 5 408 lignes qui **n'a jamais vu une entreprise
réelle** : 669 tests, tous contre un faux serveur HTTP local ; vault vide ;
zéro clé API ; préflight NO-GO avec 16 contrôles bloquants.

Dans ces conditions, la valeur de la v1 n'est **pas** son code. C'est la liste
des erreurs qu'elle a commises et corrigées, chacune payée par une régression
réelle, une revue recalée ou un défaut envoyé jusqu'en production locale.
Repartir de zéro est un choix légitime — mais repartir de zéro *en oubliant
ces erreurs* revient à les racheter au prix fort.

Chaque invariant est donc présenté ici avec trois éléments :
**ce qu'il interdit**, **ce qu'il a coûté à apprendre**, et **la question de
challenge pour la v2**. Un invariant sans coût d'apprentissage documenté est
suspect : il est probablement de la préférence déguisée en principe.

---

## Catégorie A — Invariants payés par un défaut réel

Ceux-là ont une cicatrice. Les abandonner est possible, mais doit être un
choix explicite, jamais un oubli.

### I22 — Trois états : un signal non observé n'est jamais un échec

**Interdit :** traiter l'absence d'observation comme une observation négative.
Un check vaut `ok` / `echec` / `inconnu` ; un `inconnu` sort du numérateur ET
du dénominateur.

**Coût d'apprentissage :** trois occurrences du même défaut en une seule
journée, par trois portes différentes — `_check_passes` comptant `None` comme
échec ; l'API Google Places répondant **HTTP 200 avec
`{"status": "REQUEST_DENIED", "results": []}`** quand la clé est absente, lu
comme « cette entreprise n'a pas de fiche » ; un vocabulaire métier codé en
dur produisant `mentions_offre = False` pour tout secteur non-HVAC.
Conséquence mesurée : **deux failles de gravité haute fabriquées pour
chaque entreprise diagnostiquée**, dont une alimentait l'accroche commerciale
envoyée au prospect. Une revue a recalé le chantier à **78,6 %** parce que la
correction avait été prouvée sur le moteur et non sur le chemin de production.

**La leçon dépasse le code :** violer cet invariant ne dégrade pas un score,
il **fabrique une affirmation fausse et l'envoie à un tiers**.

**Question v2 :** un socle OSINT agnostique manipule des signaux de fiabilité
hétérogène. Trois états suffisent-ils, ou faut-il un modèle plus riche
(observé / non observé / observé-mais-peu-fiable / contradictoire entre
sources) ? **La v2 doit répondre à cette question, pas la contourner.**

### I19 — Aucun chiffre non mesuré présenté comme mesuré

**Coût :** le dépôt affiche des coûts à 0,00 $ parce qu'aucun tarif n'a jamais
été relevé (`api_pricing.yaml` : `releve_le: null`, tous prix `null`). Toute
communication d'un « gain » chiffré aurait été une invention. Les estimations
d'énergie et de CO₂e portent la mention « estimation » jusque dans le contrat
HTTP de l'API.

**Question v2 :** un SaaS doit afficher des métriques de valeur à ses clients.
Comment tenir cette honnêteté **sans rendre le produit muet** ? C'est une
tension réelle, pas un détail de rédaction.

### I17 — Le LLM rédige, il ne collecte jamais

**Coût :** pas de défaut constaté — mais c'est le garde-fou qui rend le
grounding vérifiable. Le LLM ne voit que des faits déjà établis par des
collecteurs déterministes.

**Question v2 :** la recherche agentique récente pousse vers des agents qui
*décident* de leurs outils. Cet invariant est en tension frontale avec cette
tendance. **À trancher explicitement, avec un argument** — pas par défaut dans
un sens ou dans l'autre.

### I9 — Ordonnancement déterministe (+ I8, le graphe est une donnée)

**Coût :** l'ADR 0001 a explicitement **refusé un superviseur-planificateur
LLM** pour cause de coût, de non-déterminisme et de charge cognitive de
débogage. Tri topologique de Kahn, départage alphabétique : deux exécutions
donnent la même séquence.

**Question v2 :** c'est LA décision à rejuger avec la littérature en main. Le
déterminisme est-il un avantage ou un plafond quand le système doit s'étendre
à des verticales inconnues d'avance ?

---

## Catégorie B — Invariants structurels, peu coûteux, probablement à garder

Ils tiennent sans effort et rendent le système auditable.

| Invariant | Ce qu'il interdit | Question v2 |
|---|---|---|
| **I1** Un seul écrivain du vault | `os.replace()` hors `vault_io.py` — vérifié par AST | Le magasin v2 sera-t-il encore un système de fichiers ? Si non, l'invariant devient « un seul module d'écriture », pas « un seul appel » |
| **I4** Un seul chemin vers le réseau | `import requests`/`anthropic` hors `api_io.py` | À conserver — c'est ce qui rend le coût et le cache mesurables |
| **I2** Journal append-only | écriture directe dans `runs.log` | À conserver, mais le format JSONL local ne tiendra pas en multi-tenant |
| **I5/I6** Grand livre + budget bloquant **avant** l'appel | dépasser un budget | À conserver : c'est la base d'une tarification à l'usage |
| **I3** Schéma validé à l'écriture | persister un frontmatter non validé | À conserver |
| **I13** Reprise idempotente | perdre le travail déjà fait | À conserver |
| **I16** La connaissance métier est une donnée | coder une rubrique en Python | **Pierre angulaire de l'extensibilité v2** — à renforcer, pas à garder tel quel |

---

## Catégorie C — Invariants liés au produit v1, à réexaminer

Ceux-là encodent un choix produit, pas une vérité technique. La refonte les
remet légitimement en jeu.

- **I7 Machine à états intangible** (`decouvert → diagnostique → valide →
  contacte`, `* → rejete`) : l'agent ne peut faire QUE la première transition.
  C'est la **porte humaine**, déclarée non négociable par l'opératrice. En v2
  multi-tenant et multi-verticale, cette machine à états est-elle universelle
  ou spécifique au démarchage B2B ?
- **I14 Cockpit en lecture seule** : conséquence directe de I7. Tient tant que
  la porte humaine vit dans Obsidian. Si la v2 n'a plus Obsidian, à repenser
  entièrement.
- **I18 Outreach non activable** (double verrou : `enabled: false` **et**
  runner qui renvoie `bloque`) : conditionné à une validation juridique
  CASL/nLPD/RGPD jamais faite. **Le donneur d'ordre a demandé le 2026-08-04
  d'écarter l'aspect juridique du séquencement et de supposer le système
  conforme** — cet invariant est donc explicitement suspendu pour la
  conception v2. Il devra revenir avant tout envoi réel.
- **I23/I24** (axe intention, `citable=True`) : très spécifiques au produit
  v1. Le principe sous-jacent — *une affirmation adressée à un tiers doit
  être adossée à une source citable* — mérite de survivre ; sa forme, non.
- **I20/I21** (routage de modèle déterministe, bornes de frugalité avant
  émission) : sains, mais dimensionnés pour un usage mono-tenant.

---

## Ce que la v1 a raté, et que la v2 ne doit pas reproduire

Ces points ne sont pas des invariants : ce sont les **échecs de méthode**
constatés. Ils comptent davantage que les réussites.

1. **Construire loin de la réalité.** 669 tests, 0 entreprise réelle. Toute
   propriété établie l'est *contre une fixture*. Le banc d'essai a même produit
   un artefact trompeur : 7 prospects sur 9 à un score identique, en partie
   parce que le faux serveur n'expose que **deux gabarits de site**. Une v2
   doit rencontrer des données réelles **avant** d'accumuler des invariants.

2. **Un moteur générique sans contenu.** Le mécanisme multi-industrie (ADR
   0003) permet d'ajouter un secteur sans code — et **un seul ICP existe**.
   Généricité sans deuxième cas d'usage = généricité non prouvée. La v2 doit
   valider son extensibilité sur **deux verticales réelles**, pas une.

3. **Le classement ne classait pas.** Découvert le 2026-08-04 : depuis la règle
   des trois états, un score est renormalisé sur les seules dimensions
   observées — donc deux entreprises couvertes différemment ne passent pas le
   même examen et **leurs scores ne sont pas comparables**. Le correctif
   d'honnêteté a rendu chaque score individuellement juste et collectivement
   non ordonnable. L'ADR 0005 a réagi en changeant de livrable (l'audit devient
   le produit). **La v2 doit décider dès la conception si elle a besoin d'un
   ordre total, et si oui à quelle condition de comparabilité.**

4. **De l'infrastructure sans usage.** `append_historique()` est écrite,
   testée, journalisée — et aucun collecteur ne l'appelle.

5. **Un invariant annoncé mais non tenu par son mécanisme.** La règle « tout
   nouveau module de ce type doit être ajouté à la liste du préflight » n'a pas
   été suivie : `greenit.py`, `intent.py`, `serializers.py`, `legitimite.py`,
   `_decay.py` **ne sont pas** dans `_check_garde_fous_bus`. La couverture
   n'est assurée que par un test générique en `rglob`. **Leçon v2 : un
   invariant qui exige une action manuelle à chaque ajout sera violé.
   Il doit être vérifié par balayage, jamais par liste tenue à la main.**

6. **Deux messages de commit sur-attribués.** Deux fois, un message a décrit
   des fichiers absents de son diff, parce qu'il avait été rédigé depuis le
   *rapport d'un agent* (qui couvre un chantier) au lieu de `git diff --cached`
   (qui couvre un diff). Les deux fois, c'est l'agent coordinateur — celui que
   personne ne relit — qui était en faute.

---

## Ce qui, dans la v1, a le mieux fonctionné

À conserver comme **méthode**, indépendamment de l'architecture retenue.

- **La documentation exécutable.** `tests/test_doc_coherence.py` fait échouer
  le build quand un chiffre documenté diverge du réel. Il a trouvé des erreurs
  qu'aucune relecture humaine n'avait vues, et il attrape même les
  incohérences que la documentation s'inflige à elle-même.
- **La porte de revue à 97 %,** tenue par un agent **sans droit d'écriture**
  (un auditeur qui peut corriger n'est plus un auditeur), qui **ré-exécute**
  chaque contrôle au lieu de croire les rapports. Elle a recalé quatre
  chantiers — dont deux sur des erreurs du coordinateur.
- **Le repli déterministe intégral :** toute la suite tourne sans aucune clé
  API. C'est la preuve permanente que les stubs et le mode dégradé
  fonctionnent.

---

## Instruction à l'architecte v2

Traite les 24 invariants comme des **hypothèses à réfuter**, pas comme un
héritage à préserver. Pour chacun, tranche : **conservé / transformé /
abandonné**, avec un motif d'une ligne.

Un invariant abandonné n'est pas une régression — mais un invariant abandonné
**sans que quelqu'un ait lu ce qu'il a coûté** en est une.
