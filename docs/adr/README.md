# Décisions d'architecture (ADR)

Une ADR (*Architecture Decision Record*) enregistre une **décision structurante**
et son raisonnement, pour que la question ne soit pas rouverte tous les trois
mois faute de mémoire.

## Index

| N° | Titre | Statut | Date |
|---|---|---|---|
| [0001](0001-orchestrateur-dag-deterministe.md) | Orchestrateur DAG déterministe « Kemana-Flow » | acceptée — Palier 1 implémenté | 2026-08-01 |
| [0002](0002-greenit-efficience-et-observabilite.md) | GreenIT : efficience des appels IA et observabilité de l'empreinte | acceptée — implémentée | 2026-08-01 |

## Quand écrire une ADR

Écris-en une si le choix :

- contraint les itérations suivantes ;
- ajoute ou retire une dépendance externe ;
- touche un invariant de `docs/architecture/invariants.md` ;
- change un format de donnée partagé (frontmatter, ledger, colonnes d'export) ;
- a un effet légal ou budgétaire.

Sinon, une note dans `docs/architecture/` suffit. Un renommage de variable n'est
pas une ADR.

## Format

Fichier `NNNN-titre-en-kebab-case.md`, numérotation continue, sections :

1. **Statut** — proposée · acceptée · en cours d'implémentation · remplacée par NNNN
2. **Contexte** — les faits, vérifiables, qui rendent la décision nécessaire
3. **Décision** — ce qui est décidé, à l'impératif
4. **Conséquences** — positives **et** négatives, les négatives assumées explicitement
5. **Alternatives écartées** — chacune avec son motif de rejet
6. **Vérification** — les commandes qui prouvent que la décision est tenue

## Règles

- **Une ADR acceptée est immuable.** On ne la réécrit pas : on en écrit une
  nouvelle qui la remplace, et on met à jour les deux en-têtes
  (`Remplacée par` / `Remplace`).
- **Zéro invention.** Le contexte s'appuie sur des faits vérifiés dans le dépôt
  ou sur une source citée. Un chiffre sans origine n'entre pas dans une ADR.
- Une décision « en cours d'implémentation » le dit dans son statut et liste ce
  qui reste à vérifier.
