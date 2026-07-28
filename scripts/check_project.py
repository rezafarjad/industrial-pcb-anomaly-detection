"""Fast repository contract checks without starting Streamlit."""

from __future__ import annotations

import json
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    ROOT / "streamlit_app.py",
    ROOT / "pcb_anomaly" / "reference_detector.py",
    ROOT / "pcb_anomaly" / "cli.py",
    ROOT / "requirements.txt",
    ROOT / "pyproject.toml",
    ROOT / "Dockerfile",
    ROOT / "compose.yaml",
    ROOT / "assets" / "app_demo.png",
    ROOT / "docs" / "ARCHITECTURE.md",
    ROOT / "docs" / "VALIDATION.md",
    ROOT / ".github" / "workflows" / "ci.yml",
    ROOT / "CONTRIBUTING.md",
    ROOT / "SECURITY.md",
    ROOT / "Start PCB Inspector.bat",
    ROOT / "Create Desktop Shortcut.bat",
)


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED:
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"Missing or empty repository file: {path}")

    for path in (
        *ROOT.glob("*.py"),
        *ROOT.glob("pcb_anomaly/*.py"),
        *ROOT.glob("scripts/*.py"),
    ):
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

    try:
        project = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        if project["project"]["version"] != "1.0.0":
            errors.append("pyproject.toml project version is not 1.0.0")
        if "pcb-inspect" not in project["project"]["scripts"]:
            errors.append("pyproject.toml does not expose the pcb-inspect CLI")
    except (KeyError, OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        errors.append(f"Package metadata cannot be read: {error}")

    try:
        validation = json.loads(
            (ROOT / "results" / "demo_validation.json").read_text(
                encoding="utf-8"
            )
        )
        if not validation.get("all_passed"):
            errors.append("Bundled demo validation is not passing")
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        errors.append(f"Demo validation report cannot be read: {error}")

    if errors:
        print("\n".join(f"[!] {error}" for error in errors))
        return 1
    print("Repository contract validated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
