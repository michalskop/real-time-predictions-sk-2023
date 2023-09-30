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

