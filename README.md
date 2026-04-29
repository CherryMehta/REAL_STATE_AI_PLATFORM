# Real Estate AI Bot

An integrated real estate assistant with two coordinated capabilities:

1. Reactive triage for incoming communications.
2. RAG-powered quiz and learning flow based on property listing content.

The backend uses Python 3.11, FastAPI, CrewAI, Groq, spaCy, Llama 3.3, and API-backed RAG retrieval. The front-end uses React Vite with JSX and Tailwind CSS.

## What this project does

- Classifies incoming real estate messages by intent and urgency.
- Extracts key entities like IDs, dates, money values, email addresses, and phone numbers.
- Drafts context-aware responses to speed up first reply workflows.
- Ingests property listing content into a lightweight local chunk store.
- Generates quiz questions from the ingested listing data.
- Evaluates answers with an LLM and explains mistakes with targeted learning feedback.

## Directory Structure

```text
.
|-- backend
|   |-- app
|   |   |-- agents
|   |   |   |-- orchestration.py
|   |   |   |-- triage_agents.py
|   |   |   `-- triage_tasks.py
|   |   |-- api
|   |   |   `-- routes.py
|   |   |-- core
|   |   |   `-- config.py
|   |   |-- data
|   |   |   `-- sample_property_listing.md
|   |   |-- models
|   |   |   `-- schemas.py
|   |   |-- services
|   |   |   |-- groq_client.py
|   |   |   |-- quiz_service.py
|   |   |   |-- rag_service.py
|   |   |   |-- session_store.py
|   |   |   `-- triage_service.py
|   |   |-- utils
|   |   |   `-- ner.py
|   |   `-- main.py
|   |-- .env.example
|   `-- requirements.txt
|-- frontend
|   |-- index.html
|   |-- package.json
|   |-- postcss.config.js
|   |-- tailwind.config.js
|   |-- vite.config.js
|   `-- src
|       |-- App.jsx
|       |-- api.js
|       |-- index.css
|       `-- main.jsx
`-- README.md
```

## Setup Steps

### 1. Install prerequisites

- Python 3.11
- Node.js 20+
- npm 10+

### 2. Configure the backend

```powershell
cd backend
copy .env.example .env
```

Fill in:

- `GROQ_API_KEY`
- `GROQ_MODEL` if you want a different Groq model, such as `llama-3.3-70b-versatile` or `llama-3.1-8b-instant`
- `OPENAI_API_KEY` or `EMBEDDINGS_API_KEY` only if you want paid semantic retrieval through an embeddings API.

RAG does not install or run local embedding models. By default it stores listing chunks in `backend/.rag_store/listing_chunks.json` and uses a free built-in BM25 keyword retriever. If an embeddings API key is provided, it can use that for semantic retrieval, but this is optional.

### 3. Create a Python virtual environment

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

If the launcher is not available, use your installed Python 3.11 executable directly.

### 4. Install backend dependencies

```powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 -m spacy download en_core_web_sm
```

If you already installed NumPy 2.x in this environment, create a fresh virtual environment before repeating these steps so spaCy and thinc can load their compiled wheels cleanly.
If you already have an older Groq client installed, reinstall from `requirements.txt` so the API client matches the supported pre-1.0 Groq line used by this project.
Chroma DB, sentence-transformers, Torch, NumPy, and scikit-learn are not required for the RAG flow.

### 5. Configure the front-end

```powershell
cd ..\frontend
npm install
```

### 6. Run the backend

```powershell
cd ..\backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Run the front-end

```powershell
cd ..\frontend
npm run dev
```

### 8. Load sample property data

Use the quiz tab in the UI and paste the sample listing text from:

- `backend/app/data/sample_property_listing.md`

You can also send your own real estate listing content and the quiz bot will store it in the lightweight chunk store.

## API Overview

- `POST /api/triage/analyze`
- `POST /api/quiz/ingest`
- `POST /api/quiz/generate`
- `POST /api/quiz/evaluate`
- `GET /health`

## Notes

- CrewAI is used for the triage agent orchestration.
- Groq powers the Llama 3.3 model calls.
- Groq defaults to `llama-3.3-70b-versatile`; deprecated 3.1 70B IDs are auto-routed to the newer model.
- spaCy handles backend NER, with a regex fallback for key real-estate patterns.
- RAG retrieval uses the free built-in BM25 keyword retriever by default. It can use an embeddings API when configured, and never downloads local sentence-transformer models.
- The code includes fallback logic so the app can still behave sensibly even if a specific CrewAI helper class differs across installed versions.
