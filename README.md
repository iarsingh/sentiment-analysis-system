# Sentiment Analysis System

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
