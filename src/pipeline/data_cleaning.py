import pandas as pd
import argparse


def clean_data(df):
    # make a copy so we don't mess up the original dataframe
    df = df.copy()

    print(f"Starting rows: {len(df)}")

    # drop columns that are completely empty (can happen with scraped data)
    df = df.dropna(axis=1, how="all")

    # drop rows that are completely empty
    df = df.dropna(axis=0, how="all")

    # drop exact duplicate rows (common when scraping the same page twice)
    df = df.drop_duplicates()

    # strip extra whitespace and weird newlines/tabs from all text columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].str.replace(r"\s+", " ", regex=True)

    # replace common "empty" placeholders scrapers leave behind
    placeholders = ["", "nan", "none", "n/a", "null", "-"]
    df = df.replace(placeholders, pd.NA)

    # try to auto-detect and convert any column that looks like a date
    for col in df.columns:
        if "date" in col.lower():
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # drop rows that are now fully empty after cleaning
    df = df.dropna(axis=0, how="all")

    # reset index after all the dropping
    df = df.reset_index(drop=True)

    print(f"Rows after cleaning: {len(df)}")

    return df


if __name__ == "__main__":
    # lets anyone run this from the command line on any scraped csv
    parser = argparse.ArgumentParser(description="Clean a scraped data CSV file")
    parser.add_argument("input_file", help="path to the raw scraped CSV file")
    parser.add_argument("output_file", help="path to save the cleaned CSV file")
    args = parser.parse_args()

    df = pd.read_csv(args.input_file)
    cleaned_df = clean_data(df)
    cleaned_df.to_csv(args.output_file, index=False)
    print(f"Saved cleaned data to {args.output_file}")