"""Download the complete QWI input needed for this research project.

Run this file from the project root with ``python code/qwi_pipeline.py``.
The notebook is only for checking the files produced by this pipeline.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, Sequence

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


QWI_API_URL = "https://api.census.gov/data/timeseries/qwi/sa"
QWI_SCHEMA_URL = "https://lehd.ces.census.gov/data/schema/latest"

# Variables needed for hiring, employment, and separation checks.
COUNT_COLUMNS = ["Emp", "EmpEnd", "EmpTotal", "HirA", "HirAEnd", "Sep", "SepBeg"]
RATE_COLUMNS = ["HirAEndR", "SepBegR"]
MEASURE_COLUMNS = COUNT_COLUMNS + RATE_COLUMNS
STATUS_COLUMNS = [f"s{column}" for column in MEASURE_COLUMNS]

REQUEST_COLUMNS = [
    *MEASURE_COLUMNS,
    *STATUS_COLUMNS,
    "industry",
]

# These files document the labels and definitions used during each run.
SCHEMA_FILES = [
    "label_agegrp.csv",
    "label_fipsnum.csv",
    "label_industry.csv",
    "label_ownercode.csv",
    "label_flags.csv",
    "variables_qwi.csv",
]

# Fifty states plus D.C. Alaska and Michigan cannot be used because their QWI
# series end before the post-2022 study period. The validation file records
# these exclusions explicitly.
ALL_STATE_FIPS = (
    "01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13",
    "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25",
    "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36",
    "37", "38", "39", "40", "41", "42", "44", "45", "46", "47", "48",
    "49", "50", "51", "53", "54", "55", "56",
)
EXCLUDED_STATES = {
    "02": "Alaska QWI ends in 2016Q2.",
    "26": "Michigan QWI ends in 2021Q4.",
}
RESEARCH_STATE_FIPS = tuple(
    state for state in ALL_STATE_FIPS if state not in EXCLUDED_STATES
)
RESEARCH_START_QUARTER = "2015-Q1"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, value: Any) -> None:
    _write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")


def _working_stem(industry_level: str) -> str:
    """Keep industry levels in separate working files; retain the old 4-digit name."""
    level = industry_level.strip().upper()
    if level not in {"A", "S", "3", "4", "5", "6"}:
        raise ValueError(f"Unknown industry level: {industry_level!r}")
    return "qwi_research" if level == "4" else f"qwi_research_ind{level}"


def _state_fips(value: str | int) -> str:
    state = str(value).strip().zfill(2)
    if len(state) != 2 or not state.isdigit():
        raise ValueError(f"State FIPS must contain two digits: {value!r}")
    return state


def _time_spec(value: str) -> str:
    value = value.strip()
    quarter = r"\d{4}-Q[1-4]"
    if not re.fullmatch(rf"(?:{quarter}|from {quarter} to {quarter})", value):
        raise ValueError(
            "time_spec must look like '2022-Q1' or "
            "'from 2015-Q1 to 2022-Q4'."
        )
    return value


def _redact(message: str, api_key: str) -> str:
    return message.replace(api_key, "<redacted>") if api_key else message


def _expected_latest_quarter() -> str:
    """Return the current quarter minus the usual three-quarter QWI lag."""
    today = datetime.now(timezone.utc)
    current_quarter = (today.month - 1) // 3 + 1
    quarter_number = today.year * 4 + current_quarter - 1 - 3
    year, zero_based_quarter = divmod(quarter_number, 4)
    return f"{year}-Q{zero_based_quarter + 1}"


def make_session() -> requests.Session:
    """Create a web session that retries temporary Census server errors."""
    retry = Retry(
        total=4,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    session.headers["User-Agent"] = "DA401-senior-research/0.1"
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def check_api_key(session: requests.Session, api_key: str) -> None:
    """Stop before the full run if Census rejects the API key."""
    params = {
        "get": "Emp",
        "for": "state:01",
        "time": "2022-Q1",
        "key": api_key,
    }
    try:
        response = session.get(QWI_API_URL, params=params, timeout=(10, 30))
    except requests.RequestException as exc:
        raise RuntimeError(
            "Could not reach the Census API: " + _redact(str(exc), api_key)
        ) from None

    if "Invalid Key" in response.text:
        raise RuntimeError(
            "Census rejected CENSUS_API_KEY. Replace or activate the key in .env, "
            "then run the pipeline again."
        )
    if not response.ok:
        raise RuntimeError(f"Census API key check failed (HTTP {response.status_code}).")
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Census returned an unexpected response during the API key check."
        ) from exc
    if not isinstance(payload, list) or not payload:
        raise RuntimeError("Census API key check returned no data.")


def build_qwi_parameters(
    *,
    api_key: str,
    state_fips: str | int,
    time_spec: str,
    age_group: str,
    industry_level: str = "4",
    ownership_code: str = "A05",
) -> dict[str, str]:
    """Build one QWI request and check the important research selections.

    The request defaults are four-digit industries, private employment,
    all sexes, and unadjusted quarterly values. ``A03`` represents ages 22–24;
    ``A00`` represents all ages.
    """
    if not api_key or not api_key.strip():
        raise ValueError("A Census API key is required.")

    age = age_group.strip().upper()
    industry = industry_level.strip().upper()
    ownership = ownership_code.strip().upper()

    if age not in {f"A{i:02d}" for i in range(9)}:
        raise ValueError(f"Unknown age group: {age_group!r}")
    if industry not in {"A", "S", "3", "4", "5", "6"}:
        raise ValueError(f"Unknown industry level: {industry_level!r}")
    if ownership not in {"A00", "A01", "A05"}:
        raise ValueError(f"Unknown ownership code: {ownership_code!r}")

    return {
        "get": ",".join(REQUEST_COLUMNS),
        "for": f"state:{_state_fips(state_fips)}",
        "time": _time_spec(time_spec),
        "sex": "0",
        "agegrp": age,
        "ownercode": ownership,
        "seasonadj": "U",
        "ind_level": industry,
        "key": api_key.strip(),
    }


def _download_qwi(
    session: requests.Session,
    *,
    api_key: str,
    state_fips: str,
    time_spec: str,
    age_group: str,
    industry_level: str,
    ownership_code: str,
) -> tuple[pd.DataFrame, str, dict[str, Any]]:
    """Return one QWI response as a table, its untouched text, and metadata."""
    params = build_qwi_parameters(
        api_key=api_key,
        state_fips=state_fips,
        time_spec=time_spec,
        age_group=age_group,
        industry_level=industry_level,
        ownership_code=ownership_code,
    )
    response = session.get(QWI_API_URL, params=params, timeout=(10, 90))
    if not response.ok:
        detail = _redact(response.text[:500].replace("\n", " "), api_key.strip())
        raise RuntimeError(f"QWI request failed ({response.status_code}): {detail}")

    try:
        payload = response.json()
    except ValueError as exc:
        if "Invalid Key" in response.text:
            raise RuntimeError("Census rejected CENSUS_API_KEY.") from exc
        raise RuntimeError(
            "QWI returned a non-JSON response: "
            + _redact(
                re.sub(r"<[^>]+>", " ", response.text[:200]).strip(), api_key
            )
        ) from exc
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], list):
        raise RuntimeError("QWI returned an unexpected response structure.")
    if len(payload[0]) != len(set(payload[0])):
        raise RuntimeError("QWI returned duplicate column names.")

    public_params = {name: value for name, value in params.items() if name != "key"}
    metadata = {
        "source_url": QWI_API_URL,
        "request_parameters": public_params,
        "downloaded_at_utc": _now_utc(),
        "row_count": len(payload) - 1,
    }
    return pd.DataFrame(payload[1:], columns=payload[0]), response.text, metadata


def _download_schema(
    session: requests.Session,
    destination: Path,
) -> dict[str, pd.DataFrame]:
    """Download and preserve the official labels used to prepare the data."""
    tables: dict[str, pd.DataFrame] = {}
    manifest: dict[str, Any] = {"downloaded_at_utc": _now_utc(), "files": {}}

    for filename in SCHEMA_FILES:
        url = f"{QWI_SCHEMA_URL}/{filename}"
        response = session.get(url, timeout=(10, 90))
        if not response.ok:
            raise RuntimeError(f"Schema download failed for {filename}.")

        _write_text(destination / filename, response.text)
        table = pd.read_csv(StringIO(response.text), dtype="string", keep_default_na=False)
        tables[filename] = table
        manifest["files"][filename] = {"source_url": url, "row_count": len(table)}

    _write_json(destination / "manifest.json", manifest)
    return tables


def _add_label(
    data: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    data_code: str,
    label_code: str,
    label_name: str,
) -> pd.DataFrame:
    """Add one official label without dropping or multiplying data rows."""
    lookup = labels[[label_code, "label"]].copy()
    lookup[label_code] = lookup[label_code].astype("string").str.strip()
    lookup = lookup.drop_duplicates(label_code).rename(
        columns={label_code: data_code, "label": label_name}
    )
    return data.merge(lookup, on=data_code, how="left", validate="many_to_one")


def clean_qwi(raw: pd.DataFrame, schema: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Type QWI variables and add labels; do not fill or remove observations."""
    data = raw.copy()

    text_columns = [
        "state", "industry", "ind_level", "agegrp", "sex", "ownercode",
        "seasonadj", "time",
    ]
    for column in text_columns:
        data[column] = data[column].astype("string").str.strip()

    # Census returns the selected time range in one field (for example,
    # ``2015-Q1``). Separate columns are convenient for panel checks and joins.
    if not data["time"].str.fullmatch(r"\d{4}-Q[1-4]").all():
        raise RuntimeError("QWI returned an unexpected time value.")
    data["year"] = data["time"].str[:4]
    data["quarter"] = data["time"].str[-1]

    for column in COUNT_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce").astype("Int64")
    for column in RATE_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce").astype("Float64")
    for column in STATUS_COLUMNS + ["year", "quarter"]:
        data[column] = pd.to_numeric(data[column], errors="coerce").astype("Int64")

    data["period"] = data["time"].str.replace("-", "", regex=False)

    state_labels = schema["label_fipsnum.csv"]
    if "geo_level" in state_labels:
        state_labels = state_labels.loc[state_labels["geo_level"] == "S"]
    data = _add_label(
        data, state_labels, data_code="state", label_code="geography", label_name="state_name"
    )
    data = _add_label(
        data,
        schema["label_agegrp.csv"],
        data_code="agegrp",
        label_code="agegrp",
        label_name="age_group_name",
    )
    data = _add_label(
        data,
        schema["label_ownercode.csv"],
        data_code="ownercode",
        label_code="ownercode",
        label_name="ownership_name",
    )

    industries = schema["label_industry.csv"][["industry", "ind_level", "label"]].copy()
    industries["industry"] = industries["industry"].astype("string").str.strip()
    industries["ind_level"] = industries["ind_level"].astype("string").str.strip()
    industries = industries.drop_duplicates(["industry", "ind_level"]).rename(
        columns={"label": "industry_name"}
    )
    data = data.merge(
        industries, on=["industry", "ind_level"], how="left", validate="many_to_one"
    )

    return data.sort_values(["state", "industry", "agegrp", "year", "quarter"]).reset_index(
        drop=True
    )


