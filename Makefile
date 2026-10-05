PYTHON ?= python3
.PHONY: test run docker
test:
	$(PYTHON) -m pytest -q
run:
	PYTHONPATH=src $(PYTHON) -m uvicorn sentiment.main:app --reload --port 8080
docker:
	docker build -t sentiment-analysis-system:local .
