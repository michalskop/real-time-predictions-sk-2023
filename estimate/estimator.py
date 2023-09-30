"""Estimate the results from okresy. Main model."""

import datetime
import pandas as pd

# set up path
path = "/home/michal/dev/sk2023/real-time-predictions-sk-2023/"

# set up parameters
estimated_levels = {
  'full': 100,
  'finish': 90,
  'good': 35,
  'basic': 10,
  'start': 0
}
close_in_matrix = 10  # okresy closer than this are considered close

# read initial data
initial_weights = pd.read_csv(path + "estimate/initial_weights.csv")
initial_estimates = pd.read_csv(path + "estimate/initial_estimates.csv")
distance_matrix = pd.read_csv(path + "estimate/distance_matrix.csv")
parties = pd.read_csv(path + "estimate/parties.csv")
slope = pd.read_csv(path + "estimate/slope.csv")
intervals1 = pd.read_csv(path + "estimate/interval_model1.csv") # model errors
intervals1s = pd.read_csv(path + "estimate/interval_model1s.csv") # model errors

# read current data

current_overview = pd.read_csv(path + "download/downloaded/nrsr2023_med_sv_okr.csv", sep="|")
current_parties = pd.read_csv(path + "download/downloaded/nrsr2023_med_ps_okr.csv", sep="|")

"""Estimate the results from okresy. Functions."""
def get_estimated_level(perc):
  """Get estimated level from percentage."""
  if perc >= estimated_levels['full']:
    return 'full'
  elif perc >= estimated_levels['finish']:
    return 'finish'
  elif perc >= estimated_levels['good']:
    return 'good'
  elif perc >= estimated_levels['basic']:
    return 'basic'
  elif perc > estimated_levels['start']:
    return 'start'
  else:
    return 'none'

# get estimated level for each okres
current_overview = current_overview.merge(initial_weights, left_on='OKRES', right_on='code', how='right')
current_overview.loc[:, ['P_OKRSOK', 'P_ZAP', 'P_ZUC', 'P_OO', 'P_HL']] = current_overview.loc[:, ['P_OKRSOK', 'P_ZAP', 'P_ZUC', 'P_OO', 'P_HL']].fillna(0)
current_overview['counted'] = current_overview['P_OKRSOK'] / current_overview['polling_stations'] * 100
current_overview['counted_level'] = current_overview['counted'].apply(get_estimated_level)

# okresy on different level of counted are estimated differently
# rules:
# - full: use current percentage, use current number of voted
# - finish: use current percentage, estimate number of voted# - basic: use current percentage, estimate number of voted from initial number of voters
# - good: use current percentage, estimate number of voted from both current turnout and initial number of voters
# - basic: use current percentage, estimate number of voted from initial number of voters
# - basic: adjust for HU
# - start: 1 use current percentage and initial percentage, if there is close okres at higher level, use also its percentage
# - start: 2 estimate number of voted from initial number of voters
# - start: adjust for HU
# - none: 1 use initial percentage, if there is close okres at higher level, use also its percentage
# - none: 2 estimate number of voted from initial number of voters
# - abroad / start and higher: use current percentage, use current number of voted
# - abroad / none: use initial percentage, use initial number of voted

# ESTIMATIONS
estimates = pd.DataFrame(columns=['code', 'id', 'votes', 'gain'])

# get okresy on each level
possible_levels = list(estimated_levels.keys()) + ['none']
# Create an empty dictionary with keys as the possible levels
levels = {level: [] for level in possible_levels}
# Group the DataFrame by the 'counted_level' column and get the 'code' column as a list for each group
grouped = current_overview[current_overview['code'] != 900].groupby('counted_level')['code'].apply(list)
# Create the 'levels' dictionary using a dictionary comprehension
levels = {level: grouped.get(level, []) for level in possible_levels}

