# connect to R from python

# pyenv virtualenv 2.7.14 modelica-2.7.14
# In R run: install.packages('randomForest')
# pip install rpy2==2.8.6

import csv
import datetime

from epw.epw_file import EpwFile
from ets_model import ETSModel

# read a weather file
ANALYSIS_ID = "3ff422c2-ca11-44db-b955-b39a47b011e7"

epw = EpwFile('epw/USA_CO_Golden-NREL.724666_TMY3.epw')

print "Loading Models"
heating_system_model = ETSModel('output/%s/models' % ANALYSIS_ID, 'system', 'heating')
heating_ambient_model = ETSModel('output/%s/models' % ANALYSIS_ID, 'ambient', 'heating')
heating_outlet_temp_model = ETSModel('output/%s/models' % ANALYSIS_ID, 'outlet', 'heating')
cooling_system_model = ETSModel('output/%s/models' % ANALYSIS_ID, 'system', 'cooling')
cooling_ambient_model = ETSModel('output/%s/models' % ANALYSIS_ID, 'ambient', 'cooling')
cooling_outlet_temp_model = ETSModel('output/%s/models' % ANALYSIS_ID, 'outlet', 'cooling')
print "Finished Loading Models"

inlet_temps = [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
yhat_covariates = []

for inlet_temp in inlet_temps:
    time_series = [
        [
            'datetime', 'month', 'day', 'hour', 'minute', 'day_of_week', 'inlet_temp',
            'heating_system', 'heating_ambient', 'heating_outlet', 'cooling_system',
            'cooling_ambient', 'cooling_outlet'
        ]
    ]
    print "Start running models at %s" % datetime.datetime.now()

    # Structure the data so that we don't have to iterate and store the data into the time_series
    # arrays for reporting
    for index, datum in enumerate(epw.data):
        # Start on Sunday
        day_of_week = index % 7
        if index % 250 == 0:
            print "... processing ... %s - %s" % (datetime.datetime.now(), index)

        new_row = [
            datum['month'],
            datum['hour'] - 1,
            day_of_week,
            datum['dry_bulb'],
            datum['rh'],
            inlet_temp,
        ]
        yhat_covariates.append(new_row)

        new_row = [
                      "%s/%s/2017 %s:00" % (datum['month'], datum['day'], datum['hour'] - 1),
                  ] + new_row
        time_series.append(new_row)

    heating_system_model_res = heating_system_model.yhat_array(yhat_covariates)
    heating_ambient_model_res = heating_ambient_model.yhat_array(yhat_covariates)
    heating_outlet_temp_model_res = heating_outlet_temp_model.yhat_array(yhat_covariates)
    cooling_system_model_res = cooling_system_model.yhat_array(yhat_covariates)
    cooling_ambient_model_res = cooling_ambient_model.yhat_array(yhat_covariates)
    cooling_outlet_temp_model_res = cooling_outlet_temp_model.yhat_array(yhat_covariates)

    # Add in the RF model results
    for idx, time_serie in enumerate(time_series):
        if idx == 0:
            continue

        time_serie.append(heating_system_model_res[idx - 1])
        time_serie.append(heating_ambient_model_res[idx - 1])
        time_serie.append(heating_outlet_temp_model_res[idx - 1])
        time_serie.append(cooling_system_model_res[idx - 1])
        time_serie.append(cooling_ambient_model_res[idx - 1])
        time_serie.append(cooling_outlet_temp_model_res[idx - 1])

    with open('output/%s/rf_time_series_%s_deg.csv' % (ANALYSIS_ID, inlet_temp), 'wb') as file:
        writer = csv.writer(file)
        writer.writerows(time_series)
