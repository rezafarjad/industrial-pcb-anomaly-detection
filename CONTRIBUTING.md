# Contributing

Thank you for helping improve the PCB Visual Inspector. Small, focused pull
requests with reproducible evidence are easiest to review.

## Development setup

```bash
git clone https://github.com/rezafarjad/industrial-pcb-anomaly-detection.git
cd industrial-pcb-anomaly-detection
python -m venv .venv
python -m pip install -e ".[dev]"
```

Activate the environment if you prefer, or run commands through its Python
executable.

## Quality checks

Run the same checks used in continuous integration:

```bash
python scripts/check_project.py
ruff check .
pytest -q
python -m build
python scripts/smoke_app.py
```

## Pull requests

- Create a branch from the latest `main`.
- Keep the change scoped to one problem.
- Add or update tests for behavioral changes.
- Update user-facing documentation when commands or outputs change.
- Never commit downloaded datasets, feature caches, credentials, or large
  experimental prediction arrays.
- Do not add performance claims without a reproducible result file and the
  exact configuration that generated it.

## Defect data and metrics

The bundled VisA examples are third-party data under CC BY 4.0. Any additional
sample must include its source, license, split, row or file identifier, and
transformation history. Synthetic or reconstructed references must be labeled
as such.

Benchmark changes should separate smoke validation from dataset-level
evaluation. A three-image demonstration is not a production benchmark.

## Reporting problems

Use the bug-report issue form for reproducible defects. Follow `SECURITY.md`
instead for vulnerabilities or reports that contain sensitive information.
