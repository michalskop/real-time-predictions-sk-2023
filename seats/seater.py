"""Estimate the number of seats from the model."""

import datetime
import math
import numpy as np
import pandas as pd

path = "/home/michal/dev/sk2023/real-time-predictions-sk-2023/"

# load data
results = pd.read_csv(path + "estimate/result/results.csv")
results.index = results['id']
intervals = pd.read_csv(path + "estimate/interval_model1.csv") # model errors
choices = pd.read_csv(path + "estimate/initial_estimates.csv")
counted = pd.read_csv(path + "estimate/result/counted.csv")

runs = 1000

# possible coalitions
# 1	Piráti
# 2	PRINCÍP
# 3	PS
# 4	SOS
# 5	OĽaNO
# 6	KSS
# 7	Maďarské fórum
# 8	Vlastenecký blok
# 9	Modrí
# 10	SPRAVODLIVOSŤ
# 11	SHO
# 12	SaS
# 13	SME Rodina
# 14	MySlovensko
# 15	SNS
# 16	SMER-SD
# 17	HLAS-SD
# 18	Aliancia
# 19	SRDCE - SNJ
# 20	SDKÚ - DS
# 21	ĽSNS
# 22	Demokrati
# 23	KDH
# 24	KARMA
# 25	Republika
possible_coalitions = [
  {'name': 'stredopravica', 'ids': [3, 5, 12, 13, 22, 23]},
  {'name': 'stredopravica + HLAS', 'ids': [3, 5, 12, 13, 17, 22, 23]},
  {'name': 'stredopravica + HLAS bez OĽaNO', 'ids': [3, 12, 13, 17, 22, 23]},
  {'name': 'SMER + SNS + HLAS', 'ids': [15, 16, 25]},
  {'name': 'pragmatici + nacionalisti + HLAS', 'ids': [15, 16, 17, 25]},
  {'name': 'pragmatici + nacionalisti', 'ids': [15, 16, 17]},
]

# get mus, calculate standard deviation from interval
coef95 = intervals[intervals['x'] <= counted['counted'][0]]['y'].tolist()[-1]
mus = results['sloped_percentage']
sigmas = results['sloped_percentage'] * coef95  / 1.96
sigmas = sigmas.replace(0, 0.0001)

# get random values from normal distribution
samples = pd.DataFrame(np.random.normal(mus, sigmas, (runs, len(mus))))
samples.columns = mus.index

# Hagenbach-Bischoff
def hagenbach_bischoff(sample):
  """Hagenbach-Bischoff."""
  sample = sample.copy()
  sample = sample.merge(choices, left_on="party", right_on="id", how="left", suffixes=("", "_choice"))
  # remove parties with less than 5% / 7%
  sample.loc[:, 'value'] = sample.apply(lambda row: row['value'] if row['value'] >= (row['needs'] * 100) else 0, axis=1)
  # normalize to 0-1
  sample['value'] = sample['value'] / 100
  # sort by value
  sample = sample.sort_values(['value'], ascending=[False])
  # calculate HB
  sample['cumulative'] = sample['value'].cumsum()
  sample['cumulative'] = sample['cumulative'] / sample['cumulative'].max()
  sample['seats'] = sample['cumulative'].apply(lambda x: math.floor(x * 150))
  sample['seats'] = sample['seats'].diff().fillna(sample['seats'])
  sample['seats'] = sample['seats'].astype('int')
  sample['seats'] = sample['seats'].clip(lower=0)
  return sample.loc[:, ['id', 'seats']].sort_values(['seats'], ascending=[False])

# run HB for all samples, create estimates
estimates = pd.DataFrame(columns=samples.columns)
for i in range(runs):
  sample = samples.iloc[i].reset_index()
  sample.columns = ['party', 'value']
  hb = hagenbach_bischoff(sample)
  hb.index = hb.loc[:, 'id']
  estimates = pd.concat([estimates, pd.DataFrame(hb.loc[:, 'seats']).T], ignore_index=True)

# seats - best estimate
sample = results.loc[:, ['id', 'sloped_percentage']]
sample.columns = ['party', 'value']
hb = hagenbach_bischoff(sample)
hb.index = hb.loc[:, 'id']

# stats
stats = pd.DataFrame(index=results['id'])
stats['median'] = estimates.median(0)
stats['lo'] = estimates.quantile(q=0.025, interpolation='nearest')
stats['hi'] = estimates.quantile(q=0.975, interpolation='nearest')
stats['in'] = (estimates > 0).sum() / runs

# merge
stats = stats.merge(hb['seats'], on='id', how='left', suffixes=("", "_hb"))

# save
stats.to_csv(path + "seats/stats.csv", index=True)
t = datetime.datetime.now().isoformat(timespec='seconds')
stats.to_csv(path + "seats/archive/stats_" + t + ".csv", index=True)

# coalitions
coalitions = pd.DataFrame(columns=['name', 'median', 'lo', 'hi', 'in'])
for c in possible_coalitions:
  e = estimates.loc[:, c['ids']]
  item = {
    'name': c['name'],
    'median': e.sum(axis=1).median(),
    'lo': e.sum(axis=1).quantile(q=0.025, interpolation='nearest'),
    'hi': e.sum(axis=1).quantile(q=0.975, interpolation='nearest'),
    'in': (e.sum(axis=1) > 0).sum() / runs
  }
  coalitions = pd.concat([coalitions, pd.DataFrame(item, index=[0])], ignore_index=True)

# save
coalitions.to_csv(path + "seats/coalitions.csv", index=False)
coalitions.to_csv(path + "seats/archive/coalitions_" + t + ".csv", index=False)
