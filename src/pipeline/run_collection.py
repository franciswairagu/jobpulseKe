import os
import re
import hashlib
import pandas as pd

from collectors.myjobmag import collect as collect_myjobmag
from collectors.myjobmag_historical import (
    collect as collect_myjobmag_historical
)

from collectors.fuzu import collect as collect_fuzu
from collectors.fuzu_historical import (
    collect as collect_fuzu_historical
)

from collectors.brightermonday import (
    collect as collect_brightermonday
)

from collectors.brightermonday_historical import (
    collect_historical_jobs as collect_brightermonday_historical
)

from collectors.jobicy import (
    collect as collect_jobicy
)

from collectors.remotive import (
    collect as collect_remotive
)


# CONFIGURATION

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

MASTER_FILE = (
    f"{PROCESSED_DIR}/kenya_tech_jobs.csv"
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


# TEXT CLEANING

def clean_text(value):

    if pd.isna(value):
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value)
    ).strip()


def normalize_company(company):

    company = clean_text(
        company
    ).lower()

    company = re.sub(
        r"[^a-z0-9\s]",
        " ",
        company
    )

    company = re.sub(
        r"\s+",
        " ",
        company
    )

    return company.strip()


def normalize_title(title):

    title = clean_text(
        title
    ).lower()

    title = re.sub(
        r"[^a-z0-9\s]",
        " ",
        title
    )

    title = re.sub(
        r"\s+",
        " ",
        title
    )

    return title.strip()


def normalize_location(location):

    location = clean_text(
        location
    ).lower()

    location = re.sub(
        r"[^a-z0-9\s]",
        " ",
        location
    )

    location = re.sub(
        r"\s+",
        " ",
        location
    )

    return location.strip()


# DUPLICATE FINGERPRINT

def create_fingerprint(row):

    title = normalize_title(
        row.get(
            "job_title",
            ""
        )
    )

    company = normalize_company(
        row.get(
            "company",
            ""
        )
    )

    location = normalize_location(
        row.get(
            "location",
            ""
        )
    )

    return hashlib.sha256(
        f"{title}|{company}|{location}".encode(
            "utf-8"
        )
    ).hexdigest()[:20]


# NORMALIZE DATAFRAME

