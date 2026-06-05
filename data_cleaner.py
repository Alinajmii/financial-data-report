# data_cleaner.py
# src/data_cleaner.py

import pandas as pd
from pathlib import Path

def run_cleaner(input_df: pd.DataFrame, output_folder: str = "output") -> pd.DataFrame:
    """
    Cleans the raw DataFrame based on rules defined from the quality report.
    Saves the cleaned data and a cleaning report.
    Returns the cleaned DataFrame.
    """
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    initial_count = len(input_df)
    cleaning_log = []
    
    df = input_df.copy()
    
    # 1. Remove duplicates
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    cleaning_log.append(["Remove Duplicates", before - after])
    
    # 2. Handle missing dates
    if "Date" in df.columns:
        before = len(df)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        after = len(df)
        cleaning_log.append(["Remove Invalid/Missing Dates", before - after])
    
    # 3. Remove rows with critical missing values (including Date)
    critical_cols = ["Date", "Revenue", "Profit", "Cost", "Quantity"]
    before = len(df)
    df = df.dropna(subset=critical_cols)
    after = len(df)
    cleaning_log.append(["Drop Missing Critical Values", before - after])
    
    # 4. Fill non-critical missing values
    if "Customer_Segment" in df.columns:
        before_missing = df["Customer_Segment"].isna().sum()
        df["Customer_Segment"] = df["Customer_Segment"].fillna("Unknown")
        cleaning_log.append(["Fill Missing Customer_Segment", before_missing])
    
    if "Category" in df.columns:
        before_missing = df["Category"].isna().sum()
        df["Category"] = df["Category"].fillna("Unknown")
        cleaning_log.append(["Fill Missing Category", before_missing])
    
    # 5. Remove negative or invalid values (fixed: condition calculated each time)
    invalid_rules = {
        "Revenue < 0": lambda x: x["Revenue"] < 0,
        "Cost < 0": lambda x: x["Cost"] < 0,
        "Profit < 0": lambda x: x["Profit"] < 0,
        "Quantity <= 0": lambda x: x["Quantity"] <= 0,
        "Profit > Revenue": lambda x: x["Profit"] > x["Revenue"],
        "Discount_Percent < 0": lambda x: x["Discount_Percent"] < 0,
        "Discount_Percent > 100": lambda x: x["Discount_Percent"] > 100
    }
    
    for desc, condition_func in invalid_rules.items():
        before = len(df)
        df = df[~condition_func(df)]
        after = len(df)
        if before - after > 0:
            cleaning_log.append([desc, before - after])
    
    # 6. Reset index after all deletions
    df = df.reset_index(drop=True)
    
    # 7. Final count
    final_count = len(df)
    
    # Create cleaning report
    report_df = pd.DataFrame(cleaning_log, columns=["Action", "Affected_Rows"])
    report_df.loc["Total"] = ["Initial - Final", initial_count - final_count]
    
    # Save report
    report_path = Path(output_folder) / "cleaning_report.xlsx"
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        report_df.to_excel(writer, sheet_name="cleaning_log", index=False)
        
        summary_df = pd.DataFrame({
            "Metric": ["Rows Before", "Rows After", "Rows Removed"],
            "Value": [initial_count, final_count, initial_count - final_count]
        })
        summary_df.to_excel(writer, sheet_name="summary", index=False)
    
    # Save cleaned data
    clean_path = Path(output_folder) / "clean_data.xlsx"
    df.to_excel(clean_path, index=False)
    
    # Print summary
    print("\n" + "="*60)
    print("🧹 DATA CLEANING SUMMARY")
    print("="*60)
    print(f"✅ Rows BEFORE cleaning : {initial_count:,}")
    print(f"✅ Rows AFTER cleaning  : {final_count:,}")
    print(f"🔻 Rows REMOVED        : {initial_count - final_count:,}")
    print("\n📝 Cleaning Log:")
    for action, count in cleaning_log:
        if count > 0:
            print(f"   • {action:<35} : {count:>6,}")
    print("\n" + "="*60)
    print(f"💾 Cleaned data saved at : {clean_path}")
    print(f"📄 Cleaning report saved at : {report_path}")
    print("="*60)
    
    return df

if __name__ == "__main__":
    from data_loader import load_all_branches
    from data_quality import run_quality_checks
    
    raw_df = load_all_branches("branch_data_advanced")
    run_quality_checks(raw_df)
    clean_df = run_cleaner(raw_df)
    run_quality_checks(clean_df, output_folder="output/cleaned_quality")