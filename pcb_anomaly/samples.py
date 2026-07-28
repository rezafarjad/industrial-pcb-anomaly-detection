"""Paths and metadata for the small VisA demonstration set."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / "assets" / "samples"


@dataclass(frozen=True)
class Sample:
    name: str
    reference: Path
    defective: Path
    ground_truth: Path


SAMPLES = {
    category: Sample(
        name=category.upper(),
        reference=SAMPLE_ROOT / category / "reference.jpg",
        defective=SAMPLE_ROOT / category / "defective.jpg",
        ground_truth=SAMPLE_ROOT / category / "ground_truth.jpg",
    )
    for category in ("pcb1", "pcb2", "pcb3")
}


def validate_samples() -> list[str]:
    missing: list[str] = []
    for sample in SAMPLES.values():
        for path in (
            sample.reference,
            sample.defective,
            sample.ground_truth,
        ):
            if not path.is_file() or path.stat().st_size == 0:
                missing.append(str(path.relative_to(ROOT)))
    return missing
