from collections import Counter

from fastapi import FastAPI, HTTPException

from sentiment.lexicon import TextError, classify

app = FastAPI()
MAX_BATCH = 100


def checked(text):
    try:
        result = classify(text)
    except TextError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=422, detail="Text is empty.")
    return result


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/classify")
def post_classify(body: dict):
    return checked(body.get("text", ""))


@app.post("/classify/batch")
def post_batch(body: dict):
    texts = body.get("texts")
    if not isinstance(texts, list) or not 1 <= len(texts) <= MAX_BATCH:
        raise HTTPException(status_code=422, detail=f"texts must be a list of 1 to {MAX_BATCH} strings")
    results = [checked(text) for text in texts]
    counts = Counter(result["label"] for result in results)
    mean = sum(result["compound"] for result in results) / len(results)
    return {
        "results": results,
        "counts": {label: counts.get(label, 0) for label in ("positive", "neutral", "negative")},
        "mean_compound": round(mean, 4),
    }
