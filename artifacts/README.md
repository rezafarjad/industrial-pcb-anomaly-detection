# Optional learned-model artifacts

The runnable reference-comparison app does not need files in this directory.

The optional PatchCore notebook can generate category-specific PCA models,
memory banks, and calibration metadata here. Those files are deliberately not
represented as pretrained artifacts in the source repository: they should be
added only after a complete, reproducible training and validation run.

Expected research output per category:

```text
artifacts/<category>/
|-- pca.joblib
|-- patchcore_memory.npy
|-- knn_memory.npy
`-- config.json
```
