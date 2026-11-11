# Notebooks Folder

The notebooks contain the final data preparation and research analysis. Run
them in numerical order from inside the project repository using Python 3.11
or newer. The saved results were produced with Python 3.11.15.

## Notebook Order

### `01_data_preparation.ipynb`

This notebook reads the prepared QWI and industry AI-exposure files from
`data/interim/`. It validates the inputs, estimates the state-industry
log-linear employment trends from 2015 Q1-2019 Q4, compares actual and
predicted all-age employment in 2022 Q1-Q3, constructs the research variables,
and saves:

- `data/processed/final_analysis_panel.csv`
- `figures/employment_trend_comparison.png`

### `02_research_analysis.ipynb`

This notebook loads the saved final panel. It contains the descriptive
analysis; fixed-effects Poisson hiring-rate and hire-count models with and
without the employment-trend adjustment; quarter-specific models; diagnostics;
and robustness checks. The rate model uses the hire count with log average
ages 22-24 employment as an offset, while the count model uses the same outcome
without the offset.

The full panel has 148,053 observations. Poisson separation removes 245
observations from 26 groups that report zero hires in every observed quarter,
leaving 147,808 observations for the four primary same-sample models. This
notebook also creates Figures 2-5 and Figures B.1-B.3 listed in
`figures/README.md`.

## Running the Notebooks

Install the project requirements and start JupyterLab from the project root:

```bash
source .venv/bin/activate
jupyter lab
```

Run every cell in `01_data_preparation.ipynb` before running
`02_research_analysis.ipynb`. Both notebooks locate the project root
automatically, but they must be opened from somewhere inside this repository.

The notebooks are saved with executed outputs so the displayed sample counts,
estimates, tables, and figures can be checked against the final paper. Do not
manually change the processed panel; revise the preparation steps and rerun the
notebooks instead.

Large API requests and source-data processing remain in `code/`. The notebooks
are reserved for transparent research decisions, final panel construction,
analysis, and interpretation.
