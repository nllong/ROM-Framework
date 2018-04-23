# !/usr/bin/env python
#
# Author: Nicholas Long (nicholas.l.long@colorado.edu)

import argparse
import os
import zipfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.plotting import lag_plot
from scipy import stats
from sklearn import linear_model
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from scipy.stats import spearmanr, pearsonr

from lib.shared import pickle_file, save_dict_to_csv, zipdir
from lib.analyses import Analyses

# path = os.path.realpath(__file__)
# isn't the current path this anyway?
# os.chdir(path)

# Name: Small Office Building
# Covariates: Inlet Temperature
# Analysis ID: 3ff422c2-ca11-44db-b955-b39a47b011e7
# Number of Samples: 100

# Name: Small Office Building
# Covariates: Inlet Temperature, Delta T
# Analysis ID: 5564b7d5-4def-498b-ad5b-d4f12a46327
# Number of Samples: 10

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--analysis_id", default="3ff422c2-ca11-44db-b955-b39a47b011e7",
                    help="ID of the Analysis Models")
args = parser.parse_args()
print("Passed build_models.py args: %s" % args)


# Setup directories
if not os.path.exists('output/%s/images' % args.analysis_id):
    os.makedirs('output/%s/images' % args.analysis_id)

if not os.path.exists('output/%s/models' % args.analysis_id):
    os.makedirs('output/%s/models' % args.analysis_id)

# Read in the Analysis information from the analyses.json

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

    test_score = r2_score(y_data, yhat)
    spearman = spearmanr(y_data, yhat)
    pearson = pearsonr(y_data, yhat)

    slope, intercept, r_value, p_value, std_err = stats.linregress(y_data, yhat)
    performance = {
        'name': model_name,
        'slope': slope,
        'intercept': intercept,
        'r_value': r_value,
        'p_value': p_value,
        'std_err': std_err,
        'r_squared': r_value ** 2,
        'rf_r_squared': test_score,
        'spearman': spearman,
        'pearson': pearson,
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


def build_forest(data_file, covariates, responses):
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

    # Analyze the dataset
    # get the first UUID in the dataset
    simulation_id = dataset['_id'][0]
    single_simulation = dataset[dataset._id == simulation_id]
    plt.figure()
    lag_plot(single_simulation['ETSInletTemperature'])
    plt.savefig('output/%s/images/ETSInletTemperature_lag.png' % (args.analysis_id))
    plt.clf()

    plt.figure()
    lag_plot(single_simulation['DistrictHeatingMassFlowRate'])
    plt.savefig('output/%s/images/DistrictHeatingMassFlowRate_lag.png' % (args.analysis_id))
    plt.clf()

    series = dataset[['DistrictHeatingMassFlowRate']]
    plt.figure()
    series[series.DistrictHeatingMassFlowRate > 0].plot.box()
    plt.savefig('output/%s/images/HeatingMassFlowBoxPlots.png' % (args.analysis_id))
    plt.clf()

    series = dataset[['DistrictCoolingMassFlowRate']]
    plt.figure()
    series[series.DistrictCoolingMassFlowRate > 0].plot.box()
    plt.savefig('output/%s/images/CoolingMassFlowBoxPlots.png' % (args.analysis_id))
    plt.clf()

    train_x, test_x, train_y, test_y = train_test_split(dataset[covariates], dataset[responses],
                                                        train_size=0.7)
    print "Training dataset size is %s" % len(train_x)

    for response in responses:
        print "Fitting Random Forest model for %s" % response
        trained_model = RandomForestRegressor(n_estimators=10, n_jobs=-1, oob_score=True)
        trained_model.fit(train_x, train_y[response])

        pickle_file(trained_model, 'output/%s/models/%s' % (args.analysis_id, response))

        # Evaluate the forest when building them
        model_results.append(
            evaluate_forest(trained_model, response, test_x, test_y[response], covariates)
        )

        print "Fitting Linear Model for %s" % response
        lm = linear_model.LinearRegression()
        model = lm.fit(train_x, train_y[response])
        print model
        print model.predict(test_x)

    save_dict_to_csv(model_results, 'output/%s/model_results.csv' % args.analysis_id)

    # zip up the models
    zipf = zipfile.ZipFile('output/%s/models/models.zip' % args.analysis_id, 'w', zipfile.ZIP_DEFLATED)
    zipdir('output/%s/models/' % args.analysis_id, zipf, '.pkl')
    zipf.close()


print("Loading analyses.json")
analysis_file = Analyses('./analyses.json')
if analysis_file.set_analysis(args.analysis_id):
    build_forest(
        'output/%s/simulation_results.csv' % args.analysis_id,
        analysis_file.covariate_names,
        analysis_file.response_names
    )
