# inspect_raw_data.py
import pandas as pd

df_cv = pd.read_csv("data/raw/test_topcv.csv")
df_dev = pd.read_csv("data/raw/test_topdev.csv")

print("="*70)
print("KIỂM TRA ĐỊNH DẠNG DỮ LIỆU GỐC")
print("="*70)

print("\n📊 TopCV - Kiểm tra salary:")
print(f"Columns: {df_cv.columns.tolist()}")
print(f"\nSalary columns:")
for col in ['salary_range', 'salary', 'salary_min', 'salarry_max']:
    if col in df_cv.columns:
        print(f"\n  {col}:")
        for i, val in enumerate(df_cv[col].head(10)):
            print(f"    {i+1}: '{val}'")

print("\n📊 TopDev - Kiểm tra salary:")
print(f"Columns: {df_dev.columns.tolist()}")
print(f"\nSalary columns:")
for col in ['salary_range', 'salary', 'salary_min', 'salarry_max']:
    if col in df_dev.columns:
        print(f"\n  {col}:")
        for i, val in enumerate(df_dev[col].head(10)):
            print(f"    {i+1}: '{val}'")