"""Run early detection evaluation and print JSON report."""

from __future__ import annotations

import json
import sys

from src.evaluation.early_detection import evaluate_early_detection


def main() -> None:
    threshold = float(sys.argv[1]) if len(sys.argv) > 1 else 50.0
    report = evaluate_early_detection(threshold=threshold)
    print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
