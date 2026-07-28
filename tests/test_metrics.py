import numpy as np
import pytest

from pcb_anomaly.metrics import binary_overlap


def test_binary_overlap_reports_expected_values():
    prediction = np.array([[1, 1], [0, 0]], dtype=np.uint8)
    ground_truth = np.array([[0, 1], [1, 0]], dtype=np.uint8)

    metrics = binary_overlap(prediction, ground_truth)

    assert metrics["intersection_pixels"] == 1
    assert metrics["predicted_pixels"] == 2
    assert metrics["ground_truth_pixels"] == 2
    assert metrics["iou"] == pytest.approx(1 / 3)
    assert metrics["precision"] == pytest.approx(1 / 2)
    assert metrics["recall"] == pytest.approx(1 / 2)


def test_binary_overlap_rejects_different_shapes():
    with pytest.raises(ValueError):
        binary_overlap(np.zeros((2, 2)), np.zeros((3, 3)))
