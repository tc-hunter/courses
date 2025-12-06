"""
https://github.com/DOI-USGS/dataretrieval-python
    installation:
        pip install dataretrieval 
        OR
        conda install -c conda-forge dataretrieval

service options:
- instantaneous values (iv)
- daily values (dv)
- statistics (stat)
- site info (site)
- discharge peaks (peaks)
- discharge measurements (measurements)

https://help.waterdata.usgs.gov/parameter_cd?group_cd=PHY
- 00060 = Discharge, cubic feet per second
- 00065 = Gage height, feet

Written by Kim Wood, 2025.09.16
Last modified 2025.12.06
"""
from custom_func import np64_to_dt
from datetime import datetime, timedelta
import dataretrieval.nwis as nwis
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

#### Provide the streamgage ID as a string
site = '09486500'  # https://waterdata.usgs.gov/state/Arizona/
field = '00060'    # 00060 = discharge | 00065 = gage height
field_name = {'00060': 'discharge', '00065': 'gage height'}
field_label = {'00060': 'discharge [$\mathregular{ft^3\ s^{-1}}$]',
               '00065': 'gage height [ft]'}

#### Pull that location's info as its own dataframe (and format site name for later use)
site_info = nwis.get_record(sites=site, service='site')
site_name = site_info['station_nm'].item()
lowercase = 'AT OR AND NEAR'
states = 'AZ'
fixed_name = []
for entry in site_name.split():
    if lowercase.find(entry) == -1 and states.find(entry) == -1:
        entry = entry.capitalize()
    elif lowercase.find(entry) > -1:
        entry = entry.lower()
    fixed_name.append(entry)

#### Get that location's peak discharge events over its period of record
site_peak_discharge = nwis.get_record(sites=site, service='peaks')

#### Peak discharge dates (don't know why the dates are the INDEX but oh well)
peak_dates = np.array(site_peak_discharge.index.values)  # local time? I'm not sure
years = np.array([np64_to_dt(t).year for t in peak_dates])
months = np.array([np64_to_dt(t).month for t in peak_dates])
match = np.where((years>=2020)&(years<=2024)&(months>=6)&(months<=9))[0]  # Jun-Sep, 2020-2024
peak_times = np.array([str(v) for v in site_peak_discharge['peak_tm'].values])

#### Define some plot settings
# 'weight': 'bold'       make text bold (can be used with or instead of 'style')
# 'style': 'italic'      italicize text (can be used with or instead of 'weight')
# 'size': 10.5           font size
legendprop = {'size': 10., 'style': 'italic', 'weight': 'bold'}  # legend appearance

#### Let's check out the 15-minute data for a 6-day span (arbitrary)
#### (from 4 days beforehand through 2 days after)
for m in match:
    date = np64_to_dt(peak_dates[m])
    if date.hour == 0 and peak_times[m] != 'nan':
        hour, minute = peak_times[m].split(':')
        date += timedelta(hours=int(hour))
        date += timedelta(minutes=int(minute))
    start = (date - timedelta(days=5)).strftime('%Y-%m-%d')
    end = (date + timedelta(days=3)).strftime('%Y-%m-%d')
    ## service='iv' grabs instantaneous values (15-minute intervals)
    df = nwis.get_record(sites=site, service='iv', start=start, end=end)
    if df.size == 0:
        continue
    print(date)
    ## NOTE: may not span full 6-day time frame when data are missing
    times = np.array([np64_to_dt(t) for t in df.index.values])
    window = np.where((times>=date-timedelta(days=4))&(times<=date+timedelta(days=2)))[0]
    window_df = df.iloc[window]
    times = times[window].copy()
    ## Figure out reasonable y-axis tick values from input data
    maxvalue = window_df[field].values.max().item()  # maximum value of data
    for interval in np.arange(500.,5001.,500.):
        if maxvalue/interval <= 9.:
            # for readability, plot no more than ten (10) tick labels
            break
    yticks = np.arange(0.,np.ceil(maxvalue/interval)*interval+1.,interval)
    ## Quick plot to visualize discharge
    hours = int(24*(times[-1]-times[0]).days + (times[-1]-times[0]).seconds/(60*60))
    xticks = [times[0]+timedelta(hours=t) for t in range(0,hours+1,12)]
    xticklabels = [t.strftime('%H%M\n%-d %b') for t in xticks]  # format date+time labels
    ## formatting codes: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
    fig, ax = plt.subplots(figsize=(8,6))
    _ = ax.plot(times, window_df[field].values, label=field_name[field])
    _ = ax.axvline(x=date+timedelta(hours=7), c='k', lw=0.5, ls='--')  # AZ = UTC-7
    _ = ax.set_xlim(times[0], times[-1])
    _ = ax.set_xticks(xticks)
    _ = ax.set_xticklabels(xticklabels, fontsize=10.5)
    _ = ax.set_yticks(yticks)
    _ = ax.tick_params(axis='y', labelsize=11., rotation=45)  # rotate y-axis labels
    _ = ax.set_ylim(0, maxvalue*1.02)  # extend y-axis to 2% higher than max value
    _ = ax.set_ylabel(field_label[field], size=12, weight='bold')
    _ = ax.legend(frameon=False, loc='upper left', prop=legendprop)
    TF = fig.transFigure
    pos = ax.get_position()
    _ = ax.text(pos.x1, pos.y1*1.002, ' '.join(fixed_name), ha='right', va='bottom', size=12,
                weight='bold', transform=TF)
    _ = ax.text(pos.x0, pos.y1*1.002, date.strftime('year: %Y'), ha='left', va='bottom', size=12,
                weight='bold', transform=TF)
    plt.show()
    if len(match) > 1:
        break  # only do one iteration of the loop when multiple matches were found


