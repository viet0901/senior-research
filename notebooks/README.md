# Notebooks Folder

The notebooks contain the final data preparation and research analysis. Run
them in numerical order from inside the project repository using Python 3.11
or newer. The saved results were produced with Python 3.11.15.

## Notebook Order

### `01_data_preparation.ipynb`

This notebook reads the prepared QWI and industry AI-exposure files from
`data/interim/`. It validates the inputs, estimates the state-industry
employment trends, constructs the research variables, and saves:

- `data/processed/final_analysis_panel.csv`
- `figures/employment_trend_comparison.png`

### `02_research_analysis.ipynb`

This notebook loads the saved final panel. It contains the descriptive
analysis, fixed-effects Poisson models, employment-trend comparison, quarterly
analysis, diagnostics, and robustness checks. It also creates the remaining
research figures in `figures/`.

## Running the Notebooks

Install the project requirements and start JupyterLab from the project root:

```bash
source .venv/bin/activate
jupyter lab
```

Run every cell in `01_data_preparation.ipynb` before running
`02_research_analysis.ipynb`. Both notebooks locate the project root
automatically, but they must be opened from somewhere inside this repository.

The notebooks are saved with executed outputs so the displayed tables and
figures can be checked against the manuscript. Do not manually change the
processed panel; revise the preparation steps and rerun the notebooks instead.

Large API requests and source-data processing remain in `code/`. The notebooks
are reserved for transparent research decisions, final panel construction,
analysis, and interpretation.
