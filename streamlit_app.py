"""Interactive PCB reference-comparison application."""

from __future__ import annotations

import io
import json
from pathlib import Path

import streamlit as st
from PIL import Image

from pcb_anomaly import DetectorConfig, inspect
from pcb_anomaly.samples import SAMPLES, validate_samples

ROOT = Path(__file__).resolve().parent


def _open_image(source: Path | bytes) -> Image.Image:
    if isinstance(source, Path):
        return Image.open(source).convert("RGB")
    return Image.open(io.BytesIO(source)).convert("RGB")


def _png_bytes(image_array) -> bytes:
    buffer = io.BytesIO()
    Image.fromarray(image_array).save(buffer, format="PNG")
    return buffer.getvalue()


def _header() -> None:
    st.title("PCB Visual Inspector")
    st.caption(
        "Compare a board with a known-good reference, align the photographs, "
        "and localize unexpected visual changes."
    )


def _sidebar() -> tuple[str, DetectorConfig]:
    with st.sidebar:
        st.header("Inspection setup")
        source = st.radio(
            "Image source",
            ("Built-in demonstration", "Upload my own images"),
        )
        st.divider()
        st.subheader("Detector settings")
        sensitivity = st.slider(
            "Sensitivity",
            min_value=0,
            max_value=100,
            value=65,
            help="Higher values flag smaller or lower-contrast changes.",
        )
        min_region_area = st.slider(
            "Minimum changed region",
            min_value=20,
            max_value=500,
            value=80,
            step=10,
            help="Suppresses tiny isolated pixels and camera noise.",
        )
        st.caption(
            "Best results need the same PCB type, camera angle, lighting, "
            "and fixture position for both photographs."
        )
    return source, DetectorConfig(
        sensitivity=sensitivity,
        min_region_area=min_region_area,
    )


def _demo_inputs() -> tuple[Image.Image | None, Image.Image | None, Path | None]:
    missing = validate_samples()
    if missing:
        st.error("Demonstration images are missing: " + ", ".join(missing))
        return None, None, None

    control_one, control_two = st.columns(2)
    with control_one:
        category = st.selectbox("Demonstration board", tuple(SAMPLES))
    with control_two:
        sample_type = st.selectbox(
            "Test case",
            ("Defective sample", "Known-good sanity check"),
        )
    sample = SAMPLES[category]
    reference = _open_image(sample.reference)
    candidate = (
        _open_image(sample.defective)
        if sample_type == "Defective sample"
        else reference.copy()
    )
    ground_truth = (
        sample.ground_truth if sample_type == "Defective sample" else None
    )
    st.info(
        "This paired VisA demonstration uses a reference reconstructed from "
        "the annotated defect region, solely to make localization easy to "
        "verify. For real inspection, upload a genuine known-good photograph. "
        "The sanity check compares the reference with itself."
    )
    return reference, candidate, ground_truth


def _upload_inputs() -> tuple[Image.Image | None, Image.Image | None, None]:
    reference_file = st.file_uploader(
        "1. Upload a known-good reference PCB",
        type=("png", "jpg", "jpeg", "bmp", "tif", "tiff"),
        key="reference",
    )
    candidate_file = st.file_uploader(
        "2. Upload the PCB to inspect",
        type=("png", "jpg", "jpeg", "bmp", "tif", "tiff"),
        key="candidate",
    )
    if reference_file is None or candidate_file is None:
        st.info("Upload both images to enable inspection.")
        return None, None, None
    return (
        _open_image(reference_file.getvalue()),
        _open_image(candidate_file.getvalue()),
        None,
    )


def _show_inputs(reference: Image.Image, candidate: Image.Image) -> None:
    reference_column, candidate_column = st.columns(2)
    with reference_column:
        st.subheader("Known-good reference")
        st.image(reference, use_container_width=True)
    with candidate_column:
        st.subheader("Board under inspection")
        st.image(candidate, use_container_width=True)


def _show_result(result, ground_truth: Path | None) -> None:
    st.divider()
    if result.decision == "Anomaly detected":
        st.error("Anomaly detected — review the highlighted regions.")
    else:
        st.success("No significant change was detected.")

    score_column, area_column, region_column, alignment_column = st.columns(4)
    score_column.metric("Anomaly score", f"{result.score:.1f} / 100")
    area_column.metric(
        "Changed board area", f"{result.anomaly_area_percent:.3f}%"
    )
    region_column.metric("Review regions", result.region_count)
    alignment_column.metric(
        "Alignment confidence", f"{result.alignment_confidence:.0%}"
    )

    output_column, aligned_column = st.columns(2)
    with output_column:
        st.subheader("Inspection overlay")
        st.image(result.overlay_rgb, use_container_width=True)
    with aligned_column:
        st.subheader("Aligned test image")
        st.image(result.aligned_candidate_rgb, use_container_width=True)

    if ground_truth is not None:
        with st.expander("Show dataset ground-truth mask"):
            st.image(
                _open_image(ground_truth),
                caption=(
                    "VisA annotation in the original test-image coordinates; "
                    "the detector overlay is shown after alignment."
                ),
                use_container_width=True,
            )

    report = json.dumps(result.report(), indent=2)
    report_column, image_column = st.columns(2)
    report_column.download_button(
        "Download inspection report",
        data=report,
        file_name="pcb_inspection_report.json",
        mime="application/json",
        use_container_width=True,
    )
    image_column.download_button(
        "Download annotated image",
        data=_png_bytes(result.overlay_rgb),
        file_name="pcb_inspection_overlay.png",
        mime="image/png",
        use_container_width=True,
    )

    with st.expander("Technical details"):
        st.json(result.report())
        st.caption(
            "The runnable detector uses ORB/RANSAC image registration followed "
            "by robust color and edge-change analysis. It does not require a "
            "trained model. The optional research notebook explores PatchCore."
        )


def main() -> None:
    st.set_page_config(
        page_title="PCB Visual Inspector",
        page_icon="🔍",
        layout="wide",
    )
    _header()
    source, config = _sidebar()
    if source == "Built-in demonstration":
        reference, candidate, ground_truth = _demo_inputs()
    else:
        reference, candidate, ground_truth = _upload_inputs()

    if reference is None or candidate is None:
        return
    _show_inputs(reference, candidate)
    if st.button(
        "Inspect board",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner("Aligning images and measuring visual changes…"):
            result = inspect(reference, candidate, config)
        _show_result(result, ground_truth)

    st.divider()
    st.caption(
        "Decision-support demonstrator only. Validate thresholds on your own "
        "production images before operational use."
    )


if __name__ == "__main__":
    main()
