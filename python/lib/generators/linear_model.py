import zipfile

import pandas as pd
from lib.shared import pickle_file, save_dict_to_csv, zipdir
from scipy import stats
from collections import OrderedDict
from scipy.stats import spearmanr, pearsonr
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

from model_generator_base import ModelGeneratorBase


class LinearModel(ModelGeneratorBase):
    def __init__(self, analysis_id, random_seed=None):
        super(LinearModel, self).__init__(analysis_id, random_seed)

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

        return performance

    def build(self, data_file, covariates, data_types, responses):
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

        # TODO: remove hard coded simulation ID for validate_xy
        train_x, test_x, train_y, test_y, validate_xy = self.train_test_validate_split(
            dataset,
            covariates,
            responses,
            '112175a4-5b90-4ebb-a7c2-72123f87a6eb',
        )

        for response in self.responses:
            print "Fitting Linear Model for %s" % response
            trained_model = LinearRegression()
            trained_model.fit(train_x, train_y[response])
            pickle_file(trained_model, '%s/%s' % (self.models_dir, response))

            self.model_results.append(
                self.evaluate(trained_model, response, test_x, test_y[response], covariates)
            )

        if self.model_results:
            save_dict_to_csv(self.model_results, '%s/model_results.csv' % self.base_dir)

        # zip up the models
        zipf = zipfile.ZipFile('%s/models.zip' % self.models_dir, 'w', zipfile.ZIP_DEFLATED)
        zipdir(self.models_dir, zipf, '.pkl')
        zipf.close()

        # save the validate dataframe to be used later to validate the accuracy of the models
        self.save_dataframe(validate_xy, "%s/lm_validation.pkl" % self.validation_dir)
