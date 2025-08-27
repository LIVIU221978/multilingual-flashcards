
## 📝 Multilingual Flashcard Generator

This project is a simple learning tool that creates study flashcards from any topic you type in. The flashcards can then be translated into different languages using Google Gemini, and exported either as a PDF file or in a format that can be imported into Anki.

Stack: **Streamlit + Google Gemini API + ReportLab**. 

### 📎 Link **Live App**:  🌐 [Open on Streamlit](https://liviu221978-multilingual-flashcards-app-rvw4zy.streamlit.app/)  

<img width="1600" height="740" alt="Screenshot from 2025-08-27 17-57-19 (1)" src="https://github.com/user-attachments/assets/719130d8-d88c-44d7-99db-f9ef514ba971" />


## 🚀 Quick Start

1- Install the requirements:
```bash
pip install -r requirements.txt
```

2- Set your Gemini API key:

```bash
export GEMINI_API_KEY="YOUR_KEY"     macOS / Linux
```

```bash
setx GEMINI_API_KEY "YOUR_KEY"       Windows PowerShell
```

3- Run the app:
```bash
streamlit run app.py
```

## ✨ Features

- Generate short, clear flashcards from any study topic
- Translate the cards into multiple languages
- Export flashcards as a PDF document
- Export flashcards as an Anki-ready CSV file
- Simple and lightweight user interface built in Streamlit

## 🛠️ How It Works
You enter a topic and choose languages and app asks Gemini to create flashcards. It asks Gemini to translate the output into the target languages and you review cards, then u can also download it.
