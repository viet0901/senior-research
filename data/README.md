# Data directory

Research data files stay local and are excluded from Git. This README is
tracked so that the folder structure remains documented.

- `raw/`: Original downloaded files, source documentation, and retrieval
  records. These files should not be edited.
- `interim/qwi/`: QWI data created by `code/qwi_pipeline.py`.
- `interim/ai_exposure/`: Industry AI-exposure data created by
  `code/prepare_ai_exposure.py`.
- `processed/`: The final analysis panel created and checked in
  `notebooks/01_data_preparation.ipynb`.

Do not replace missing or Census-suppressed values with zero, and do not store
API keys here. API keys belong in the local `.env` file. The data can be rebuilt
from the two preparation programs and the first notebook.
