from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

from app.services.safety import evaluate_safety
from app.services.retrieval import PhoneCatalog
from app.services.nlp import parse_query
from app.services.recommender import build_recommendations_response, build_comparison_response, build_explainer_response


app = FastAPI(title="AI Phone Shopping Assistant", version="1.0.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


class ChatRequest(BaseModel):
    message: str
    context_phone_id: Optional[str] = None


catalog = PhoneCatalog(data_path="app/data/phones.json")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/chat")
async def chat(req: ChatRequest):
    user_text = (req.message or "").strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Empty message")

    safety = evaluate_safety(user_text)
    if safety.blocked:
        return JSONResponse(
            {
                "type": "refusal",
                "message": safety.message,
            }
        )

    # Parse intent
    intent = parse_query(user_text, catalog.get_index())

    # Knowledge/explainer path
    if intent.mode == "explain" and intent.topic:
        return JSONResponse(build_explainer_response(intent.topic))

    # Compare path
    if intent.mode == "compare" and intent.compare_models:
        phones = catalog.match_by_names(intent.compare_models)
        if not phones:
            return JSONResponse({
                "type": "no_results",
                "message": "I couldn't find those models in the catalog. Try exact model names or rephrase."
            })
        return JSONResponse(build_comparison_response(phones))

    # Retrieval + recommend path
    results = catalog.search(
        min_price=intent.min_price,
        max_price=intent.max_price,
        brand=intent.brand,
        features=intent.features,
        compact=intent.compact,
    )

    if not results:
        return JSONResponse({
            "type": "no_results",
            "message": "No phones matched your criteria. Try relaxing budget or features.",
        })

    response = build_recommendations_response(
        query=intent,
        phones=results,
        top_k=3,
    )
    return JSONResponse(response)


@app.get("/health")
async def health():
    return {"status": "ok"}


