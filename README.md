# Scene Words

Context-based language learning MVP for a CYD dashboard, a small web input page, and a FastAPI NLP backend.

## Project Layout

```text
backend/
  main.py            FastAPI routes
  nlp_engine.py      rule-based text cleaning, keyword extraction, phrase extraction, context tagging
  database.py        SQLite setup and storage helpers
  seed_data.json     2 real-world contexts and 2 story contexts
web/
  index.html         minimal browser input and result preview
lvgl9_firmwares/
  touch_color_test.py
requirements.txt
scene_words.db       created automatically when the API starts
```

## Run Backend

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload
```

API base URL:

```text
http://localhost:8000
```

## MVP API

```text
POST /analyze_text
GET  /contexts
GET  /context/{id}
POST /save_item
GET  /dashboard
```

## Open Web Input

Open `web/index.html` in a browser after the backend is running.
