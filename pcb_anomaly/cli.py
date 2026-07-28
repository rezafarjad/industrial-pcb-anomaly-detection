"""Command-line interface for repeatable PCB inspections."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import cv2
from PIL import Image

from .reference_detector import DetectorConfig, inspect


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pcb-inspect",
        description=(
            "Align a PCB photograph with a known-good reference and export "
            "an anomaly report."
        ),
    )
    parser.add_argument("reference", type=Path, help="Known-good reference image")
    parser.add_argument("candidate", type=Path, help="PCB image to inspect")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("inspection-output"),
        help="Directory for the report and annotated images",
    )
    parser.add_argument(
        "--sensitivity",
        type=int,
        default=65,
        choices=range(0, 101),
        metavar="0-100",
        help="Change sensitivity (default: 65)",
    )
    parser.add_argument(
        "--min-region-area",
        type=int,
        default=80,
        help="Minimum connected anomaly area in pixels (default: 80)",
    )
    parser.add_argument(
        "--working-width",
        type=int,
        default=900,
        help="Maximum reference width used for inspection (default: 900)",
    )
    return parser


def _load_image(path: Path) -> Image.Image:
    if not path.is_file():
        raise FileNotFoundError(f"Image does not exist: {path}")
    with Image.open(path) as source:
        source.load()
        return source.convert("RGB")


def run_inspection(args: argparse.Namespace) -> dict:
    config = DetectorConfig(
        sensitivity=args.sensitivity,
        min_region_area=args.min_region_area,
        working_width=args.working_width,
    )
    result = inspect(
        _load_image(args.reference),
        _load_image(args.candidate),
        config,
    )
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    Image.fromarray(result.overlay_rgb).save(output_dir / "overlay.png")
    Image.fromarray(result.aligned_candidate_rgb).save(
        output_dir / "aligned_candidate.png"
    )
    cv2.imwrite(str(output_dir / "anomaly_mask.png"), result.anomaly_mask)

    report = result.report()
    report["inputs"] = {
        "reference": str(args.reference.resolve()),
        "candidate": str(args.candidate.resolve()),
    }
    report["outputs"] = {
        "overlay": "overlay.png",
        "aligned_candidate": "aligned_candidate.png",
        "anomaly_mask": "anomaly_mask.png",
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = run_inspection(args)
    except (FileNotFoundError, OSError, ValueError) as error:
        parser.error(str(error))

    print(f"Decision: {report['decision']}")
    print(f"Anomaly score: {report['anomaly_score']:.1f} / 100")
    print(f"Review regions: {report['region_count']}")
    print(f"Report: {(args.output_dir.resolve() / 'report.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
