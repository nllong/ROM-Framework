# pyenv virtualenv 2.7.14 modelica-2.7.14

import os

from lib.metamodels import Metamodels
from lib.analysis_definition import AnalysisDefinition

# ANALYSIS_ID = "3ff422c2-ca11-44db-b955-b39a47b011e7"
ANALYSIS_ID = "66fb9766-26e7-4bed-bdf9-0fbfbc8d6c7e"  # with mass flow

# Load in the models for analysis
reduced_order_model = Metamodels('./metamodels.json')
reduced_order_model.set_analysis(ANALYSIS_ID)
reduced_order_model.load_models()

## Cooling
analysis = AnalysisDefinition('sweep-massflow-cooling.json')
analysis.load_weather_file('lib/epw/USA_CO_Golden-NREL.724666_TMY3.epw')
data = analysis.as_dataframe()
data['HeatingElectricity'] = reduced_order_model.yhat('HeatingElectricity', data)
data['CoolingElectricity'] = reduced_order_model.yhat('CoolingElectricity', data)
data['DistrictCoolingChilledWaterEnergy'] = reduced_order_model.yhat('DistrictCoolingChilledWaterEnergy', data)
data['DistrictHeatingHotWaterEnergy'] = reduced_order_model.yhat('DistrictHeatingHotWaterEnergy', data)
data['ETSHeatingOutletTemperature'] = reduced_order_model.yhat('ETSHeatingOutletTemperature', data)
data['ETSCoolingOutletTemperature'] = reduced_order_model.yhat('ETSCoolingOutletTemperature', data)
reduced_order_model.save_2d_csvs(data, 'ETSInletTemperature', 'DistrictCoolingMassFlowRate', 'mass_flow', 'cooling', True)

## Heating
analysis = AnalysisDefinition('sweep-massflow-heating.json')
analysis.load_weather_file('lib/epw/USA_CO_Golden-NREL.724666_TMY3.epw')
data = analysis.as_dataframe()
data['HeatingElectricity'] = reduced_order_model.yhat('HeatingElectricity', data)
data['CoolingElectricity'] = reduced_order_model.yhat('CoolingElectricity', data)
data['DistrictCoolingChilledWaterEnergy'] = reduced_order_model.yhat('DistrictCoolingChilledWaterEnergy', data)
data['DistrictHeatingHotWaterEnergy'] = reduced_order_model.yhat('DistrictHeatingHotWaterEnergy', data)
data['ETSHeatingOutletTemperature'] = reduced_order_model.yhat('ETSHeatingOutletTemperature', data)
data['ETSCoolingOutletTemperature'] = reduced_order_model.yhat('ETSCoolingOutletTemperature', data)
reduced_order_model.save_2d_csvs(data, 'ETSInletTemperature', 'DistrictHeatingMassFlowRate', 'mass_flow', 'heating', True)
