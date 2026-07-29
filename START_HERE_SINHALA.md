# EduAgent LK — ආරම්භ කිරීම

## 1. Project එක open කරන්න

```powershell
cd eduagent-lk
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. API key එක දාන්න

`.streamlit/secrets.toml.example` file එක copy කර `.streamlit/secrets.toml` කියලා rename කරන්න.

```toml
GROQ_API_KEY = "ඔබගේ Groq API key එක"
FAST_PROVIDER = "groq"
FAST_MODEL = "llama-3.1-8b-instant"
REASONING_PROVIDER = "groq"
REASONING_MODEL = "openai/gpt-oss-120b"
REVIEW_PROVIDER = "groq"
REVIEW_MODEL = "llama-3.1-8b-instant"
OFFLINE_DEMO = "false"
```

API key එක GitHub එකට push කරන්න එපා.

## 3. Official knowledge documents ලබාගන්න

```powershell
python scripts/download_official_sources.py --pages-per-doc 8
```

මෙය NIE Grade 9 සහ Grade 10 English Teacher Guides download කර, RAG සඳහා page-range Markdown documents ලෙස වෙන් කරයි.

## 4. RAG check කරන්න

```powershell
python scripts/ingest.py
python scripts/evaluate_retrieval.py
```

`data/retrieval_evaluation_results.json` file එක බලලා query 5ට retrieved context relevant ද කියලා README එකේ comment කරන්න.

## 5. Tests run කරන්න

```powershell
pytest -q
```

## 6. App එක run කරන්න

```powershell
streamlit run app.py
```

Browser එකේ ලැබෙන local URL එක open කරන්න.

## 7. GitHub upload කිරීම

README එකේ `YOUR-USERNAME`, student name, student ID සහ live URL placeholders replace කරන්න. Feature branches භාවිත කර small commits කරන්න. Existing files එකවර single bulk commit එකකින් upload නොකර, ඔබ test සහ modify කරන features අනුව commits වෙන් කරන්න.

## 8. Streamlit deploy කිරීම

- GitHub repository එක Streamlit Community Cloud එකට connect කරන්න.
- Main file: `app.py`
- Advanced Settings → Secrets එකට local `secrets.toml` content paste කරන්න.
- Deploy කළ පසු live URL එක README එකට දාන්න.
