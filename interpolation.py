import pandas as pd
import numpy as np

pd.set_option('display.max_rows', 100)
pd.set_option('display.min_rows', 100)

def create_interpolation_series(df, percentiles):
    x = df['percentile'].to_numpy()
    y = df['min_income'].to_numpy()
    return np.interp(percentiles, x, y, left=0)
    


DATA_FILE = 'data/income_classes_processed.csv'
df = pd.read_csv(DATA_FILE)
group_by_headers = ['age_range', 'gender']
df['percent_of_people'] = df['number_of_people'] / df.groupby(group_by_headers)['number_of_people'].transform('sum')
df['percentile'] = df.groupby(group_by_headers)['percent_of_people'].cumsum()
df['percentile'] = df['percentile'] * 100
df['selected_income_bracket'] = False

percentile_dfs_list = []

percentiles=list(range(0,101))
for headers, group in df.groupby(group_by_headers):
    interpolated_incomes = create_interpolation_series(df, percentiles)
    group_df = pd.DataFrame({
        'percentile': percentiles,
        'interpolated_income': interpolated_incomes
        })

    group_df[group_by_headers[0]] = headers[0]
    group_df[group_by_headers[1]] = headers[1]
    percentile_dfs_list.append(group_df)

percentile_dfs = pd.concat(percentile_dfs_list)
print(percentile_dfs)
    


