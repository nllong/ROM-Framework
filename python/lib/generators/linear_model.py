import time
import zipfile
from collections import OrderedDict

import numpy as np
from lib.shared import pickle_file, save_dict_to_csv, zipdir
from scipy import stats
from scipy.stats import spearmanr, pearsonr
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

from model_generator_base import ModelGeneratorBase


class LinearModel(ModelGeneratorBase):
    def __init__(self, analysis_id, random_seed=None, **kwargs):
        super(LinearModel, self).__init__(analysis_id, random_seed, **kwargs)

    def evaluate(self, model, model_name, model_type, x_data, y_data, downsample, build_time):
        """
        Evaluate the performance of the forest based on known x_data and y_data.

        :param model:
        :param model_name:
        :param x_data:
        :param y_data:
        :param downsample:
        :param build_time:
        :return:
        """
        yhat = model.predict(x_data)

        test_score = r2_score(y_data, yhat)
        errors = abs(yhat - y_data)
        spearman = spearmanr(y_data, yhat)
        pearson = pearsonr(y_data, yhat)

        slope, intercept, r_value, p_value, std_err = stats.linregress(y_data, yhat)

        self.yy_plots(y_data, yhat, model_name)
        self.anova_plots(y_data, yhat, model_name)

        return OrderedDict([
            ('name', model_name),
            ('model_type', model_type),
            ('downsample', downsample),
            ('slope', slope),
            ('intercept', intercept),
            ('mae', np.mean(errors)),
            ('r_value', r_value),
            ('p_value', p_value),
            ('std_err', std_err),
            ('r_squared', r_value ** 2),
            ('rf_r_squared', test_score),
            ('spearman', spearman[0]),
            ('pearson', pearson[0]),
            ('time_to_build', build_time),
            ('time_to_cv', 0),
        ])

    def build(self, data_file, validation_id, covariates, data_types, responses, **kwargs):
        super(LinearModel, self).build(
            data_file, validation_id, covariates, data_types, responses, **kwargs
        )

        # analysis_options = kwargs.get('algorithm_options', {})

        train_x, test_x, train_y, test_y, validate_xy = self.train_test_validate_split(
            self.dataset,
            covariates,
            responses,
            validation_id,
            downsample=self.downsample
        )

        # save the validate dataframe to be used later to validate the accuracy of the models
        self.save_dataframe(validate_xy, "%s/lm_validation.pkl" % self.validation_dir)

        for response in self.responses:
            print "Fitting Linear Model for %s" % response
            trained_model = LinearRegression()

            start = time.time()
            trained_model.fit(train_x, train_y[response])
            build_time = time.time() - start

            pickle_file(trained_model, '%s/%s' % (self.models_dir, response))

            self.model_results.append(
                self.evaluate(
                    trained_model, response, 'best', test_x, test_y[response], self.downsample,
                    build_time
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

        # save the data that was used in the models for future processing and analysis
        self.dataset.to_csv('%s/data.csv' % self.data_dir)
