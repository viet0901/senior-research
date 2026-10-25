# DA 401 Senior Research

## Research question

After accounting for unusually high pandemic-era employment growth, is greater
exposure to generative AI associated with lower hiring among workers ages
22–24?

This is an observational study. The results will be described as associations,
not causal effects.

## Simple workflow

The project has two data-preparation programs and one main analysis notebook:

1. `code/qwi_pipeline.py` downloads and cleans Census QWI data.
2. `code/prepare_ai_exposure.py` creates a three-digit industry AI-exposure
   file from ACS PUMS occupation shares and the Eloundou et al. score.
3. `notebooks/01_research_analysis.ipynb` merges the prepared data, constructs
   the employment-trend measure, checks the sample, and performs the analysis.

The Python files handle API requests or processing that is too large for a
notebook. Research decisions, diagnostics, charts, and models stay visible in
the notebook.

## Project folders

- `code/`: the two data-preparation programs
- `notebooks/`: the main research analysis notebook
- `data/raw/`: unchanged source files
- `data/interim/`: prepared inputs for the notebook
- `data/processed/`: the final analysis dataset, created later
- `writing/`: proposal, literature review, research design, and paper drafts
- `figures/`: final research figures

Local data, credentials, and AI context notes are excluded from Git. The
researcher runs the notebook and makes every Git commit.

## Code checks

Install the development tools and run the same checks used by GitHub Actions:

```bash
pip install -r requirements-dev.txt
ruff check code tests
ruff format --check code tests
pytest -q
```

The tests use synthetic inputs and do not require the local research data or a
Census API key.
