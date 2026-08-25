import os
import re
import hashlib
import pandas as pd


RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

MASTER_FILE = (
    f"{PROCESSED_DIR}/kenya_tech_jobs_master.csv"
)


STANDARD_COLUMNS = [
    "job_id",
    "source",
    "source_job_id",
    "job_title",
    "company",
    "job_description",
    "location",
    "country",
    "work_mode",
    "remote_eligible",
    "remote_scope",
    "job_field",
    "industry",
    "employment_type",
    "experience_required",
    "education_required",
    "salary",
    "currency",
    "date_posted",
    "application_deadline",
    "tech_category",
    "vacancy_url",
    "scraped_at",
]


# ============================================================
# CLEANING
# ============================================================

def clean_text(value):

    if pd.isna(value):
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value)
    ).strip()


def normalize_text(value):

    value = clean_text(
        value
    ).lower()

    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# ============================================================
# DUPLICATE FINGERPRINT
# ============================================================

def create_fingerprint(row):

    title = normalize_text(
        row["job_title"]
    )

    company = normalize_text(
        row["company"]
    )

    location = normalize_text(
        row["location"]
    )

    return hashlib.sha256(
        (
            f"{title}|"
            f"{company}|"
            f"{location}"
        ).encode("utf-8")
    ).hexdigest()[:20]


# ============================================================
# NORMALIZE DATAFRAME
# ============================================================

def normalize_dataframe(df):

    if df.empty:
        return df

    df = df.copy()

    # --------------------------------------------------------
    # Ensure schema
    # --------------------------------------------------------

    for column in STANDARD_COLUMNS:

        if column not in df.columns:

            df[column] = ""

    df = df[
        STANDARD_COLUMNS
    ].copy()

    # --------------------------------------------------------
    # Clean text fields
    # --------------------------------------------------------

    text_columns = [
        "job_id",
        "source",
        "source_job_id",
        "job_title",
        "company",
        "job_description",
        "location",
        "country",
        "work_mode",
        "remote_scope",
        "job_field",
        "industry",
        "employment_type",
        "experience_required",
        "education_required",
        "salary",
        "currency",
        "date_posted",
        "application_deadline",
        "tech_category",
        "vacancy_url",
        "scraped_at",
    ]

    for column in text_columns:

        df[column] = (
            df[column]
            .fillna("")
            .map(clean_text)
        )

    # --------------------------------------------------------
    # Remote flag
    # --------------------------------------------------------

    df["remote_eligible"] = (
        pd.to_numeric(
            df["remote_eligible"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    # --------------------------------------------------------
    # Remove invalid titles
    # --------------------------------------------------------

    df = df[
        df["job_title"].str.len() > 2
    ]

    # --------------------------------------------------------
    # Remove duplicate URLs
    # --------------------------------------------------------

    df = df[
        df["vacancy_url"] != ""
    ]

    df = df.drop_duplicates(
        subset=["vacancy_url"],
        keep="first"
    )

    # --------------------------------------------------------
    # Cross-source fingerprint
    # --------------------------------------------------------

    df["_fingerprint"] = df.apply(
        create_fingerprint,
        axis=1
    )

    df = df.drop_duplicates(
        subset=["_fingerprint"],
        keep="first"
    )

    df = df.drop(
        columns=["_fingerprint"]
    )

    return df.reset_index(
        drop=True
    )


# ============================================================
# LOAD SOURCE FILES
# ============================================================

def load_source_files():

    files = [
        "myjobmag_jobs.csv",
        "myjobmag_historical_jobs.csv",

        "fuzu_jobs.csv",
        "fuzu_historical_jobs.csv",

        "brightermonday_jobs.csv",
        "brightermonday_historical_jobs.csv",

        "jobicy_jobs.csv",
        "remotive_jobs.csv",
    ]

    frames = []

    print()
    print("=" * 75)
    print("LOADING JOBPULSE SOURCE DATA")
    print("=" * 75)

    for filename in files:

        path = os.path.join(
            RAW_DIR,
            filename
        )

        if not os.path.exists(path):

            print(
                f"Skipping missing: {filename}"
            )

            continue

        try:

            df = pd.read_csv(
                path,
                low_memory=False
            )

            print(
                f"{filename:<40}"
                f"{len(df):>6} records"
            )

            frames.append(
                df
            )

        except Exception as e:

            print(
                f"Failed {filename}: {e}"
            )

    return frames


# ============================================================
# BUILD MASTER
# ============================================================

def build_master():

    os.makedirs(
        PROCESSED_DIR,
        exist_ok=True
    )

    frames = load_source_files()

    if not frames:

        print(
            "No source files found."
        )

        return

    combined = pd.concat(
        frames,
        ignore_index=True
    )

    print()
    print(
        f"Raw accumulated records: "
        f"{len(combined)}"
    )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    master = normalize_dataframe(
        combined
    )

    print(
        f"After deduplication: "
        f"{len(master)}"
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    master = master.sort_values(
        by=[
            "date_posted",
            "source",
            "job_title",
        ],
        ascending=[
            False,
            True,
            True,
        ],
        na_position="last"
    )

    master = master.reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    master.to_csv(
        MASTER_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print()
    print("=" * 75)
    print("JOBPULSE MASTER DATASET")
    print("=" * 75)

    print(
        f"MASTER RECORDS: {len(master)}"
    )

    print()
    print("BY SOURCE")

    print(
        master["source"]
        .value_counts()
        .to_string()
    )

    print()
    print("BY TECH CATEGORY")

    print(
        master["tech_category"]
        .value_counts()
        .to_string()
    )

    print()
    print("DATE COVERAGE")

    raw_dates = master["date_posted"].astype(str).str.strip()

    # Parse dates safely
    dates = pd.to_datetime(
        raw_dates,
        errors="coerce",
        utc=True,
        dayfirst=True
    )

    # Remove timezone so comparisons are consistent
    dates = dates.dt.tz_localize(None)

    # Remove obviously invalid dates
    valid_dates = dates[
        (dates >= pd.Timestamp("2020-01-01")) &
        (dates <= pd.Timestamp.today())
    ]

    print(f"Valid dates: {valid_dates.notna().sum()}")
    print(f"Invalid/missing dates: {dates.isna().sum()}")

    if len(valid_dates) > 0:
        print(f"Earliest: {valid_dates.min().date()}")
        print(f"Latest: {valid_dates.max().date()}")
    else:
        print("No valid dates found.")

    print()
    print(
        f"Saved master dataset:"
    )

    print(
        MASTER_FILE
    )

    print("=" * 75)


if __name__ == "__main__":

    build_master()