# FULL
# - full: use current percentage, use current number of voted
# get okresy on full level
dffull = current_parties[current_parties['OKRES'].isin(levels['full'])]
dffull.rename(columns={'OKRES': 'code', 'PS': 'id', 'P_HL_PS': 'votes'}, inplace=True)

if len(dffull) > 0:
  # append to estimates
  estimates = pd.concat([estimates, dffull.loc[:, ['code', 'id', 'votes']]], ignore_index=True)

# FINISH
# - finish: use current percentage, estimate number of voted# - basic: use current percentage, estimate number of voted from initial number of voters
# get okresy on finish level
dffinish = current_parties[current_parties['OKRES'].isin(levels['finish'])]
dffinish.rename(columns={'OKRES': 'code', 'PS': 'id', 'P_HL_PS': 'votes'}, inplace=True)

if len(dffinish) > 0:
  # merge current_overview
  dffinish = dffinish.merge(current_overview.loc[:, ['code', 'counted', 'estimate_votes', 'estimate_voters', 'P_ZAP', 'P_HL']], on='code', how='left')

  # estimate turnout, linear regression: good -> full
  dffinish['initial_turnout'] = dffinish['estimate_votes'] / dffinish['estimate_voters'] * 100
  dffinish['current_turnout'] = dffinish['P_HL'] / dffinish['P_ZAP'] * 100
  dffinish['estimate_turnout'] = dffinish['initial_turnout'] + (dffinish['counted'] - estimated_levels['good']) / (estimated_levels['full'] - estimated_levels['good']) * (dffinish['current_turnout'] - dffinish['initial_turnout'])

  # estimate voters, linear regression, finish -> full
  dffinish['current_estimate_voters'] = dffinish['P_ZAP'] * 100 / dffinish['counted']

  # estimate votes
  # 1
  # dffinish['current_estimate_votes'] = dffinish['votes'] * 100 / dffinish['counted']
  # 2
  dffinish['estimate_percentage'] = dffinish['votes'] / dffinish['P_HL'] * 100
  dffinish['current_estimate_votes'] = dffinish['estimate_percentage'] / 100 * dffinish['current_estimate_voters'] * dffinish['estimate_turnout'] / 100

  # append to estimates
  t = dffinish.loc[:, ['code', 'id', 'current_estimate_votes']].rename(columns={'current_estimate_votes': 'votes'})
  estimates = pd.concat([estimates, t], ignore_index=True)


# GOOD
# - good: use current percentage, estimate number of voted from both current turnout and initial number of voters
# get okresy on good level
dfgood = current_parties[current_parties['OKRES'].isin(levels['good'])]
dfgood.rename(columns={'OKRES': 'code', 'PS': 'id', 'P_HL_PS': 'votes'}, inplace=True)

if len(dfgood) > 0:
  # merge current_overview
  dfgood = dfgood.merge(current_overview.loc[:, ['code', 'counted', 'estimate_votes', 'estimate_voters', 'P_ZAP', 'P_HL']], on='code', how='left')

  # estimate turnout, linear regression
  dfgood['initial_tournout'] = dfgood['estimate_votes'] / dfgood['estimate_voters'] * 100
  dfgood['current_turnout'] = dfgood['P_HL'] / dfgood['P_ZAP'] * 100

  # estimate turnout, linear regression: good -> full
  dfgood['initial_turnout'] = dfgood['estimate_votes'] / dfgood['estimate_voters'] * 100
  dfgood['current_turnout'] = dfgood['P_HL'] / dfgood['P_ZAP'] * 100
  dfgood['estimate_turnout'] = dfgood['initial_turnout'] + (dfgood['counted'] - estimated_levels['good']) / (estimated_levels['full'] - estimated_levels['good']) * (dfgood['current_turnout'] - dfgood['initial_turnout'])

  # estimate votes
  dfgood['estimate_percentage'] = dfgood['votes'] / dfgood['P_HL'] * 100
  dfgood['current_estimate_votes'] = dfgood['estimate_percentage'] / 100 * dfgood['estimate_turnout'] / 100 * dfgood['estimate_voters']

  # append to estimates
  t = dfgood.loc[:, ['code', 'id', 'current_estimate_votes']].rename(columns={'current_estimate_votes': 'votes'})
  estimates = pd.concat([estimates, t], ignore_index=True)


