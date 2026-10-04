import math
import re

LEXICON = {
    "stable": 2.0, "fast": 1.5, "clear": 1.5, "good": 2.0, "reliable": 2.0,
    "resolved": 2.0, "great": 3.0, "smooth": 2.0, "quick": 1.5, "helpful": 2.0,
    "outage": -3.0, "broken": -2.5, "slow": -1.5, "failed": -2.5, "down": -2.0,
    "error": -2.0, "crash": -3.0, "flaky": -2.0, "timeout": -2.0, "bad": -2.0,
}
NEGATORS = {"not", "no", "never", "isn't", "wasn't", "didn't", "don't", "without", "hardly", "aren't", "weren't"}
INTENSIFIERS = {"very": 1.5, "extremely": 1.8, "really": 1.3, "slightly": 0.6, "somewhat": 0.7}
NEGATION_WINDOW = 3
MAX_CHARS = 5000
NORMALIZER = 15


class TextError(ValueError):
    pass


def tokens(text):
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())


def classify(text):
    if not isinstance(text, str):
        raise TextError("text must be a string")
    if len(text) > MAX_CHARS:
        raise TextError(f"text is longer than {MAX_CHARS} characters")
    words = tokens(text)
    if not words:
        return None
    pivot = max((i for i, word in enumerate(words) if word == "but"), default=None)
    total = 0.0
    terms = []
    for index, word in enumerate(words):
        if word not in LEXICON:
            continue
        value = LEXICON[word]
        if index and words[index - 1] in INTENSIFIERS:
            value *= INTENSIFIERS[words[index - 1]]
        window = words[max(0, index - NEGATION_WINDOW):index]
        negated = any(item in NEGATORS for item in window)
        if negated:
            value *= -0.5
        if pivot is not None:
            value *= 0.5 if index < pivot else 1.5
        total += value
        terms.append({"term": word, "value": round(value, 4), "negated": negated})
    compound = total / math.sqrt(total * total + NORMALIZER)
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    return {
        "label": label,
        "compound": round(compound, 4),
        "positive": sum(term["value"] > 0 for term in terms),
        "negative": sum(term["value"] < 0 for term in terms),
        "terms": terms,
    }