def normalize_dataframe(df):

    if df is None:
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    df = df.copy()

    # Remove internal columns

    internal_columns = [
        column
        for column in df.columns
        if column.startswith("_")
    ]

    if internal_columns:

        df = df.drop(
            columns=internal_columns
        )

    # Ensure schema

    for column in STANDARD_COLUMNS:

        if column not in df.columns:

            df[column] = ""

    # Keep standard schema

    df = df[
        STANDARD_COLUMNS
    ].copy()

    # Clean text fields

    text_columns = [
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
        "source",
        "source_job_id",
        "job_id",
        "scraped_at",
    ]

    for column in text_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .fillna("")
                .map(clean_text)
            )

    # Remote flag

    df["remote_eligible"] = (
        pd.to_numeric(
            df["remote_eligible"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    # Remove empty titles

    df = df[
        df["job_title"].str.len() > 2
    ]

    # Remove duplicate URLs

    df = df.drop_duplicates(
        subset=[
            "vacancy_url"
        ],
        keep="first"
    )

    # Cross-source fingerprint

    df["_fingerprint"] = df.apply(
        create_fingerprint,
        axis=1
    )

    df = df.drop_duplicates(
        subset=[
            "_fingerprint"
        ],
        keep="first"
    )

    df = df.drop(
        columns=[
            "_fingerprint"
        ]
    )

    return df.reset_index(
        drop=True
    )


# SAVE RAW SOURCE

def save_raw(
    df,
    filename
):

    if df is None:
        return

    os.makedirs(
        RAW_DIR,
        exist_ok=True
    )

    path = os.path.join(
        RAW_DIR,
        filename
    )

    df.to_csv(
        path,
        index=False
    )

    print(
        f"Saved: {path}"
    )


# LOAD EXISTING MASTER

def load_existing_master():

    if not os.path.exists(
        MASTER_FILE
    ):

        print(
            "No existing master CSV found."
        )

        return pd.DataFrame()

    print()
    print(
        "Loading existing master:"
    )
    print(
        MASTER_FILE
    )

    df = pd.read_csv(
        MASTER_FILE
    )

    print(
        f"Existing master records: "
        f"{len(df)}"
    )

    return df


# COLLECTOR RUNNER

def run_collector(
    name,
    collector,
    filename,
    **kwargs
):

    print()
    print("=" * 75)
    print(
        f"SOURCE: {name}"
    )
    print("=" * 75)

    try:

        df = collector(
            **kwargs
        )

        if df is None:
            df = pd.DataFrame()

        print(
            f"{name} returned: "
            f"{len(df)} records"
        )

        if not df.empty:

            save_raw(
                df,
                filename
            )

        return df

    except Exception as e:

        print()
        print(
            f"{name} FAILED:"
        )
        print(
            repr(e)
        )

        return pd.DataFrame()


# MAIN

def main():

    os.makedirs(
        RAW_DIR,
        exist_ok=True
    )

    os.makedirs(
        PROCESSED_DIR,
        exist_ok=True
    )

    print()
    print("=" * 75)
    print(
        "JOBPULSE MASTER COLLECTION"
    )
    print("=" * 75)

    # LOAD EXISTING MASTER

    existing_master = (
        load_existing_master()
    )

    frames = []

    if not existing_master.empty:

        frames.append(
            existing_master
        )

    # 1. MYJOBMAG CURRENT

    myjobmag_df = run_collector(
        "MyJobMag Current",
        collect_myjobmag,
        "myjobmag_jobs.csv"
    )

    frames.append(
        myjobmag_df
    )

    # 2. MYJOBMAG HISTORICAL

    myjobmag_historical_df = (
        run_collector(
            "MyJobMag Historical",
            collect_myjobmag_historical,
            "myjobmag_historical_jobs.csv"
        )
    )

    frames.append(
        myjobmag_historical_df
    )

    # 3. FUZU CURRENT

    fuzu_df = run_collector(
        "Fuzu Current",
        collect_fuzu,
        "fuzu_jobs.csv"
    )

    frames.append(
        fuzu_df
    )

    # 4. FUZU HISTORICAL

    fuzu_historical_df = (
        run_collector(
            "Fuzu Historical",
            collect_fuzu_historical,
            "fuzu_historical_jobs.csv"
        )
    )

    frames.append(
        fuzu_historical_df
    )

    # 5. BRIGHTERMONDAY CURRENT

    brightermonday_df = (
        run_collector(
            "BrighterMonday Current",
            collect_brightermonday,
            "brightermonday_jobs.csv",
            max_pages=10
        )
    )

    frames.append(
        brightermonday_df
    )

    # 6. BRIGHTERMONDAY HISTORICAL

    brightermonday_historical_df = (
        run_collector(
            "BrighterMonday Historical",
            collect_brightermonday_historical,
            "brightermonday_historical_jobs.csv"
        )
    )

    frames.append(
        brightermonday_historical_df
    )

    # 7. JOBICY

    jobicy_df = run_collector(
        "Jobicy",
        collect_jobicy,
        "jobicy_jobs.csv",
        count=100
    )

    frames.append(
        jobicy_df
    )

    # 8. REMOTIVE

    remotive_df = run_collector(
        "Remotive",
        collect_remotive,
        "remotive_jobs.csv",
        limit=100
    )

    frames.append(
        remotive_df
    )

    # REMOVE EMPTY DATAFRAMES

    frames = [
        df
        for df in frames
        if df is not None
        and not df.empty
    ]

    if not frames:

        print()
        print(
            "No data collected."
        )

        return

    # COMBINE EVERYTHING

    print()
    print("=" * 75)
    print(
        "BUILDING MASTER DATASET"
    )
    print("=" * 75)

    combined = pd.concat(
        frames,
        ignore_index=True
    )

    print(
        f"Combined records before "
        f"deduplication: {len(combined)}"
    )

    # NORMALIZE

    final_df = normalize_dataframe(
        combined
    )

    print(
        f"Final unique records: "
        f"{len(final_df)}"
    )

    # SAVE MASTER

    final_df.to_csv(
        MASTER_FILE,
        index=False
    )

    # REPORT

    print()
    print("=" * 75)
    print(
        "MASTER DATASET COMPLETE"
    )
    print("=" * 75)

    print(
        f"Total records: "
        f"{len(final_df)}"
    )

    print()

    print(
        "BY SOURCE"
    )

    print(
        final_df[
            "source"
        ]
        .value_counts()
        .to_string()
    )

    print()

    print(
        "BY TECH CATEGORY"
    )

    print(
        final_df[
            "tech_category"
        ]
        .value_counts()
        .to_string()
    )

    print()

    print(
        "BY WORK MODE"
    )

    print(
        final_df[
            "work_mode"
        ]
        .replace(
            "",
            "Not specified"
        )
        .value_counts()
        .to_string()
    )

    print()

    print(
        "BY COUNTRY"
    )

    print(
        final_df[
            "country"
        ]
        .replace(
            "",
            "Not specified"
        )
        .value_counts()
        .head(20)
        .to_string()
    )

    print()
    print(
        "MASTER FILE:"
    )

    print(
        MASTER_FILE
    )

    print()
    print("=" * 75)
    print(
        "JOBPULSE COLLECTION FINISHED"
    )
    print("=" * 75)


if __name__ == "__main__":

    main()