def validate_qwi(data: pd.DataFrame) -> dict[str, Any]:
    """Create a small report of coverage, missing values, flags, and duplicates."""
    key = ["state", "industry", "agegrp", "year", "quarter", "ownercode", "sex"]
    flag_counts: dict[str, dict[str, int]] = {}
    for column in STATUS_COLUMNS:
        counts = data[column].astype("string").fillna("<missing>").value_counts()
        flag_counts[column] = {
            str(value): int(count) for value, count in counts.items()
        }
    return {
        "observation_count": len(data),
        "states": sorted(data["state"].dropna().astype(str).unique().tolist()),
        "age_groups": sorted(data["agegrp"].dropna().astype(str).unique().tolist()),
        "period_min": data["period"].min(),
        "period_max": data["period"].max(),
        "industry_count": int(data["industry"].nunique()),
        "duplicate_key_rows": int(data.duplicated(key, keep=False).sum()),
        "missing_measure_values": {
            column: int(data[column].isna().sum()) for column in MEASURE_COLUMNS
        },
        "unmatched_industry_labels": int(data["industry_name"].isna().sum()),
        "status_flag_counts": flag_counts,
    }


def _latest_common_period(data: pd.DataFrame) -> str:
    """Find the latest quarter present for every returned state-age group."""
    coverage = data[["state", "agegrp", "period"]].drop_duplicates()
    period_sets = [
        set(group["period"].dropna().astype(str))
        for _, group in coverage.groupby(["state", "agegrp"], observed=True)
    ]
    if not period_sets:
        raise RuntimeError("No state-age coverage was available.")

    common_periods = set.intersection(*period_sets)
    if not common_periods:
        raise RuntimeError("The returned state-age groups have no common quarter.")
    return max(common_periods, key=lambda value: (int(value[:4]), int(value[-1])))


