# Data preparation

Only two Python programs are part of the active workflow.

## 1. QWI data

```bash
python code/qwi_pipeline.py
```

This downloads three-digit QWI data for ages 22–24 (`A03`) and all ages
(`A00`), using private-sector, all-sex, unadjusted observations. It reads the
Census key from `.env`, preserves raw API responses, and creates:

```text
data/interim/qwi/qwi_research_ind3.csv
data/interim/qwi/qwi_research_ind3_validation.json
```

If an interrupted download must be resumed:

```bash
python code/qwi_pipeline.py --resume-run-id RUN_FOLDER_NAME
```

## 2. Industry AI exposure

```bash
python code/prepare_ai_exposure.py
```

This reads the preserved 2015–2019 ACS PUMS person file and official
crosswalks. It keeps employed private wage-and-salary workers (`ESR` 1/2 and
`COW` 1/2), uses person weight `PWGTP`, and creates:

```text
data/interim/ai_exposure/industry_ai_exposure_3digit.csv
data/interim/ai_exposure/occupation_coverage.csv
data/interim/ai_exposure/ai_exposure_validation.json
```

Ambiguous occupation or industry links remain missing. The program does not
build the final panel, estimate employment trends, make figures, or run a
regression. Those tasks belong in `notebooks/01_research_analysis.ipynb`.
