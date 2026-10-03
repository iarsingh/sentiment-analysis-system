from fastapi import FastAPI, HTTPException
from sentiment.lexicon import classify

app = FastAPI()

@app.post("/classify")
def post_classify(body: dict):
    result = classify(body.get("text", ""))
    if result is None:
        raise HTTPException(status_code=422, detail="Text is empty.")
    return result
