"""Model 0 - current values."""

import datetime
import pandas as pd

path = "/home/michal/dev/sk2023/real-time-predictions-sk-2023/"

# read current data
current_overview = pd.read_csv(path + "download/downloaded/nrsr2023_med_suma_sr.csv", sep="|")
parties = pd.read_csv(path + "estimate/parties.csv")

results = pd.DataFrame(index=parties['id'].tolist())

# add current values to the results
for i in results.index:
  try:
    results.loc[i, 'percentage'] = current_overview['P_HL_PS' + str(i).zfill(2) + '_PCT'][0].replace(",", ".")
  except:
    results.loc[i, 'percentage'] = 0

# save results
results['id'] = results.index
results.to_csv(path + "estimate/result/model0.csv", index=False)
t = datetime.datetime.now().isoformat(timespec='seconds')
results.to_csv(path + "estimate/result/archive/model0_" + t + ".csv", index=False)

print("Model 0 done.")