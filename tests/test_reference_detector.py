from pathlib import Path

import pytest
from PIL import Image

from pcb_anomaly import DetectorConfig, inspect
from pcb_anomaly.metrics import align_binary_mask, binary_overlap

ROOT = Path(__file__).resolve().parents[1]


def _image(category: str, filename: str) -> Image.Image:
    path = ROOT / "assets" / "samples" / category / filename
    return Image.open(path).convert("RGB")


@pytest.mark.parametrize("category", ("pcb1", "pcb2", "pcb3"))
def test_identical_reference_has_no_significant_change(category):
    reference = _image(category, "reference.jpg")
    result = inspect(reference, reference.copy(), DetectorConfig())
    assert result.decision == "No significant change"
    assert result.score == 0.0
    assert result.region_count == 0
    assert result.overlay_rgb.shape == result.reference_rgb.shape


@pytest.mark.parametrize("category", ("pcb1", "pcb2", "pcb3"))
def test_bundled_defect_is_detected(category):
    result = inspect(
        _image(category, "reference.jpg"),
        _image(category, "defective.jpg"),
        DetectorConfig(),
    )
    assert result.decision == "Anomaly detected"
    assert result.score >= result.threshold
    assert result.region_count >= 1
    assert 0.0 <= result.alignment_confidence <= 1.0
    ground_truth = align_binary_mask(
        _image(category, "ground_truth.jpg"),
        result.homography,
        result.reference_rgb.shape[:2],
    )
    overlap = binary_overlap(result.anomaly_mask, ground_truth)
    assert overlap["iou"] >= 0.35
    assert overlap["recall"] >= 0.75


def test_invalid_detector_settings_are_rejected():
    with pytest.raises(ValueError):
        DetectorConfig(sensitivity=101)
