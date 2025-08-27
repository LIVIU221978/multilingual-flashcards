
# Multilingual Flashcard Generator

Stack: **Streamlit + Google Gemini API + ReportLab**.  

## Quickstart
```bash
pip install -r requirements.txt
export GEMINI_API_KEY="YOUR_KEY"      # macOS/Linux
setx GEMINI_API_KEY "YOUR_KEY"     # Windows PowerShell
streamlit run app.py
```

## Features
- Generate concise flashcards from a topic using Gemini (gemini-1.5-flash by default)
- Translate to multiple languages using Gemini (same key)
- Download **PDF** (ReportLab) and **Anki CSV** exports
- No external paid services

## Notes
- Right-to-left scripts and complex shaping may require custom fonts; current layout targets Latin scripts.
- All prompts instruct Gemini to return strict JSON for reliable parsing.
