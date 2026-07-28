# Reproducible results

`python scripts/validate_samples.py` writes `demo_validation.json` from the
currently bundled samples and detector settings. It also writes one annotated
`*_demo_overlay.png` per PCB category so the localization can be inspected
visually.

The optional PatchCore notebook may also write benchmark tables and heatmaps to
this directory. Large per-image prediction arrays are ignored by Git. No
benchmark numbers should be added to the repository unless they were produced
by the corresponding committed code and configuration.
