import time
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
from sklearn.model_selection import GridSearchCV

from model_generator_base import ModelGeneratorBase


class RandomForest(ModelGeneratorBase):
    def __init__(self, analysis_id, random_seed=None, **kwargs):
        super(RandomForest, self).__init__(analysis_id, random_seed, **kwargs)

    def evaluate(self, model, model_name, model_type, x_data, y_data, covariates, downsample, build_time, cv_time):
        """
        Evaluate the performance of the forest based on known x_data and y_data.

        :param model:
        :param model_name:
        :param model_type:
        :param x_data:
        :param y_data:
        :param covariates:
        :param downsample:
        :param build_time:
        :param cv_time:
        :return:
        """
        yhat = model.predict(x_data)

        # perform stats on all the data
        test_score = r2_score(y_data, yhat)
        errors = abs(yhat - y_data)
        spearman = spearmanr(y_data, yhat)
        pearson = pearsonr(y_data, yhat)

        slope, intercept, r_value, p_value, std_err = stats.linregress(y_data, yhat)

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
            ('n_estimators', model.n_estimators),
            ('max_depth', model.max_depth),
            ('max_features', model.max_features),
            ('min_samples_leaf', model.min_samples_leaf),
            ('min_samples_split', model.min_samples_leaf),
            ('time_to_build', build_time),
            ('time_to_cv', cv_time),
        ])

    def save_cv_results(self, cv_results, response, downsample, filename):
        """
        Save the cv_results to a CSV file. Data in the cv_results file looks like the following.

        {
            'param_kernel': masked_array(data=['poly', 'poly', 'rbf', 'rbf'],
                                         mask=[False False False False]...)
            'param_gamma': masked_array(data=[-- -- 0.1 0.2],
                                        mask=[True  True False False]...),
            'param_degree': masked_array(data=[2.0 3.0 - - --],
                                         mask=[False False  True  True]...),
            'split0_test_score': [0.8, 0.7, 0.8, 0.9],
            'split1_test_score': [0.82, 0.5, 0.7, 0.78],
            'mean_test_score': [0.81, 0.60, 0.75, 0.82],
            'std_test_score': [0.02, 0.01, 0.03, 0.03],
            'rank_test_score': [2, 4, 3, 1],
            'split0_train_score': [0.8, 0.9, 0.7],
            'split1_train_score': [0.82, 0.5, 0.7],
            'mean_train_score': [0.81, 0.7, 0.7],
            'std_train_score': [0.03, 0.03, 0.04],
            'mean_fit_time': [0.73, 0.63, 0.43, 0.49],
            'std_fit_time': [0.01, 0.02, 0.01, 0.01],
            'mean_score_time': [0.007, 0.06, 0.04, 0.04],
            'std_score_time': [0.001, 0.002, 0.003, 0.005],
            'params': [{'kernel': 'poly', 'degree': 2}, ...],
        }

        :param cv_results:
        :param filename:
        :return:
        """

        data = {}
        data['downsample'] = []
        for params in cv_results['params']:
            for param, value in params.items():
                if not data.get(param, None):
                    data[param] = []
                data[param].append(value)
                data['downsample'] = downsample
                data['response'] = response
        data['mean_train_score'] = cv_results['mean_train_score']
        data['mean_test_score'] = cv_results['mean_test_score']
        data['mean_fit_time'] = cv_results['mean_fit_time']
        data['mean_score_time'] = cv_results['mean_score_time']
        data['rank_test_score'] = cv_results['rank_test_score']

        df = pd.DataFrame.from_dict(data)
        df.to_csv(filename)

    def build(self, data_file, validation_id, covariates, data_types, responses, **kwargs):
        super(RandomForest, self).build(data_file, validation_id, covariates, data_types, responses, **kwargs)

        analysis_options = kwargs.get('algorithm_options', {})


        train_x, test_x, train_y, test_y, validate_xy = self.train_test_validate_split(
            self.dataset,
            covariates,
            responses,
            validation_id,
            downsample=self.downsample
        )

        # save the validate dataframe to be used later to validate the accuracy of the models
        self.save_dataframe(validate_xy, "%s/rf_validation.pkl" % self.validation_dir)

        for response in self.responses:
            print "Fitting random forest model for %s" % response

            start = time.time()
            base_fit_params = analysis_options.get('base_fit_params', {})
            rf = RandomForestRegressor(**base_fit_params)
            base_rf = rf.fit(train_x, train_y[response])
            build_time = time.time() - start

            # Evaluate the forest when building them
            self.model_results.append(
                self.evaluate(
                    base_rf, response, 'base', test_x, test_y[response], covariates,
                    self.downsample, build_time, 0
                )
            )

            if not kwargs.get('skip_cv', False):
                rf = RandomForestRegressor()

                kfold = 3
                print('Perfoming CV with k-fold equal to %s' % kfold)
                # grab the param grid from what was specified in the metamodels.json file
                param_grid = analysis_options.get('param_grid', None)
                total_candidates = 1
                for param, options in param_grid.items():
                    total_candidates = len(options) * total_candidates

                print('CV will result in %s candidates' % total_candidates)

                grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=kfold,
                                           n_jobs=-1, verbose=2)

                start = time.time()
                grid_search.fit(train_x, train_y[response])
                cv_time = time.time() - start

                best_rf = grid_search.best_estimator_

                pickle_file(best_rf, '%s/%s' % (self.models_dir, response))

                # save the cv results
                self.save_cv_results(
                    grid_search.cv_results_, response, self.downsample,
                    '%s/cv_results_%s.csv' % (self.base_dir, response)
                )

                self.model_results.append(
                    self.evaluate(
                        best_rf, response, 'best', test_x, test_y[response], covariates,
                        self.downsample, build_time, cv_time
                    )
                )
            else:
                pickle_file(base_rf, '%s/%s' % (self.models_dir, response))

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

