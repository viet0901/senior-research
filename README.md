# DA 401 Senior Research - Viet Nguyen

## Project Title

AI Exposure or Post-Pandemic Employment Adjustment? Explaining the Decline in Early-Career Hiring

## Research Question

What question are you trying to answer?

- Working Project Question: After accounting for employment growth above pre-COVID trends, is greater generative AI exposure associated with a larger decline in hiring among workers ages 22 to 24?

This is an observational study, so the results are interpreted as associations rather than causal effects.

## Data Sources

Where is your data coming from?

- [U.S. Census Bureau Quarterly Workforce Indicators (QWI)](https://www.census.gov/data/developers/data-sets/qwi.html)
- [2015-2019 American Community Survey Public Use Microdata Sample (ACS PUMS)](https://www.census.gov/programs-surveys/acs/microdata/documentation.2019.html)
- [Census industry and occupation code lists and crosswalks](https://www.census.gov/topics/employment/industry-occupation/guidance/code-lists.html)
- [GPT-4 occupation-level AI exposure scores](https://github.com/openai/GPTs-are-GPTs/blob/main/data/occ_level.csv) from [Eloundou et al.](https://doi.org/10.1126/science.adj0998)

## Related Research

- [Tucker (2026), *You're (Not) Hired: Artificial Intelligence and Early Career Hiring in the Quarterly Workforce Indicators*](https://www2.census.gov/library/working-papers/2026/adrm/ces/CES-WP-26-27.pdf)
- [Eloundou et al. (2024), *GPTs are GPTs: Labor Market Impact Potential of LLMs*](https://doi.org/10.1126/science.adj0998)

## Methods

Which methods or models will you use?

- Descriptive statistics and visualizations
- Log-linear pre-COVID employment trends for each state-industry group
- Fixed-effects panel regression with state-industry and quarter fixed effects
- Industry-clustered standard errors
- Event-study and sensitivity analyses
- Hiring rates as the primary outcome and hire counts as a secondary outcome

## Current Status

- QWI and ACS PUMS data-preparation programs are complete
- The three-digit industry AI-exposure measure and final analysis panel are complete
- Descriptive analysis and preliminary fixed-effects models are complete
- Model diagnostics show heavy-tailed residuals, but the initial conclusion is not driven by a small number of extreme observations
- Secondary-outcome, event-study, and final sensitivity analyses are in progress

## Expected Timeline

What do you expect to produce every week?

- Weeks 1-2: Finalize the research design and prepare the QWI data pipeline
- Weeks 3-4: Construct the industry AI-exposure measure and final analysis panel
- Week 5: Complete descriptive analysis and preliminary fixed-effects models
- Week 6: Estimate secondary-outcome and event-study models
- Week 7: Complete sensitivity checks and finalize figures and tables
- Week 8: Write, revise, and prepare the final research paper

## Repository Structure

- `code/`: Data collection and preparation programs
- `notebooks/`: Data preparation, analysis, visualizations, and models
- `writing/`: Proposal, literature review, research design, and paper drafts
- `figures/`: Research plots and visualizations
- `data/raw/`: Unchanged source data
- `data/interim/`: Prepared inputs for the notebook
- `data/processed/`: Final analysis data
- `tests/`: Unit tests for the data-preparation programs

The data folders are stored locally and excluded from Git. The researcher runs the notebook and creates every Git commit.

## Project Workflow

The project uses two data-preparation programs and one main notebook:

1. `code/qwi_pipeline.py` downloads and validates the Census QWI data.
2. `code/prepare_ai_exposure.py` constructs the three-digit industry AI-exposure measure.
3. `notebooks/01_research_analysis.ipynb` creates the final panel, documents research decisions, performs diagnostics, produces figures, and estimates the models.

Python files are used only for API requests and large-data preparation. The research analysis remains in the notebook so that each decision and result can be reviewed clearly.

## Reproduce the Project

Create and activate the environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.template` to `.env`, add a valid Census API key, and run the preparation programs:

```bash
python code/qwi_pipeline.py
python code/prepare_ai_exposure.py
jupyter lab
```

See [code/README.md](code/README.md) for the required local ACS and crosswalk files. Then open `notebooks/01_research_analysis.ipynb` and run the notebook in order. Large source data, generated data, credentials, and local research context are not committed to Git.

## Important Research Notes

- The analysis uses three-digit industries because the ACS, occupation-exposure, and QWI classifications cannot always be linked defensibly at a more detailed level.
- The AI-exposure measure represents potential task exposure, not actual AI adoption or worker replacement.
- Approximately 42.2% of eligible ACS worker weight can be linked jointly to a usable industry and occupation exposure score.
- Missing and Census-suppressed observations remain missing rather than being replaced with zero.
- The primary estimates are interpreted as associations, not causal effects.

## Code Checks

```bash
pip install -r requirements-dev.txt
ruff check code tests
ruff format --check code tests
pytest -q
```

The tests use synthetic inputs and do not require local research data or a Census API key.
