import pandas as pd
import duckdb

baseline_map = {"Partizan": pd.to_datetime("2023-01-01")}
selected_channels = ["Partizan"]
baseline_conditions = []
for channel, b_date in baseline_map.items():
    if channel in selected_channels:
        b_date_str = b_date.strftime('%Y-%m-%d')
        baseline_conditions.append(f"(CHANNEL_TITLE = '{channel}' AND METRIC_DATE > '{b_date_str}')")
        
baseline_sql = " OR ".join(baseline_conditions)
print("baseline_sql:", baseline_sql)
