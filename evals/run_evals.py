"""Checks extraction against the correct answers in labels.json.

Step 2 is done when the amount and due date are correct on at least 8 of 10 documents.

How to add a document:
  1. Put the photo in evals/test_docs/ (real documents stay out of Git automatically).
  2. Add its correct total, currency and due date to evals/labels.json.

Run:  uv run python -m evals.run_evals
Each document is one AI call, so mind your daily free-tier limit.
"""

import json
import sys
from pathlib import Path

from app.extract import DocumentData, extract
from app.images import PhotoProblem
from app.llm import ConfigError, get_model

HERE = Path(__file__).parent
DOCS = HERE / "test_docs"


def check(data: DocumentData, label: dict) -> dict:
    amount_ok = any(abs(a.value - label["total"]) < 0.01 for a in data.amounts)
    currency_ok = any(a.currency == label.get("currency") for a in data.amounts) if label.get("currency") else True
    date_ok = any(d.date == label["due_date"] for d in data.deadlines)
    return {"amount": amount_ok, "currency": currency_ok, "due_date": date_ok}


def main() -> None:
    try:
        get_model()  # check .env before spending time on the documents
    except ConfigError as problem:
        print(f"Problem: {problem}")
        sys.exit(1)

    labels = json.loads((HERE / "labels.json").read_text(encoding="utf-8"))
    passed = 0
    mistakes = []

    for name, label in labels.items():
        path = DOCS / name
        if not path.exists():
            print(f"SKIP  {name} (file not found)")
            continue
        try:
            data = extract(path)
        except PhotoProblem as problem:
            print(f"FAIL  {name}: unreadable ({problem.tip})")
            mistakes.append({"file": name, "problem": "unreadable"})
            continue

        result = check(data, label)
        ok = result["amount"] and result["due_date"]
        passed += ok
        marks = "  ".join(f"{k}={'✓' if v else '✗'}" for k, v in result.items())
        print(f"{'PASS' if ok else 'FAIL'}  {name}  {marks}")
        if not ok:
            mistakes.append({
                "file": name,
                "expected": label,
                "got_amounts": [a.model_dump() for a in data.amounts],
                "got_deadlines": [d.model_dump() for d in data.deadlines],
            })

    print(f"\n{passed}/{len(labels)} documents have the correct amount and due date.")
    if mistakes:
        print("\nMistakes (write these down, they become test cases):")
        print(json.dumps(mistakes, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
