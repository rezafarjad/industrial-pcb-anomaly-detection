"""Registration-based visual inspection for aligned PCB photographs.

This detector is deliberately model-free. It compares a test photograph with a
known-good reference after geometric and photometric alignment, then highlights
statistically unusual local changes. It is useful for a runnable demonstration
and controlled inspection stations where the camera and board pose are stable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import cv2
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class DetectorConfig:
    """Controls the registration and change-detection pipeline."""

    sensitivity: int = 65
    min_region_area: int = 80
    working_width: int = 900
    decision_threshold: float = 20.0

    def __post_init__(self) -> None:
        if not 0 <= self.sensitivity <= 100:
            raise ValueError("sensitivity must be between 0 and 100")
        if self.min_region_area < 1:
            raise ValueError("min_region_area must be positive")
        if self.working_width < 256:
            raise ValueError("working_width must be at least 256")


@dataclass
class InspectionResult:
    """Images and measurements produced by one inspection."""

    decision: str
    score: float
    threshold: float
    anomaly_area_percent: float
    region_count: int
    alignment_method: str
    alignment_confidence: float
    reference_rgb: np.ndarray
    aligned_candidate_rgb: np.ndarray
    heatmap_rgb: np.ndarray
    overlay_rgb: np.ndarray
    anomaly_mask: np.ndarray
    homography: np.ndarray
    regions: list[dict[str, Any]]
    config: DetectorConfig

    def report(self) -> dict[str, Any]:
        """Return a JSON-serializable inspection report."""

        return {
            "decision": self.decision,
            "anomaly_score": round(self.score, 3),
            "decision_threshold": round(self.threshold, 3),
            "anomaly_area_percent": round(self.anomaly_area_percent, 4),
            "region_count": self.region_count,
            "alignment": {
                "method": self.alignment_method,
                "confidence": round(self.alignment_confidence, 4),
            },
            "regions": self.regions,
            "settings": asdict(self.config),
        }


def _as_rgb_array(image: Image.Image | np.ndarray) -> np.ndarray:
    if isinstance(image, Image.Image):
        array = np.asarray(image.convert("RGB"))
    else:
        array = np.asarray(image)
        if array.ndim == 2:
            array = cv2.cvtColor(array.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        elif array.ndim != 3 or array.shape[2] not in (3, 4):
            raise ValueError("image array must be grayscale, RGB, or RGBA")
        elif array.shape[2] == 4:
            array = cv2.cvtColor(array.astype(np.uint8), cv2.COLOR_RGBA2RGB)
    return np.ascontiguousarray(array.astype(np.uint8))


def _resize_reference(reference_rgb: np.ndarray, width: int) -> np.ndarray:
    height, original_width = reference_rgb.shape[:2]
    scale = min(1.0, width / float(original_width))
    if scale == 1.0:
        return reference_rgb.copy()
    target = (max(1, round(original_width * scale)), max(1, round(height * scale)))
    return cv2.resize(reference_rgb, target, interpolation=cv2.INTER_AREA)


def _resize_candidate(candidate_rgb: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    height, width = shape
    interpolation = (
        cv2.INTER_AREA
        if candidate_rgb.shape[0] > height or candidate_rgb.shape[1] > width
        else cv2.INTER_CUBIC
    )
    return cv2.resize(candidate_rgb, (width, height), interpolation=interpolation)


def _valid_homography(matrix: np.ndarray, width: int, height: int) -> bool:
    if matrix is None or not np.isfinite(matrix).all():
        return False
    corners = np.float32(
        [[[0, 0]], [[width - 1, 0]], [[width - 1, height - 1]], [[0, height - 1]]]
    )
    transformed = cv2.perspectiveTransform(corners, matrix).reshape(-1, 2)
    area = abs(float(cv2.contourArea(transformed.astype(np.float32))))
    reference_area = float(width * height)
    return 0.25 * reference_area <= area <= 4.0 * reference_area


def _orb_alignment(
    reference_rgb: np.ndarray, candidate_rgb: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str, float]:
    """Warp the candidate onto the reference with ORB and RANSAC."""

    height, width = reference_rgb.shape[:2]
    reference_gray = cv2.cvtColor(reference_rgb, cv2.COLOR_RGB2GRAY)
    candidate_gray = cv2.cvtColor(candidate_rgb, cv2.COLOR_RGB2GRAY)

    orb = cv2.ORB_create(
        nfeatures=5000,
        scaleFactor=1.2,
        nlevels=8,
        edgeThreshold=19,
        fastThreshold=10,
    )
    reference_points, reference_descriptors = orb.detectAndCompute(
        reference_gray, None
    )
    candidate_points, candidate_descriptors = orb.detectAndCompute(
        candidate_gray, None
    )

    identity = np.eye(3, dtype=np.float64)
    full_mask = np.full((height, width), 255, dtype=np.uint8)
    if (
        reference_descriptors is None
        or candidate_descriptors is None
        or len(reference_points) < 10
        or len(candidate_points) < 10
    ):
        return candidate_rgb, full_mask, identity, "resize fallback", 0.0

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    pairs = matcher.knnMatch(candidate_descriptors, reference_descriptors, k=2)
    matches = [
        first
        for first, second in pairs
        if first.distance < 0.78 * second.distance
    ]
    if len(matches) < 10:
        return candidate_rgb, full_mask, identity, "resize fallback", 0.0

    source = np.float32(
        [candidate_points[match.queryIdx].pt for match in matches]
    ).reshape(-1, 1, 2)
    destination = np.float32(
        [reference_points[match.trainIdx].pt for match in matches]
    ).reshape(-1, 1, 2)
    matrix, inliers = cv2.findHomography(
        source, destination, cv2.RANSAC, ransacReprojThreshold=4.0
    )
    if (
        matrix is None
        or inliers is None
        or int(inliers.sum()) < 8
        or not _valid_homography(matrix, width, height)
    ):
        return candidate_rgb, full_mask, identity, "resize fallback", 0.0

    aligned = cv2.warpPerspective(
        candidate_rgb,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
    )
    valid = cv2.warpPerspective(
        full_mask,
        matrix,
        (width, height),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    inlier_ratio = float(inliers.mean())
    match_factor = min(1.0, len(matches) / 80.0)
    confidence = float(np.clip(inlier_ratio * match_factor, 0.0, 1.0))
    return aligned, valid, matrix, "ORB homography", confidence


def _largest_board_region(reference_rgb: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Estimate a broad board ROI from its contrast with the image border."""

    height, width = reference_rgb.shape[:2]
    lab = cv2.cvtColor(reference_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    border = max(4, round(min(height, width) * 0.035))
    border_pixels = np.concatenate(
        [
            lab[:border].reshape(-1, 3),
            lab[-border:].reshape(-1, 3),
            lab[:, :border].reshape(-1, 3),
            lab[:, -border:].reshape(-1, 3),
        ],
        axis=0,
    )
    background = np.median(border_pixels, axis=0)
    distance = np.linalg.norm(lab - background, axis=2)
    distance_u8 = np.uint8(np.clip(distance * 3.0, 0, 255))
    _, foreground = cv2.threshold(
        distance_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    kernel_size = max(7, round(min(height, width) * 0.025) | 1)
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
    )
    foreground = cv2.morphologyEx(foreground, cv2.MORPH_CLOSE, kernel)

    count, labels, stats, _ = cv2.connectedComponentsWithStats(foreground)
    if count <= 1:
        board = np.full((height, width), 255, dtype=np.uint8)
    else:
        largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        board = np.uint8(labels == largest) * 255
        component_area = int(stats[largest, cv2.CC_STAT_AREA])
        if component_area < height * width * 0.08:
            board[:] = 255
        else:
            dilation = max(5, round(min(height, width) * 0.018) | 1)
            board = cv2.dilate(
                board,
                cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE, (dilation, dilation)
                ),
            )

    margin = max(3, round(min(height, width) * 0.018))
    board[:margin] = 0
    board[-margin:] = 0
    board[:, :margin] = 0
    board[:, -margin:] = 0
    return cv2.bitwise_and(board, valid)


