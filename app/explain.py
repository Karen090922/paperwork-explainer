"""Step 3: structured data -> plain-language explanation.

explain() turns DocumentData into four short answers: What is this? What do I do?
By when? What if I don't? It only sees the extracted facts, never the photo, so
it has nothing to invent from. find_unsupported_numbers() double-checks that.

Try it:  uv run python -m app.explain evals/test_docs/sample_water_bill.jpg --language Russian
"""

import argparse
import json
import re
import sys

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.extract import DocumentData, extract
from app.images import PhotoProblem
from app.llm import ConfigError, get_model
from app.prompts import EXPLANATION_PROMPT, LEVEL_INSTRUCTIONS

# Shown in the language picker -> name sent to the model. Add your languages here.
LANGUAGES = {
    "English": "English",
    "Русский": "Russian",
    "Հայերեն": "Armenian",
}

# Written in code, not by the model, so it's always there and always correct.
DISCLAIMERS = {
    "English": "This isn't legal or financial advice. For anything important, contact the sender.",
    "Russian": "Это не юридическая и не финансовая консультация. По важным вопросам свяжитесь с отправителем.",
    "Armenian": "Սա իրավաբանական կամ ֆինանսական խորհուրդ չէ։ Կարևոր հարցերով դիմեք փաստաթուղթն ուղարկողին։",
}


class Explanation(BaseModel):
    what_is_this: str = Field(description="1 or 2 sentences: what kind of document, from whom, about what")
    what_to_do: list[str] = Field(description="Steps the reader must take, one short sentence each")
    deadlines: list[str] = Field(description="One line per deadline, starting with the date")
    if_ignored: str = Field(description="What the document says happens if the reader does nothing")


def explain(data: DocumentData, language: str = "English", level: str = "simple") -> Explanation:
    """Explain the document's facts in plain words. language is an English name, like 'Russian'."""
    if level not in LEVEL_INSTRUCTIONS:
        raise ValueError(f"level must be one of {list(LEVEL_INSTRUCTIONS)}")

    system_prompt = EXPLANATION_PROMPT.format(
        language=language, level_instructions=LEVEL_INSTRUCTIONS[level]
    )
    facts = data.model_dump_json(indent=2, exclude={"is_readable", "retake_tip"})

    model = get_model().with_structured_output(Explanation)
    result = model.invoke(
        [SystemMessage(system_prompt), HumanMessage(f"Document facts:\n{facts}")]
    )
    if result is None:
        raise RuntimeError("The AI model didn't return an explanation. Please try again.")
    return result


# ---------- Grounding check ----------
# Any number in the explanation that isn't in the extracted data is a bug,
# not a style issue. This finds them so the UI can warn the user.

_NUMBER = re.compile(r"\d+(?:[.,  ]\d+)*")


def _numbers_in_text(text: str) -> list[str]:
    return [match.group().strip() for match in _NUMBER.finditer(text)]


def _possible_values(token: str) -> set[float]:
    """'1,234.50' could mean 1234.5; '45,20' could mean 45.2. Return every reasonable reading."""
    parts = re.split(r"[.,  ]", token)
    values = {float("".join(parts))}  # all separators are thousands separators
    if len(parts) > 1:  # the last separator is a decimal point
        values.add(float("".join(parts[:-1]) + "." + parts[-1]))
    return values


def _known_numbers(data: DocumentData) -> set[float]:
    known: set[float] = set()
    for amount in data.amounts:
        known.add(round(amount.value, 2))
    dates = [data.issue_date] + [d.date for d in data.deadlines]
    for iso in filter(None, dates):
        known.update(float(part) for part in iso.split("-"))
    text_fields = [data.document_type, data.sender, *data.actions_required, *data.consequences_if_ignored]
    text_fields += [a.label for a in data.amounts] + [d.what for d in data.deadlines]
    for text in filter(None, text_fields):
        for token in _numbers_in_text(text):
            known.update(round(v, 2) for v in _possible_values(token))
            known.update(float(p) for p in re.split(r"[.,  ]", token))
    return known


def find_unsupported_numbers(explanation: Explanation, data: DocumentData) -> list[str]:
    """Return numbers that appear in the explanation but not in the document's facts."""
    known = _known_numbers(data)
    text = " ".join([explanation.what_is_this, *explanation.what_to_do, *explanation.deadlines, explanation.if_ignored])
    unsupported = []
    for token in _numbers_in_text(text):
        if any(round(v, 2) in known for v in _possible_values(token)):
            continue
        parts = re.split(r"[.,  ]", token)  # dates like 05.12.2026
        if len(parts) > 1 and all(float(p) in known for p in parts):
            continue
        if token not in unsupported:
            unsupported.append(token)
    return unsupported


def main() -> None:
    parser = argparse.ArgumentParser(description="Explain a document photo in plain language.")
    parser.add_argument("photo")
    parser.add_argument("--language", default="English", help="English, Russian, Armenian, ...")
    parser.add_argument("--level", default="simple", choices=list(LEVEL_INSTRUCTIONS))
    args = parser.parse_args()

    try:
        data = extract(args.photo)
        result = explain(data, args.language, args.level)
    except (PhotoProblem, ConfigError) as problem:
        print(f"Problem: {problem}")
        if isinstance(problem, PhotoProblem):
            print(f"Tip: {problem.tip}")
        sys.exit(1)

    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    unsupported = find_unsupported_numbers(result, data)
    if unsupported:
        print(f"\nWarning: these numbers aren't in the document: {', '.join(unsupported)}")


if __name__ == "__main__":
    main()
