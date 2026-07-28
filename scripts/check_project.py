"""Fast repository contract checks without starting Streamlit."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    ROOT / "streamlit_app.py",
    ROOT / "pcb_anomaly" / "reference_detector.py",
    ROOT / "requirements.txt",
    ROOT / "Start PCB Inspector.bat",
    ROOT / "Create Desktop Shortcut.bat",
)


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED:
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"Missing or empty repository file: {path}")

    for path in (*ROOT.glob("*.py"), *ROOT.glob("pcb_anomaly/*.py")):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as error:
            errors.append(f"{path.relative_to(ROOT)}: {error}")

    notebook_path = (
        ROOT / "notebooks" / "industrial_pcb_anomaly_detection_local.ipynb"
    )
    try:
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        if notebook.get("nbformat") != 4:
            errors.append("Research notebook is not nbformat 4")
    except Exception as error:
        errors.append(f"Research notebook cannot be read: {error}")

    for category in ("pcb1", "pcb2", "pcb3"):
        for filename in ("reference.jpg", "defective.jpg", "ground_truth.jpg"):
            path = ROOT / "assets" / "samples" / category / filename
            if not path.is_file() or path.stat().st_size == 0:
                errors.append(f"Missing sample asset: {path.relative_to(ROOT)}")
    manifest = ROOT / "assets" / "samples" / "manifest.json"
    try:
        json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        errors.append(f"Sample manifest cannot be read: {error}")

    if errors:
        print("\n".join(f"[!] {error}" for error in errors))
        return 1
    print("Repository contract validated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
