# Optional PatchCore research path

The notebook
`notebooks/industrial_pcb_anomaly_detection_local.ipynb` explores a separate
unsupervised research pipeline:

- ImageNet ResNet50 `layer2` and `layer3` patch features;
- per-category PCA retaining 95% explained variance;
- approximate k-center PatchCore coreset selection;
- five-nearest-neighbor comparison baseline;
- image AUROC, pixel AUROC, AUPRO@0.30, false-negative rate, and latency.

It is intentionally not a runtime dependency of the Streamlit application.

## Setup

Start from the repository root:

```bash
python -m venv .venv
python -m pip install -r requirements-train.txt
jupyter lab
```

Open the notebook and execute phases in order.

## Resource expectations

The selected VisA PCB category archives are approximately 730 MB before
decoded images and feature caches. Full feature extraction and PCA require
substantially more temporary disk and memory. A CUDA GPU is recommended for a
complete run.

## Generated files

The notebook may create:

```text
data/                 # decoded local dataset, ignored
.cache/features/      # extracted feature grids, ignored
artifacts/<category>/ # PCA and memory-bank research outputs
results/              # tables, plots, heatmaps, and prediction archives
```

Do not commit a trained artifact merely because the notebook produced a file.
Record the data version, configuration, validation results, and artifact hash.
Large files should use a release asset or an artifact registry rather than
ordinary Git history.

## Reproducibility boundary

The source repository does not claim pretrained PatchCore performance. Results
must come from an executed, validated run and should never be copied from
unrelated experiments or fabricated to complete a table.
