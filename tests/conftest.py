import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DAGS_DIR = REPO_ROOT / "dags"

# etl.*/utils.* live at the repo root; the shared `config` package lives
# under dags/ (dags/config/settings.py) so Composer's DAG-folder sync can
# reach it too (see docs/MIGRATION.md). Both must be on sys.path for
# etl.*'s `from config import settings` imports to resolve here.
#
# Note: repo root also has a plain `config/` directory (local-dev Airflow
# config, config/airflow.cfg, no __init__.py) - not a regular Python
# package. Because dags/config/ *does* have __init__.py, Python's import
# system always resolves a bare `import config` to dags/config as a
# regular package in preference to the root config/ directory's
# namespace-package candidacy, regardless of sys.path order - so the two
# don't collide despite both existing.
for path in (str(REPO_ROOT), str(DAGS_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)
