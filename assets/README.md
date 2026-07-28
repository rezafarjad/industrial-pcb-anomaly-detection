# Application assets

`samples/pcb1`, `samples/pcb2`, and `samples/pcb3` each contain:

- `reference.jpg`: a demonstration baseline reconstructed by inpainting the
  annotated defect region;
- `defective.jpg`: an anomalous VisA test image;
- `ground_truth.jpg`: the dataset annotation for that test image.

These files make the app demonstrable immediately after cloning. They are
attributed in the repository's `THIRD_PARTY_NOTICES.md` and remain subject to
the VisA CC BY 4.0 license. `samples/manifest.json` records the exact dataset
rows and reference-generation method. The reconstructed references are
demonstration fixtures, not original VisA normal images or production-quality
golden samples.
