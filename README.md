# Industrial PCB Anomaly Detection

A runnable visual-inspection app for printed circuit boards. It aligns a board
photograph with a known-good reference, measures robust color and edge changes,
and marks regions that should be reviewed.

The repository now has two separate paths:

- **Runnable inspector:** works immediately, needs no trained model, and includes
  three small PCB demonstrations.
- **PatchCore research notebook:** an optional, resource-intensive experiment
  using ResNet50 patch features, per-category PCA, and memory-bank scoring.

The distinction is intentional: the app is usable after cloning, while the
research notebook does not pretend that ungenerated model files already exist.

## Start the app on Windows

1. Download the repository ZIP from GitHub and extract it.
2. Double-click **`Start PCB Inspector.bat`**.
3. On the first launch, wait while a private Python environment is created.
   Your browser then opens automatically. Later launches skip installation.

To put it on your desktop, double-click **`Create Desktop Shortcut.bat`** once.
After that, open **PCB Visual Inspector** from the desktop whenever you want.

Python 3.10 or newer is the only prerequisite. Keep the launcher window open
while using the app; closing it stops the local server.

## Start from a terminal

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run streamlit_app.py
```

Linux and macOS users can use:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run streamlit_app.py
```

## Use the inspector

The built-in demonstration is selected when the app opens. Choose PCB1, PCB2,
or PCB3, then inspect either the defective example or the known-good sanity
check.

For your own images:

1. Select **Upload my own images**.
2. Upload a known-good board as the reference.
3. Upload a photograph of the same board type to inspect.
4. Keep the camera, lighting, fixture, and board orientation as consistent as
   possible.
5. Adjust sensitivity only after testing it on representative good and
   defective boards.

The app provides an aligned image, anomaly overlay, review boxes, a JSON report,
and a downloadable annotated PNG.

## How the runnable detector works

1. Resize both images to a common working resolution.
2. Register the test image to the reference with ORB feature matching and a
   RANSAC homography.
3. Estimate the board region and normalize moderate lighting differences.
4. Combine perceptual color differences with local edge changes.
5. Use robust median/MAD statistics and connected-component filtering to
   localize unusual regions.

This model-free method is most appropriate for controlled, approximately
aligned inspection stations. It is not a replacement for production
calibration, a validated learned model, or human review.

## Optional PatchCore experiment

The notebook at
`notebooks/industrial_pcb_anomaly_detection_local.ipynb` explores unsupervised
PatchCore-style inspection on PCB1–PCB3 from VisA. It downloads roughly 730 MB
of category data before caches, needs substantially more disk space during
feature extraction, and is **not required** for the runnable app.

Install the research dependencies with:

```bash
python -m pip install -r requirements-train.txt
jupyter lab
```

Generated data, caches, and large prediction archives stay outside Git. Model
artifacts are not presented as pretrained models until they have actually been
trained and validated.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python scripts/check_project.py
pytest -q
ruff check .
```

The automated tests exercise all three included defective samples, identical
known-good comparisons, repository structure, and Python syntax.

## Repository structure

```text
.
|-- pcb_anomaly/                 # registration and anomaly detector
|-- assets/samples/              # small attributed VisA demonstrations
|-- notebooks/                   # optional PatchCore research path
|-- scripts/                     # validation and Windows launch helpers
|-- tests/                       # behavior and repository tests
|-- streamlit_app.py             # Streamlit interface
|-- Start PCB Inspector.bat      # double-click launcher
`-- Create Desktop Shortcut.bat  # one-time shortcut installer
```

## Dataset attribution

The bundled demonstration images are derived from the
[VisA dataset](https://github.com/amazon-science/spot-diff), released under
CC BY 4.0. Each reference is a clearly disclosed, inpainted reconstruction of
the paired annotated image—not an original normal sample. This makes the
localization demonstrable without implying a trained model or dataset
benchmark. Exact rows and derivation parameters are recorded in
`assets/samples/manifest.json`. See
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Limitations

- It expects the same PCB design in the reference and test image.
- Strong reflections, pose changes, occlusion, or lighting changes can be
  mistaken for defects.
- Sensitivity must be calibrated on images from the real inspection station.
- This is a decision-support demonstrator, not a certified autonomous quality
  control system.
