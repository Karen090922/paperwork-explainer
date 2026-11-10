"""Step 3: a simple web page for the app.

Run it:  uv run streamlit run ui/streamlit_app.py
The photo stays in memory only. It's never written to disk.
"""

import hashlib
from datetime import date
from typing import NoReturn

import streamlit as st

from app.explain import DISCLAIMERS, LANGUAGES, explain, find_unsupported_numbers
from app.extract import DocumentData, extract_from_bytes
from app.images import PhotoProblem
from app.llm import ConfigError

st.set_page_config(page_title="Paperwork Explainer", page_icon="📄", layout="centered")
st.title("📄 Paperwork Explainer")
st.caption("Photograph a bill or official letter and get a plain-language explanation.")

# ---------- Settings ----------
left, right = st.columns(2)
language_label = left.selectbox("Language", list(LANGUAGES))
language = LANGUAGES[language_label]
level = right.radio("Level", ["simple", "detailed"], horizontal=True)

# ---------- Photo ----------
camera_tab, upload_tab = st.tabs(["📷 Camera", "📁 Upload"])
with camera_tab:
    shot = st.camera_input("Take a photo of the document")
with upload_tab:
    upload = st.file_uploader(
        "Upload a photo", type=["jpg", "jpeg", "png", "webp", "heic", "heif"]
    )

photo = shot or upload
if photo is None:
    st.info("Take or upload a photo to start. On a phone, Upload also lets you use the camera.")
    st.stop()

image_bytes = photo.getvalue()
photo_id = hashlib.sha256(image_bytes).hexdigest()


def show_error(title: str, tip: str | None = None) -> NoReturn:
    st.error(f"**{title}**")
    if tip:
        st.info(f"💡 {tip}")
    st.stop()


# ---------- Step 2: read the photo (only once per photo) ----------
if st.session_state.get("photo_id") != photo_id:
    with st.spinner("Reading the document…"):
        try:
            data = extract_from_bytes(image_bytes)
        except PhotoProblem as problem:
            show_error(problem.message, problem.tip)
        except ConfigError as problem:
            show_error("Setup problem", str(problem))
        except Exception as problem:  # network errors, rate limits, ...
            show_error("Something went wrong while reading the photo.", f"{type(problem).__name__}: {str(problem)[:300]}")
    st.session_state.photo_id = photo_id
    st.session_state.data = data
    st.session_state.explanations = {}

del image_bytes  # we don't need the photo any more
data: DocumentData = st.session_state.data

# ---------- Step 3: explain (once per language and level) ----------
cache_key = (language, level)
if cache_key not in st.session_state.explanations:
    with st.spinner("Writing the explanation…"):
        try:
            st.session_state.explanations[cache_key] = explain(data, language, level)
        except Exception as problem:
            show_error("Something went wrong while writing the explanation.", f"{type(problem).__name__}: {str(problem)[:300]}")
explanation = st.session_state.explanations[cache_key]


# ---------- Deadlines first: that's what users care about most ----------
def days_left_text(iso: str) -> tuple[str, str]:
    """Return (text, urgency). Computed in code, so it's always correct."""
    days = (date.fromisoformat(iso) - date.today()).days
    if days < 0:
        return f"{-days} days overdue", "overdue"
    if days == 0:
        return "due today", "urgent"
    if days <= 7:
        return f"in {days} days", "urgent"
    return f"in {days} days", "normal"


st.subheader("⏰ Deadlines")
if not data.deadlines:
    st.info("No deadline found in this document. If you're not sure, ask the sender.")
for deadline in data.deadlines:
    if deadline.date:
        when, urgency = days_left_text(deadline.date)
        box = {"overdue": st.error, "urgent": st.warning, "normal": st.info}[urgency]
        box(f"### {deadline.date}  ·  {when}\n{deadline.what}")
    else:
        st.info(f"**No exact date**\n\n{deadline.what}")

if data.amounts:
    columns = st.columns(min(len(data.amounts), 3))
    for i, amount in enumerate(data.amounts):
        columns[i % len(columns)].metric(amount.label, f"{amount.value:,.2f} {amount.currency or ''}")

# ---------- The four answers ----------
st.subheader("What is this?")
st.write(explanation.what_is_this)

st.subheader("What do I do?")
for step in explanation.what_to_do:
    st.markdown(f"- {step}")

st.subheader("By when?")
if explanation.deadlines:
    for line in explanation.deadlines:
        st.markdown(f"- {line}")
else:
    st.write("—")

st.subheader("What if I don't?")
st.write(explanation.if_ignored)

# ---------- Warnings ----------
if data.unreadable_fields:
    st.warning("Some parts couldn't be read: " + ", ".join(data.unreadable_fields) + ". Check them on the paper.")

unsupported = find_unsupported_numbers(explanation, data)
if unsupported:
    st.warning(
        "These numbers in the explanation weren't found in the document: "
        + ", ".join(unsupported) + ". Double-check them on the paper."
    )

st.caption("⚠️ " + DISCLAIMERS.get(language, DISCLAIMERS["English"]))

with st.expander("Extracted data (for checking)"):
    st.json(data.model_dump())
