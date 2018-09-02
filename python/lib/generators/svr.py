import time
import zipfile

import pandas as pd
from lib.shared import save_dict_to_csv, zipdir
from sklearn.svm import SVR as SKL_SVR

from model_generator_base import ModelGeneratorBase


class SVR(ModelGeneratorBase):
    def __init__(self, analysis_id, random_seed=None, **kwargs):
        super(SVR, self).__init__(analysis_id, random_seed, **kwargs)

    def evaluate(self, model, model_name, model_type, x_data, y_data, downsample,
                 build_time, cv_time, covariates=None):
        """
        Evaluate the performance of the forest based on known x_data and y_data.
        """
        yhat, performance = super(SVR, self).evaluate(
            model, model_name, model_type, x_data, y_data, downsample,
            build_time, cv_time, covariates
        )
        return performance

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
        super(SVR, self).build(data_file, validation_id, covariates, data_types, responses,
                               **kwargs)

        analysis_options = kwargs.get('algorithm_options', {})

        train_x, test_x, train_y, test_y, validate_xy = self.train_test_validate_split(
            self.dataset,
            covariates,
            responses,
            validation_id,
            downsample=self.downsample, scale=True
        )

        # from sklearn.preprocessing import RobustScaler
        #  scaler = RobustScaler()
        #  X = scaler.fit_transfrom(X)

        # from sklearn.preprocessing import MinMaxScaler
        # scaling = MinMaxScaler(feature_range=(-1, 1)).fit(X_train)
        # X_train = scaling.transform(X_train)
        # X_test = scaling.transform(X_test)

        # save the validate dataframe to be used later to validate the accuracy of the models
        self.save_dataframe(validate_xy, "%s/rf_validation.pkl" % self.validation_dir)

        for response in self.responses:
            print "Fitting %s model for %s" % (self.__class__.__name__, response)

            start = time.time()
            base_fit_params = analysis_options.get('base_fit_params', {})
            base_fit_params['kernel'] = 'rbf'
            base_fit_params['C'] = 1000
            base_fit_params['gamma'] = 0.1
            rf = SKL_SVR(**base_fit_params)
            base_rf = rf.fit(train_x, train_y[response])
            build_time = time.time() - start

            # Evaluate with the building them
            self.model_results.append(
                self.evaluate(
                    base_rf, response, 'base', test_x, test_y[response], covariates,
                    self.downsample, build_time, 0
                )
            )

            # if not kwargs.get('skip_cv', False):
            #     rf = SKL_SVR()
            #
            #     kfold = 3
            #     print('Perfoming CV with k-fold equal to %s' % kfold)
            #     # grab the param grid from what was specified in the metamodels.json file
            #     param_grid = analysis_options.get('param_grid', {})
            #     total_candidates = 1
            #     for param, options in param_grid.items():
            #         total_candidates = len(options) * total_candidates
            #
            #     print('CV will result in %s candidates' % total_candidates)
            #
            #     grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=kfold,
            #                                n_jobs=-1, verbose=2, refit=True)
            #
            #     start = time.time()
            #     grid_search.fit(train_x, train_y[response])
            #     cv_time = time.time() - start
            #
            #     # This should work, but the size of the model is really large after, so
            #     # trying to recreate the best_rf to save space.
            #     # best_rf = grid_search.best_estimator_
            #
            #     print('The best params were %s' % grid_search.best_params_)
            #
            #     # rebuild only the best rf, and save the results
            #     rf = RandomForestRegressor(**grid_search.best_params_)
            #     best_rf = rf.fit(train_x, train_y[response])
            #
            #     pickle_file(best_rf, '%s/%s' % (self.models_dir, response))
            #
            #     # save the cv results
            #     self.save_cv_results(
            #         grid_search.cv_results_, response, self.downsample,
            #         '%s/cv_results_%s.csv' % (self.base_dir, response)
            #     )
            #
            #     self.model_results.append(
            #         self.evaluate(
            #             best_rf, response, 'best', test_x, test_y[response], covariates,
            #             self.downsample, build_time, cv_time
            #         )
            #     )
            # else:
            #     pickle_file(base_rf, '%s/%s' % (self.models_dir, response))

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
