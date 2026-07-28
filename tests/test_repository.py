import json
import re
from pathlib import Path
from urllib.parse import unquote

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib

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


def test_release_metadata_and_professional_files_are_present():
    project = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert project["project"]["version"] == "1.0.0"
    assert project["project"]["scripts"]["pcb-inspect"] == "pcb_anomaly.cli:main"

    required = (
        ROOT / "assets" / "app_demo.png",
        ROOT / "Dockerfile",
        ROOT / "compose.yaml",
        ROOT / "CONTRIBUTING.md",
        ROOT / "SECURITY.md",
        ROOT / "docs" / "ARCHITECTURE.md",
        ROOT / "docs" / "VALIDATION.md",
        ROOT / ".github" / "workflows" / "ci.yml",
        ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml",
    )
    for path in required:
        assert path.stat().st_size > 0


def test_readme_local_links_resolve():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    targets = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", readme)
    local_targets = [
        unquote(target.split("#", 1)[0])
        for target in targets
        if target
        and not target.startswith(("http://", "https://", "mailto:"))
    ]
    assert local_targets
    for target in local_targets:
        assert (ROOT / target).exists(), target


def test_committed_demo_validation_meets_acceptance_thresholds():
    report = json.loads(
        (ROOT / "results" / "demo_validation.json").read_text(encoding="utf-8")
    )
    assert report["all_passed"] is True
    for case in report["cases"]:
        assert case["passed"] is True
        assert case["localization"]["iou"] >= report["acceptance"]["minimum_iou"]
        assert (
            case["localization"]["recall"]
            >= report["acceptance"]["minimum_recall"]
        )