def _normalize_lighting(
    reference_lab: np.ndarray,
    candidate_lab: np.ndarray,
    roi: np.ndarray,
) -> np.ndarray:
    normalized = candidate_lab.copy().astype(np.float32)
    selected = roi > 0
    if int(selected.sum()) < 100:
        return normalized
    for channel in range(3):
        reference_values = reference_lab[..., channel][selected]
        candidate_values = candidate_lab[..., channel][selected]
        reference_median = float(np.median(reference_values))
        candidate_median = float(np.median(candidate_values))
        reference_spread = float(
            np.percentile(reference_values, 90)
            - np.percentile(reference_values, 10)
        )
        candidate_spread = float(
            np.percentile(candidate_values, 90)
            - np.percentile(candidate_values, 10)
        )
        scale = np.clip(
            reference_spread / max(candidate_spread, 1.0), 0.75, 1.25
        )
        normalized[..., channel] = (
            normalized[..., channel] - candidate_median
        ) * scale + reference_median
    return np.clip(normalized, 0, 255)


def _difference_map(
    reference_rgb: np.ndarray,
    candidate_rgb: np.ndarray,
    roi: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    reference_lab = cv2.cvtColor(reference_rgb, cv2.COLOR_RGB2LAB).astype(
        np.float32
    )
    candidate_lab = cv2.cvtColor(candidate_rgb, cv2.COLOR_RGB2LAB).astype(
        np.float32
    )
    candidate_lab = _normalize_lighting(reference_lab, candidate_lab, roi)

    reference_blur = cv2.GaussianBlur(reference_lab, (0, 0), sigmaX=1.2)
    candidate_blur = cv2.GaussianBlur(candidate_lab, (0, 0), sigmaX=1.2)
    channel_difference = reference_blur - candidate_blur
    color_difference = np.sqrt(
        channel_difference[..., 0] ** 2
        + 0.55 * channel_difference[..., 1] ** 2
        + 0.55 * channel_difference[..., 2] ** 2
    )

    reference_gray = cv2.cvtColor(reference_rgb, cv2.COLOR_RGB2GRAY)
    candidate_gray = cv2.cvtColor(
        np.uint8(candidate_lab), cv2.COLOR_LAB2RGB
    )
    candidate_gray = cv2.cvtColor(candidate_gray, cv2.COLOR_RGB2GRAY)
    reference_gradient = cv2.magnitude(
        cv2.Sobel(reference_gray, cv2.CV_32F, 1, 0, ksize=3),
        cv2.Sobel(reference_gray, cv2.CV_32F, 0, 1, ksize=3),
    )
    candidate_gradient = cv2.magnitude(
        cv2.Sobel(candidate_gray, cv2.CV_32F, 1, 0, ksize=3),
        cv2.Sobel(candidate_gray, cv2.CV_32F, 0, 1, ksize=3),
    )
    gradient_difference = cv2.absdiff(
        reference_gradient, candidate_gradient
    )
    raw = 0.78 * color_difference + 0.22 * gradient_difference
    raw = cv2.GaussianBlur(raw.astype(np.float32), (0, 0), sigmaX=1.6)

    selected = raw[roi > 0]
    if selected.size == 0:
        selected = raw.ravel()
    median = float(np.median(selected))
    mad = float(np.median(np.abs(selected - median)))
    robust_scale = max(1.4826 * mad, 1.75)
    z_score = np.maximum((raw - median) / robust_scale, 0.0)
    z_score[roi == 0] = 0.0
    return raw, z_score


def _filter_regions(
    z_score: np.ndarray,
    roi: np.ndarray,
    config: DetectorConfig,
) -> tuple[np.ndarray, list[dict[str, Any]], float]:
    z_threshold = 9.0 - 0.065 * config.sensitivity
    binary = np.uint8(z_score >= z_threshold) * 255
    binary = cv2.bitwise_and(binary, roi)
    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
    )
    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)),
    )

    roi_area = max(int(np.count_nonzero(roi)), 1)
    scaled_minimum = round(roi_area * 0.00008)
    minimum_area = max(config.min_region_area, scaled_minimum)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary)
    filtered = np.zeros_like(binary)
    regions: list[dict[str, Any]] = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < minimum_area:
            continue
        x = int(stats[label, cv2.CC_STAT_LEFT])
        y = int(stats[label, cv2.CC_STAT_TOP])
        width = int(stats[label, cv2.CC_STAT_WIDTH])
        height = int(stats[label, cv2.CC_STAT_HEIGHT])
        region = labels == label
        filtered[region] = 255
        regions.append(
            {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "area_pixels": area,
                "peak_change": round(float(z_score[region].max()), 3),
            }
        )
    regions.sort(key=lambda item: item["area_pixels"], reverse=True)
    return filtered, regions, z_threshold


