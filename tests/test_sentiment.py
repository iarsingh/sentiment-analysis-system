from fastapi.testclient import TestClient
from sentiment.main import app

def test_labels():
    client = TestClient(app)
    assert client.post("/classify", json={"text": "The deploy was stable and fast."}).json()["label"] == "positive"
    assert client.post("/classify", json={"text": "The service was broken and slow."}).json()["label"] == "negative"
    assert client.post("/classify", json={"text": "   "}).status_code == 422
