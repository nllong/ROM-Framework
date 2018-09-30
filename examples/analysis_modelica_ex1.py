# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This example file shows how to load the models using a method based approach for use in Modelica.
The run_model takes only a list of numbers (int and floats). The categorical variables are
converted as needed in order to correctly populate the list of covariates in the dataframe.

For use in Modelica ake sure that the python path is set, such as by running
export PYTHONPATH=`pwd`

Call the following bash command shown below to run this example. This example runs as an
entrypoint; however, when connected to modelica the def run_model will be called directory. Also,
note that the run_model method loads the models every time it is called. This is non-ideal when
using this code in a timestep by timestep simulation. Work needs to be done to determine how to
load the reduced order models only once and call the reduced order model yhat methods each timestep.

.. code-block:: bash

        python analysis_modelica_ex1.py

.. moduleauthor:: Nicholas Long (nicholas.l.long@colorado.edu, nicholas.lee.long@gmail.com)
"""
# Add the parent directory to the path so the metamodel and analysis definitiona libraries
# can be found.
import sys

sys.path.append("..")  # Adds higher directory to python modules path.

import pandas as pd
from rom.metamodels import Metamodels


def load_models(metamodel_filename, model_type, models_to_load):
    rom = Metamodels(metamodel_filename)
    rom.set_analysis('smoff_parametric_sweep')

    # Load the exising models
    if rom.models_exist(model_type, models_to_load=models_to_load, root_path='smoff'):
        rom.load_models(model_type, models_to_load=models_to_load, root_path='smoff')
    else:
        raise Exception('ROMs do not exist')

    return rom


def run_model(values):
    model = int(values[0])
    response = int(values[1])
    data = {
        'Month': int(values[2]),
        'Hour': int(values[3]),
        'DayofWeek': int(values[4]),
        'SiteOutdoorAirDrybulbTemperature': float(values[5]),
        'SiteOutdoorAirRelativeHumidity': float(values[6]),
        'lpd_average': float(values[7]),
        'ETSInletTemperature': float(values[8]),
    }

    # Convert the model integer to correct ROM type
    if model == 1:
        model = 'LinearModel'
    elif model == 2:
        model = 'RandomForest'
    elif model == 3:
        model = 'SVR'

    # Convert the response integer to the correct type
    if response == 1:
        response = 'CoolingElectricity'
    elif response == 2:
        response = 'HeatingElectricity'
    elif response == 3:
        response = 'DistrictCoolingChilledWaterEnergy'
    elif response == 4:
        response = 'DistrictHeatingHotWaterEnergy'
    elif response == 5:
        response = 'ETSOutletTemperature'

    rom = load_models('smoff/metamodels.json', model, [response])

    print('Predicting...')
    df = pd.DataFrame([data])
    print(rom.yhat(response, df)[0])
    v = rom.yhat(response, df)[0]
    print(f'Predicted value is {v}')

    return v


if __name__ == '__main__':
    print("Testing running Modelica-based interface")

    # random forest, heating electricity,
    v = run_model([2, 2, 1, 12, 3, -5, 50, 9.5, 10])
    print(v)
