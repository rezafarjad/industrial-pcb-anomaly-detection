"""Run the detector on the bundled samples and save an honest smoke report."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pcb_anomaly import DetectorConfig, inspect  # noqa: E402
from pcb_anomaly.samples import SAMPLES  # noqa: E402


def main() -> int:
    config = DetectorConfig()
    rows = []
    failures = []
    for category, sample in SAMPLES.items():
        reference = Image.open(sample.reference).convert("RGB")
        defective = Image.open(sample.defective).convert("RGB")
        good_result = inspect(reference, reference.copy(), config)
        defective_result = inspect(reference, defective, config)
        Image.fromarray(defective_result.overlay_rgb).save(
            ROOT / "results" / f"{category}_demo_overlay.png"
        )
        passed = (
            good_result.decision == "No significant change"
            and defective_result.decision == "Anomaly detected"
        )
        if not passed:
            failures.append(category)
        rows.append(
            {
                "category": category,
                "passed": passed,
                "known_good": good_result.report(),
                "defective": defective_result.report(),
            }
        )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "Smoke validation on the bundled examples; not a dataset benchmark"
        ),
        "all_passed": not failures,
        "cases": rows,
    }
    output = ROOT / "results" / "demo_validation.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {output.relative_to(ROOT)}")
    if failures:
        print("Unexpected decisions: " + ", ".join(failures))
        return 1
    print("All bundled sample decisions matched expectations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
