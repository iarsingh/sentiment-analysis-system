# sentiment-analysis-system — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does sentiment-analysis-system address, and what can you demonstrate?

A rule-based classifier for operations text such as incident notes and release feedback. It does not call a language model, so every score can be traced to the words that produced it.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/sentiment/main.py`](src/sentiment/main.py): Implementation or supporting configuration.
- [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`src/sentiment/__init__.py`](src/sentiment/__init__.py): Implementation or supporting configuration.
- [`tests/test_sentiment.py`](tests/test_sentiment.py): Executable checks and regression examples.
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml): GitHub Actions job definitions.
- [`README.md`](README.md): Project explanations or operating notes.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `classify` and explain the decision it makes?

The main walkthrough here is `classify(text)` in [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py#L25).

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
```

This is an excerpt; follow the source link for the rest of the branches.

The implementation calls `TextError`, `any`, `enumerate`, `isinstance`, `len`, `math.sqrt`, `max`, `round`, `sum`. In an interview, trace those calls in execution order using a fixture input.

## 4. What responsibility does `checked` have?

`checked(text)` is defined in [`src/sentiment/main.py`](src/sentiment/main.py#L11).

Its return expressions include:

- `result`

It uses `HTTPException`, `classify`, `str`. This is the code path I would compare against the caller to explain responsibility boundaries.

## 5. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `TextError('text must be a string')` in [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py#L27).
- `TextError(f'text is longer than {MAX_CHARS} characters')` in [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py#L29).
- `HTTPException(status_code=422, detail='Text is empty.')` in [`src/sentiment/main.py`](src/sentiment/main.py#L17).
- `HTTPException(status_code=422, detail=f'texts must be a list of 1 to {MAX_BATCH} strings')` in [`src/sentiment/main.py`](src/sentiment/main.py#L35).
- `HTTPException(status_code=422, detail=str(exc))` in [`src/sentiment/main.py`](src/sentiment/main.py#L15).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 6. Which test would you use to demonstrate correctness?

[`tests/test_sentiment.py`](tests/test_sentiment.py#L13) contains `test_labels`:

```python
def test_labels():
    assert label("The deploy was stable and fast.") == "positive"
    assert label("The service was broken and slow.") == "negative"
    assert client.post("/classify", json={"text": "   "}).status_code == 422
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 7. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/sentiment/main.py`](src/sentiment/main.py#L22).
- `POST /classify` → `post_classify` in [`src/sentiment/main.py`](src/sentiment/main.py#L27).
- `POST /classify/batch` → `post_batch` in [`src/sentiment/main.py`](src/sentiment/main.py#L32).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 8. Where does state live, and what happens with multiple workers?

Module-level containers include `LEXICON`, `NEGATORS`, `INTENSIFIERS` in [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py).

These containers belong to a Python process. Inspect which are constant fixtures and which are mutated. Mutable process state needs an explicit shared-storage or synchronization strategy before multiple workers can provide consistent behavior.

## 9. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 10. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 11. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 12. What is the input-to-output contract of `classify`?

In [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py#L25), `classify(text)` receives the inputs. The function computes these intermediate values:

- `words = tokens(text)`
- `pivot = max((i for i, word in enumerate(words) if word == 'but'), default=None)`
- `total = 0.0`
- `terms = []`
- `compound = total / math.sqrt(total * total + NORMALIZER)`

Its result is defined by:

- `{'label': label, 'compound': round(compound, 4), 'positive': sum((term['value'] > 0 for term in terms)), 'negative': sum((term['value'] < 0 for term in terms)), 'terms': terms}`
- `None`

## 13. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/sentiment/lexicon.py`](src/sentiment/lexicon.py#L25) branches on:

- `not isinstance(text, str)`
- `len(text) > MAX_CHARS`
- `not words`
- `compound >= 0.05`
- `word not in LEXICON`
- `index and words[index - 1] in INTENSIFIERS`
- `negated`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.
