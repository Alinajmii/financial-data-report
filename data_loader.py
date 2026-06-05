# src/data_loader.py

import pandas as pd
import os
from pathlib import Path

def load_all_branches(data_folder: str = "branch_data_advanced") -> pd.DataFrame:
    """
    Reads all Excel files from the given folder and returns a single master DataFrame.
    No cleaning, no KPI, no analysis — just loading and merging.
    """
    data_path = Path(data_folder)
    
    if not data_path.exists():
        raise FileNotFoundError(f"Folder '{data_folder}' not found.")
    
    all_files = list(data_path.glob("*.xlsx"))
    
    # Ignore summary files (those starting with 00_)
    branch_files = [f for f in all_files if not f.name.startswith("00_")]
    
    if not branch_files:
        raise ValueError("No branch Excel files found in the folder.")
    
    df_list = []
    
    for file in branch_files:
        print(f"📂 Reading: {file.name}")
        df = pd.read_excel(file)
        df_list.append(df)
    
    master_df = pd.concat(df_list, ignore_index=True)
    
    return master_df

if __name__ == "__main__":
    # Just to test the loader
    df = load_all_branches("branch_data_advanced")
    
    print("\n✅ Master DataFrame created successfully.")
    print(f"📊 Shape: {df.shape}")
    print(f"📋 Columns: {list(df.columns)}")
    print("\n🔍 First 5 rows:")
    print(df.head())