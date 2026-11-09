# Paperwork Explainer

Take a photo of a bill, contract or official letter. Get a plain-language explanation:
what it is, what to do, by when, and what happens if you don't.

> This isn't legal or financial advice. For anything important, contact the sender.

## Status

| Step | What | Status |
| --- | --- | --- |
| 1 | Git, GitHub and project setup | ✅ |
| 2 | Photo → structured data (`app/extract.py`) | ✅ code in place, testing with my samples |
| 3 | Plain-language explanation and Streamlit UI | ✅ code in place, testing with my samples |
| Later | Knowledge base, agent, MCP calendar tools, API, Telegram bot, Docker, AWS | Not started |

## Setup

You need [uv](https://docs.astral.sh/uv/) installed. It installs the right Python for you.

```bash
uv sync                 # installs everything
cp .env.example .env    # Windows PowerShell: Copy-Item .env.example .env
```

Open `.env` and paste your API key. A free Google key from
[Google AI Studio](https://aistudio.google.com) is enough to start.

## Run it

```bash
# The web page (opens in your browser)
uv run streamlit run ui/streamlit_app.py

# Just the extraction, prints JSON
uv run python -m app.extract evals/test_docs/sample_water_bill.jpg

# Extraction + explanation in another language
uv run python -m app.explain evals/test_docs/sample_water_bill.jpg --language Russian

# Offline tests (no API key needed, free)
uv run pytest

# Check extraction against the correct answers in evals/labels.json
uv run python -m evals.run_evals
```

### On your phone

Run `uv run streamlit run ui/streamlit_app.py --server.address 0.0.0.0`, then on a
phone on the same Wi-Fi open `http://<your-computer's-IP>:8501`. Phone browsers only
allow the live camera on `https` pages, so use the **Upload** tab there. It still lets
you take a photo with the camera.

## How it works

1. `app/images.py` turns the photo upright, shrinks it and converts it to JPEG.
2. `app/extract.py` sends it to a vision-capable AI model with `EXTRACTION_PROMPT`.
   LangChain's `with_structured_output` makes the model return a `DocumentData` object,
   and Pydantic checks every field. Dates that aren't real are removed and marked
   unreadable instead of being kept.
3. `app/explain.py` sends only the extracted facts, never the photo, to the model with
   `EXPLANATION_PROMPT` and gets back four short answers.
4. `find_unsupported_numbers()` checks that every number in the explanation exists in the
   document. If one doesn't, the page shows a warning.
5. Deadline cards, "days left" and amounts on the page come straight from the extracted
   data, not from the explanation, so they can't be reworded wrong.

The AI provider is set in `.env` (`LLM_PROVIDER`): Google, Anthropic or OpenAI.

**About temperature:** the plan says to use temperature 0. Newer models such as Gemini 3.8
Flash and Claude Haiku 5.5 ignore or reject that setting, so the app only sends it if you
set `LLM_TEMPERATURE` in `.env`. Consistency comes from the strict prompt, structured
output and the evals instead.

## Privacy rules

- API keys live only in `.env`, which is in `.gitignore` and never committed.
- Test with sample documents I made, or family documents used with permission and with
  account numbers blacked out. Real documents in `evals/test_docs/` stay out of Git
  automatically. Only files named `sample_*` are committed.
- Photos are kept in memory only while being processed and are never saved to disk.
  Document text isn't logged.
- The extraction prompt tells the model to keep only the last 4 digits of account,
  card and ID numbers.
- The app always says it isn't legal or financial advice.

## Project structure

```
app/
  llm.py           # creates the AI model from .env settings
  images.py        # photo -> upright, resized JPEG
  prompts.py       # the instructions sent to the model
  extract.py       # photo -> DocumentData   (Step 2)
  explain.py       # DocumentData -> Explanation + grounding check   (Step 3)
  rag/, agent.py, api.py    # later steps
mcp_server/server.py        # later step
ui/
  streamlit_app.py # the web page   (Step 3)
  telegram_bot.py  # later step
evals/
  test_docs/       # sample photos (real ones stay out of Git)
  labels.json      # correct answers
  run_evals.py     # scores extraction
tests/             # offline tests
knowledge/         # official guides for the knowledge base (later step)
```
