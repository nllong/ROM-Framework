# !/usr/bin/env python
#
# Author: Nicholas Long (nicholas.l.long@colorado.edu)

import os
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

from lib.shared import pickle_file, save_dict_to_csv

# path = os.path.realpath(__file__)
# isn't the current path this anyway?
# os.chdir(path)

# Name: Small Office Building
# Covariates: Inlet Temperature
# Analysis ID: 3ff422c2-ca11-44db-b955-b39a47b011e7
# Number of Samples: 100

# Name: Small Office Building
# Covariates: Inlet Temperature, Delta T
# Analysis ID: 5564b7d5-4def-498b-ad5b-d4f12a463275
# Number of Samples: 10

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--analysis_id", default="3ff422c2-ca11-44db-b955-b39a47b011e7", help="ID of the Analysis Models")
args = parser.parse_args()

# Setup directories
if not os.path.exists('output/%s/images' % args.analysis_id):
    os.makedirs('output/%s/images' % args.analysis_id)

if not os.path.exists('output/%s/models' % args.analysis_id):
    os.makedirs('output/%s/models' % args.analysis_id)


def evaluate_forest(model, model_name, x_data, y_data, covariates):
    """
    Evaluate the performance of the forest based on known x_data and y_data.

    :param model:
    :param model_name:
    :param x_data:
    :param y_data:
    :param covariates: list, names of the covariates in the dataframes
    :return:
    """
    yhat = model.predict(x_data)

    plt.scatter(y_data, yhat)
    plt.subplots_adjust(left=0.125)
    plt.savefig('output/%s/images/%s.png' % (args.analysis_id, model_name))
    plt.xlabel('y')
    plt.ylabel('yhat')
    plt.clf()

    slope, intercept, r_value, p_value, std_err = stats.linregress(y_data, yhat)
    performance = {
        'name': model_name,
        'slope': slope,
        'intercept': intercept,
        'r_value': r_value,
        'p_value': p_value,
        'std_err': std_err,
        'r_squared': r_value ** 2,
    }

    importances = model.feature_importances_
    indices = np.argsort(importances)
    covariates_array = np.asarray(covariates)

    plt.title('Feature Importances')
    plt.barh(range(len(indices)), importances[indices], color='b', align='center')
    plt.yticks(range(len(indices)), covariates_array[indices])
    plt.xlabel('Relative Importance')
    plt.subplots_adjust(left=0.5)
    plt.savefig('output/%s/images/%s_importance.png' % (args.analysis_id, model_name))
    plt.clf()

    return performance


def build_forest(data_file):
    model_results = []

    # data_file_to_csv()
    dataset = pd.read_csv(data_file)
    # this column is a redundant column
    dataset = dataset.drop('DistrictCoolingOutletTemperature', 1)
    # update some of the column names so they make sense to this model
    dataset = dataset.rename(columns={
        'DistrictHeatingOutletTemperature': 'ETSInletTemperature',
        'DistrictHeatingInletTemperature': 'ETSHeatingOutletTemperature',
        'DistrictCoolingInletTemperature': 'ETSCoolingOutletTemperature',
    })

    print dataset.columns.values
    # We are now regressing on the entire dataset and not limiting based on the heating / cooling
    # mode.

    # only keep data where there is massflow rates
    # heating_dataset = dataset[
    #     (dataset.DistrictCoolingMassFlowRate == 0) & (dataset.DistrictHeatingMassFlowRate > 0)
    # ]
    # dataset = heating_dataset
    # dataset = dataset[
    #     (dataset.DistrictHeatingMassFlowRate != 0) | (dataset.DistrictCoolingMassFlowRate != 0)
    # ]

    # TODO: Read this from a JSON file in the results directory
    # covariates of interest
    covariates = [
        'Month',
        'Hour',
        'DayofWeek',
        'SiteOutdoorAirDrybulbTemperature',
        'SiteOutdoorAirRelativeHumidity',
        'ETSInletTemperature',
        # 'ambient_loop_temperature_setpoint.design_delta',
    ]
    responses = [
        'HeatingElectricity',
        'CoolingElectricity',
        'ETSHeatingOutletTemperature',
        'ETSCoolingOutletTemperature',
        'DistrictCoolingChilledWaterEnergy',
        'DistrictHeatingHotWaterEnergy',
    ]

    train_x, test_x, train_y, test_y = train_test_split(dataset[covariates], dataset[responses],
                                                        train_size=0.7)

    for response in responses:
        trained_model = RandomForestRegressor(n_estimators=50, n_jobs=-1)
        trained_model.fit(train_x, train_y[response])

        pickle_file(trained_model, 'output/%s/models/%s' % (args.analysis_id, response))

        # Evaluate the forest when building them
        model_results.append(
            evaluate_forest(trained_model, response, test_x, test_y[response], covariates)
        )
        print "Training dataset size is %s" % len(train_x)

    save_dict_to_csv(model_results, 'output/%s/model_results.csv' % args.analysis_id)

build_forest('output/%s/simulation_results.csv' % args.analysis_id)

