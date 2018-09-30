# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This example CLI file shows how a simple application can be built that reads in all the values
from the command line and reports the values of the responses passed.

.. code-block:: bash

    # Single response - with only setting the inlet temperature
    python analysis_cli_ex1.py -f smoff/metamodels.json -i 18

    # Multiple responses - with only setting the inlet temperature
    python analysis_cli_ex1.py -f smoff/metamodels.json -i 18 -r HeatingElectricity DistrictHeatingHotWaterEnergy

.. moduleauthor:: Nicholas Long (nicholas.l.long@colorado.edu, nicholas.lee.long@gmail.com)
"""

import argparse
import json
import sys

import pandas as pd

sys.path.append('..')  # Adds higher directory to python modules path.

from rom.metamodels import Metamodels

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', help='Description file to use', default='metamodels.json')
parser.add_argument('-a', '--analysis_id', default='smoff_parametric_sweep',
                    help='ID of the Analysis Models')

parser.add_argument('--model_type', default='RandomForest',
                    choices=['LinearModel', 'RandomForest', 'SVR'])
parser.add_argument('-r', '--responses', nargs='*', default=['HeatingElectricity'],
                    help='List of responses')
parser.add_argument('-d', '--day_of_week', type=int, default=0, help='Day of Week: 0-Sun to 6-Sat')
parser.add_argument('-m', '--month', type=int, default=1, help='Month: 1-Jan to 12-Dec')
parser.add_argument('-H', '--hour', type=int, default=9, help='Hour of Day: 0 to 23')
parser.add_argument('-T', '--outdoor_drybulb', type=float, default=-5,
                    help='Outdoor Drybulb Temperature')
parser.add_argument('-RH', '--outdoor_rh', type=float, default=50,
                    help='Percent Outdoor Relative Humidity')
parser.add_argument('-i', '--inlet_temp', type=float, default=20, help='Inlet Temperature')
parser.add_argument('--lpd', type=float, default=9.5, help='Lighting Power Density (W/m2)')

args = parser.parse_args()
# Print out the arguments that are being run
print(json.dumps(vars(args), indent=2, sort_keys=True))

rom = Metamodels(args.file)
rom.set_analysis(args.analysis_id)

# Load the exising models
if rom.models_exist(args.model_type, models_to_load=args.responses, root_path='smoff'):
    rom.load_models(args.model_type, models_to_load=args.responses, root_path='smoff')
else:
    raise Exception('ROMs do not exist')

# put the data into a dataframe for evaluation
data = {
    'Month': args.month,
    'Hour': args.hour,
    'DayofWeek': args.day_of_week,
    'SiteOutdoorAirDrybulbTemperature': args.outdoor_drybulb,
    'SiteOutdoorAirRelativeHumidity': args.outdoor_rh,
    'lpd_average': args.lpd,
    'ETSInletTemperature': args.inlet_temp,
}
df = pd.DataFrame([data])
for response in args.responses:
    v = rom.yhat(response, df)
    print(v[0])