# BASIC
# - basic: use current percentage, estimate number of voted from initial number of voters
# - basic: adjust for HU
# get okresy on basic level
dfbasic = current_parties[current_parties['OKRES'].isin(levels['basic'])]
dfbasic.rename(columns={'OKRES': 'code', 'PS': 'id', 'P_HL_PS': 'votes'}, inplace=True)

# HU vs. non-HU okresy 
hu_codes = initial_weights['code'][initial_weights['estimate_hu'] > 0].tolist()
sk_codes = initial_weights['code'][initial_weights['estimate_hu'] == 0].tolist()

if len(dfbasic) > 0:
  # merge current_overview
  dfbasic = dfbasic.merge(current_overview.loc[:, ['code', 'counted', 'estimate_votes', 'estimate_voters', 'estimate_hu', 'P_ZAP', 'P_HL']], on='code', how='left')

  dfbasic['estimate_percentage'] = dfbasic['votes'] / dfbasic['P_HL'] * 100

  dfbasic_hu = dfbasic[dfbasic['code'].isin(hu_codes)]
  dfbasic_sk = dfbasic[dfbasic['code'].isin(sk_codes)]

  # non-HU okresy
  # estimate votes
  dfbasic_sk['estimate_percentage'] = dfbasic_sk['votes'] / dfbasic_sk['P_HL'] * 100
  dfbasic_sk['current_estimate_votes'] = dfbasic_sk['estimate_percentage'] / 100 * dfbasic_sk['estimate_votes']

  # append to estimates
  t = dfbasic_sk.loc[:, ['code', 'id', 'current_estimate_votes']].rename(columns={'current_estimate_votes': 'votes'})
  estimates = pd.concat([estimates, t], ignore_index=True)

  # HU okresy
  # hu votes
  hu_ids = initial_estimates['id'][initial_estimates['hu'] > 1].tolist()
  sk_ids = initial_estimates['id'][initial_estimates['hu'] == 0].tolist()

  # calculate total votes for HU and non-HU parties by okres
  pthu = pd.pivot_table(dfbasic_hu[dfbasic_hu['id'].isin(hu_ids)], index=['code'], columns=['id'], values=['votes'], aggfunc='sum')
  ptsk = pd.pivot_table(dfbasic_hu[dfbasic_hu['id'].isin(sk_ids)], index=['code'], columns=['id'], values=['votes'], aggfunc='sum')
  pthus = pthu.sum(axis=1)
  ptsks = ptsk.sum(axis=1)
  pthus = pthus.to_frame()
  ptsks = ptsks.to_frame()
  pthus.columns = ['hu_votes']
  ptsks.columns = ['sk_votes']

  # add this to dfbasic_hu (hungarian okresy)
  dfbasic_hu = dfbasic_hu.merge(pthus, on='code', how='left')
  dfbasic_hu = dfbasic_hu.merge(ptsks, on='code', how='left')

  # calculate total votes for HU and non-HU parties by okres
  dfbasic_hu_hu = dfbasic_hu[dfbasic_hu['id'].isin(hu_ids)]
  dfbasic_hu_sk = dfbasic_hu[dfbasic_hu['id'].isin(sk_ids)]

  # estimate votes
  dfbasic_hu_hu['estimate_votes_hu'] = dfbasic_hu_hu['estimate_votes'] * dfbasic_hu_hu['estimate_hu']
  dfbasic_hu_hu['estimate_percentage_hu'] = dfbasic_hu_hu['votes'] / dfbasic_hu_hu['hu_votes'] * 100
  dfbasic_hu_hu['current_estimate_votes'] = dfbasic_hu_hu['estimate_percentage_hu'] / 100 * dfbasic_hu_hu['estimate_votes_hu']

  dfbasic_hu_sk['estimate_votes_sk'] = dfbasic_hu_sk['estimate_votes'] * (1 - dfbasic_hu_sk['estimate_hu'])
  dfbasic_hu_sk['estimate_percentage_sk'] = dfbasic_hu_sk['votes'] / dfbasic_hu_sk['sk_votes'] * 100
  dfbasic_hu_sk['current_estimate_votes'] = dfbasic_hu_sk['estimate_percentage_sk'] / 100 * dfbasic_hu_sk['estimate_votes_sk']

  # append to estimates
  t = dfbasic_hu_hu.loc[:, ['code', 'id', 'current_estimate_votes']].rename(columns={'current_estimate_votes': 'votes'})
  estimates = pd.concat([estimates, t], ignore_index=True)
  t = dfbasic_hu_sk.loc[:, ['code', 'id', 'current_estimate_votes']].rename(columns={'current_estimate_votes': 'votes'})
  estimates = pd.concat([estimates, t], ignore_index=True)


