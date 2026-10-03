import re

POSITIVE = {"stable", "fast", "clear", "good", "reliable"}
NEGATIVE = {"outage", "broken", "slow", "failed", "down"}

def classify(text):
    tokens = re.findall(r"[a-z]+", text.lower())
    if not tokens:
        return None
    positive = sum(token in POSITIVE for token in tokens)
    negative = sum(token in NEGATIVE for token in tokens)
    if positive > negative:
        label = "positive"
    elif negative > positive:
        label = "negative"
    else:
        label = "neutral"
    return {"label": label, "positive": positive, "negative": negative}