def run_qwi_download(
    *,
    api_key: str,
    states: Sequence[str | int],
    time_spec: str,
    age_groups: Sequence[str] = ("A03", "A00"),
    industry_level: str = "4",
    ownership_code: str = "A05",
    project_root: str | Path = ".",
    pause_seconds: float = 0.25,
    show_progress: bool = True,
    resume_run_id: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any], list[dict[str, str]]]:
    """Download QWI data, preserve the raw files, and make a working copy.

    Returns ``(data, validation, errors)`` for review in the notebook. New runs
    get a unique raw directory; resuming reuses only matching saved responses.
    """
    root = Path(project_root)
    working_stem = _working_stem(industry_level)
    if resume_run_id is not None and not re.fullmatch(r"\d{8}T\d{12}Z", resume_run_id):
        raise ValueError("resume_run_id must be an existing QWI timestamp directory name.")
    run_id = resume_run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = root / "data" / "raw" / "qwi" / run_id
    if resume_run_id is not None and not run_dir.is_dir():
        raise FileNotFoundError(f"QWI run to resume does not exist: {run_dir}")
    response_dir = run_dir / "responses"
    interim_dir = root / "data" / "interim" / "qwi"

    session = make_session()
    if show_progress:
        print("Checking Census API key...")
    check_api_key(session, api_key)
    if show_progress:
        print("API key accepted.")
    if resume_run_id is None:
        if show_progress:
            print("Downloading current Census schema files...")
        schema = _download_schema(session, run_dir / "schema")
    else:
        schema = {
            name: pd.read_csv(run_dir / "schema" / name, dtype="string", keep_default_na=False)
            for name in SCHEMA_FILES
        }
    frames: list[pd.DataFrame] = []
    errors: list[dict[str, str]] = []

    requests_to_make = len(states) * len(age_groups)
    request_number = 0

    for state_value in states:
        state = _state_fips(state_value)
        for age_value in age_groups:
            age = age_value.strip().upper()
            request_number += 1
            if show_progress:
                print(
                    f"[{request_number}/{requests_to_make}] "
                    f"state {state}, age group {age}...",
                    end=" ",
                    flush=True,
                )
            filename = "_".join(
                [
                    f"state{state}",
                    _safe_name(_time_spec(time_spec)),
                    age,
                    f"ind{industry_level}",
                    ownership_code.upper(),
                ]
            )
            raw_path = response_dir / f"{filename}.json"
            metadata_path = response_dir / f"{filename}_metadata.json"
            try:
                if raw_path.exists() != metadata_path.exists():
                    raise RuntimeError(f"Only one file exists for saved QWI response {filename}.")
                if raw_path.exists():
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                    expected = build_qwi_parameters(
                        api_key=api_key, state_fips=state, time_spec=time_spec,
                        age_group=age, industry_level=industry_level,
                        ownership_code=ownership_code,
                    )
                    expected.pop("key")
                    if metadata.get("request_parameters") != expected:
                        raise RuntimeError(f"Saved request settings differ for {filename}.")
                    payload = json.loads(raw_path.read_text(encoding="utf-8"))
                    if not isinstance(payload, list) or not payload or not isinstance(payload[0], list):
                        raise RuntimeError(f"Saved QWI response is invalid: {filename}.")
                    raw = pd.DataFrame(payload[1:], columns=payload[0])
                    if len(raw) != metadata.get("row_count"):
                        raise RuntimeError(f"Saved QWI row count differs for {filename}.")
                    reused = True
                else:
                    raw, raw_text, metadata = _download_qwi(
                        session,
                        api_key=api_key,
                        state_fips=state,
                        time_spec=time_spec,
                        age_group=age,
                        industry_level=industry_level,
                        ownership_code=ownership_code,
                    )
                    _write_text(raw_path, raw_text)
                    _write_json(metadata_path, metadata)
                    reused = False
                frames.append(clean_qwi(raw, schema))
                if show_progress:
                    print(f"{'reused' if reused else 'saved'} {len(raw):,} rows")
            except Exception as exc:
                errors.append(
                    {
                        "state": state,
                        "age_group": age,
                        "error_type": type(exc).__name__,
                        "message": _redact(str(exc), api_key.strip()),
                    }
                )
                if show_progress:
                    print("failed (recorded in errors.json)")
            if pause_seconds > 0:
                time.sleep(pause_seconds)

    _write_json(response_dir / "errors.json", errors)
    session.close()

    if not frames:
        raise RuntimeError(f"No QWI request succeeded. Check {response_dir / 'errors.json'}")

    combined = pd.concat(frames, ignore_index=True)
    latest_common_period = _latest_common_period(combined)
    before_common_period_filter = len(combined)
    combined = combined.loc[combined["period"] <= latest_common_period].copy()
    validation = validate_qwi(combined)
    validation.update(
        {
            "run_id": run_id,
            "raw_directory": str(run_dir.relative_to(root)),
            "industry_level": industry_level,
            "working_file": str((interim_dir / f"{working_stem}.csv").relative_to(root)),
            "working_file_written": not errors,
            "latest_common_period": latest_common_period,
            "rows_returned_before_common_period_filter": before_common_period_filter,
            "successful_request_count": len(frames),
            "failed_request_count": len(errors),
        }
    )

    # A partial download is useful for diagnosis but must not replace a
    # previously complete working extract.
    if not errors:
        interim_dir.mkdir(parents=True, exist_ok=True)
        combined.to_csv(interim_dir / f"{working_stem}.csv", index=False)
        _write_json(interim_dir / f"{working_stem}_validation.json", validation)
    return combined, validation, errors