# START
# - start: 1 use current percentage and initial percentage, if there is close okres at higher level, use also its percentage
# - start: 2 estimate number of voted from initial number of voters
# - start: adjust for HU

# get okresy on start level
dfstart = current_parties[current_parties['OKRES'].isin(levels['start'])]
dfstart.rename(columns={'OKRES': 'code', 'PS': 'id', 'P_HL_PS': 'votes'}, inplace=True)

if len(dfstart) > 0:
  # merge current_overview
  dfstart = dfstart.merge(current_overview.loc[:, ['code', 'counted', 'estimate_votes', 'estimate_voters', 'estimate_hu', 'P_ZAP', 'P_HL']], on='code', how='left')

  # - start: 1 use current percentage and initial percentage, if there is close okres at higher level, use also its percentage
  higher_codes = dffull['code'].unique().tolist() + dffinish['code'].unique().tolist() + dfgood['code'].unique().tolist() + dfbasic['code'].unique().tolist()
  higher_codes = [str(code) for code in higher_codes]
  codes = dfstart['code'].unique().tolist()

  # get closest okresy
  dm = distance_matrix.copy()
  dm.index = dm['code']
  df_selected = dm[dm['code'].isin(codes)].loc[:, higher_codes]
  df_selected = df_selected.mask(df_selected > close_in_matrix, pd.NA)
  if (len(df_selected) > 0) & (len(df_selected.columns) > 0):
    min_cols = df_selected.idxmin(axis=1)
  else:
    min_cols = pd.Series()
  # propage values to dfstart
  min_cols = pd.DataFrame(min_cols)
  min_cols.columns = ['min_code']
  min_cols.rename_axis('code', inplace=True)
  min_cols.reset_index(inplace=True)
  dfstart = dfstart.merge(min_cols, left_on='code', right_on='code', how='left')

  # calculate current percentage/gain the same way as in BASIC
  # start copy BASIC

  # HU vs. non-HU okresy 
  dfstart_hu = dfstart[dfstart['code'].isin(hu_codes)]
  dfstart_sk = dfstart[dfstart['code'].isin(sk_codes)]

  # non-HU okresy
  # estimate votes
  dfstart_sk['estimate_percentage'] = dfstart_sk['votes'] / dfstart_sk['P_HL'] * 100
  dfstart_sk['current_estimate_votes'] = dfstart_sk['estimate_percentage'] / 100 * dfstart_sk['estimate_votes']

  # HU okresy
  # hu votes
  hu_ids = initial_estimates['id'][initial_estimates['hu'] > 1].tolist()
  sk_ids = initial_estimates['id'][initial_estimates['hu'] == 0].tolist()

  # calculate total votes for HU and non-HU parties by okres
  pthu = pd.pivot_table(dfstart_hu[dfstart_hu['id'].isin(hu_ids)], index=['code'], columns=['id'], values=['votes'], aggfunc='sum')
  ptsk = pd.pivot_table(dfstart_hu[dfstart_hu['id'].isin(sk_ids)], index=['code'], columns=['id'], values=['votes'], aggfunc='sum')
  pthus = pthu.sum(axis=1)
  ptsks = ptsk.sum(axis=1)
  pthus = pthus.to_frame()
  ptsks = ptsks.to_frame()
  pthus.columns = ['hu_votes']
  ptsks.columns = ['sk_votes']

  # add this to dfstart_hu (hungarian okresy)
  dfstart_hu = dfstart_hu.merge(pthus, on='code', how='left')
  dfstart_hu = dfstart_hu.merge(ptsks, on='code', how='left')

  # calculate total votes for HU and non-HU parties by okres
  dfstart_hu_hu = dfstart_hu[dfstart_hu['id'].isin(hu_ids)]
  dfstart_hu_sk = dfstart_hu[dfstart_hu['id'].isin(sk_ids)]

  # estimate votes
  dfstart_hu_hu['estimate_votes_hu'] = dfstart_hu_hu['estimate_votes'] * dfstart_hu_hu['estimate_hu']
  dfstart_hu_hu['estimate_percentage_hu'] = dfstart_hu_hu['votes'] / dfstart_hu_hu['hu_votes'] * 100
  dfstart_hu_hu['current_estimate_votes'] = dfstart_hu_hu['estimate_percentage_hu'] / 100 * dfstart_hu_hu['estimate_votes_hu']

  dfstart_hu_sk['estimate_votes_sk'] = dfstart_hu_sk['estimate_votes'] * (1 - dfstart_hu_sk['estimate_hu'])
  dfstart_hu_sk['estimate_percentage_sk'] = dfstart_hu_sk['votes'] / dfstart_hu_sk['sk_votes'] * 100
  dfstart_hu_sk['current_estimate_votes'] = dfstart_hu_sk['estimate_percentage_sk'] / 100 * dfstart_hu_sk['estimate_votes_sk']

  # end copy BASIC

  # merge back to dfstart
  dfstart = pd.concat([dfstart_sk, dfstart_hu_hu, dfstart_hu_sk], ignore_index=True)

  # add gain to dfstart
  sum_votes = dfstart.groupby('code')['votes'].transform('sum')
  dfstart['current_gain'] = dfstart['votes'] / sum_votes

  # add gain to estimates
  sum_votes = estimates.groupby('code')['votes'].transform('sum')
  estimates['gain'] = estimates['votes'] / sum_votes

  # estimate votes from current gain and closest okres gains
  # merge with estimates
  e = estimates.copy()
  e['code'] = e['code'].astype(str)
  dfstart = dfstart.merge(e, left_on=['min_code', 'id'], right_on=['code', 'id'], how='left', suffixes=('', '_estimates'))

  # estimate votes, linear approximation of gain and current_gain
  dfstart['estimate_gain'] = ((dfstart['counted'] / estimated_levels['basic'] * dfstart['current_gain']) + (1 - dfstart['counted'] / estimated_levels['basic']) * dfstart['gain']).fillna(dfstart['current_gain'])
  dfstart['current_estimate_votes'] = dfstart['estimate_gain'] * dfstart['estimate_votes']

  # append to estimates
  t = dfstart.loc[:, ['code', 'id', 'current_estimate_votes']].rename(columns={'current_estimate_votes': 'votes'})
  estimates = pd.concat([estimates, t], ignore_index=True)

  # add gain to estimates
  sum_votes = estimates.groupby('code')['votes'].transform('sum')
  estimates['gain'] = estimates['votes'] / sum_votes


