"""
test_pipeline_cli.py — CLI de l'orchestrateur (run_pipeline.py) + rétro-compat.

Vérifie que :
  - `run_pipeline.py --help` fonctionne (exit 0) ;
  - run_pipeline importe l'orchestrateur sans toucher au réseau (garde-fou AST) ;
  - les entrypoints run_discovery / run_diagnostic exposent toujours leurs
    symboles historiques (aucune régression : ils tournent encore seuls).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_RACINE = Path(__file__).resolve().parent.parent


def test_help_exit_zero():
    r = subprocess.run(
        [sys.executable, "run_pipeline.py", "--help"],
        cwd=_RACINE, capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0
    assert "orchestrateur" in r.stdout.lower() or "kemana" in r.stdout.lower()


def test_run_pipeline_dans_garde_fou_bus():
    """run_pipeline.py + orchestrator.py sont couverts par le garde-fou AST."""
    from diagnostic.preflight import _check_garde_fous_bus
    checks = _check_garde_fous_bus()
    couverts = {c.message.split(" :")[0] for c in checks}
    assert "run_pipeline.py" in couverts
    assert "orchestrator.py" in couverts
    for c in checks:
        assert c.ok, f"Garde-fou bus VIOLATION : {c.message}"


def test_retrocompat_run_discovery():
    """run_discovery garde main(), run() injectable et _candidate_vers_fiche."""
    import run_discovery
    assert callable(run_discovery.main)
    assert callable(run_discovery.run)
    assert callable(run_discovery._candidate_vers_fiche)


def test_retrocompat_run_diagnostic():
    """run_diagnostic garde main() et _build_pipeline (api_io optionnel)."""
    import inspect
    import run_diagnostic
    assert callable(run_diagnostic.main)
    sig = inspect.signature(run_diagnostic._build_pipeline)
    assert "api_io" in sig.parameters
    # _build_pipeline sans api_io reste valide (comportement J1 inchangé).
    assert run_diagnostic._build_pipeline() is not None
