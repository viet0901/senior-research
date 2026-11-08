# Data collection and preparation code

Only two Python programs are part of the active workflow. They handle API
requests and heavier source-data preparation; final panel construction and
research analysis remain in the notebooks.

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

The program expects these preserved source files:

- `data/raw/acs_pums/2015_2019_national/csv_pus.zip` — [2019 ACS five-year national PUMS person file](https://www2.census.gov/programs-surveys/acs/data/pums/2019/5-Year/csv_pus.zip)
- `data/raw/ai_exposure/occ_level.csv` — [Eloundou et al. occupation exposure scores](https://github.com/openai/GPTs-are-GPTs/blob/main/data/occ_level.csv)
- `data/raw/acs_pums/crosswalks/onet_2019_to_soc2018_crosswalk.csv` — [O*NET occupational taxonomy and crosswalks](https://www.onetcenter.org/taxonomy.html)
- `data/raw/acs_pums/crosswalks/2018-ACS-PUMS-and-2018-SIPP-Public-Use-Occupation-Code-List.xlsx`
- `data/raw/acs_pums/crosswalks/2022-Census-Industry-Code-List-with-Crosswalk.xlsx`

The two Census workbooks come from the [Census industry and occupation code-list page](https://www.census.gov/topics/employment/industry-occupation/guidance/code-lists.html). The local PUMS manifest and `data/raw/ai_exposure/SOURCES.md` preserve retrieval details and checksums.

This reads the preserved 2015–2019 ACS PUMS person file and official
crosswalks. It keeps employed private wage-and-salary workers (`ESR` 1/2 and
`COW` 1/2), uses person weight `PWGTP`, and creates:

```text
data/interim/ai_exposure/industry_ai_exposure_3digit.csv
data/interim/ai_exposure/occupation_coverage.csv
data/interim/ai_exposure/ai_exposure_validation.json
```

Ambiguous occupation or industry links remain missing. Neither program builds
the final panel, estimates employment trends, makes figures, or runs a model.
Final panel construction belongs in
`notebooks/01_data_preparation.ipynb`; figures and models belong in
`notebooks/02_research_analysis.ipynb`.

The occupation parser also stops a `Combines:` block when the next Census
section heading begins, so broad SOC headings are not assigned to the preceding
ACS occupation.
