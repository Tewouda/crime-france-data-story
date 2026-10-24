PY ?= python3

.PHONY: install data validate run clean zip

install:      ## create venv and install pinned dependencies
	$(PY) -m venv .venv && .venv/bin/pip install -r requirements.txt

data:         ## download pinned source files (skips files already present)
	$(PY) scripts/download_data.py

validate:     ## run cleaning + validation checks headlessly
	$(PY) scripts/validate_data.py

run:          ## launch the app on http://localhost:8501
	$(PY) -m streamlit run app.py

clean:
	rm -rf data/processed/*.parquet __pycache__ */__pycache__
