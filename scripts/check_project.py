from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []

app = ROOT / "streamlit_app.py"
notebook = (
    ROOT / "notebooks"
    / "industrial_pcb_anomaly_detection_local.ipynb"
)
for path in (app, notebook, ROOT / "requirements.txt"):
    if not path.exists():
        errors.append(f"Missing repository file: {path}")

if app.exists():
    try:
        compile(app.read_text(encoding="utf-8"), str(app), "exec")
    except SyntaxError as error:
        errors.append(f"streamlit_app.py: {error}")

if notebook.exists():
    try:
        payload = json.loads(notebook.read_text(encoding="utf-8"))
        if payload.get("nbformat") != 4:
            errors.append("Notebook is not nbformat 4")
    except Exception as error:
        errors.append(f"Notebook validation: {error}")

for category in ("pcb1", "pcb2", "pcb3"):
    directory = ROOT / "artifacts" / category
    for filename in (
        "pca.joblib",
        "patchcore_memory.npy",
        "config.json",
    ):
        path = directory / filename
        if not path.exists():
            errors.append(
                f"Artifact not generated yet: {path.relative_to(ROOT)}"
            )

if errors:
    print("\\n".join(f"[!] {error}" for error in errors))
    raise SystemExit(1)
print("Repository contract validated successfully.")
