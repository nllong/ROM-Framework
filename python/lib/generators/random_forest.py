import zipfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lib.shared import pickle_file, save_dict_to_csv, zipdir
from pandas.plotting import lag_plot
from scipy import stats
from scipy.stats import spearmanr, pearsonr
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

from model_generator_base import ModelGeneratorBase


class RandomForest(ModelGeneratorBase):
    def __init__(self, analysis_id, random_seed=None):
        super(RandomForest, self).__init__(analysis_id, random_seed)

    def evaluate(self, model, model_name, x_data, y_data, covariates):
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
        plt.savefig('%s/%s.png' % (self.images_dir, model_name))
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
        plt.savefig('%s/%s_importance.png' % (self.images_dir, model_name))
        plt.clf()

        return performance

    def build(self, data_file, covariates, data_types, responses):
        # data_file_to_csv()
        dataset = pd.read_csv(data_file)
        # this column is a redundant column

        print list(dataset.columns.values)
        if 'DistrictCoolingOutletTemperature' in list(dataset.columns.values):
            dataset = dataset.drop('DistrictCoolingOutletTemperature', 1)

        # update some of the column names so they make sense to this model
        dataset = dataset.rename(columns={
            'DistrictHeatingOutletTemperature': 'ETSInletTemperature',
            'DistrictHeatingInletTemperature': 'ETSHeatingOutletTemperature',
            'DistrictCoolingInletTemperature': 'ETSCoolingOutletTemperature',
        })

        # type cast the columns - this is probably not needed.
        dataset[data_types['float']] = dataset[data_types['float']].astype(float)
        dataset[data_types['int']] = dataset[data_types['int']].astype(int)

        # Analyze the dataset
        # get the first UUID in the dataset

        simulation_id = dataset['_id'][0]
        single_simulation = dataset[dataset._id == simulation_id]

        for var in ['ETSInletTemperature', 'DistrictHeatingMassFlowRate']:
            # lag variables
            if var in list(single_simulation.columns.values):
                plt.figure()
                lag_plot(single_simulation[var])
                plt.savefig('%s/%s_lag.png' % (self.images_dir, var))
                plt.clf()

        for var in ['DistrictHeatingMassFlowRate', 'DistrictCoolingMassFlowRate']:
            if var in list(single_simulation.columns.values):
                series = dataset[['var']]
                plt.figure()
                series[series.DistrictHeatingMassFlowRate > 0].plot.box()
                plt.savefig('%s/%sPlots.png' % (self.images_dir, var))
                plt.clf()

        train_x, test_x, train_y, test_y = train_test_split(
            dataset[covariates],
            dataset[responses],
            train_size=0.7,
            test_size=0.3,
            random_state=self.random_seed
        )
        print "Training dataset size is %s" % len(train_x)

        for response in responses:
            print "Fitting Random Forest model for %s" % response
            trained_model = RandomForestRegressor(n_estimators=10, n_jobs=-1)
            trained_model.fit(train_x, train_y[response])
            # print the data types of the training set
            # print train_x.columns.to_series().groupby(train_x.dtypes).groups
            pickle_file(trained_model, '%s/%s' % (self.models_dir, response))

            # Evaluate the forest when building them
            self.model_results.append(
                self.evaluate(trained_model, response, test_x, test_y[response], covariates)
            )

            # print "Fitting Linear Model for %s" % response
            # lm = linear_model.LinearRegression()
            # model = lm.fit(train_x, train_y[response])
            # print model
            # print model.predict(test_x)

        save_dict_to_csv(self.model_results, '%s/model_results.csv' % self.base_dir)

        # zip up the models
        zipf = zipfile.ZipFile('%s/models.zip' % self.models_dir, 'w', zipfile.ZIP_DEFLATED)
        zipdir(self.models_dir, zipf, '.pkl')
        zipf.close()
