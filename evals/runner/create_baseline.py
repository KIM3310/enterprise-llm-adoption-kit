"""Baseline report generator that runs the eval suite and saves the output.

Executes ``run_eval`` to produce a latest report, then copies it to the
specified baseline path for use by the eval gate.
"""

import argparse
import shutil
from pathlib import Path

from run_eval import run_eval


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write baseline JSON report",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Reuse run_eval to generate latest_report.* then copy to baseline.
    run_eval(dataset_path, args.base_url, Path("/dev/null"))

    reports_dir = Path("evals/reports")
    latest_json = reports_dir / "latest_report.json"
    latest_md = reports_dir / "latest_report.md"

    if not latest_json.exists():
        raise SystemExit("latest_report.json not found; run_eval failed")

    shutil.copyfile(latest_json, output_path)
    if latest_md.exists():
        baseline_md = output_path.with_suffix(".md")
        shutil.copyfile(latest_md, baseline_md)

    print(f"Baseline report written: {output_path}")


if __name__ == "__main__":
    main()
