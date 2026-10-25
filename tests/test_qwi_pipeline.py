"""Unit tests for the small, deterministic parts of the QWI pipeline."""

from __future__ import annotations

import pandas as pd
import pytest

import qwi_pipeline


def make_raw_qwi_row() -> pd.DataFrame:
    """Return one synthetic Census response row."""
    row = {column: "10" for column in qwi_pipeline.COUNT_COLUMNS}
    row.update({column: "0.25" for column in qwi_pipeline.RATE_COLUMNS})
    row.update({column: "1" for column in qwi_pipeline.STATUS_COLUMNS})
    row.update(
        {
            "industry": "111",
            "time": "2022-Q1",
            "sex": "0",
            "agegrp": "A03",
            "ownercode": "A05",
            "seasonadj": "U",
            "ind_level": "3",
            "state": "01",
        }
    )
    return pd.DataFrame([row])


def make_schema() -> dict[str, pd.DataFrame]:
    """Return the minimum official-label tables needed by ``clean_qwi``."""
    return {
        "label_fipsnum.csv": pd.DataFrame(
            {"geography": ["01"], "label": ["Alabama"], "geo_level": ["S"]}
        ),
        "label_agegrp.csv": pd.DataFrame({"agegrp": ["A03"], "label": ["22-24 years"]}),
        "label_ownercode.csv": pd.DataFrame({"ownercode": ["A05"], "label": ["All Private"]}),
        "label_industry.csv": pd.DataFrame(
            {"industry": ["111"], "ind_level": ["3"], "label": ["Crop Production"]}
        ),
    }


def test_build_qwi_parameters_uses_research_selections() -> None:
    parameters = qwi_pipeline.build_qwi_parameters(
        api_key="test-key",
        state_fips=1,
        time_spec="from 2015-Q1 to 2022-Q4",
        age_group="a03",
        industry_level="3",
        ownership_code="a05",
    )

    assert parameters["for"] == "state:01"
    assert parameters["time"] == "from 2015-Q1 to 2022-Q4"
    assert parameters["agegrp"] == "A03"
    assert parameters["ind_level"] == "3"
    assert parameters["ownercode"] == "A05"
    assert parameters["sex"] == "0"
    assert parameters["seasonadj"] == "U"
    assert parameters["get"] == ",".join(qwi_pipeline.REQUEST_COLUMNS)
    assert parameters["key"] == "test-key"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("state_fips", "ABC"),
        ("time_spec", "2022Q1"),
        ("age_group", "A99"),
        ("industry_level", "2"),
        ("ownership_code", "A02"),
    ],
)
def test_build_qwi_parameters_rejects_invalid_codes(field: str, value: str) -> None:
    arguments = {
        "api_key": "test-key",
        "state_fips": "01",
        "time_spec": "2022-Q1",
        "age_group": "A03",
        "industry_level": "3",
        "ownership_code": "A05",
    }
    arguments[field] = value

    with pytest.raises(ValueError):
        qwi_pipeline.build_qwi_parameters(**arguments)


def test_clean_qwi_types_codes_and_adds_labels() -> None:
    cleaned = qwi_pipeline.clean_qwi(make_raw_qwi_row(), make_schema())
    row = cleaned.iloc[0]

    assert row["state"] == "01"
    assert row["industry"] == "111"
    assert row["period"] == "2022Q1"
    assert row["year"] == 2022
    assert row["quarter"] == 1
    assert row["EmpEnd"] == 10
    assert row["HirAEndR"] == 0.25
    assert row["state_name"] == "Alabama"
    assert row["age_group_name"] == "22-24 years"
    assert row["ownership_name"] == "All Private"
    assert row["industry_name"] == "Crop Production"
    assert str(cleaned["EmpEnd"].dtype) == "Int64"
    assert str(cleaned["HirAEndR"].dtype) == "Float64"


def test_validate_qwi_reports_duplicate_research_keys() -> None:
    cleaned = qwi_pipeline.clean_qwi(make_raw_qwi_row(), make_schema())
    duplicated = pd.concat([cleaned, cleaned], ignore_index=True)

    report = qwi_pipeline.validate_qwi(duplicated)

    assert report["observation_count"] == 2
    assert report["duplicate_key_rows"] == 2
    assert report["states"] == ["01"]
    assert report["age_groups"] == ["A03"]
    assert report["period_min"] == "2022Q1"
    assert report["period_max"] == "2022Q1"
    assert report["unmatched_industry_labels"] == 0


def test_latest_common_period_uses_every_state_age_group() -> None:
    data = pd.DataFrame(
        {
            "state": ["01", "01", "01", "01", "04", "04"],
            "agegrp": ["A00", "A00", "A03", "A03", "A00", "A03"],
            "period": ["2022Q1", "2022Q2", "2022Q1", "2022Q2", "2022Q1", "2022Q1"],
        }
    )

    assert qwi_pipeline._latest_common_period(data) == "2022Q1"
