# Paperwork Explainer

An app that turns a photo of a bill, contract or official letter into a plain-language
explanation, a to-do list and calendar reminders.

**Demo goal:** photograph a real utility bill on a phone. Within ~10 seconds the app says
what it is, how much is owed, the due date and what happens if it's late. Tapping
"Add reminder" puts the deadline in Google Calendar.

## About me and how to help

I'm learning AI engineering. This project is how I learn, so teach, don't just do.

- Before writing code, explain the idea in a few plain sentences.
- Work in small pieces. After each piece, tell me in one line what it does.
- When something breaks, give me a hint first, not the fix. Give the fix if I ask again.
- Before running a command, say what it will do.
- At the end of each task, give me two sentences per new file to put in my notes.
- The code for Steps 1–3 was generated for me. When I ask about a file, walk me through
  it line by line in plain words.

## Stack

Python, uv, a vision-capable LLM through LangChain (provider set in .env), Pydantic,
LangGraph, Chroma, MCP Python SDK, FastAPI, Streamlit (then a Telegram bot),
LangSmith or Langfuse, Docker, AWS (EC2, S3, CloudWatch), GitHub Actions.

## How the code is organized

- `app/llm.py`: `get_model()` creates the model from .env. Always use it; never create
  a model directly.
- `app/images.py`: `prepare_image()` and `PhotoProblem` (an error with a tip for the user).
- `app/prompts.py`: all prompts live here.
- `app/extract.py`: `DocumentData` schema and `extract()` (Step 2).
- `app/explain.py`: `Explanation` schema, `explain()` and `find_unsupported_numbers()` (Step 3).
- `ui/streamlit_app.py`: the web page.
- `evals/`: sample photos, correct answers and the scoring script.
- Files that only contain a docstring are placeholders for later steps.

## Commands

- Install everything: `uv sync`
- Add a package: `uv add <package>`
- Web page: `uv run streamlit run ui/streamlit_app.py`
- Extraction only: `uv run python -m app.extract evals/test_docs/sample_water_bill.jpg`
- Offline tests: `uv run pytest`
- Evals (uses API calls): `uv run python -m evals.run_evals`

## Rules (never break these)

- Never read, print or commit `.env`. Secrets live only in `.env`; `.env.example` has
  placeholder names only.
- Never put real account numbers, names or addresses in code, tests, logs or commits.
  Real documents in `evals/test_docs/` are gitignored; only `sample_*` files are committed.
- Never save uploaded photos to disk. Don't log document text.
- Explanations use only facts from the extracted data. The app always says it isn't
  legal or financial advice.
- Run `uv run pytest` before every commit. Keep tests offline (no API calls).

## Git workflow

- Each plan step gets its own branch, like `step-4-knowledge-base`.
- Commit after every change that works, with a short clear message.
- When a step's "Done when" check passes, open a pull request into `main`.

## Progress

Current step: testing Steps 2–3 with my own 10 sample documents.
<!-- Update this line when you start a new step. -->