# NONE
# - none: 1 use initial percentage, if there is close okres at higher level, use also its percentage
# create dfnone
# Create the MultiIndex from the Cartesian product of codes and ids
index = pd.MultiIndex.from_product([levels['none'], parties['id'].unique()], names=['code', 'id'])
# Create the DataFrame with three columns
dfnone = pd.DataFrame({'votes': 0}, index=index).reset_index()
dfnone['gain'] = pd.NA
# merge current_overview
dfnone = dfnone.merge(current_overview.loc[:, ['code', 'counted', 'estimate_votes', 'estimate_voters', 'estimate_hu', 'P_ZAP', 'P_HL']], on='code', how='left')

if len(dfnone) > 0:
  # find closest okresy
  higher_codes = dffull['code'].unique().tolist() + dffinish['code'].unique().tolist() + dfgood['code'].unique().tolist() + dfbasic['code'].unique().tolist() + dfstart['code'].unique().tolist()
  higher_codes = [str(code) for code in higher_codes]
  codes = dfnone['code'].unique().tolist()

  # get closest okresy
  dm = distance_matrix.copy()
  dm.index = dm['code']
  df_selected = dm[dm['code'].isin(codes)].loc[:, higher_codes]
  df_selected = df_selected.mask(df_selected > close_in_matrix, pd.NA)
  if (len(df_selected) > 0) & (len(df_selected.columns) > 0):
    min_cols = df_selected.idxmin(axis=1)
  else:
    min_cols = pd.Series()
  # propage values to dfstart
  min_cols = pd.DataFrame(min_cols)
  min_cols.columns = ['min_code']
  min_cols.rename_axis('code', inplace=True)
  min_cols.reset_index(inplace=True)
  dfnone = dfnone.merge(min_cols, left_on='code', right_on='code', how='left')

  # merge with estimates
  e = estimates.copy()
  e['code'] = e['code'].astype(str)
  dfnone = dfnone.merge(e, left_on=['min_code', 'id'], right_on=['code', 'id'], how='left', suffixes=('', '_estimates'))

  # merge with initial_estimates
  dfnone = dfnone.merge(initial_estimates, on=['id'], how='left', suffixes=('', '_initial'))
  dfnone['gain_initial'] = dfnone['estimate'] / 100

  # estimate votes, use gain_estimates, if NA, use use gain_initial
  dfnone['estimate_gain'] = dfnone['gain_estimates'].fillna(dfnone['gain_initial'])
  dfnone['current_estimate_votes'] = dfnone['estimate_gain'] * dfnone['estimate_votes']

  # append to estimates
  t = dfnone.loc[:, ['code', 'id', 'current_estimate_votes']].rename(columns={'current_estimate_votes': 'votes'})
  estimates = pd.concat([estimates, t], ignore_index=True)

