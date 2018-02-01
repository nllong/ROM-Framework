# !/usr/bin/env python
#
# Author: Nicholas Long (nicholas.l.long@colorado.edu

import os
import pickle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

path = '/Users/nlong/working-simulations/analysis/ambient_loop/python'
os.chdir(path)

BUILD_FOREST = True


def pickle_file(obj, filename):
    list_pickle = open(filename, 'wb')
    pickle.dump(obj, list_pickle)
    list_pickle.close()


def unpickle_file(filename):
    list_unpickle = open(filename, 'rb')
    return pickle.load(list_unpickle)


if BUILD_FOREST:
    # data_file_to_csv()
    dataset = pd.read_csv('../results/results.csv')
    # update some of the column names so they make sense to this model
    dataset = dataset.rename(columns={
        'DistrictHeatingOutletTemperature': 'ETSHeatingInletTemperature',
        'DistrictHeatingInletTemperature': 'ETSHeatingOutletTemperature',
        'DistrictCoolingOutletTemperature': 'ETSCoolingInletTemperature',
        'DistrictCoolingInletTemperature': 'ETSCoolingOutletTemperature',
    })
    # dataset.describe()

    # covariates of interest
    covariates = [
        'Month',
        'Day',
        'DayofWeek',
        'SiteOutdoorAirDrybulbTemperature',
        'SiteOutdoorAirRelativeHumidity',
        'ETSHeatingInletTemperature',
        'ETSCoolingInletTemperature'
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
        print(response)
        trained_model = RandomForestRegressor()
        trained_model.fit(train_x, train_y[response])

        pickle_file(trained_model, '../models/%s.pkl' % response)
        # pickle_file(test_x, 'test_data.pkl')

        # model results
        yhat = trained_model.predict(test_x)

        plt.scatter(test_y[response], yhat)
        plt.savefig('output/%s.png' % response)
        plt.clf()

        slope, intercept, r_value, p_value, std_err = stats.linregress(test_y[response], yhat)
        print("slope: %s" % slope)
        print("intercept: %s" % intercept)
        print("r_value: %s" % r_value)
        print("p_value: %s" % p_value)
        print("std_err: %s" % std_err)
        print("r-squared: %s" % r_value ** 2)

        importances = trained_model.feature_importances_
        indices = np.argsort(importances)
        covariates_array = np.asarray(covariates)

        plt.title('Feature Importances')
        plt.barh(range(len(indices)), importances[indices], color='b', align='center')
        plt.yticks(range(len(indices)), covariates_array[indices])
        plt.xlabel('Relative Importance')
        plt.savefig('output/%s_importance.png' % response)
        plt.clf()

# test_x = unpickle_file('test_data.pkl')
# model = unpickle_file('model.pkl')
# predictions = model.predict(test_x)
#
# print predictions
