
# 📝 Multilingual Flashcard Generator

Created a concise study flashcards from any topic, translate them to multiple languages using Google Gemini, and export to PDF and Anki CSV—all.

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
- Lightweight UI in Streamlit, easy to run locally or deploy on Streamlit Cloud

## How It Works 
You enter a topic and choose languages. App asks Gemini to create N flashcards in strict JSON. App asks Gemini to translate that JSON into the target languages and you review cards, then download as PDF or Anki CSV

## Notes
Right-to-left scripts and complex shaping may require custom fonts; current layout targets Latin scripts and all prompts instruct Gemini to return strict JSON for reliable parsing.