# ABROAD
# - abroad / start and higher: use current percentage, use current number of voted
# - abroad / none: use initial percentage, use initial number of voted
dfabroad = current_parties[current_parties['OKRES'] == 900]
dfabroad.rename(columns={'OKRES': 'code', 'PS': 'id', 'P_HL_PS': 'votes'}, inplace=True)
if len(dfabroad) > 0:
  counted = current_overview[current_overview['code'] == 900]['counted'].values[0]
  dfabroad['current_estimate_votes'] = dfabroad['votes'] / counted * 100
else:
  dfabroad = initial_estimates.copy()
  dfabroad['current_estimate_votes'] = dfabroad['mail'] / 100 * initial_weights[initial_weights['code'] == 900]['estimate_votes'].values[0]
  dfabroad['code'] = 900

# append to estimates
tabroad = dfabroad.loc[:, ['code', 'id', 'current_estimate_votes']].rename(columns={'current_estimate_votes': 'votes'})
estimates_900 = estimates.copy()
estimates = pd.concat([estimates, tabroad], ignore_index=True)


# SUMMARIZE
# summarize estimates
results = estimates.groupby(['id'])['votes'].sum().reset_index()
# add percentage
results['percentage'] = results['votes'] / results['votes'].sum() * 100


# SLOPE CORRECTION
# correct only part without 900
# get slope
counted_percentage = current_overview['P_OKRSOK'].sum() / initial_weights['polling_stations'].sum() * 100
current_slope = slope[slope['x'] >= counted_percentage].head(1)['y'].values[0]

