PYTHON ?= python

test:
	$(PYTHON) -m pytest -q

run:
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

demo:
	$(PYTHON) scripts/run_demo.py
