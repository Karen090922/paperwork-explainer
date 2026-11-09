"""Step 2: photo -> structured data.

extract() sends a photo to a vision-capable AI model and gets back a DocumentData
object. Pydantic checks every field, so the rest of the app can trust the shape of
the data.

Try it:  uv run python -m app.extract evals/test_docs/sample_water_bill.jpg
"""

import json
import sys
from datetime import date
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field, field_validator, model_validator

from app.images import PhotoProblem, prepare_image
from app.llm import ConfigError, get_model
from app.prompts import EXTRACTION_PROMPT

DEFAULT_RETAKE_TIP = "Retake the photo in good light, holding the phone straight above the page."


class Amount(BaseModel):
    label: str = Field(description="What the amount is for, copied from the document, like 'Total due'")
    value: float = Field(description="The number only, like 1234.50")
    currency: str | None = Field(description="3-letter code like USD, EUR, AMD or RUB, or null if unclear")

    @field_validator("currency")
    @classmethod
    def upper_case_currency(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else None


class Deadline(BaseModel):
    what: str = Field(description="What must be done by this date, like 'Pay the total due'")
    date: str | None = Field(description="YYYY-MM-DD, or null if the document gives no exact date")


class DocumentData(BaseModel):
    """Everything the app needs from one document. Each field's description is sent to the model."""

    is_readable: bool = Field(description="False only if the photo is too unclear to find the main facts")
    retake_tip: str | None = Field(description="If not readable: one practical tip for a better photo")
    document_type: str | None = Field(description="Short description, like 'electricity bill'")
    sender: str | None = Field(description="Who sent the document")
    issue_date: str | None = Field(description="YYYY-MM-DD")
    amounts: list[Amount]
    deadlines: list[Deadline]
    actions_required: list[str] = Field(description="Short sentences starting with a verb")
    consequences_if_ignored: list[str] = Field(description="Only what the document itself says")
    language: str | None = Field(description="Language of the document, in English")
    unreadable_fields: list[str] = Field(description="Fields that are on the page but couldn't be read")

    @model_validator(mode="after")
    def check_dates(self) -> "DocumentData":
        """A date that isn't real YYYY-MM-DD is removed and marked unreadable, never kept."""
        if self.issue_date and not _is_iso_date(self.issue_date):
            self.issue_date = None
            self._mark_unreadable("issue_date")
        for i, deadline in enumerate(self.deadlines):
            if deadline.date and not _is_iso_date(deadline.date):
                deadline.date = None
                self._mark_unreadable(f"deadlines[{i}].date")
        return self

    def _mark_unreadable(self, field_name: str) -> None:
        if field_name not in self.unreadable_fields:
            self.unreadable_fields.append(field_name)


def _is_iso_date(text: str) -> bool:
    try:
        date.fromisoformat(text)
        return len(text) == 10
    except ValueError:
        return False


def extract_from_bytes(image_bytes: bytes) -> DocumentData:
    """Read a document photo (as bytes) and return its facts.

    Raises PhotoProblem if the photo can't be used. Its .tip says what to do.
    The photo is only kept in memory and is never saved.
    """
    image_b64 = prepare_image(image_bytes)

    model = get_model().with_structured_output(DocumentData)
    messages = [
        SystemMessage(EXTRACTION_PROMPT),
        HumanMessage(
            content=[
                {"type": "text", "text": "Extract the facts from this document photo."},
                {"type": "image", "base64": image_b64, "mime_type": "image/jpeg"},
            ]
        ),
    ]
    data = model.invoke(messages)

    if data is None:
        raise RuntimeError("The AI model didn't return valid data. Please try again.")
    if not data.is_readable:
        raise PhotoProblem("The document couldn't be read.", data.retake_tip or DEFAULT_RETAKE_TIP)
    return data


def extract(image_path: str | Path) -> DocumentData:
    """Read a document photo from a file and return its facts."""
    return extract_from_bytes(Path(image_path).read_bytes())


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: uv run python -m app.extract path/to/photo.jpg")
        sys.exit(2)
    try:
        data = extract(sys.argv[1])
    except (PhotoProblem, ConfigError) as problem:
        print(f"Problem: {problem}")
        if isinstance(problem, PhotoProblem):
            print(f"Tip: {problem.tip}")
        sys.exit(1)
    print(json.dumps(data.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
