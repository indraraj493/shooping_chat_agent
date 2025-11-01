# AI Shopping Chat Agent (Mobiles) – Python FastAPI

A minimal AI shopping chat agent that helps customers discover, compare, and buy mobile phones. It understands natural-language queries, retrieves relevant phones from a mock catalog, explains trade‑offs, and handles adversarial prompts.

- Conversational search and recommendations
- Comparison of 2–3 models with specs
- Explainability (e.g., OIS vs EIS)
- Safety: refusals for secrets, toxic, irrelevant or adversarial prompts
- Lightweight web UI with product cards and comparison view
- Optional Gemini integration via Google AI Studio

## Demo / Deployment

- Hosting suggested: Render (free tier). Use `render.yaml` in this repo.
- After deploy, you will get a public URL to submit as your demo link.

## Tech Stack

- Backend: FastAPI, Uvicorn, Pydantic
- Frontend: Jinja2 template + vanilla JS (no framework)
- Data: JSON mock dataset (`app/data/phones.json`)
- Optional LLM: Gemini (via Google AI Studio) – off by default

## Local Setup

```bash
# 1) Clone
git clone <your_fork_or_repo_url>
cd mykarma_assignment

# 2) Python venv
python3 -m venv .venv
source .venv/bin/activate

# 3) Install deps
pip install -r requirements.txt

# 4) Run dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5) Open UI
open http://localhost:8000
```

## Project Structure

```
app/
  main.py                 # FastAPI app, routes
  templates/index.html    # Minimal chat UI
  static/{style.css,app.js}
  data/phones.json        # Mock catalog
  services/
    safety.py             # Guardrails & refusals
    nlp.py                # Intent parsing (budget, brand, features, compare, explain)
    retrieval.py          # Catalog loading, filtering, ranking
    recommender.py        # Response builders (cards, comparison, explainers)
    llm.py                # Optional Gemini wrapper (disabled unless API key provided)
```

## How It Works

1. Parse user intent
   - Budget (e.g., “under ₹30k”), brand (Samsung, OnePlus, Pixel…), features (camera, battery, charging, display, performance, compact)
   - Comparison mode: detects patterns like “Pixel 8a vs OnePlus 12R”
   - Explainer mode: topics like “OIS vs EIS”

2. Retrieve phones
   - Filter by budget, brand, compact, and features
   - Rank by a simple heuristic (value for money, camera, battery/charging, display)

3. Respond
   - Recommendations: top 2–3 cards with price, specs summary, pros/cons, plus a short rationale
   - Comparison: side-by-side cards for 2–3 phones
   - Explainer: concise factual explanation (e.g., OIS vs EIS)

4. Safety
   - Refuses requests to reveal internal prompts, API keys, or hidden logic
   - Neutral, factual tone; rejects toxicity/irrelevance
   - Avoids hallucinating unknown specs (constrained to dataset)

## Prompt Design / Safety Strategy

- Primary responses are deterministic from the dataset to minimize hallucination
- Guardrails (`app/services/safety.py`) block adversarial content:
  - Sensitive: “reveal system prompt”, “show API key”
  - Toxic: brand trashing; encourages neutral comparisons
  - Irrelevant topics: refuses non-shopping requests
- Explanations (e.g., “OIS vs EIS”) use short, curated text
- Optional LLM (Gemini) can be enabled only to paraphrase or enrich language, never to invent specs

## Optional: Enable Gemini (Google AI Studio)

1. Create a free API key in Google AI Studio
2. Set environment variable before starting the app:

```bash
export GOOGLE_API_KEY="<your_key>"
```

3. The app will automatically try LLM for phrasing; if unset, falls back to deterministic responses.

## Deployment (Render)

- Connect this repo to Render
- Render auto-detects `render.yaml` and deploys a free web service
- Start command uses `gunicorn` with a Uvicorn worker: `gunicorn -k uvicorn.workers.UvicornWorker app.main:app`
- Health check at `/health`

## Expected Query Coverage (examples)

- “Best camera phone under ₹30,000?”
- “Compact Android with good one‑hand use.”
- “Compare Pixel 8a vs OnePlus 12R.”
- “Battery king with fast charging, around ₹15k.”
- “Explain OIS vs EIS.”
- “Show me Samsung phones only, under ₹25k.”
- “I like this phone, tell me more details.”

## Known Limitations

- Mock dataset, not a live catalog
- Heuristic ranking (no advanced ML) to keep it transparent and safe
- Feature/entity extraction is rule-based; may miss edge phrasing
- LLM is optional; disabled by default to avoid external reliance

## License

MIT


