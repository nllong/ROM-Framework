# pyenv virtualenv 2.7.14 modelica-2.7.14

import os

from lib.analyses import Analyses
from lib.analysis_definition import AnalysisDefinition
from lib.save_csv import save_multidimensional_csvs

# ANALYSIS_ID = "3ff422c2-ca11-44db-b955-b39a47b011e7"
ANALYSIS_ID = "66fb9766-26e7-4bed-bdf9-0fbfbc8d6c7e"  # with mass flow
if not os.path.exists('output/%s/lookup_tables' % ANALYSIS_ID):
    os.makedirs('output/%s/lookup_tables' % ANALYSIS_ID)

# Load in the models for analysis
reduced_order_model = Analyses('./analyses.json')
reduced_order_model.set_analysis(ANALYSIS_ID)

# Load in the analysis definition
analysis = AnalysisDefinition('sweep-massflow-cooling.json', 'lib/epw/USA_CO_Golden-NREL.724666_TMY3.epw')
data = analysis.as_dataframe()
# TODO: add a method to calculate all responses automatically
data['HeatingElectricity'] = reduced_order_model.yhat('HeatingElectricity', data)
data['CoolingElectricity'] = reduced_order_model.yhat('CoolingElectricity', data)
data['DistrictCoolingChilledWaterEnergy'] = reduced_order_model.yhat('DistrictCoolingChilledWaterEnergy', data)
data['DistrictHeatingHotWaterEnergy'] = reduced_order_model.yhat('DistrictHeatingHotWaterEnergy', data)
data['ETSHeatingOutletTemperature'] = reduced_order_model.yhat('ETSHeatingOutletTemperature', data)
data['ETSCoolingOutletTemperature'] = reduced_order_model.yhat('ETSCoolingOutletTemperature', data)

save_multidimensional_csvs(data, reduced_order_model, analysis, ANALYSIS_ID, 'DistrictCoolingMassFlowRate')


analysis = AnalysisDefinition('sweep-massflow-heating.json', 'lib/epw/USA_CO_Golden-NREL.724666_TMY3.epw')
data = analysis.as_dataframe()
# TODO: add a method to calculate all responses automatically
data['HeatingElectricity'] = reduced_order_model.yhat('HeatingElectricity', data)
data['CoolingElectricity'] = reduced_order_model.yhat('CoolingElectricity', data)
data['DistrictCoolingChilledWaterEnergy'] = reduced_order_model.yhat('DistrictCoolingChilledWaterEnergy', data)
data['DistrictHeatingHotWaterEnergy'] = reduced_order_model.yhat('DistrictHeatingHotWaterEnergy', data)
data['ETSHeatingOutletTemperature'] = reduced_order_model.yhat('ETSHeatingOutletTemperature', data)
data['ETSCoolingOutletTemperature'] = reduced_order_model.yhat('ETSCoolingOutletTemperature', data)

save_multidimensional_csvs(data, reduced_order_model, analysis, ANALYSIS_ID, 'DistrictHeatingMassFlowRate')