def _visualizations(
    candidate_rgb: np.ndarray,
    z_score: np.ndarray,
    anomaly_mask: np.ndarray,
    regions: list[dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray]:
    heat_intensity = np.uint8(np.clip(z_score / 12.0, 0.0, 1.0) * 255)
    heat_bgr = cv2.applyColorMap(heat_intensity, cv2.COLORMAP_TURBO)
    heat_rgb = cv2.cvtColor(heat_bgr, cv2.COLOR_BGR2RGB)
    muted_heat = candidate_rgb.copy()
    active = anomaly_mask > 0
    muted_heat[active] = heat_rgb[active]
    overlay = cv2.addWeighted(candidate_rgb, 0.66, muted_heat, 0.34, 0)
    for region in regions:
        x, y = region["x"], region["y"]
        right = x + region["width"]
        bottom = y + region["height"]
        cv2.rectangle(overlay, (x, y), (right, bottom), (255, 54, 72), 3)
    return heat_rgb, overlay


def inspect(
    reference: Image.Image | np.ndarray,
    candidate: Image.Image | np.ndarray,
    config: DetectorConfig | None = None,
) -> InspectionResult:
    """Compare ``candidate`` with a known-good ``reference`` image."""

    active_config = config or DetectorConfig()
    reference_rgb = _resize_reference(
        _as_rgb_array(reference), active_config.working_width
    )
    height, width = reference_rgb.shape[:2]
    candidate_rgb = _resize_candidate(
        _as_rgb_array(candidate), (height, width)
    )
    (
        aligned,
        valid,
        homography,
        alignment_method,
        alignment_confidence,
    ) = _orb_alignment(reference_rgb, candidate_rgb)
    roi = _largest_board_region(reference_rgb, valid)
    _, z_score = _difference_map(reference_rgb, aligned, roi)
    anomaly_mask, regions, _ = _filter_regions(z_score, roi, active_config)

    roi_area = max(int(np.count_nonzero(roi)), 1)
    anomaly_area_percent = (
        100.0 * float(np.count_nonzero(anomaly_mask)) / roi_area
    )
    if regions:
        region_signal = float(
            np.percentile(z_score[anomaly_mask > 0], 90)
        )
        score = float(
            np.clip(
                (region_signal - 2.0) * 7.0
                + np.sqrt(anomaly_area_percent) * 9.0,
                0.0,
                100.0,
            )
        )
    else:
        score = 0.0
    decision = (
        "Anomaly detected"
        if regions and score >= active_config.decision_threshold
        else "No significant change"
    )
    heatmap, overlay = _visualizations(
        aligned, z_score, anomaly_mask, regions
    )
    return InspectionResult(
        decision=decision,
        score=score,
        threshold=active_config.decision_threshold,
        anomaly_area_percent=anomaly_area_percent,
        region_count=len(regions),
        alignment_method=alignment_method,
        alignment_confidence=alignment_confidence,
        reference_rgb=reference_rgb,
        aligned_candidate_rgb=aligned,
        heatmap_rgb=heatmap,
        overlay_rgb=overlay,
        anomaly_mask=anomaly_mask,
        homography=homography,
        regions=regions,
        config=active_config,
    )
