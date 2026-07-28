# Industrial PCB Anomaly Detection

Local-first unsupervised visual inspection for printed circuit boards
using PatchCore, multi-scale ImageNet ResNet50 features, and
category-specific PCA.

## What this repository demonstrates

- Training with defect-free images only
- Multi-scale `layer2` and `layer3` patch representations
- Per-category PCA retaining 95% explained variance
- Approximate k-center PatchCore coreset selection
- Five-nearest-neighbor baseline
- Pixel heatmaps and good/defective overlays
- Image AUROC, pixel AUROC, AUPRO@0.30, FNR, and latency
- A standalone Streamlit inspection interface

## Dataset

The notebook downloads only `pcb1`, `pcb2`, and `pcb3` from the
[VisA industrial anomaly dataset](https://github.com/amazon-science/spot-diff).
Data is stored under `data/` on the local machine and is excluded from
Git. VisA is released under CC BY 4.0.

## Repository structure

```text
.
├── notebooks/
│   └── industrial_pcb_anomaly_detection_local.ipynb
├── streamlit_app.py
├── requirements.txt
├── requirements-train.txt
├── artifacts/
├── results/
├── assets/
├── scripts/check_project.py
└── tests/test_repository.py
```

## Local setup

```bash
git clone https://github.com/rezafarjad/industrial-pcb-anomaly-detection
python -m venv .venv
python -m venv .venv
```

Activate the environment:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install training dependencies and open Jupyter:

```bash
pip install -r requirements-train.txt
jupyter lab
```

Open `notebooks/industrial_pcb_anomaly_detection_local.ipynb` and run
Phases 1-8. Data and feature caches remain local. The notebook exports
the compact inference models into `artifacts/`.

## Run the application

After the notebook has generated the three category artifacts:

```bash
streamlit run streamlit_app.py
```

Streamlit prints a local browser URL, normally
`http://localhost:8501`.

## Evaluation

Phase 7 creates the real benchmark table at `results/summary.csv`.
Copy those values into this section after completing the full run.
Results are intentionally not fabricated in the source repository.

## Free public deployment

Push the completed repository to GitHub, then create a public app at
[Streamlit Community Cloud](https://share.streamlit.io) using:

- Repository: your GitHub repository
- Branch: `main`
- Entry point: `streamlit_app.py`

## Limitations

- The correct PCB category must be selected.
- Free cloud hosting performs inference on CPU.
- Subtle defects can produce false negatives.
- Thresholds require recalibration for a real production line.
- This is a portfolio demonstrator, not a certified inspection system.
