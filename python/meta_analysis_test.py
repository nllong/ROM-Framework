# pyenv virtualenv 2.7.14 modelica-2.7.14

import os

from lib.analysis_definition import AnalysisDefinition
from lib.metamodels import Metamodels

# ANALYSIS_ID = "3ff422c2-ca11-44db-b955-b39a47b011e7"
ANALYSIS_ID = "66fb9766-26e7-4bed-bdf9-0fbfbc8d6c7e"  # with mass flow

# Load in the models for analysis
reduced_order_model = Metamodels('./metamodels.json')
reduced_order_model.set_analysis(ANALYSIS_ID)
# Load the exising models
reduced_order_model.load_models('RandomForest', models_to_load=['ETSHeatingOutletTemperature'])

# Load in the analysis definition
analysis = AnalysisDefinition('sweep-temp-test.json')
data = analysis.as_dataframe()
# TODO: add a method to calculate all responses automatically
data['RF_ETSHeatingOutletTemperature'] = reduced_order_model.yhat('ETSHeatingOutletTemperature', data)

print data
print data.describe()
print data.iloc[0]
print data.iloc[7]
print data[(data.Hour == 1) & (data.SiteOutdoorAirDrybulbTemperature == 7.8) & (data.DistrictHeatingMassFlowRate == 0) & (data.SiteOutdoorAirRelativeHumidity == 73) & (data.ETSInletTemperature == 15.4355)]
print data.columns.to_series().groupby(data.dtypes).groups
