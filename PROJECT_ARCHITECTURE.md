# sentiment-analysis-system — project architecture

[README](README.md) · [Interview questions and answers](INTERVIEW_QA.md)

## Purpose and scope

A rule-based classifier for operations text such as incident notes and release feedback. It does not call a language model, so every score can be traced to the words that produced it.

This document describes files and symbols in this checkout. Deployment templates and statements in the original overview are distinguished from a verified running environment.

## Component diagram

```mermaid
flowchart LR
    M0["src/sentiment/__init__.py"]
    M1["src/sentiment/lexicon.py"]
    M2["src/sentiment/main.py"]
    M2 -->|imports| M1
```

For Python repositories, arrows show resolved local imports, not network calls or deployment order. Otherwise the diagram is a repository component map; containment arrows do not assert runtime integration.

## Components and responsibilities

| Component | Responsibility |
| --- | --- |
| [`src/sentiment/main.py`](src/sentiment/main.py) | HTTP handlers: `GET /healthz`, `POST /classify`, `POST /classify/batch` |
| [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py) | Functions: `tokens`, `classify` |
| [`requirements.txt`](requirements.txt) | Implementation or supporting configuration |
| [`src/sentiment/__init__.py`](src/sentiment/__init__.py) | Implementation or supporting configuration |
| [`tests/test_sentiment.py`](tests/test_sentiment.py) | Executable checks and regression examples |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | GitHub Actions job definitions |
| [`README.md`](README.md) | Project explanations or operating notes |

## Request interface

| Method and path | Handler | Source |
| --- | --- | --- |
| `GET /healthz` | `healthz` | [`src/sentiment/main.py`](src/sentiment/main.py#L22) |
| `POST /classify` | `post_classify` | [`src/sentiment/main.py`](src/sentiment/main.py#L27) |
| `POST /classify/batch` | `post_batch` | [`src/sentiment/main.py`](src/sentiment/main.py#L32) |

The table lists literal route decorators found in the inspected Python modules. Router prefixes and middleware can add behavior; check the linked handler and application setup before calling an endpoint.

## Implementation walkthrough

### `classify(text)`

Source: [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py#L25).

Calls visible in this function: `TextError`, `any`, `enumerate`, `isinstance`, `len`, `math.sqrt`, `max`, `round`, `sum`, `terms.append`, `tokens`.

```python
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
```

The excerpt is truncated; the linked source contains the full implementation.

### `checked(text)`

Source: [`src/sentiment/main.py`](src/sentiment/main.py#L11).

Calls visible in this function: `HTTPException`, `classify`, `str`.

```python
def checked(text):
    try:
        result = classify(text)
    except TextError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=422, detail="Text is empty.")
    return result
```

### `tokens(text)`

Source: [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py#L21).

Calls visible in this function: `re.findall`, `text.lower`.

```python
def tokens(text):
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())
```

## Validation and failure paths

| Explicit exception | Source |
| --- | --- |
| `TextError('text must be a string')` | [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py#L27) |
| `TextError(f'text is longer than {MAX_CHARS} characters')` | [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py#L29) |
| `HTTPException(status_code=422, detail='Text is empty.')` | [`src/sentiment/main.py`](src/sentiment/main.py#L17) |
| `HTTPException(status_code=422, detail=f'texts must be a list of 1 to {MAX_BATCH} strings')` | [`src/sentiment/main.py`](src/sentiment/main.py#L35) |
| `HTTPException(status_code=422, detail=str(exc))` | [`src/sentiment/main.py`](src/sentiment/main.py#L15) |

These are explicit exceptions in the inspected source, rather than a claim that every failure is handled. Follow the calling handler to see whether the exception becomes an HTTP response or propagates.

## Data and state

- [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py) defines module-level containers: `LEXICON`, `NEGATORS`, `INTENSIFIERS`.

Module-level dictionaries/lists live in a Python process. They can be fixtures or mutable state; inspect writes before treating them as persistent storage. A production extension would need to define persistence and concurrency behavior explicitly.

## Data flow and design decisions

### What is the input-to-output contract of `classify`

In [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py#L25), `classify(text)` receives the inputs. The function computes these intermediate values:

- `words = tokens(text)`
- `pivot = max((i for i, word in enumerate(words) if word == 'but'), default=None)`
- `total = 0.0`
- `terms = []`
- `compound = total / math.sqrt(total * total + NORMALIZER)`

Its result is defined by:

- `{'label': label, 'compound': round(compound, 4), 'positive': sum((term['value'] > 0 for term in terms)), 'negative': sum((term['value'] < 0 for term in terms)), 'terms': terms}`
- `None`

### Which decision rules or boundary conditions should an interviewer challenge

The implementation in [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py#L25) branches on:

- `not isinstance(text, str)`
- `len(text) > MAX_CHARS`
- `not words`
- `compound >= 0.05`
- `word not in LEXICON`
- `index and words[index - 1] in INTENSIFIERS`
- `negated`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

## Setup and verification

The following commands are derived from the checked-in dependency/test contracts. Execute them from the repository root; the block prepares a local environment, not a cloud deployment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Python dependencies: [`requirements.txt`](requirements.txt).

Test entry points: [`tests/test_sentiment.py`](tests/test_sentiment.py).

Automation definitions: [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Read their triggers and job steps to determine what CI actually runs.

## Operating boundaries and design review

Before turning this checkout into a customer deployment, establish the input contract, data ownership, access controls, failure response, evaluation criteria, and rollback owner. Repository fixtures and unit tests demonstrate local behavior; they do not establish throughput, uptime, compliance, or business impact.

A useful architecture review starts with the linked implementation: identify where input enters, where a decision is made, which state can change, and which external dependency can fail. Add a deployment view only for infrastructure that is actually configured and exercised.
