# QWI research pipeline

`qwi_pipeline.py` collects the complete QWI input for this research. The
notebook only checks the files produced by the pipeline.

## Run

From the project root:

```bash
python code/qwi_pipeline.py
```

The command reads `CENSUS_API_KEY` from `.env` and prints progress while it
downloads each state-age request. It first checks the key with one small Census
request and stops immediately if Census rejects it.

## Research sample

- 2015Q1 through the latest expected QWI quarter;
- all usable states plus D.C.;
- ages 22–24 (`A03`) and all ages (`A00`);
- four-digit NAICS industries;
- private employment (`A05`), all sexes, unadjusted data; and
- official hiring, employment, separation, rate, and status variables.

Alaska is excluded because its series ends in 2016Q2. Michigan is excluded
because its series ends in 2021Q4. Neither state can support the post-2022
research outcome. These exclusions are also recorded in the validation file.

The pipeline finds the latest quarter shared by every included state-age group.
Raw responses retain everything returned by Census; the working CSV ends at
that common quarter.

The API request places only `industry` in the varying output dimensions. Census
automatically returns the fixed state, age, ownership, seasonal-adjustment, and
time fields. This keeps each request below the API's 400,000-cell limit.

## Output

```text
data/
  raw/qwi/<run_id>/
    schema/                 # Census labels and definitions
    responses/              # untouched API JSON, metadata, and errors
  interim/qwi/
    qwi_research.csv
    qwi_research_validation.json
```

Each raw run has a unique timestamp and is never overwritten. The interim CSV
and validation file represent the latest run. Missing or suppressed values are
not converted to zero, and the API key is never saved.

After the command finishes, open `notebooks/01_qwi_pipeline_test.ipynb` to
inspect coverage, duplicate keys, missing measures, and status flags.
