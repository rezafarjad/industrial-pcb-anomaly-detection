import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_python_sources_compile():
    sources = (
        *ROOT.glob("*.py"),
        *ROOT.glob("pcb_anomaly/*.py"),
        *ROOT.glob("scripts/*.py"),
    )
    for path in sources:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


def test_notebook_is_valid_json():
    path = ROOT / "notebooks" / "industrial_pcb_anomaly_detection_local.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4


def test_launchers_and_samples_are_present():
    assert (ROOT / "Start PCB Inspector.bat").stat().st_size > 0
    assert (ROOT / "Create Desktop Shortcut.bat").stat().st_size > 0
    for category in ("pcb1", "pcb2", "pcb3"):
        directory = ROOT / "assets" / "samples" / category
        assert (directory / "reference.jpg").stat().st_size > 0
        assert (directory / "defective.jpg").stat().st_size > 0
        assert (directory / "ground_truth.jpg").stat().st_size > 0
    manifest = json.loads(
        (ROOT / "assets" / "samples" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(manifest["samples"]) == 3
    assert manifest["reference_derivation"]["algorithm"]
