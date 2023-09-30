"""Write current estimates to GSheet."""

import datetime
import gspread
import pandas as pd

sheetkey = "1S-Jah-eOdCKPH49w_AJYqanD8aYDrgnIvv4LKQTRkf8"

path = "/home/michal/dev/sk2023/real-time/2023/"

# connect
gc = gspread.service_account()
sh = gc.open_by_key(sheetkey)

# load data
counted = pd.read_csv(path + "estimate/result/counted.csv")
seats = pd.read_csv(path + "seats/stats.csv")
parties = pd.read_csv(path + "estimate/parties.csv")
model1 = pd.read_csv(path + "estimate/result/results.csv")
model0 = pd.read_csv(path + "estimate/result/model0.csv")

# counted
counted_value = counted['counted'][0]

# overview 1
t = datetime.datetime.now().isoformat(timespec='seconds')
ws = sh.worksheet("models")
history = ws.get_all_records()
models = pd.DataFrame(history)
models.loc[0, 'counted'] = counted_value
models.loc[0, 'date'] = t

# model 1 + 1s
if (model1['sloped_percentage'].sum() > 75) & (model1['sloped_percentage'].sum() < 125):
  # model 1s
  ws = sh.worksheet("model 1s")
  history = ws.get_all_values()
  p = parties.merge(model1, on='id', how='left').fillna(0)
  row = [counted_value, t] + p['sloped_percentage'].tolist()
  row = [str(x) for x in row]
  history = history + [row]
  ws.update('A1', history)

  models['model 1s'] = round(p['sloped_percentage'], 2).tolist()

  # model 1
  ws = sh.worksheet("model 1")
  history = ws.get_all_values()
  row = [counted_value, t] + p['percentage'].tolist()
  row = [str(x) for x in row]
  history = history + [row]
  ws.update('A1', history)

  models['model 1'] = round(p['percentage'], 2).tolist()


# model 0
if (model0['percentage'].sum() > 75) & (model0['percentage'].sum() < 125):
  ws = sh.worksheet("model 0")
  history = ws.get_all_values()
  p = parties.merge(model0, on='id', how='left').fillna(0)
  row = [counted_value, t] + p['percentage'].tolist()
  row = [str(x) for x in row]
  history = history + [row]
  ws.update('A1', history)

  models['model 0'] = round(p['percentage'], 2).tolist()


# model 2


# overview
ws = sh.worksheet("models")
# write models into the sheet
models['abbreviation'] = parties['abbreviation'].tolist()
models = models.fillna('')
models = models.astype(str)
ws.update([models.columns.values.tolist()] + models.values.tolist())
