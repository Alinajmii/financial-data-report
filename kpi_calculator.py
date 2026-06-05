# src/kpi_calculator.py

import pandas as pd
from pathlib import Path

def run_kpi_calculator(input_df: pd.DataFrame) -> dict:
    """
    Calculates all Key Performance Indicators (KPIs) from the featured dataset.
    Returns a dictionary of dataframes (raw numbers, no string formatting).
    Formatting belongs to report_generator.py or dashboard_builder.py.
    """
    df = input_df.copy()
    
    kpi_dfs = {}
    
    # ==========================================
    # Sheet 1: Executive Summary (raw numbers)
    # ==========================================
    total_revenue = df["Revenue"].sum()
    total_cost = df["Cost"].sum()
    total_profit = df["Profit"].sum()
    profit_margin = (total_profit / total_revenue * 100) if total_revenue != 0 else 0
    total_orders = df["Order_ID"].nunique()
    total_quantity = df["Quantity"].sum()
    avg_order_value = total_revenue / total_orders if total_orders != 0 else 0
    avg_quantity_per_order = total_quantity / total_orders if total_orders != 0 else 0
    avg_profit_per_order = total_profit / total_orders if total_orders != 0 else 0
    
    executive_df = pd.DataFrame({
        "Metric": [
            "Total Revenue (Toman)",
            "Total Cost (Toman)",
            "Total Profit (Toman)",
            "Profit Margin (%)",
            "Total Orders",
            "Total Quantity Sold",
            "Average Order Value (Toman)",
            "Average Quantity per Order",
            "Average Profit per Order (Toman)"
        ],
        "Value": [
            total_revenue,
            total_cost,
            total_profit,
            profit_margin,
            total_orders,
            total_quantity,
            avg_order_value,
            avg_quantity_per_order,
            avg_profit_per_order
        ]
    })
    kpi_dfs["executive_summary"] = executive_df
    
    # ==========================================
    # Sheet 2: Branch KPIs (raw numbers)
    # ==========================================
    branch_kpis = df.groupby("Branch").agg({
        "Revenue": "sum",
        "Profit": "sum",
        "Order_ID": "nunique",
        "Quantity": "sum"
    }).rename(columns={"Order_ID": "Orders"}).reset_index()
    
    # Safe division for Profit Margin
    branch_kpis["Profit_Margin_%"] = (
        branch_kpis["Profit"]
        .div(branch_kpis["Revenue"])
        .replace([float("inf"), -float("inf")], 0)
        .fillna(0) * 100
    ).round(2)
    
    kpi_dfs["branch_kpis"] = branch_kpis
    
    # ==========================================
    # Sheet 3: Product KPIs (raw numbers)
    # ==========================================
    product_kpis = df.groupby("Product").agg({
        "Revenue": "sum",
        "Profit": "sum",
        "Order_ID": "nunique",
        "Quantity": "sum"
    }).rename(columns={"Order_ID": "Orders"}).reset_index()
    
    # Add Profit Margin for products
    product_kpis["Profit_Margin_%"] = (
        product_kpis["Profit"]
        .div(product_kpis["Revenue"])
        .replace([float("inf"), -float("inf")], 0)
        .fillna(0) * 100
    ).round(2)
    
    product_kpis = product_kpis.sort_values("Revenue", ascending=False)
    kpi_dfs["product_kpis"] = product_kpis
    
    # ==========================================
    # Sheet 4: Category KPIs (if Category exists)
    # ==========================================
    if "Category" in df.columns:
        category_kpis = df.groupby("Category").agg({
            "Revenue": "sum",
            "Profit": "sum",
            "Order_ID": "nunique"
        }).rename(columns={"Order_ID": "Orders"}).reset_index()
        category_kpis = category_kpis.sort_values("Revenue", ascending=False)
        kpi_dfs["category_kpis"] = category_kpis
    
    # ==========================================
    # Sheet 5: Customer Segment KPIs (if exists)
    # ==========================================
    if "Customer_Segment" in df.columns:
        segment_kpis = df.groupby("Customer_Segment").agg({
            "Revenue": "sum",
            "Profit": "sum",
            "Order_ID": "nunique"
        }).rename(columns={"Order_ID": "Orders"}).reset_index()
        segment_kpis = segment_kpis.sort_values("Revenue", ascending=False)
        kpi_dfs["customer_segment_kpis"] = segment_kpis
    
    # ==========================================
    # Sheet 6: Monthly KPIs with Growth (rounded, no NaN)
    # ==========================================
    df["YearMonth"] = df["Date"].dt.strftime("%Y-%m")
    monthly_kpis = df.groupby("YearMonth").agg({
        "Revenue": "sum",
        "Profit": "sum",
        "Order_ID": "nunique",
        "Quantity": "sum"
    }).rename(columns={"Order_ID": "Orders"}).reset_index()
    monthly_kpis = monthly_kpis.sort_values("YearMonth").reset_index(drop=True)
    
    # Add Growth metrics with rounding and fill NaN with 0
    monthly_kpis["Revenue_Growth_%"] = (monthly_kpis["Revenue"].pct_change() * 100).round(2).fillna(0)
    monthly_kpis["Profit_Growth_%"] = (monthly_kpis["Profit"].pct_change() * 100).round(2).fillna(0)
    monthly_kpis["Orders_Growth_%"] = (monthly_kpis["Orders"].pct_change() * 100).round(2).fillna(0)
    
    kpi_dfs["monthly_kpis"] = monthly_kpis
    
    # ==========================================
    # Sheet 7: Top Performers (unified column names)
    # ==========================================
    # Top 5 Branches by Revenue
    branch_revenue = df.groupby("Branch")["Revenue"].sum().sort_values(ascending=False).head(5)
    top_branches = pd.DataFrame({
        "Category": ["Top Branches"] * len(branch_revenue),
        "Rank": range(1, len(branch_revenue) + 1),
        "Name": branch_revenue.index,
        "Metric_Value": branch_revenue.values,
        "Metric_Type": "Revenue"
    })
    
    # Top 5 Products by Revenue
    product_revenue = df.groupby("Product")["Revenue"].sum().sort_values(ascending=False).head(5)
    top_products_rev = pd.DataFrame({
        "Category": ["Top Products by Revenue"] * len(product_revenue),
        "Rank": range(1, len(product_revenue) + 1),
        "Name": product_revenue.index,
        "Metric_Value": product_revenue.values,
        "Metric_Type": "Revenue"
    })
    
    # Top 5 Products by Profit
    product_profit = df.groupby("Product")["Profit"].sum().sort_values(ascending=False).head(5)
    top_products_profit = pd.DataFrame({
        "Category": ["Top Products by Profit"] * len(product_profit),
        "Rank": range(1, len(product_profit) + 1),
        "Name": product_profit.index,
        "Metric_Value": product_profit.values,
        "Metric_Type": "Profit"
    })
    
    top_performers = pd.concat([top_branches, top_products_rev, top_products_profit], ignore_index=True)
    kpi_dfs["top_performers"] = top_performers
    
    return kpi_dfs


if __name__ == "__main__":
    from data_loader import load_all_branches
    from data_cleaner import run_cleaner
    from feature_engineering import run_feature_engineering
    
    print("🚀 Running KPI Calculator (Final Version)...")
    
    raw_df = load_all_branches("branch_data_advanced")
    clean_df = run_cleaner(raw_df, output_folder="output")
    featured_df = run_feature_engineering(clean_df, output_folder="output")
    kpis = run_kpi_calculator(featured_df)
    
    print(f"\n✅ KPI DataFrames created: {len(kpis)} categories")
    for name, df in kpis.items():
        print(f"   • {name}: {df.shape[0]} rows, {df.shape[1]} columns")
    
    print("\n📊 Monthly KPIs Preview (Growth with fillna=0):")
    print(kpis["monthly_kpis"][["YearMonth", "Revenue_Growth_%", "Profit_Growth_%"]].head(10).to_string(index=False))
    
    print("\n📊 Top Performers Preview (unified columns):")
    print(kpis["top_performers"].head(10).to_string(index=False))