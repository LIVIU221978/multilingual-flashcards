import os
import json
import re
import time
from typing import List, Dict, Any
import streamlit as st

# Local helpers
from pdf_utils import build_pdf_bytes
from utils import pretty_now  

# Gemini SDK
try:
    import google.generativeai as genai
except Exception:
    genai = None


# -------------------------
# JSON repair helpers
# -------------------------


def _strip_code_fences(s: str) -> str:
    return re.sub(r"```(?:json)?\s*|\s*```", "", s).strip()

def _coerce_json(text: str):
    """
    Parse model JSON robustly:
    - strip code fences
    - normalize smart quotes
    - trim to outermost JSON braces/brackets
    - drop trailing commas
    """
    s = _strip_code_fences(text)
    s = s.replace("“", '"').replace("”", '"').replace("’", "'")

    try:
        return json.loads(s)
    except Exception:
        pass

    first_brace = s.find("{")
    last_brace = s.rfind("}")
    first_brack = s.find("[")
    last_brack = s.rfind("]")

    candidate = None
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = s[first_brace:last_brace + 1]
    elif first_brack != -1 and last_brack != -1 and last_brack > first_brack:
        candidate = s[first_brack:last_brack + 1]
    else:
        candidate = s

    candidate = re.sub(r",\s*([\]}])", r"\1", candidate)
    return json.loads(candidate)


# -------------------------
# CSV builder that respects selected section
# -------------------------


from io import StringIO

def build_csv_bytes(language: str, cards: List[Dict[str, Any]], section: str) -> bytes:
    """
    CSV columns: Front, Back, Tags
    - Front = term
    - Back  = only the selected section (Definition OR Example OR Q/A)
    """
    out = StringIO()
    import csv
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["Front", "Back", "Tags"])
    for c in cards or []:
        term = c.get("term", "")
        definition = c.get("definition", "")
        example = c.get("example", "")
        qa = c.get("qa", {}) if isinstance(c.get("qa", {}), dict) else {}
        q = qa.get("question", "")
        a = qa.get("answer", "")

        if section == "Definition":
            back = definition
        elif section == "Example":
            back = f"Example: {example}"
        else:  # Q&A
            back = f"Q: {q}\nA: {a}"

        w.writerow([term, back, language])
# UTF-8 with BOM so Excel opens non-Latin cleanly
    return out.getvalue().encode("utf-8-sig")


# -------------------------
# Streamlit UI
# -------------------------

st.set_page_config(page_title="Multilingual Flashcard Generator", page_icon="📝", layout="wide")
st.title("Multilingual Flashcard Generator")

with st.sidebar:
    st.header("API & Settings")
    api_key = st.text_input("GEMINI_API_KEY", type="password", placeholder="paste here or set env var")
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY", "")
    model_name = st.selectbox("Gemini model", ["gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"], index=0)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.6, 0.05)
    st.caption("Note: Only Google Gemini is used (free key).")

st.subheader("Enter Topic & Options")
c1, c2, c3 = st.columns(3)
with c1:
    topic = st.text_input("Study Topic / Subject", placeholder="e.g., Basic SQL Joins")
with c2:
    num_cards = st.slider("Number of flashcards", 4, 30, 10, 1)
with c3:
    difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"], index=0)

languages = st.multiselect(
    "Output Languages",
    ["English", "French", "Romanian", "Urdu"],
    default=["English", "French", "Romanian"]
)

# main Card Content option (Definition OR Q&A OR Example)


card_section = st.selectbox("Card Content", ["Definition", "Q&A", "Example"], index=0)

cA, cB = st.columns(2)
with cA:
    add_pdf = st.checkbox("Enable PDF export", value=True)
with cB:
    add_csv = st.checkbox("Enable Anki CSV export", value=True)

run = st.button("Generate Flashcards", type="primary", use_container_width=True, disabled=not topic)


# -------------------------
# Gemini setup
# -------------------------
def get_model():
    if not genai:
        st.error("google-generativeai not installed. Run: pip install -r requirements.txt")
        return None
    if not api_key:
        st.error("No API key found. Enter it in the sidebar or set GEMINI_API_KEY.")
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        return model
    except Exception as e:
        st.error(f"Failed to configure Gemini: {e}")
        return None


# -------------------------
# Content generation
# -------------------------
def generate_base_cards(model, topic: str, num_cards: int, difficulty: str, temperature: float) -> List[Dict[str, Any]]:
    # We always ask for all fields (term/definition/example/qa) for stability.
    # UI will display/export only the selected section.
    prompt = f"""
You are an expert teacher. Create {num_cards} concise flashcards for the topic "{topic}".
Audience difficulty: {difficulty}.
Return ONLY valid JSON as a list of objects. Do not include any commentary.
Each card must have these fields:
- "term": a short key phrase or question (<= 8 words)
- "definition": 2-3 precise sentences
- "example": 1 practical example (<= 2 sentences)
- "qa": an object with "question" and "answer" (short, factual)

Constraints:
- No markdown. No code fences. No extra text.
- Keep language as English for this step.
"""
    generation_config = {
        "temperature": temperature,
        "top_p": 0.9,
        "top_k": 40,
        "response_mime_type": "application/json",
        "max_output_tokens": 2048
    }
    resp = model.generate_content(prompt, generation_config=generation_config)
    text = getattr(resp, "text", "")
    try:
        data = _coerce_json(text)
        if not isinstance(data, list):
            raise ValueError("Expected a JSON list.")
        return data
    except Exception as e:
        st.error("Failed to parse base flashcards JSON.")
        with st.expander("Raw model output (debug)"):
            st.code(text[:5000])
        st.exception(e)
        return []


