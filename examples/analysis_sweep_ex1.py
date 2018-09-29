# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example analysis script demonstrating how to programatically load and run already persisted
reduced order models using a weather file. This example is very similar to the analysis_ex1.py
excpet for the analysis.load_weather_file method. This method and the smoff-one-year.json file
together specify how to parse the weather file.

The second part of this script using seaborn to generate heatmaps of the two responses of
interest. The plots are stored in a child directory.

Run the example by calling the following:

.. code-block:: bash

    python analysis_sweep_ex1.py

.. moduleauthor:: Nicholas Long (nicholas.l.long@colorado.edu, nicholas.lee.long@gmail.com)
"""

import os
# Add the parent directory to the path so the metamodel and analysis definitiona libraries
# can be found.
import sys

import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append("..")  # Adds higher directory to python modules path.

from rom.metamodels import Metamodels
from rom.analysis_definition.analysis_definition import AnalysisDefinition

# Load in the models for analysis
rom = Metamodels('./smoff/metamodels.json')
rom.set_analysis('smoff_parametric_sweep')

# Load the exising models
if rom.models_exist(
        'RandomForest',
        models_to_load=['HeatingElectricity', 'DistrictHeatingHotWaterEnergy'],
        root_path='smoff'):
    rom.load_models(
        'RandomForest',
        models_to_load=['HeatingElectricity', 'DistrictHeatingHotWaterEnergy'],
        root_path='smoff')
else:
    raise Exception('ROMs do not exist')

# Load in the analysis definition
analysis = AnalysisDefinition('smoff-one-year.json')
analysis.load_weather_file('lib/USA_CO_Golden-NREL.724666_TMY3.epw')

# convert the analysis definition to a dataframe for use in the rom
data = analysis.as_dataframe()
data = rom.yhats(data, 'RF', ['HeatingElectricity', 'DistrictHeatingHotWaterEnergy'])

# describe the data
print(data.describe())

# view a couple single rows
print(data.iloc[0])
print(data.iloc[3000])

# Create heat maps of the modeled data
output_dir = 'analysis_sweep_ex1_output'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

responses = [
    'RF_HeatingElectricity',
    'RF_DistrictHeatingHotWaterEnergy',
]
for response in responses:
    heatdata = data[["DayOfYear", "Hour", response]].pivot("DayOfYear", "Hour", response)
    f, ax = plt.subplots(figsize=(5, 12))
    sns.heatmap(heatdata)
    filename = '%s/%s.png' % (output_dir, response.replace(' ', '_'))
    plt.savefig(filename)
    plt.close('all')
