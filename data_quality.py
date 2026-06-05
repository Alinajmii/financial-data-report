# src/data_quality.py

import pandas as pd
from pathlib import Path

def run_quality_checks(df: pd.DataFrame, output_folder: str = "output") -> None:
    """
    Performs data quality checks on the master DataFrame.
    No cleaning, only reporting.
    Saves a quality report as Excel file.
    Returns nothing, only produces the report.
    """
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    quality_report = {}
    
    # 0. Dataset Info
    info_df = pd.DataFrame({
        "Metric": ["Rows", "Columns"],
        "Value": [df.shape[0], df.shape[1]]
    })
    quality_report["dataset_info"] = info_df
    
    # 1. Missing values (with percentage)
    missing_counts = df.isnull().sum()
    missing_pct = (missing_counts / len(df)) * 100
    missing_df = pd.DataFrame({
        "Column": missing_counts.index,
        "Missing_Count": missing_counts.values,
        "Missing_Percent": missing_pct.values
    })
    missing_df = missing_df[missing_df["Missing_Count"] > 0]
    quality_report["missing_values"] = missing_df
    
    # 2. Duplicate rows
    duplicate_count = df.duplicated().sum()
    duplicate_pct = (duplicate_count / len(df)) * 100
    quality_report["duplicate_rows"] = pd.DataFrame({
        "Count": [duplicate_count],
        "Percent": [duplicate_pct]
    })
    
    # 3. Date validation (without modifying original df)
    if "Date" in df.columns:
        date_series = pd.to_datetime(df["Date"], errors="coerce")
        min_date = date_series.min()
        max_date = date_series.max()
        null_dates = date_series.isnull().sum()
        
        quality_report["date_validation"] = pd.DataFrame({
            "Check": ["Min Date", "Max Date", "Null Dates"],
            "Value": [min_date, max_date, null_dates]
        })
    
    # 4. Invalid values (with division by zero protection)
    profit_margin = pd.Series(0.0, index=df.index)
    revenue_not_zero = df["Revenue"] != 0
    profit_margin[revenue_not_zero] = (df.loc[revenue_not_zero, "Profit"] / df.loc[revenue_not_zero, "Revenue"]) * 100
    
    quality_report["invalid_values"] = pd.DataFrame({
        "Check": [
            "Revenue < 0",
            "Profit < 0",
            "Cost < 0",
            "Quantity <= 0",
            "Discount_Percent < 0",
            "Profit > Revenue",
            "Profit_Margin > 50%"
        ],
        "Count": [
            (df["Revenue"] < 0).sum(),
            (df["Profit"] < 0).sum(),
            (df["Cost"] < 0).sum(),
            (df["Quantity"] <= 0).sum(),
            (df["Discount_Percent"] < 0).sum(),
            (df["Profit"] > df["Revenue"]).sum(),
            (profit_margin > 50).sum()
        ]
    })
    
    # 5. Branch summary
    if "Branch" in df.columns:
        branch_summary = df.groupby("Branch").agg({
            "Order_ID": "count",
            "Revenue": "sum",
            "Profit": "sum"
        }).rename(columns={"Order_ID": "Record_Count"}).reset_index()
        quality_report["branch_summary"] = branch_summary
    
    # 6. Product summary
    if "Product" in df.columns:
        product_summary = df.groupby("Product").agg({
            "Order_ID": "count",
            "Revenue": "sum",
            "Profit": "sum"
        }).rename(columns={"Order_ID": "Record_Count"}).reset_index()
        quality_report["product_summary"] = product_summary
    
    # 7. Category summary
    if "Category" in df.columns:
        category_summary = df.groupby("Category").agg({
            "Order_ID": "count",
            "Revenue": "sum",
            "Profit": "sum"
        }).rename(columns={"Order_ID": "Record_Count"}).reset_index()
        quality_report["category_summary"] = category_summary
    
    # 8. Customer Segment summary
    if "Customer_Segment" in df.columns:
        customer_summary = df.groupby("Customer_Segment").agg({
            "Order_ID": "count",
            "Revenue": "sum",
            "Profit": "sum"
        }).rename(columns={"Order_ID": "Record_Count"}).reset_index()
        quality_report["customer_summary"] = customer_summary
    
    # Save report
    output_path = Path(output_folder) / "quality_report.xlsx"
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, data in quality_report.items():
            data.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # Print summary
    print("\n" + "="*70)
    print("📋 DATA QUALITY REPORT (Complete)")
    print("="*70)
    print(f"📊 Dataset Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"\n🔍 Missing Values:\n{missing_df.to_string(index=False) if not missing_df.empty else '   None'}")
    print(f"\n🔁 Duplicate Rows: {duplicate_count} ({duplicate_pct:.2f}%)")
    print("\n⚠️ Invalid Values:")
    for _, row in quality_report["invalid_values"].iterrows():
        print(f"   {row['Check']}: {int(row['Count'])}")
    
    if "date_validation" in quality_report:
        print("\n📅 Date Validation:")
        for _, row in quality_report["date_validation"].iterrows():
            print(f"   {row['Check']}: {row['Value']}")
    
    if "branch_summary" in quality_report:
        print("\n📂 Branch Summary (Top 5 by Revenue):")
        print(branch_summary.sort_values("Revenue", ascending=False).head(5).to_string(index=False))
    
    if "product_summary" in quality_report:
        print("\n📦 Product Summary (Top 5 by Revenue):")
        print(product_summary.sort_values("Revenue", ascending=False).head(5).to_string(index=False))
    
    if "category_summary" in quality_report:
        print("\n🏷️ Category Summary:")
        print(category_summary.to_string(index=False))
    
    if "customer_summary" in quality_report:
        print("\n👥 Customer Segment Summary:")
        print(customer_summary.to_string(index=False))
    
    print("="*70)
    print(f"✅ Full quality report saved at: {output_path}")

if __name__ == "__main__":
    from data_loader import load_all_branches
    
    df_master = load_all_branches("branch_data_advanced")
    run_quality_checks(df_master)