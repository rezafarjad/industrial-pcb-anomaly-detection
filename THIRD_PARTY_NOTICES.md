# Third-party data notice

## VisA

The files under `assets/samples/` are a small subset of the Visual Anomaly
(VisA) dataset:

- Project: Spot-the-Difference Self-Supervised Pre-training for Anomaly
  Detection and Segmentation
- Authors: Yang Zou, Jongheon Jeong, Latha Pemula, Dongqing Zhang, and Onkar
  Dabeer
- Source: https://github.com/amazon-science/spot-diff
- License: Creative Commons Attribution 4.0 International (CC BY 4.0)

The samples were obtained from the public `BrachioLab/visa` dataset packaging
on Hugging Face. Each PCB category contains one anomalous test image, its
ground-truth mask, and a derived demonstration reference. The reference was
reconstructed with OpenCV TELEA inpainting over a dilated copy of the
ground-truth region so the app has a deterministic paired example. It is not an
original normal VisA image. Exact split rows and parameters are recorded in
`assets/samples/manifest.json`.
