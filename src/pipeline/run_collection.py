import os
import re
import hashlib

import pandas as pd

from collectors.myjobmag import collect as collect_myjobmag
from collectors.fuzu import collect as collect_fuzu
from collectors.brightermonday import (
    collect as collect_brightermonday
)
from collectors.jobicy import (
    collect as collect_jobicy
)

from collectors.remotive import (
    collect as collect_remotive
)

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

FINAL_OUTPUT = (
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


def create_fingerprint(row):

    title = normalize_title(
        row["job_title"]
    )

    company = normalize_company(
        row["company"]
    )

    location = normalize_location(
        row["location"]
    )

    return hashlib.sha256(
        f"{title}|{company}|{location}".encode(
            "utf-8"
        )
    ).hexdigest()[:20]


def normalize_dataframe(df):

    if df.empty:
        return df

    # Remove internal collector columns
    internal_columns = [
        column
        for column in df.columns
        if column.startswith("_")
    ]

    if internal_columns:

        df = df.drop(
            columns=internal_columns
        )

    # Ensure all standard columns exist
    for column in STANDARD_COLUMNS:

        if column not in df.columns:

            df[column] = ""

    # Keep only unified schema
    df = df[
        STANDARD_COLUMNS
    ].copy()

    # Clean text
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
    ]

    for column in text_columns:

        df[column] = (
            df[column]
            .fillna("")
            .map(clean_text)
        )

    # Boolean-ish fields
    df["remote_eligible"] = (
        pd.to_numeric(
            df["remote_eligible"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    # Remove completely empty titles
    df = df[
        df["job_title"].str.len() > 2
    ]

    # Create duplicate fingerprint
    df["_fingerprint"] = df.apply(
        create_fingerprint,
        axis=1
    )

    # URL duplicates
    df = df.drop_duplicates(
        subset=[
            "vacancy_url"
        ]
    )

    # Cross-source duplicates
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


def save_raw(
    df,
    filename
):

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
        f"Saved raw source: {path}"
    )


def main():

    os.makedirs(
        RAW_DIR,
        exist_ok=True
    )

    os.makedirs(
        PROCESSED_DIR,
        exist_ok=True
    )

    print("=" * 75)
    print(
        "JOBPULSE MULTI-SOURCE COLLECTION"
    )
    print("=" * 75)

    # ========================================================
    # MYJOBMAG
    # ========================================================

    print()
    print(
        "SOURCE 1: MyJobMag"
    )

    try:

        myjobmag_df = collect_myjobmag()

        save_raw(
            myjobmag_df,
            "myjobmag_jobs.csv"
        )

    except Exception as e:

        print(
            f"MyJobMag failed: {e}"
        )

        myjobmag_df = pd.DataFrame()
    print(
        f"Records returned: {len(myjobmag_df)}"
    )

    # ========================================================
    # FUZU
    # ========================================================

    print()
    print(
        "SOURCE 2: Fuzu"
    )

    try:

        fuzu_df = collect_fuzu()

        save_raw(
            fuzu_df,
            "fuzu_jobs.csv"
        )

    except Exception as e:

        print(
            f"Fuzu failed: {e}"
        )

        fuzu_df = pd.DataFrame()
    print(
        f"Records returned: {len(fuzu_df)}"
    )

    # ========================================================
    # BRIGHTERMONDAY
    # ========================================================

    print()
    print(
        "SOURCE 3: BrighterMonday"
    )

    try:

        brightermonday_df = (
            collect_brightermonday(
                max_pages=10
            )
        )

        save_raw(
            brightermonday_df,
            "brightermonday_jobs.csv"
        )

    except Exception as e:

        print(
            f"BrighterMonday failed: {e}"
        )

        brightermonday_df = pd.DataFrame()
    print(
        f"Records returned: {len(brightermonday_df)}"
    )

    # ========================================================
    # JOBICY
    # ========================================================

    print()
    print(
        "SOURCE 4: Jobicy"
    )

    try:

        jobicy_df = collect_jobicy(
            count=100
        )

        save_raw(
            jobicy_df,
            "jobicy_jobs.csv"
        )

        print(
            f"Records returned: "
            f"{len(jobicy_df)}"
        )

    except Exception as e:

        print(
            f"Jobicy failed: {e}"
        )

        jobicy_df = pd.DataFrame()


    # ========================================================
    # REMOTIVE
    # ========================================================

    print()
    print(
        "SOURCE 5: Remotive"
    )

    try:

        remotive_df = collect_remotive(
            limit=100
        )

        save_raw(
            remotive_df,
            "remotive_jobs.csv"
        )

        print(
            f"Records returned: "
            f"{len(remotive_df)}"
        )

    except Exception as e:

        print(
            f"Remotive failed: {e}"
        )

        remotive_df = pd.DataFrame()

    # ========================================================
    # COMBINE
    # ========================================================

    print()
    print(
        "COMBINING SOURCES"
    )

    frames = [
        df
        for df in [
            myjobmag_df,
            fuzu_df,
            brightermonday_df,
            jobicy_df,
            remotive_df,
        ]
        if not df.empty
    ]
    

    if not frames:

        print(
            "No source returned data."
        )

        return

    combined = pd.concat(
        frames,
        ignore_index=True
    )

    print(
        f"Raw combined records: "
        f"{len(combined)}"
    )

    # ========================================================
    # NORMALIZE / DEDUPLICATE
    # ========================================================

    final_df = normalize_dataframe(
        combined
    )

    print(
        f"After deduplication: "
        f"{len(final_df)}"
    )

    # ========================================================
    # FINAL TECH FILTER
    # ========================================================

    # Each source already feeds us technology-oriented
    # listings. MyJobMag has an additional title filter.
    #
    # We therefore don't run another aggressive NLP filter here.
    #
    # That comes later in processing and can be evaluated.

    # ========================================================
    # SAVE
    # ========================================================

    final_df.to_csv(
        FINAL_OUTPUT,
        index=False
    )

    # ========================================================
    # REPORT
    # ========================================================

    print()
    print("=" * 75)
    print(
        "COLLECTION COMPLETE"
    )
    print("=" * 75)

    print(
        f"Final records: "
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
        .value_counts()
        .to_string()
    )

    print()

    print(
        f"Saved final dataset to:"
    )

    print(
        FINAL_OUTPUT
    )


if __name__ == "__main__":
    main()