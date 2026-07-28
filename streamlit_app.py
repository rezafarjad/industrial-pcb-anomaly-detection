from __future__ import annotations

import json
from pathlib import Path

import cv2
import joblib
import numpy as np
import streamlit as st
import torch
import torch.nn.functional as F
from PIL import Image
from sklearn.neighbors import NearestNeighbors
from torchvision import models, transforms


ROOT = Path(__file__).resolve().parent
ARTIFACT_ROOT = ROOT / "artifacts"
CATEGORIES = ["pcb1", "pcb2", "pcb3"]
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

PREPROCESS = transforms.Compose(
    [
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


class ResNetPatchExtractor(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        network = models.resnet50(
            weights=models.ResNet50_Weights.IMAGENET1K_V2
        )
        self.stem = torch.nn.Sequential(
            network.conv1,
            network.bn1,
            network.relu,
            network.maxpool,
            network.layer1,
        )
        self.layer2 = network.layer2
        self.layer3 = network.layer3
        self.eval()
        for parameter in self.parameters():
            parameter.requires_grad_(False)

    @torch.inference_mode()
    def forward(
        self, batch: torch.Tensor, patch_stride: int = 2
    ) -> torch.Tensor:
        x = self.stem(batch)
        raw_layer2 = self.layer2(x)
        raw_layer3 = self.layer3(raw_layer2)
        layer2 = F.avg_pool2d(
            raw_layer2, kernel_size=3, stride=1, padding=1
        )
        layer3 = F.avg_pool2d(
            raw_layer3, kernel_size=3, stride=1, padding=1
        )
        layer3 = F.interpolate(
            layer3,
            size=layer2.shape[-2:],
            mode="bilinear",
            align_corners=False,
        )
        patches = torch.cat([layer2, layer3], dim=1)
        patches = patches[:, :, ::patch_stride, ::patch_stride]
        return patches.permute(0, 2, 3, 1).contiguous()


@st.cache_resource(show_spinner="Loading ImageNet ResNet50…")
def load_backbone() -> ResNetPatchExtractor:
    return ResNetPatchExtractor().to(DEVICE)


@st.cache_resource(show_spinner=False)
def load_category_bundle(category: str) -> dict:
    category_dir = ARTIFACT_ROOT / category
    required = {
        "PCA": category_dir / "pca.joblib",
        "PatchCore memory": category_dir / "patchcore_memory.npy",
        "configuration": category_dir / "config.json",
    }
    missing = [
        f"{label}: {path.relative_to(ROOT)}"
        for label, path in required.items()
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError(
            "Exported model files are missing:\n" + "\n".join(missing)
        )

    memory = np.ascontiguousarray(
        np.load(required["PatchCore memory"]).astype(np.float32)
    )
    index = NearestNeighbors(n_neighbors=1, metric="euclidean")
    index.fit(memory)
    return {
        "pca": joblib.load(required["PCA"]),
        "index": index,
        "config": json.loads(required["configuration"].read_text()),
    }


def overlay_heatmap(
    image: Image.Image, anomaly_map: np.ndarray
) -> Image.Image:
    rgb = np.asarray(
        image.convert("RGB").resize((256, 256)), dtype=np.uint8
    )
    normalized = anomaly_map - float(anomaly_map.min())
    normalized /= float(normalized.max()) + 1e-8
    heatmap = cv2.applyColorMap(
        np.uint8(np.clip(normalized, 0, 1) * 255),
        cv2.COLORMAP_JET,
    )
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    return Image.fromarray(
        cv2.addWeighted(rgb, 0.58, heatmap, 0.42, 0)
    )


@torch.inference_mode()
def predict(image: Image.Image, category: str) -> tuple:
    backbone = load_backbone()
    bundle = load_category_bundle(category)
    config = bundle["config"]

    batch = PREPROCESS(image.convert("RGB")).unsqueeze(0).to(DEVICE)
    feature_grid = backbone(
        batch, patch_stride=int(config.get("patch_stride", 2))
    )[0].cpu().numpy()
    height, width, channels = feature_grid.shape

    reduced = bundle["pca"].transform(
        feature_grid.reshape(-1, channels)
    )
    distances, _ = bundle["index"].kneighbors(
        np.ascontiguousarray(reduced.astype(np.float32)),
        n_neighbors=1,
    )
    patch_scores = distances[:, 0]
    score = float(patch_scores.max())
    threshold = float(config["thresholds"]["patchcore"])
    decision = "Defective" if score >= threshold else "Good"

    anomaly_map = cv2.resize(
        patch_scores.reshape(height, width),
        (256, 256),
        interpolation=cv2.INTER_CUBIC,
    )
    sigma = float(config.get("gaussian_sigma", 4.0))
    anomaly_map = cv2.GaussianBlur(
        anomaly_map, (0, 0), sigmaX=sigma, sigmaY=sigma
    )
    return score, threshold, decision, overlay_heatmap(image, anomaly_map)


st.set_page_config(
    page_title="PCB Anomaly Detection",
    page_icon="🔍",
    layout="wide",
)

st.title("Industrial PCB Anomaly Detection")
st.caption(
    "Unsupervised PatchCore inspection using ImageNet ResNet50 layer2/layer3 "
    "features and category-specific PCA memory banks."
)

with st.sidebar:
    st.header("Inspection settings")
    category = st.selectbox("PCB category", CATEGORIES)
    st.markdown(
        "**Model:** PatchCore  \n"
        "**Backbone:** ResNet50 IMAGENET1K_V2  \n"
        "**Training data:** defect-free images only"
    )

uploaded_file = st.file_uploader(
    "Upload a PCB inspection image",
    type=["png", "jpg", "jpeg", "bmp", "tif", "tiff"],
)

if uploaded_file is None:
    st.info("Upload an image and choose its matching PCB category.")
else:
    inspection_image = Image.open(uploaded_file).convert("RGB")
    input_column, output_column = st.columns(2)
    with input_column:
        st.subheader("Input")
        st.image(inspection_image, use_container_width=True)

    if st.button("Run inspection", type="primary", use_container_width=True):
        try:
            with st.spinner("Extracting patch features and scoring anomalies…"):
                score, threshold, decision, overlay = predict(
                    inspection_image, category
                )
            with output_column:
                st.subheader("PatchCore localization")
                st.image(overlay, use_container_width=True)

            score_column, threshold_column, decision_column = st.columns(3)
            score_column.metric("Anomaly score", f"{score:.4f}")
            threshold_column.metric("Decision threshold", f"{threshold:.4f}")
            decision_column.metric("Classification", decision)

            if decision == "Defective":
                st.error(
                    "Defect suspected. Review the highlighted region before "
                    "accepting the component."
                )
            else:
                st.success(
                    "No anomaly exceeded the calibrated category threshold."
                )
            st.caption(
                "This portfolio demonstrator supports human inspection; it is "
                "not certified for autonomous production decisions."
            )
        except FileNotFoundError as error:
            st.error(str(error))
            st.info(
                "Copy the exported Colab artifacts into artifacts/pcb1, "
                "artifacts/pcb2, and artifacts/pcb3 before deployment."
            )
        except Exception as error:
            st.exception(error)
