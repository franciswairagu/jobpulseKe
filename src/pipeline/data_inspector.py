import pandas as pd

def inspect(filepath):
    # load the data into a pandas dataframe
    df = pd.read_csv(filepath)

    # Inspect data info
    print("="*10)
    print("DATA INFO")
    print("="*10)
    print(f"\n{df.info()}")

    # Check missing values 
    print("="*10)
    print("MISSING VALUES")
    print("="*10)
    print(f"\n{df.isna().sum()}")

    