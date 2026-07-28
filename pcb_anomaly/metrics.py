"""Small, dependency-light metrics used by bundled-sample validation."""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image


def align_binary_mask(
    mask: Image.Image | np.ndarray,
    homography: np.ndarray,
    target_shape: tuple[int, int],
) -> np.ndarray:
    """Resize and warp a candidate-coordinate mask into reference coordinates."""

    if isinstance(mask, Image.Image):
        array = np.asarray(mask.convert("L"))
    else:
        array = np.asarray(mask)
        if array.ndim == 3:
            array = cv2.cvtColor(array.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    binary = np.uint8(array > 127)
    height, width = target_shape
    resized = cv2.resize(
        binary,
        (width, height),
        interpolation=cv2.INTER_NEAREST,
    )
    return (
        cv2.warpPerspective(
            resized,
            homography,
            (width, height),
            flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )
        > 0
    )


def binary_overlap(
    prediction: np.ndarray,
    ground_truth: np.ndarray,
) -> dict[str, float | int]:
    """Compute IoU, precision, and recall for two binary masks."""

    predicted = np.asarray(prediction) > 0
    expected = np.asarray(ground_truth) > 0
    if predicted.shape != expected.shape:
        raise ValueError("prediction and ground_truth must have the same shape")

    intersection = int(np.count_nonzero(predicted & expected))
    union = int(np.count_nonzero(predicted | expected))
    predicted_pixels = int(np.count_nonzero(predicted))
    ground_truth_pixels = int(np.count_nonzero(expected))
    return {
        "intersection_pixels": intersection,
        "predicted_pixels": predicted_pixels,
        "ground_truth_pixels": ground_truth_pixels,
        "iou": intersection / max(union, 1),
        "precision": intersection / max(predicted_pixels, 1),
        "recall": intersection / max(ground_truth_pixels, 1),
    }