def translate_cards(model, cards: List[Dict[str, Any]], languages: List[str], temperature: float) -> Dict[str, List[Dict[str, Any]]]:

# Always include English

    langs = [l for l in languages if l]
    if "English" not in langs:
        langs = ["English"] + langs

 # First attempt: multi-language JSON

    src_json = json.dumps(cards, ensure_ascii=False)
    prompt = f"""
You are a multilingual translator. Translate the JSON flashcards provided below from English into the requested target languages.
Keep JSON structure identical. For each target language, produce a key with the language name mapping to the list of cards.
Translate fields: "term", "definition", "example", "qa.question", "qa.answer".
Do not add or remove fields. Do not include any commentary. Output JSON only.
Target languages: {", ".join(langs)}

INPUT_JSON:
{src_json}
"""
    generation_config = {
        "temperature": min(temperature, 0.3),
        "top_p": 0.9,
        "top_k": 40,
        "response_mime_type": "application/json",
        "max_output_tokens": 4096
    }
    resp = model.generate_content(prompt, generation_config=generation_config)
    text = getattr(resp, "text", "")

    try:
        data = _coerce_json(text)
        if isinstance(data, dict) and all(k in data for k in langs):
            return data
    except Exception:
        pass  

# Per-language fallback
    result: Dict[str, List[Dict[str, Any]]] = {"English": cards}
    for lang in langs:
        if lang == "English":
            continue
        single_prompt = f"""
Translate the following list of flashcards from English into {lang}.
Keep EXACT same JSON structure (JSON array of objects with keys: term, definition, example, qa={{question,answer}}).
Output JSON ONLY (no commentary, no markdown).

INPUT_JSON:
{src_json}
"""
        r = model.generate_content(single_prompt, generation_config=generation_config)
        t = getattr(r, "text", "")
        try:
            translated_list = _coerce_json(t)
            if isinstance(translated_list, list):
                result[lang] = translated_list
            else:
                result[lang] = []
        except Exception:
            result[lang] = []
    return result


# -------------------------
# Utility: filter cards for selected section
# -------------------------

def filter_for_section(cards: List[Dict[str, Any]], section: str) -> List[Dict[str, Any]]:
    """Return shallow-copied cards where only the selected section carries content; others blank."""
    filtered = []
    for c in cards or []:
        term = c.get("term", "")
        definition = c.get("definition", "")
        example = c.get("example", "")
        qa = c.get("qa", {}) if isinstance(c.get("qa", {}), dict) else {}
        q = qa.get("question", "")
        a = qa.get("answer", "")

        if section == "Definition":
            filtered.append({"term": term, "definition": definition, "example": "", "qa": {"question": "", "answer": ""}})
        elif section == "Example":
            filtered.append({"term": term, "definition": "", "example": example, "qa": {"question": "", "answer": ""}})
        else:  # Q&A
            filtered.append({"term": term, "definition": "", "example": "", "qa": {"question": q, "answer": a}})
    return filtered


# -------------------------
# Run flow
# -------------------------

if "flashcards_translated" not in st.session_state:
    st.session_state.flashcards_translated = None

if run:
    model = get_model()
    if model:
        with st.spinner("Generating base English flashcards with Gemini..."):
            base = generate_base_cards(model, topic, num_cards, difficulty, temperature)
        if base:
            with st.spinner("Translating to selected languages with Gemini..."):
                translated = translate_cards(model, base, languages, temperature)
                st.session_state.flashcards_translated = translated
        else:
            st.warning("No flashcards returned. Adjust topic or try again.")


# -------------------------
# Render results
# -------------------------

if st.session_state.flashcards_translated:
    st.success(f"Flashcards ready • Content: {card_section}")
    tabs = st.tabs(list(st.session_state.flashcards_translated.keys()))
    for idx, lang in enumerate(st.session_state.flashcards_translated.keys()):
        with tabs[idx]:
            cards = st.session_state.flashcards_translated[lang]
            st.subheader(f"{lang} — {len(cards)} cards")

# Only show selected section
            for i, c in enumerate(cards, 1):
                with st.expander(f"{i}. {c.get('term','(no term)')}"):
                    if card_section == "Definition":
                        st.write("Definition:", c.get("definition", ""))
                    elif card_section == "Example":
                        st.write("Example:", c.get("example", ""))
                    else:
                        qa = c.get("qa", {}) if isinstance(c.get("qa", {}), dict) else {}
                        st.write("Q:", qa.get("question", ""))
                        st.write("A:", qa.get("answer", ""))

# Downloads honoring the selected section
            fname_base = f"flashcards_{lang}_{int(time.time())}"

# PDF: we reuse existing PDF builder; we pass filtered cards 
            if add_pdf:
                pdf_cards = filter_for_section(cards, card_section)
                pdf_bytes = build_pdf_bytes(topic, lang, pdf_cards)
                st.download_button(
                    label=f"Download PDF ({lang}, {card_section})",
                    data=pdf_bytes,
                    file_name=f"{fname_base}_{card_section.lower()}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

# CSV: we build here to include only selected section
            if add_csv:
                csv_bytes = build_csv_bytes(lang, cards, card_section)
                st.download_button(
                    label=f"Download Anki CSV ({lang}, {card_section})",
                    data=csv_bytes,
                    file_name=f"{fname_base}_{card_section.lower()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

