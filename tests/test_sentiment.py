from fastapi.testclient import TestClient

from sentiment.lexicon import classify
from sentiment.main import app

client = TestClient(app)


def label(text):
    return client.post("/classify", json={"text": text}).json()["label"]


def test_labels():
    assert label("The deploy was stable and fast.") == "positive"
    assert label("The service was broken and slow.") == "negative"
    assert client.post("/classify", json={"text": "   "}).status_code == 422


def test_negation_flips_and_softens():
    payload = client.post("/classify", json={"text": "The deploy was not stable."}).json()
    assert payload["label"] == "negative"
    assert payload["terms"] == [{"term": "stable", "value": -1.0, "negated": True}]


def test_contraction_negates():
    assert label("The release isn't reliable.") == "negative"


def test_intensifier_strengthens():
    assert classify("very slow")["compound"] < classify("slow")["compound"]
    assert classify("slightly slow")["compound"] > classify("slow")["compound"]


def test_clause_after_but_dominates():
    assert label("The release was fast but the dashboard is broken.") == "negative"
    assert label("There was an outage but it was resolved and stable.") == "positive"


def test_no_lexicon_words_is_neutral():
    payload = client.post("/classify", json={"text": "Nothing to report today."}).json()
    assert payload["label"] == "neutral"
    assert payload["compound"] == 0


def test_compound_is_bounded():
    payload = classify("great great great great great great great great")
    assert 0.9 < payload["compound"] < 1


def test_long_and_non_string_text_are_refused():
    assert client.post("/classify", json={"text": "a" * 5001}).status_code == 422
    assert client.post("/classify", json={"text": 42}).status_code == 422


def test_batch_counts_labels():
    texts = ["stable and fast", "broken", "nothing here"]
    payload = client.post("/classify/batch", json={"texts": texts}).json()
    assert payload["counts"] == {"positive": 1, "neutral": 1, "negative": 1}
    assert len(payload["results"]) == 3
    assert client.post("/classify/batch", json={"texts": []}).status_code == 422
