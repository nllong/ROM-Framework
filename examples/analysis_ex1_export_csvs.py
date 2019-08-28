# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example analysis script demonstrating how to programatically load and run already persisted
reduced order models. This example loads two response variables (models) from the small office
random forest reduced order models. The loaded models are then passed through the
sweep-temp-test.json analysis definition file. The analysis definition has a few fixed
covariates and a few covariates with multiple values to run.

.. code-block:: bash

    python analysis_ex1.py

.. moduleauthor:: Nicholas Long (nicholas.l.long@colorado.edu, nicholas.lee.long@gmail.com)
"""

import sys

# Add the parent directory to the path so the metamodel and analysis definitiona libraries
# can be found.
sys.path.append("..")  # Adds higher directory to python modules path.

from rom.metamodels import Metamodels
from rom.analysis_definition.analysis_definition import AnalysisDefinition

models = [
    {
        "analysis_name": "smoff_sweep_v2",
        "root_path": "../output/smoff_sweep_v2",
        "sweep_file": "sweep-temp-v2.json",
        "models_to_load": [
            'HeatingElectricity',
            'DistrictHeatingHotWaterEnergy',
            'CoolingElectricity',
            'DistrictCoolingChilledWaterEnergy',
            'ETSHeatingOutletTemperature'
        ]
    },
    {
        "analysis_name": "smoff_sweep_no_ets_v2",
        "root_path": "../output/smoff_sweep_no_ets_v2",
        "sweep_file": "sweep-temp-no-ets-v2.json",
        "models_to_load": [
            'HeatingTotal',
            'CoolingElectricity'
        ]
    },
    {
        "analysis_name": "retail_sweep_v2",
        "root_path": "../output/retail_sweep_v2",
        "sweep_file": "sweep-temp-v2.json",
        "models_to_load": [
            'HeatingElectricity',
            'DistrictHeatingHotWaterEnergy',
            'CoolingElectricity',
            'DistrictCoolingChilledWaterEnergy',
            'ETSHeatingOutletTemperature'
        ]
    },
    {
        "analysis_name": "retail_sweep_no_ets_v2",
        "root_path": "../output/retail_sweep_no_ets_v2",
        "sweep_file": "sweep-temp-no-ets-v2.json",
        "models_to_load": [
            'HeatingTotal',
            'CoolingElectricity'
        ]
    }
]

for m in models:
    print(f"Running metamodel {m['analysis_name']}")
    # Load in the models for analysis
    rom = Metamodels('../metamodels.json')
    rom.set_analysis(m['analysis_name'])

    # Load the exising models
    if rom.models_exist(
            'RandomForest',
            models_to_load=m['models_to_load'],
            root_path=m['root_path'],
            downsample=0.005):
        rom.load_models(
            'RandomForest',
            models_to_load=m['models_to_load'],
            root_path=m['root_path'],
            downsample=0.005)
    else:
        raise Exception('ROMs do not exist')

    # Load in the analysis definition
    analysis = AnalysisDefinition(m['sweep_file'])
    analysis.load_weather_file('lib/USA_CO_Golden-NREL.724666_TMY3.epw')

    # convert the analysis definition to a dataframe for use in the rom
    data = analysis.as_dataframe()
    data = rom.yhats(data, 'RF', m['models_to_load'])

    responses = [f'RF_{r}' for r in m['models_to_load']]
    rom.save_2d_csvs(data, 'ETSInletTemperature', 'smoff_sweep_v2')

    # for response in responses:
    #     heatdata = data[["DayOfYear", "Hour", response]].pivot("DayOfYear", "Hour", response)
    #     f, ax = plt.subplots(figsize=(5, 12))
    #     sns.heatmap(heatdata)
    #     filename = '%s/%s.png' % (output_dir, response.replace(' ', '_'))
    #     plt.savefig(filename)
    #     plt.close('all')
