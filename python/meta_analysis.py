# pyenv virtualenv 2.7.14 modelica-2.7.14

from lib.analysis_definition import AnalysisDefinition
from lib.metamodels import Metamodels

ANALYSIS_NAME = "smoff_vary_temp"  # with mass flow
reduced_order_model = Metamodels('./metamodels.json')
reduced_order_model.set_analysis(ANALYSIS_NAME)
reduced_order_model.load_models()

# ## Cooling
# analysis = AnalysisDefinition('sweep-massflow-cooling.json')
# analysis.load_weather_file('lib/epw/USA_CO_Golden-NREL.724666_TMY3.epw')
# data = analysis.as_dataframe()
# data['HeatingElectricity'] = reduced_order_model.yhat('HeatingElectricity', data)
# data['CoolingElectricity'] = reduced_order_model.yhat('CoolingElectricity', data)
# data['DistrictCoolingChilledWaterEnergy'] = reduced_order_model.yhat('DistrictCoolingChilledWaterEnergy', data)
# data['DistrictHeatingHotWaterEnergy'] = reduced_order_model.yhat('DistrictHeatingHotWaterEnergy', data)
# data['ETSHeatingOutletTemperature'] = reduced_order_model.yhat('ETSHeatingOutletTemperature', data)
# data['ETSCoolingOutletTemperature'] = reduced_order_model.yhat('ETSCoolingOutletTemperature', data)
# reduced_order_model.save_2d_csvs(data, 'ETSInletTemperature', 'DistrictCoolingMassFlowRate', 'mass_flow', 'cooling', True)
#
# ## Heating
# analysis = AnalysisDefinition('sweep-massflow-heating.json')
# analysis.load_weather_file('lib/epw/USA_CO_Golden-NREL.724666_TMY3.epw')
# data = analysis.as_dataframe()
# data['HeatingElectricity'] = reduced_order_model.yhat('HeatingElectricity', data)
# data['CoolingElectricity'] = reduced_order_model.yhat('CoolingElectricity', data)
# data['DistrictCoolingChilledWaterEnergy'] = reduced_order_model.yhat('DistrictCoolingChilledWaterEnergy', data)
# data['DistrictHeatingHotWaterEnergy'] = reduced_order_model.yhat('DistrictHeatingHotWaterEnergy', data)
# data['ETSHeatingOutletTemperature'] = reduced_order_model.yhat('ETSHeatingOutletTemperature', data)
# data['ETSCoolingOutletTemperature'] = reduced_order_model.yhat('ETSCoolingOutletTemperature', data)
# reduced_order_model.save_2d_csvs(data, 'ETSInletTemperature', 'DistrictHeatingMassFlowRate', 'mass_flow', 'heating', True)

## Temps only -- both heating and cooling
analysis = AnalysisDefinition('sweep-inlet-temperatures.json')
analysis.load_weather_file('lib/epw/USA_CO_Golden-NREL.724666_TMY3.epw')
data = analysis.as_dataframe()
data['HeatingElectricity'] = reduced_order_model.yhat('HeatingElectricity', data)
data['CoolingElectricity'] = reduced_order_model.yhat('CoolingElectricity', data)
data['DistrictCoolingChilledWaterEnergy'] = reduced_order_model.yhat('DistrictCoolingChilledWaterEnergy', data)
data['DistrictHeatingHotWaterEnergy'] = reduced_order_model.yhat('DistrictHeatingHotWaterEnergy', data)
data['ETSHeatingOutletTemperature'] = reduced_order_model.yhat('ETSHeatingOutletTemperature', data)
data['ETSCoolingOutletTemperature'] = reduced_order_model.yhat('ETSCoolingOutletTemperature', data)
reduced_order_model.save_2d_csvs(data, 'ETSInletTemperature', 'lookup', True)


#
# # ANALYSIS_NAME = "retail_no_ets"
# ANALYSIS_NAME = "smoff_no_ets"
# reduced_order_model = Metamodels('./metamodels.json')
# reduced_order_model.set_analysis(ANALYSIS_NAME)
# reduced_order_model.load_models()
#
# analysis = AnalysisDefinition('sweep-smoff-loadonly.json')
# # analysis = AnalysisDefinition('sweep-retail-loadonly.json')
# analysis.load_weather_file('lib/epw/USA_CO_Golden-NREL.724666_TMY3.epw')
# data = analysis.as_dataframe()
# data['HeatingElectricity'] = reduced_order_model.yhat('HeatingElectricity', data)
# data['CoolingElectricity'] = reduced_order_model.yhat('CoolingElectricity', data)
# # reduced_order_model.save_2d_csvs(data, 'ETSInletTemperature', 'DistrictHeatingMassFlowRate', 'mass_flow', 'heating', True)
# reduced_order_model.save_csv(data, '%s_building_loads' % ANALYSIS_NAME)
