"""Download data from SUSR and save them."""

import base64
import datetime
import io
import requests
import pandas as pd
# import time

# credentials
# Note: it should be in a separate file gitignored **TODO**
# however this credentials are for this day only
url = "https://volbysr.sk/media/"
username = "SeznamCZ"
password = "648+mvc/PQR8o1s"

path = "/home/michal/dev/sk2023/real-time-predictions-sk-2023/download/"

data_path = "downloaded/"

# connect
credentials = username + ":" + password
encoded_credentials = base64.b64encode(credentials.encode("ascii")).decode("ascii")
headers = {"Authorization": "Basic " + encoded_credentials}
r = requests.get(url, headers=headers)
# r.status_code

# all files
# files = ['nrsr2023_med_kan_sr', 'nrsr2023_med_kandidati', 'nrsr2023_med_okresy', 'nrsr2023_med_ps_okr', 'nrsr2023_med_psubjekty', 'nrsr2023_med_suma_sr', 'nrsr2023_med_sv_okr']
# important files only
# files = ['nrsr2023_med_ps_okr', 'nrsr2023_med_sv_okr', 'nrsr2023_med_suma_sr']
# changing file only
files = ['nrsr2023_med_kan_sr', 'nrsr2023_med_ps_okr', 'nrsr2023_med_suma_sr', 'nrsr2023_med_sv_okr']

t = datetime.datetime.now().isoformat(timespec='seconds')

for f in files:
  url = "https://volbysr.sk/media/" + f + ".csv"
  r = requests.get(url, headers=headers)
  print(url, r.status_code)
  if r.status_code == 200:
    # save only if correct CSV
    try:
      x = pd.read_csv(io.StringIO(r.content.decode('utf-8')), sep="|")
      x.to_csv(path + data_path + f + ".csv", index=False, sep="|")
      # archive
      x.to_csv(path + data_path + "archive/" + f + "_" + t + ".csv", index=False, sep="|")

      # x = pd.read_csv(path + data_path + f + ".csv", sep="|")
      # with open(path + data_path + f + ".csv", 'wb') as file:
      #   print("ok 1")
      #   # file.write(r.content)
      # # archive
      # with open(path + data_path + "archive/" + f + "_" + t + ".csv", 'wb') as file:
      #   file.write(r.content)
    except:
      print("Error: file not CSV.")
      pass

# time.sleep(20)