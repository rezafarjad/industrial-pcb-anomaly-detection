import json
from pathlib import Path

from pcb_anomaly.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_cli_exports_complete_inspection_bundle(tmp_path):
    sample = ROOT / "assets" / "samples" / "pcb1"
    output_dir = tmp_path / "inspection"

    exit_code = main(
        [
            str(sample / "reference.jpg"),
            str(sample / "defective.jpg"),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    assert (output_dir / "overlay.png").stat().st_size > 0
    assert (output_dir / "aligned_candidate.png").stat().st_size > 0
    assert (output_dir / "anomaly_mask.png").stat().st_size > 0
    report = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
    assert report["decision"] == "Anomaly detected"
    assert report["outputs"]["overlay"] == "overlay.png"
