# Tests

These unit tests check the two data-preparation programs without downloading
the full research data.

- `test_qwi_pipeline.py` checks the QWI API selections, data types, labels,
  duplicate detection, and common-period logic.
- `test_prepare_ai_exposure.py` checks code cleaning, occupation-score rules,
  Census crosswalk parsing, industry matching, and required-file errors.
- `conftest.py` makes the programs in `code/` importable during testing.

Run the tests from the project root:

```bash
pytest -q
```

Run the same code-quality checks used by continuous integration:

```bash
ruff check code tests
ruff format --check code tests
```

The tests use small constructed examples. They do not call the Census API,
replace the notebook data checks, or validate the interpretation of the final
research models.
