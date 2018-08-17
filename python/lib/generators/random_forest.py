import zipfile
from collections import OrderedDict

import numpy as np
import pandas as pd
import seaborn as sns
from lib.shared import pickle_file, save_dict_to_csv, zipdir
from scipy import stats
from scipy.stats import spearmanr, pearsonr
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from math import ceil
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

        # perform stats on all the data
        test_score = r2_score(y_data, yhat)
        spearman = spearmanr(y_data, yhat)
        pearson = pearsonr(y_data, yhat)

        slope, intercept, r_value, p_value, std_err = stats.linregress(y_data, yhat)

        performance = OrderedDict([
            ('name', model_name),
            ('slope', slope),
            ('intercept', intercept),
            ('r_value', r_value),
            ('p_value', p_value),
            ('std_err', std_err),
            ('r_squared', r_value ** 2),
            ('rf_r_squared', test_score),
            ('spearman', spearman[0]),
            ('pearson', pearson[0]),
        ])

        self.yy_plots(y_data, yhat, model_name)

        importance_data = pd.Series(model.feature_importances_, index=np.asarray(covariates))
        importance_data = importance_data.nlargest(20)
        ax = sns.barplot(x=list(importance_data), y=list(importance_data.index.values),
                         color="salmon", ci=None)
        ax.set(xlabel='Relative Importance', ylabel='')
        ax.set_title("Importance of %s" % model_name)
        fig = ax.get_figure()
        fig.tight_layout()  # nice magic function!
        fig.savefig('%s/%s_importance.png' % (self.images_dir, model_name))
        fig.clf()

        return performance

    def build(self, data_file, covariates, data_types, responses):
        # TODO: Load some of this from SUPER
        self.responses = responses

        # data_file_to_csv()
        dataset = pd.read_csv(data_file)

        # print list(dataset.columns.values)
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

        param_grid = {
            'max_depth': [None, 5, 50, 500],
            'max_features': [ceil(len(covariates) / 4), ceil(len(covariates) / 3), ceil(len(covariates) / 2)],
            'min_samples_leaf': [1, 5, 10],
            'min_samples_split': [2, 20, 200],
            'n_estimators': [25, 50, 100, 150, 200]
        }

        # Perform randomized search of parameters
        # http://scikit-learn.org/stable/auto_examples/model_selection/plot_randomized_search.html
        # https://towardsdatascience.com/hyperparameter-tuning-the-random-forest-in-python-using-scikit-learn-28d2aa77dd74
        # param_dist = {"max_depth": [3, None],
        #               "max_features": sp_randint(1, 11),
        #               "min_samples_split": sp_randint(2, 11),
        #               "min_samples_leaf": sp_randint(1, 11),
        #               "bootstrap": [True, False],
        #               "criterion": ["gini", "entropy"]}
        #
        # # run randomized search
        # n_iter_search = 20
        # random_search = RandomizedSearchCV(clf, param_distributions=param_grid,
        #                                    n_iter=n_iter_search)

        # TODO: remove hard coded simulation ID for validate_xy
        train_x, test_x, train_y, test_y, validate_xy = self.train_test_validate_split(
            dataset,
            covariates,
            responses,
            '112175a4-5b90-4ebb-a7c2-72123f87a6eb',
        )

        for response in self.responses:
            print "Fitting Random Forest model for %s" % response
            trained_model = RandomForestRegressor(n_estimators=40, n_jobs=-1)
            trained_model.fit(train_x, train_y[response])
            # print the data types of the training set
            # print train_x.columns.to_series().groupby(train_x.dtypes).groups
            pickle_file(trained_model, '%s/%s' % (self.models_dir, response))

            # Evaluate the forest when building them
            self.model_results.append(
                self.evaluate(
                    trained_model, response, test_x, test_y[response], covariates
                )
            )

        if self.model_results:
            save_dict_to_csv(self.model_results, '%s/model_results.csv' % self.base_dir)

        # zip up the models
        zipf = zipfile.ZipFile(
            '%s/models.zip' % self.models_dir, 'w', zipfile.ZIP_DEFLATED, allowZip64=True
        )
        zipdir(self.models_dir, zipf, '.pkl')
        zipf.close()

        # save the validate dataframe to be used later to validate the accuracy of the models
        self.save_dataframe(validate_xy, "%s/rf_validation.pkl" % self.validation_dir)
