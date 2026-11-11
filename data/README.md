# Data directory

The data files are stored locally and ignored by Git. Only this README is
tracked.

## Do I need to download anything?

For the current working copy of this project, no. The required raw files,
prepared inputs, and final analysis panel already exist. You can open and run
the notebooks without downloading the data again.

After a fresh Git clone, yes. Git provides the code and this README, but not the
research data. Follow the rebuilding steps below.

## Folder structure

### `raw/`: original source files

These files are preserved as received and should not be edited.

- `raw/qwi/<run timestamp>/`: Census QWI API responses, request metadata, and
  schema files. `code/qwi_pipeline.py` downloads these automatically and gives
  every run its own timestamped folder. Do not download them manually.
- `raw/acs_pums/2015_2019_national/csv_pus.zip`: National 2015–2019 ACS PUMS
  person records. The exposure program reads the ZIP directly; extraction is
  not required.
- `raw/acs_pums/crosswalks/`: Official Census and O*NET files used to connect
  ACS occupations and industries to the AI scores and QWI industries.
- `raw/ai_exposure/occ_level.csv`: Occupation-level GPT-4 exposure scores from
  Eloundou et al.

The additional sample files, extracted PUMS files, PDFs, and older crosswalks
currently under `raw/acs_pums/` document earlier matching audits. They are not
required by the active preparation program. The local `SOURCES.md` and
`manifest.json` files record source links, checksums, and retrieval details.

### `interim/`: prepared notebook inputs

- `interim/qwi/qwi_research_ind3.csv`: Cleaned three-digit QWI research data.
- `interim/qwi/qwi_research_ind3_validation.json`: QWI settings, raw-run path,
  coverage, and validation results.
- `interim/ai_exposure/industry_ai_exposure_3digit.csv`: Industry AI-exposure
  scores used in the research.
- `interim/ai_exposure/occupation_coverage.csv`: Occupation matching coverage.
- `interim/ai_exposure/ai_exposure_validation.json`: Exposure construction and
  coverage checks.

These files are outputs of the two programs in `code/`; they are not original
source data. The QWI file contains ages 22-24 hiring outcomes and all-age
quarter-end employment. The exposure file contains one national ACS-weighted
AI-exposure score for each of 81 three-digit industries.

### `processed/`: final analysis data

- `processed/final_analysis_panel.csv`: Final state-industry-quarter panel
  created and checked by `notebooks/01_data_preparation.ipynb`. This is the file
  loaded by `notebooks/02_research_analysis.ipynb`.

The final panel contains 148,053 observations from 3,719 state-industry
groups, 81 industries, 49 jurisdictions, and 42 quarters. Its comparison
period is 2015 Q1-2022 Q3, its post period is 2023 Q1-2025 Q3, and 2022 Q4 is
excluded. The panel includes:

- `hire_count`, the normalized name for the ages 22-24 QWI `HirAEnd` measure;
- `hiring_rate` and `hiring_rate_pct`, derived from the published QWI
  `HirAEndR` measure;
- `young_average_employment`, reconstructed as `(Emp + EmpEnd) / 2` for ages
  22-24;
- the three-digit industry AI-exposure score; and
- all-age employment above the state-industry group's predicted pre-COVID
  trend.

The hiring rate is a quarterly labor-flow rate rather than an individual
probability, so valid values can exceed 100% in small groups.

## Rebuild the data after a fresh clone

### 1. Download QWI automatically

Copy `.env.template` to `.env`, add a valid Census API key, and run:

```bash
python code/qwi_pipeline.py
```

The program downloads both the raw QWI responses and the Census schema, then
creates the two QWI interim files. If a request is interrupted, use the
`--resume-run-id` command documented in `code/README.md`.

### 2. Add the five AI-exposure source files

`code/prepare_ai_exposure.py` does not download its source files. Download the
following files and keep these exact names and locations:

1. [`raw/acs_pums/2015_2019_national/csv_pus.zip`](https://www2.census.gov/programs-surveys/acs/data/pums/2019/5-Year/csv_pus.zip)
2. [`raw/ai_exposure/occ_level.csv`](https://raw.githubusercontent.com/openai/GPTs-are-GPTs/refs/heads/main/data/occ_level.csv)
3. [`raw/acs_pums/crosswalks/onet_2019_to_soc2018_crosswalk.csv`](https://www.onetcenter.org/taxonomy/2019/soc/2019_to_SOC_Crosswalk.csv?fmt=csv)
4. [`raw/acs_pums/crosswalks/2018-ACS-PUMS-and-2018-SIPP-Public-Use-Occupation-Code-List.xlsx`](https://www2.census.gov/programs-surveys/demo/guidance/industry-occupation/2018-ACS-PUMS-and-2018-SIPP-Public-Use-Occupation-Code-List.xlsx)
5. [`raw/acs_pums/crosswalks/2022-Census-Industry-Code-List-with-Crosswalk.xlsx`](https://www2.census.gov/programs-surveys/demo/guidance/industry-occupation/2022-Census-Industry-Code-List-with-Crosswalk.xlsx)

The national PUMS ZIP is approximately 2.24 GB. The QWI program must be run
first because exposure preparation also reads the QWI validation file and its
saved industry labels.

Then run:

```bash
python code/prepare_ai_exposure.py
```

### 3. Build the final panel

Run `notebooks/01_data_preparation.ipynb`. It combines the two interim inputs,
constructs the employment-trend measure, checks the final sample, and saves the
processed panel. Then run `notebooks/02_research_analysis.ipynb` to reproduce
the descriptive results, models, diagnostics, and figures in the paper.

Do not replace missing or Census-suppressed values with zero. API keys belong
only in the ignored `.env` file, never in `data/`.
