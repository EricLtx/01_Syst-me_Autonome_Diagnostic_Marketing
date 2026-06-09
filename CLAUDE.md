# CLAUDE.md — contexte projet pour Claude Code

> Ce fichier est lu automatiquement par Claude Code à chaque session. C'est
> sa mémoire du projet. `/init` peut le (re)générer ; ici il est pré-rempli.
> Le tenir à jour est l'étape la plus rentable et la plus souvent oubliée.

## Ce qu'est ce projet

Module `diagnostic` (J1) : le pivot d'un écosystème d'agents de prospection
pour une consultante en marketing / branding. Entrée = une entreprise ;
sortie = un diagnostic scoré + un mini-audit de marque lisible. Cible
actuelle : persona 1 (détaillant / installateur HVAC), séquence Québec → Suisse.

## Architecture (à respecter)

Chaîne : `entrée → collecteurs → signaux → scoring → synthèse+QA → sortie`.

Quatre règles non négociables :
1. **Collecte déterministe ≠ raisonnement LLM.** Les collecteurs vont chercher
   des faits ; le LLM (synthesis.py) rédige à partir de faits déjà établis. Le
   LLM ne fetch jamais.
2. **Collecteurs isolés et enfichables** (héritent de `Collector`, échec via
   `safe_collect`). On en ajoute un sans toucher aux autres.
3. **La rubrique est une donnée** (`knowledge/rubric_*.yaml`), jamais du code.
   Nouveau persona = nouvelle rubrique, `scoring.py` ne bouge pas.
4. **QA avant sortie** : le mini-audit part à un vrai prospect, donc aucune
   affirmation non adossée aux failles réelles.

## Commandes

```bash
pip install -r requirements.txt
python scripts/run_diagnostic.py --nom "X" --url "https://..." --region "..."
python scripts/run_diagnostic.py --nom "X" --url "https://..." --json
```

## Conventions

- Python 3.10+, type hints partout, `from __future__ import annotations`.
- Commentaires en français, orientés "pourquoi" plutôt que "quoi".
- Scraping poli : User-Agent honnête, timeout, cache disque, une requête par cible.
- Pas de secret en dur. Clé LLM via `ANTHROPIC_API_KEY` (optionnelle).

## Prochaines tâches (J2)

Implémenter les collecteurs stub : `gbp.py`, `reviews.py` (API Google Places),
`seo.py`, `social.py`. Chacun suit le gabarit de `website.py`.
