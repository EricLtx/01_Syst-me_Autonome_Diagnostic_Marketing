# Module `diagnostic` — J1, le pivot

Premier jalon de l'écosystème d'agents de prospection. Ce module prend une
entreprise en entrée et produit un **diagnostic de marque scoré** + un
**mini-audit lisible**. Il est volontairement autonome : on le valide seul,
sur le client québécois + 2-3 look-alikes, avant de câbler quoi que ce soit
autour (sourcing, rédaction, CRM — ce sera J2 à J4).

## Arborescence

```
diagnostic/
├─ README.md                      ← ce fichier
├─ CLAUDE.md                      ← contexte projet pour Claude Code
├─ requirements.txt
├─ knowledge/
│  └─ rubric_persona1.yaml        ← LA RUBRIQUE (le jugement métier, en données)
├─ diagnostic/
│  ├─ models.py                   ← le contrat de données (Diagnostic, Company, Gap)
│  ├─ config.py                   ← charge rubrique + base de connaissances
│  ├─ pipeline.py                 ← orchestre la chaîne entrée → sortie
│  ├─ scoring.py                  ← moteur générique (applique la rubrique)
│  ├─ synthesis.py                ← rédaction LLM + contrôle qualité (+ repli)
│  └─ collectors/
│     ├─ base.py                  ← interface Collector (enfichable, anti-crash)
│     ├─ website.py               ← IMPLÉMENTÉ — testable tout de suite
│     ├─ gbp.py                   ← stub (J2)
│     ├─ reviews.py               ← stub (J2)
│     ├─ seo.py                   ← stub (J2)
│     └─ social.py                ← stub (J2)
└─ scripts/
   └─ run_diagnostic.py           ← CLI
```

## Installation et test

```bash
python -m venv .venv && source .venv/bin/activate    # Windows : .venv\Scripts\activate
pip install -r requirements.txt

python scripts/run_diagnostic.py \
    --nom "Climatisation Tremblay" \
    --url "https://exemple-hvac.ca" \
    --region "Québec, QC"
```

Sans clé API, la synthèse utilise un **repli déterministe** : ça tourne
hors-ligne. Pour la rédaction par le LLM, pose `ANTHROPIC_API_KEY` puis
`pip install anthropic`.

---

## Construire et étendre ce module avec Claude Code et Claude Cowork

L'objectif n'est pas seulement de livrer du code : c'est de te remettre au
développement, augmenté par l'IA. La compétence a bougé — elle est désormais
dans la **direction** et la **revue**, plus dans la frappe ligne à ligne.

### Claude Code — pour le code (le J1 et au-delà)

Claude Code est l'agent de codage en terminal : il lit le dépôt, édite les
fichiers, exécute les commandes et gère git, sans quitter la ligne de commande.

**Mise en place (5 min).** Il faut un compte payant (Claude Pro à 20 $/mois
suffit ; le plan gratuit n'inclut pas Claude Code).
```bash
# Installeur natif (aucun Node requis) :
curl -fsSL https://claude.ai/install.sh | bash
# — ou via npm (nécessite Node.js 18+) :
npm install -g @anthropic-ai/claude-code

cd diagnostic     # le dossier de ce module
claude            # démarre la session
```
Si tu préfères une interface graphique, l'app Desktop existe aussi.

**Le réflexe à prendre : `/init`.** Dans une session, `/init` génère (ou met à
jour) un `CLAUDE.md` — le contexte persistant que Claude Code relit à chaque
fois. C'est l'étape la plus rentable et la plus souvent zappée. Un `CLAUDE.md`
est déjà fourni ici : ouvre-le, c'est lui qui garde tes règles d'architecture
(rubrique = donnée, collecte ≠ LLM, etc.) à portée de l'agent.

**Comment piloter — les trois mouvements du J2 :**

1. *Donner le cap, pas la solution.* Pointe l'architecture, laisse-le proposer :
   > « Implémente `GbpCollector` dans `collectors/gbp.py` via l'API Google
   >  Places (Place Details). Respecte le gabarit de `website.py` : cache,
   >  timeout, échec gracieux. Renvoie `verified`, `has_photos`, `photo_count`.
   >  Montre-moi ton plan avant de coder. »
2. *Relire le diff, pas le réécrire.* C'est là qu'est ta valeur de dev : tu
   challenges, tu corriges la conception, tu valides. Demande-lui de lancer le
   `run_diagnostic.py` sur une vraie fiche pour vérifier la sortie.
3. *Capitaliser.* Quand une convention émerge (gestion d'erreurs API, format de
   cache), demande-lui de l'inscrire dans `CLAUDE.md`. Le projet s'auto-documente.

Ton historique C++/VHDL joue ici : la pensée système — pipelines, états,
contraintes — est exactement ce qu'une architecture d'agents réclame. Python
et JS reviendront vite ; le reste, c'est de la direction.

### Claude Cowork — pour ce qui n'est pas du code

Cowork est l'app de travail agentique pour les tâches hors-dev. C'est le
**cockpit de la consultante** sur ce projet :

- **Affûter la rubrique sans coder.** `rubric_persona1.yaml` est du texte
  lisible : dans Cowork, on peut raisonner « pour un installateur HVAC, les
  avis pèsent-ils plus que le SEO ? » et ajuster les poids. La logique métier
  se règle là ; le moteur, lui, ne change pas.
- **Relire les diagnostics en lot.** Avant l'outreach (J3), c'est l'endroit
  pour valider que les mini-audits tiennent la route — la gouvernance humaine
  en bout de chaîne dont on a parlé.
- **Préparer le persona 2.** Dériver `rubric_persona2.yaml` (cabinet d'avocats)
  est un travail de réflexion, pas de code : Cowork est taillé pour ça.

La division du travail, en une phrase : **Claude Code touche au code, Cowork
touche au jugement et au contenu.** Le même socle (la rubrique, le contrat de
données) sert de pont entre les deux.

---

## Conformité et bonnes manières

Le scraping est volontairement minimal et poli (User-Agent, timeout, cache,
une requête par cible). Côté prospection à venir (J3+), garde en tête que
CASL (Québec) et la nLPD + art. 3 LCD (Suisse) encadrent l'email à froid :
ciblage B2B, identification claire, désinscription. Rien de bloquant, mais à
câbler dès la rédaction — et à faire valider par un juriste.