def run_research_pipeline(
    *,
    end_quarter: str | None = None,
    industry_level: str = "3",
    project_root: str | Path | None = None,
    resume_run_id: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any], list[dict[str, str]]]:
    """Collect the research QWI series (three-digit industries by default)."""
    from dotenv import load_dotenv

    root = (
        Path(project_root).resolve()
        if project_root is not None
        else Path(__file__).resolve().parents[1]
    )
    # Use this project's key even if the shell contains an older value.
    load_dotenv(root / ".env", override=True)
    api_key = os.getenv("CENSUS_API_KEY", "").strip()
    if not api_key or api_key == "replace_with_your_census_api_key":
        raise RuntimeError("Add a valid CENSUS_API_KEY to the project .env file.")

    last_quarter = end_quarter or _expected_latest_quarter()
    time_spec = f"from {RESEARCH_START_QUARTER} to {_time_spec(last_quarter)}"

    print("QWI research pipeline")
    print(f"Period requested: {time_spec}")
    print(f"Geographies: {len(RESEARCH_STATE_FIPS)} states/D.C.")
    print("Age groups: A03 (ages 22-24) and A00 (all ages)")
    print(f"Industry level: {industry_level}")
    print("Excluded:")
    for state, reason in EXCLUDED_STATES.items():
        print(f"  {state}: {reason}")

    data, validation, errors = run_qwi_download(
        api_key=api_key,
        states=RESEARCH_STATE_FIPS,
        time_spec=time_spec,
        age_groups=("A03", "A00"),
        industry_level=industry_level,
        ownership_code="A05",
        project_root=root,
        resume_run_id=resume_run_id,
    )
    validation["excluded_states"] = EXCLUDED_STATES
    print(f"\nRaw data: {validation['raw_directory']}")
    if errors:
        raise RuntimeError(
            f"{len(errors)} request(s) failed. Raw successes were preserved; "
            "the previous working file was not replaced. Review errors.json."
        )
    print(f"Working data: {validation['working_file']}")
    print(f"Rows: {len(data):,}")
    print(f"Latest common quarter: {validation['latest_common_period']}")
    print("Pipeline completed without request errors.")
    return data, validation, errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume-run-id", help="Complete an interrupted raw QWI run.")
    args = parser.parse_args()
    run_research_pipeline(resume_run_id=args.resume_run_id)