# correct results
if counted_percentage > 0:
  estimates_900 = estimates_900.merge(initial_estimates.loc[:, ['id', 'slope']], on='id', how='left')
  estimates_900['sloped_votes'] = estimates_900['votes'] * (1 + estimates_900['slope'] * current_slope)
  # add 900
  estimates_900 = pd.concat([estimates_900, tabroad], ignore_index=True)
  # fill NA with votes
  estimates_900['sloped_votes'] = estimates_900['sloped_votes'].fillna(estimates_900['votes'])

  # Summarize
  results_900 = estimates_900.groupby(['id'])['sloped_votes'].sum().reset_index()
  # add percentage
  results_900['sloped_percentage'] = results_900['sloped_votes'] / results_900['sloped_votes'].sum() * 100
  # merge to get slope
  results_900 = results_900.merge(initial_estimates.loc[:, ['id', 'slope']], on='id', how='left')

  # merge with results
  results = results.merge(results_900, on='id', how='left')

else:
  results['sloped_percentage'] = results['percentage']

# ADD INTERVALS
# note: adding intervals1 to both results and results_sloped
# for results_sloped "just in case"
coef95 = intervals1[intervals1['x'] <= counted_percentage]['y'].tolist()[-1]
coef95s = intervals1[intervals1['x'] <= counted_percentage]['y'].tolist()[-1] # for sloped intervals1s or conservative intervals1
results['lo'] = results['percentage'] / (1 + coef95)
results['hi'] = results['percentage'] * (1 + coef95)
results['sloped_lo'] = results['sloped_percentage'] / (1 + coef95s)
results['sloped_hi'] = results['sloped_percentage'] * (1 + coef95s)

# save results
r = results.loc[:, ['id', 'votes', 'percentage', 'sloped_percentage', 'lo', 'hi', 'sloped_lo', 'sloped_hi']].merge(parties.loc[:, ['id', 'abbreviation']], on='id', how='left')
r.to_csv(path + "estimate/result/results.csv", index=False)
t = datetime.datetime.now().isoformat(timespec='seconds')
r.to_csv(path + "estimate/result/archive/results_" + t + ".csv", index=False)

# save counted
item = {
  "date": t,
  "counted": counted_percentage,
}
c = pd.DataFrame([item])
c.to_csv(path + "estimate/result/counted.csv", index=False)
c.to_csv(path + "estimate/result/archive/counted.csv", index=False, header=False, mode='a')

# OKRESY estimates
pt1 = pd.pivot_table(estimates, index=['code'], columns=['id'], values=['votes'], aggfunc='sum')
pt1.columns = pt1.columns.droplevel(0)
pt2 = pt1.copy()
pt1.reset_index(inplace=True)
pt1.to_csv(path + "estimate/result/okresy_m1.csv")
pt1.to_csv(path + "estimate/result/archive/okresy_m1_" + t + ".csv")

if counted_percentage > 0:
  pt2x = pt2.T.merge(results.loc[:, ['id', 'slope']], on='id', how='left')
  pt2y = pt2x.iloc[:, 1:(len(pt2x.columns) - 1)].multiply(1 + pt2x['slope'] * current_slope, axis=0)
  pt2 = pt2y.T
pt2.reset_index(inplace=True)
pt2.to_csv(path + "estimate/result/okresy_m1s.csv")
pt2.to_csv(path + "estimate/result/archive/okresy_m1s_" + t + ".csv")

print("Estimation done.")