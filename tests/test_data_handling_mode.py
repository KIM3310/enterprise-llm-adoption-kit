import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_data_handling_enterprise_hashes():
    env = os.environ.copy()
    env["DATA_HANDLING_MODE"] = "enterprise"
    env["PYTHONPATH"] = str(ROOT_DIR / "app/backend")
    code = (
        "from app.audit import build_payload;"
        "print(build_payload('secret','output'))"
    )
    result = subprocess.check_output([sys.executable, "-c", code], env=env, text=True)
    assert "input_hash" in result
    assert "output_hash" in result
    assert "mode': 'enterprise" in result or 'mode\": \"enterprise' in result
