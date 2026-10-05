# Sentiment Analysis System

<!-- project-guide:start -->
## Project guide

[Project architecture](PROJECT_ARCHITECTURE.md) · [Interview questions and answers](INTERVIEW_QA.md)

Use the architecture document for the component diagram, implementation boundaries, and verification entry points. The interview guide includes source-backed answers and project walkthroughs.

### Implementation map

| Component | Responsibility |
| --- | --- |
| [`src/sentiment/main.py`](src/sentiment/main.py) | HTTP handlers: `GET /healthz`, `POST /classify`, `POST /classify/batch` |
| [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py) | Functions: `tokens`, `classify` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`src/sentiment/__init__.py`](src/sentiment/__init__.py) | Implementation or supporting configuration |
| [`tests/test_sentiment.py`](tests/test_sentiment.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |

### Local setup and verification

From the repository root (the commands follow the checked-in manifests):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

To serve the FastAPI application locally, install the server separately if it is not already available:

```bash
python -m pip install uvicorn
PYTHONPATH=src python -m uvicorn sentiment.main:app --reload
```

<!-- project-guide:end -->

Level: 5 — NLP

Skills: Python, tokenization, a weighted lexicon, negation and intensifier rules, batch scoring

A rule-based classifier for operations text such as incident notes and release feedback. It does not call a language model, so every score can be traced to the words that produced it.

How a score is built:

1. Each word in the lexicon has a weight, for example `outage` -3 and `stable` +2.
2. An intensifier right before the word scales it (`very` 1.5, `slightly` 0.6).
3. A negator within the three previous words (`not`, `isn't`, `never`, `without` and others) flips the weight and halves it, so "not stable" is mildly negative rather than strongly negative.
4. If the text contains `but`, words before the last `but` count half and words after count one and a half times.
5. The total is squashed to a compound score between -1 and 1. At or above 0.05 is positive, at or below -0.05 is negative, and anything between is neutral.

```bash
pip install -r requirements.txt
pytest -q
PYTHONPATH=src uvicorn sentiment.main:app --reload
```

| Method and path | Returns |
| --- | --- |
| `POST /classify` | `label`, `compound`, positive and negative term counts, and each matched term with its final value |
| `POST /classify/batch` | Up to 100 texts, label counts, and the mean compound score |

```bash
curl -s -X POST localhost:8000/classify -H 'content-type: application/json' \
  -d '{"text":"The release was fast but the dashboard is broken."}'
```

Refused: empty text, text that is not a string, text over 5000 characters, and an empty or oversized batch.
