import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_app_compiles():
    app = ROOT / "streamlit_app.py"
    compile(app.read_text(encoding="utf-8"), str(app), "exec")


def test_notebook_is_valid_json():
    notebook = json.loads(
        (
            ROOT
            / "notebooks"
            / "industrial_pcb_anomaly_detection_local.ipynb"
        ).read_text(encoding="utf-8")
    )
    assert notebook["nbformat"] == 4
    text = "\\n".join(
        "".join(cell["source"]) for cell in notebook["cells"]
    )
    assert "Google Drive" not in text
    assert 'CATEGORIES = ["pcb1", "pcb2", "pcb3"]' in text
