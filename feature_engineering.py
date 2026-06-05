# src/feature_engineering.py

import pandas as pd
import numpy as np
from pathlib import Path

def run_feature_engineering(input_df: pd.DataFrame, output_folder: str = "output") -> pd.DataFrame:
    """
    Adds analytical features to the cleaned dataset.
    Saves the featured data and returns the enhanced DataFrame.
    """
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    df = input_df.copy()
    
    # 1. Time-based features (Gregorian calendar - no Iranian approximation)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month
        df["Quarter"] = df["Date"].dt.quarter
        df["Month_Name"] = df["Date"].dt.month_name()
        df["Weekday"] = df["Date"].dt.day_name()
        
        # Weekend based on Iran: Friday is official holiday
        df["Is_Weekend"] = df["Weekday"].isin(["Friday"]).astype(int)
        
        # Season based on Gregorian calendar
        def get_season(month):
            if month in [3, 4, 5]:
                return "Spring"
            elif month in [6, 7, 8]:
                return "Summer"
            elif month in [9, 10, 11]:
                return "Autumn"
            else:
                return "Winter"
        
        df["Season"] = df["Month"].apply(get_season)
    
    # 2. Profit Margin (with division by zero protection)
    revenue_not_zero = df["Revenue"] != 0
    df["Profit_Margin"] = 0.0
    df.loc[revenue_not_zero, "Profit_Margin"] = (
        df.loc[revenue_not_zero, "Profit"] / df.loc[revenue_not_zero, "Revenue"]
    ) * 100
    df["Profit_Margin"] = df["Profit_Margin"].round(2)
    
    # 3. Average Item Value (Revenue per unit)
    df["Avg_Item_Value"] = df["Revenue"] / df["Quantity"]
    df["Avg_Item_Value"] = df["Avg_Item_Value"].round(0).astype(int)
    
    # 4. Revenue Band (dynamic using qcut - based on distribution)
    try:
        df["Revenue_Band"], bins = pd.qcut(
            df["Revenue"], 
            q=4, 
            labels=["Low", "Medium", "High", "Premium"], 
            retbins=True,
            duplicates="drop"
        )
    except ValueError:
        # If qcut fails (not enough unique values), fallback to manual bins
        median = df["Revenue"].median()
        mean = df["Revenue"].mean()
        p75 = df["Revenue"].quantile(0.75)
        
        def manual_revenue_band(x):
            if x <= median:
                return "Low"
            elif x <= mean:
                return "Medium"
            elif x <= p75:
                return "High"
            else:
                return "Premium"
        
        df["Revenue_Band"] = df["Revenue"].apply(manual_revenue_band)
    
    # 5. Order Size (dynamic based on actual quantity distribution)
    q1 = df["Quantity"].quantile(0.25)
    q3 = df["Quantity"].quantile(0.75)
    
    def get_order_size(qty):
        if qty <= q1:
            return "Small"
        elif qty <= q3:
            return "Medium"
        else:
            return "Large"
    
    df["Order_Size"] = df["Quantity"].apply(get_order_size)
    
    # 6. Is Discounted
    df["Is_Discounted"] = (df["Discount_Percent"] > 0).astype(int)
    
    # 7. Price Category (Premium vs Standard) - with column existence check
    if "Category" in df.columns and "Unit_Price" in df.columns:
        avg_price_per_category = df.groupby("Category")["Unit_Price"].transform("mean")
        df["Is_Premium_Price"] = (df["Unit_Price"] > avg_price_per_category).astype(int)
    else:
        df["Is_Premium_Price"] = 0
    
    # 8. Revenue per Category (useful for later analysis)
    if "Category" in df.columns:
        df["Revenue_Per_Category"] = df.groupby("Category")["Revenue"].transform("sum")
    
    # 9. Clean up column order
    preferred_order = [
        "Order_ID", "Date", "Year", "Month", "Month_Name", "Quarter", "Season",
        "Weekday", "Is_Weekend", "Branch", "Category", "Product", "Customer_Segment",
        "Quantity", "Order_Size", "Unit_Price", "Avg_Item_Value", "Is_Premium_Price",
        "Discount_Percent", "Is_Discounted", "Revenue", "Revenue_Band", "Revenue_Per_Category",
        "Cost", "Profit", "Profit_Margin"
    ]
    
    existing_cols = [col for col in preferred_order if col in df.columns]
    df = df[existing_cols + [col for col in df.columns if col not in existing_cols]]
    
    # Save output
    output_path = Path(output_folder) / "featured_data.xlsx"
    df.to_excel(output_path, index=False)
    
    # Print summary
    print("\n" + "="*60)
    print("🔧 FEATURE ENGINEERING SUMMARY")
    print("="*60)
    print(f"✅ New features added:")
    print("   • Year, Month, Quarter, Month_Name, Weekday, Is_Weekend, Season")
    print("   • Profit_Margin (with zero-protection)")
    print("   • Avg_Item_Value")
    print("   • Revenue_Band (dynamic: Low, Medium, High, Premium)")
    print("   • Order_Size (dynamic based on Q1/Q3: Small, Medium, Large)")
    print("   • Is_Discounted")
    print("   • Is_Premium_Price (only if Category exists)")
    print("   • Revenue_Per_Category (only if Category exists)")
    print(f"\n💾 Featured data saved at : {output_path}")
    print("="*60)
    
    return df

if __name__ == "__main__":
    from data_loader import load_all_branches
    from data_quality import run_quality_checks
    from data_cleaner import run_cleaner
    
    print("🚀 Running full pipeline up to Feature Engineering...")
    
    raw_df = load_all_branches("branch_data_advanced")
    run_quality_checks(raw_df)
    clean_df = run_cleaner(raw_df)
    featured_df = run_feature_engineering(clean_df)
    
    print("\n✅ Pipeline completed. Featured data is ready for KPI calculation.")