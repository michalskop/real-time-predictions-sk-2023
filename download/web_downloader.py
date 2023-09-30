"""Donwload data directly from interactive server. Backup for the case of failure of the official server."""

import csv
import json
import requests

# NRSR 2020
base_url = "https://volby.statistics.sk/nrsr/nrsr2020/json/"
# NRSR 2023 ?
# base_url = "https://volbysr.sk/sk/json/"
# base_url = "https://volby.statistics.sk/nrsr/nrsr2023/json/"

url1 = "graph01d/"
url2 = "tab02d/"

path = "/home/michal/dev/sk2023/real-time/2023/download/"

out_ps = []

# open list of okresy
with open(path + "../estimate/initial_weights.csv") as f:
  dr = csv.DictReader(f)
  for row in dr:
    url = base_url + url1 + row['code'] + ".json"
    r = requests.get(url)
    print(row['code'], r.status_code)
    if r.status_code == 200:
      for rx in r.json():
        item = {
          'OKRES': row['code'],
          'PS': rx['id'],
          'P_HL_PS': str(rx['y']).replace(' ', '')
        }
        out_ps.append(item)

# save to CSV
with open(path + "downloaded/web_backup/nrsr2023_med_ps_okr.csv", "w") as f:
  header = ['OKRES', 'PS', 'P_HL_PS']
  dw = csv.DictWriter(f, header, delimiter='|')
  dw.writeheader()
  for item in out_ps:
    dw.writerow(item)

out_sv = []
# open list of okresy
with open(path + "../estimate/initial_weights.csv") as f:
  dr = csv.DictReader(f)
  for row in dr:
    url = base_url + url2 + row['code'] + ".json"
    r = requests.get(url)
    print(row['code'], r.status_code)
    if r.status_code == 200:
      rx = r.json()[-1]
      item = {
        "OKRES": row['code'],
        "P_OKRSOK": rx['C03'],  # **TODO** check: may be C04
        "P_ZAP": rx['C06'].replace(' ', ''),
        "P_ZUC": rx['C07'].replace(' ', ''),
        "P_OO": rx['C09'].replace(' ', ''),
        "P_HL": rx['C13'].replace(' ', '')
      }
      out_sv.append(item)

# save to CSV
with open(path + "downloaded/web_backup/nrsr2023_med_sv_okr.csv", "w") as f:
  header = ['OKRES', 'P_OKRSOK', 'P_ZAP', 'P_ZUC', 'P_OO', 'P_HL']
  dw = csv.DictWriter(f, header, delimiter='|')
  dw.writeheader()
  for item in out_sv:
    dw.writerow(item)