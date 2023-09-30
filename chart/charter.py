"""Prepare data for the charts."""

import datetime
import pandas as pd

path = "/home/michal/dev/sk2023/real-time-predictions-sk-2023/"

t = datetime.datetime.now().isoformat(timespec='seconds')

# Chart 1
# https://public.flourish.studio/visualisation/15187377/
# load data
results = pd.read_csv(path + "estimate/result/results.csv")
# sort results
results = results.sort_values(['sloped_percentage'], ascending=[False])
# prepare data for chart
chart1t = results.loc[:, ['abbreviation', 'sloped_percentage', 'sloped_lo', 'sloped_hi']]
chart1 = chart1t.round(1).iloc[0:11, :].T
# replace index
chart1.index = ['Strana', 'zisk', 'zisk', 'zisk']
# save to CSV
chart1.to_csv(path + "chart/charts/chart_prediction_percentage.csv", header=False)
chart1.to_csv(path + "chart/charts/archive/chart_prediction_percentage_" + t + ".csv", header=False)

# Chart 2
# https://public.flourish.studio/visualisation/15168321/
# load data
seats = pd.read_csv(path + "seats/stats.csv")
parties = pd.read_csv(path + "estimate/parties.csv")
# merge
seats = seats.merge(parties, on="id", how="left")
# sort data
seats = seats.sort_values(['seats', 'hi', 'lo'], ascending=[False, False, False])
# select only those with hi > 0
seats = seats[seats['hi'] > 0]
# prepare data for chart
chart2 = pd.DataFrame(columns=['strana', 'mandáty', 'počet', 'počty mandátov'])

chart2_lo = chart2.copy()
chart2_lo = pd.concat([chart2_lo, seats.loc[:, ['abbreviation', 'lo']].rename(columns={'abbreviation': 'strana', 'lo': 'počet'})], ignore_index=True)
chart2_lo['mandáty'] = 'Takmer isté'
chart2_lo['počty mandátov'] = 'Takmer isté' + ': ' + chart2_lo['počet'].astype('str')

chart2_mid = chart2.copy()
chart2_mids = seats.loc[:, ['abbreviation', 'seats', 'lo']]
chart2_mids['diff'] = chart2_mids['seats'] - chart2_mids['lo']
chart2_mids = chart2_mids.rename(columns={'abbreviation': 'strana', 'diff': 'počet'})
chart2_mids['mandáty'] = 'Pravdepodobné'
chart2_mids['počty mandátov'] = 'Pravdepodobné: ' + chart2_mids['lo'].astype('str') + '+' + chart2_mids['počet'].astype('str')
chart2_mid = chart2_mids.loc[:, ['strana', 'mandáty', 'počet', 'počty mandátov']]

chart2_hi = chart2.copy()
chart2_his = seats.loc[:, ['abbreviation', 'seats', 'hi', 'lo']]
chart2_his['diff'] = chart2_his['hi'] - chart2_his['seats']
chart2_his['diff2'] = chart2_his['seats'] - chart2_his['lo']
chart2_his = chart2_his.rename(columns={'abbreviation': 'strana', 'diff': 'počet'})
chart2_his['mandáty'] = 'Menej pravdepodobné'
chart2_his['počty mandátov'] = 'Menej pravdepodobné: ' + chart2_his['lo'].astype('str') + '+' + chart2_his['diff2'].astype('str') + '+' + chart2_his['počet'].astype('str')
chart2_hi = chart2_his.loc[:, ['strana', 'mandáty', 'počet', 'počty mandátov']]

chart2 = pd.concat([chart2_lo, chart2_mid, chart2_hi], ignore_index=True)

# save to CSV
chart2.to_csv(path + "chart/charts/chart_prediction_seats.csv", index=False)
chart2.to_csv(path + "chart/charts/archive/chart_prediction_seats_" + t + ".csv", index=False)