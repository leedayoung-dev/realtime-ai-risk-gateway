"""Run sample-prompt benchmark and print JSON."""

from __future__ import annotations

import json

from src.evaluation.runner import run_benchmark


def main() -> None:
    report = run_benchmark()
    print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
