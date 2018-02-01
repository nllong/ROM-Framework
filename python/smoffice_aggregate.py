# connect to R from python

# pyenv virtualenv 2.7.14 modelica-2.7.14
# In R run: install.packages('randomForest')
# pip install rpy2==2.8.6

import csv

import datetime

from epw.epw_file import EpwFile
from rf_models import ETSModel

# read a weather file

epw = EpwFile('epw/USA_CO_Golden-NREL.724666_TMY3.epw')

heating_system_model = ETSModel('system', 'heating')
heating_ambient_model = ETSModel('ambient', 'heating')
heating_outlet_temp_model = ETSModel('outlet', 'heating')
cooling_system_model = ETSModel('system', 'cooling')
cooling_ambient_model = ETSModel('ambient', 'cooling')
cooling_outlet_temp_model = ETSModel('outlet', 'cooling')

inlet_temp = 20

time_series = [
    [
        'datetime', 'month', 'day', 'hour', 'minute', 'day_of_week', 'heating_system',
        'heating_ambient', 'heating_outlet', 'cooling_system', 'cooling_ambient',
        'cooling_outlet'
    ]
]

print datetime.datetime.now()
for index, datum in enumerate(epw.data):
    # Start on Sunday
    day_of_week = index % 7

    if index % 250 == 0:
        print "... processing ... %s - %s" % (datetime.datetime.now(), index)

    new_row = [
        "%s/%s/2017 %s:00" % (datum['month'], datum['day'], datum['hour'] - 1),
        datum['month'],
        datum['day'],
        datum['hour'] - 1,
        datum['minute'],
        day_of_week,
        heating_system_model.yhat(
            datum['month'], datum['hour'] - 1, day_of_week, datum['dry_bulb'], datum['rh'], inlet_temp
        ),
        heating_ambient_model.yhat(
            datum['month'], datum['hour'] - 1, day_of_week, datum['dry_bulb'], datum['rh'], inlet_temp
        ),
        heating_outlet_temp_model.yhat(
            datum['month'], datum['hour'] - 1, day_of_week, datum['dry_bulb'], datum['rh'], inlet_temp
        ),
        cooling_system_model.yhat(
            datum['month'], datum['hour'] - 1, day_of_week, datum['dry_bulb'], datum['rh'],
            inlet_temp
        ),
        cooling_ambient_model.yhat(
            datum['month'], datum['hour'] - 1, day_of_week, datum['dry_bulb'], datum['rh'],
            inlet_temp
        ),
        cooling_outlet_temp_model.yhat(
            datum['month'], datum['hour'] - 1, day_of_week, datum['dry_bulb'], datum['rh'],
            inlet_temp
        ),
    ]

    time_series.append(new_row)

    # if index > 100:
    #     break

print datetime.datetime.now()

with open('model_output.csv', 'wb') as file:
    writer = csv.writer(file)
    writer.writerows(time_series)

print time_series
