# Validation

## What is validated

The repository contains three paired PCB demonstrations derived from VisA.
Each pair includes an anomalous image, its ground-truth mask, and a disclosed
reference reconstructed by inpainting the annotated region.

`python scripts/validate_samples.py` checks two behaviors for every category:

1. comparing the reference with itself produces `No significant change`;
2. comparing the paired anomalous image produces `Anomaly detected`.

It also measures localization overlap against the ground-truth mask after
applying the detector's alignment transform.

| Category | IoU | Precision | Recall |
| --- | ---: | ---: | ---: |
| PCB1 | 0.558 | 0.601 | 0.887 |
| PCB2 | 0.526 | 0.526 | 1.000 |
| PCB3 | 0.440 | 0.489 | 0.814 |

## Reproduce

```bash
python -m pip install -r requirements-dev.txt
python scripts/validate_samples.py
```

Outputs:

- `results/demo_validation.json`
- `results/pcb1_demo_overlay.png`
- `results/pcb2_demo_overlay.png`
- `results/pcb3_demo_overlay.png`

## Interpretation

This is a deterministic smoke validation, not a dataset benchmark. The
references were reconstructed from the paired annotations so that localization
can be checked without distributing trained model artifacts.

The smoke validation supports claims about:

- application wiring;
- alignment and localization execution;
- report generation;
- known-good self-comparison;
- overlap on the three bundled examples.

It does **not** establish production sensitivity, specificity, robustness to a
new camera, or performance on the complete VisA dataset.

## Production validation checklist

Before operational use:

- collect representative known-good and defective boards from the actual
  station;
- hold out validation data from threshold calibration;
- measure false-negative and false-positive rates by defect type;
- include camera drift, lighting drift, reflections, and normal board
  tolerances;
- define a minimum acceptable alignment-confidence policy;
- validate operator review and escalation procedures;
- version the reference images, settings, code, and evaluation results
  together.
