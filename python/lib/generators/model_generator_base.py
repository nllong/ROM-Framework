import fnmatch
import math
import os
import shutil
import time
from collections import OrderedDict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from scipy import stats
from scipy.stats import spearmanr, pearsonr
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


class ModelGeneratorBase(object):

    def __init__(self, analysis_id, random_seed=None, **kwargs):
        """
        Base class for generating ROMs

        :param analysis_id: string, identifier of the model to build
        :param random_seed: int, random seed to use
        :param kwargs:
            See below

        :Keyword Arguments:
            * *downsample* (``double``) -- Fraction to downsample the dataframe. If this exists
              then the data will be downsampled, and the results will be stored in a directory with
              this value appended.
        """
        self.analysis_id = analysis_id
        self.random_seed = random_seed if random_seed else np.random.seed(time.time())
        self.model_results = []
        self.model_type = self.__class__.__name__
        self.dataset = None
        self.downsample = kwargs.get('downsample', None)

        print("initializing %s" % self.model_type)

        # Initialize the directories where results are to be stored.
        if self.downsample:
            self.base_dir = 'output/%s_%s/%s' % (self.analysis_id, self.downsample, self.model_type)
        else:
            self.base_dir = 'output/%s/%s' % (self.analysis_id, self.model_type)
        self.images_dir = '%s/images' % self.base_dir
        self.models_dir = '%s/models' % self.base_dir
        if self.downsample:
            self.validation_dir = 'output/%s_%s/ValidationData' % (
                self.analysis_id, self.downsample)
        else:
            self.validation_dir = 'output/%s/ValidationData' % self.analysis_id
        self.data_dir = '%s/data' % self.base_dir

        # Remove some directories if they exist
        for dir in ['images_dir', 'models_dir', 'data_dir']:
            if os.path.exists(getattr(self, dir)):
                # print("removing the directory %s" % dir)
                shutil.rmtree(getattr(self, dir))

        # create directory if not exist for each of the above
        for dir in ['base_dir', 'images_dir', 'models_dir', 'data_dir', 'validation_dir']:
            if not os.path.exists(getattr(self, dir)):
                os.makedirs(getattr(self, dir))

        for root, dirnames, filenames in os.walk(self.base_dir):
            for filename in fnmatch.filter(filenames, 'cv_results_*.csv'):
                os.remove('%s/%s' % (self.base_dir, filename))

            for filename in fnmatch.filter(filenames, 'model_results.csv'):
                os.remove('%s/%s' % (self.base_dir, filename))

    def save_dataframe(self, dataframe, path):
        dataframe.to_pickle(path)

    def read_dataframe(self, path):
        return pd.read_pickle(path)

    def evaluate(self, model, model_name, model_moniker, x_data, y_data, downsample,
                 build_time, cv_time, covariates=None, scaler=None):
        """
        Generic base function to evaluate the performance of the models.

        :param model:
        :param model_name:
        :param x_data:
        :param y_data:
        :param downsample:
        :param build_time:
        :return: Ordered dict
        """

        yhat = model.predict(x_data)

        if scaler:
            yhat = scaler[model_name].inverse_transform(yhat)
            y_data = scaler[model_name].inverse_transform(y_data)

        errors = abs(yhat - y_data)
        spearman = spearmanr(y_data, yhat)
        pearson = pearsonr(y_data, yhat)

        slope, intercept, r_value, _p_value, _std_err = stats.linregress(y_data, yhat)

        self.yy_plots(y_data, yhat, model_name)

        return yhat, OrderedDict([
            ('name', model_name),
            ('model_type', model_moniker),
            ('downsample', downsample),
            ('slope', slope),
            ('intercept', intercept),
            ('mae', np.mean(errors)),
            ('r_value', r_value),
            ('r_squared', r_value ** 2),
            ('spearman', spearman[0]),
            ('pearson', pearson[0]),
            ('time_to_build', build_time),
            ('time_to_cv', cv_time),
        ])

    def build(self, data_file, metamodel, **kwargs):
        self.dataset = pd.read_csv(data_file)

        # print list(dataset.columns.values)
        if 'DistrictCoolingOutletTemperature' in list(self.dataset.columns.values):
            self.dataset = self.dataset.drop('DistrictCoolingOutletTemperature', 1)
        # update some of the column names so they make sense to this model

        self.dataset = self.dataset.rename(columns={
            'DistrictHeatingOutletTemperature': 'ETSInletTemperature',
            'DistrictHeatingInletTemperature': 'ETSHeatingOutletTemperature',
            'DistrictCoolingInletTemperature': 'ETSCoolingOutletTemperature',
        })

        # type cast the columns - this is probably not needed.
        data_types = metamodel.covariate_types(self.model_type)
        self.dataset[data_types['float']] = self.dataset[data_types['float']].astype(float)
        self.dataset[data_types['int']] = self.dataset[data_types['int']].astype(int)

    def apply_cyclic_transform(self, row, column_name, category_count):
        return math.sin(2 * math.pi * row[column_name] / category_count)

    def train_test_validate_split(self, dataset, metamodel, downsample=None, scale=False):
        """
        Use the built in method to generate the train and test data. This adds an additional
        set of data for validation. This vaildation dataset is a unique ID that is pulled out
        of the dataset before the test_train method is called.

        # :param dataset: dataframe, data to process
        # :param covariates: list, dict of covariates and information
        # :param responses: list, of responses to keep in the dataset
        # :param validation_id: str, unique ID of model to extract
        :param kwargs: downsample - fraction of dataframe to keep (after validation data extraction)
        :return: dataframes, dataframe: 1) dataset with removed validation data, 2) validation data
        """
        print "Initial dataset size is %s" % len(dataset)
        if metamodel.validation_id and metamodel.validation_id in dataset['_id'].unique():
            print('Extracting validation dataset and converting to date time')
            validate_xy = dataset[dataset['_id'] == metamodel.validation_id]

            # Covert the validation dataset datetime to actual datetime objects
            # validate_xy['DateTime'] = pd.to_datetime(dataset['DateTime'])
            #
            # Constrain to minute precision to make this method much faster
            validate_xy['DateTime'] = validate_xy['DateTime'].astype('datetime64[m]')

            dataset = dataset[dataset['_id'] != metamodel.validation_id]
        else:
            raise Exception(
                "Validation id does not exist in dataframe. ID was %s" % metamodel.validation_id)

        if downsample:
            num_rows = int(len(dataset.index.values) * downsample)
            print("Downsampling dataframe by %s to %s rows" % (downsample, num_rows))
            dataset = dataset.sample(n=num_rows)

        for cv in metamodel.covariates(self.model_type):
            if cv.get('algorithm_options', None):
                if cv['algorithm_options'].get(self.model_type, None):
                    if cv['algorithm_options'][self.model_type].get('variable_type', None):
                        if cv['algorithm_options'][self.model_type]['variable_type'] == 'cyclical':
                            print("Transforming covariate to be cyclical %s" % cv['name'])
                            dataset[cv['name']] = dataset.apply(
                                self.apply_cyclic_transform,
                                column_name=cv['name'],
                                category_count=cv['algorithm_options'][self.model_type][
                                    'category_count'],
                                axis=1
                            )

        train_x, test_x, train_y, test_y = train_test_split(
            dataset[metamodel.covariate_names(self.model_type)],
            dataset[metamodel.available_response_names(self.model_type)],
            train_size=0.7,
            test_size=0.3,
            random_state=self.random_seed
        )

        # If scaling, then fit the scaler on the training data, then use the trained data
        # scalar to scale the test data.
        if scale:
            scalers = {}
            scalers['features'] = StandardScaler()
            train_x[train_x.columns] = scalers['features'].fit_transform(train_x[train_x.columns])
            test_x[test_x.columns] = scalers['features'].transform(test_x[test_x.columns])

            for response in metamodel.available_response_names(self.model_type):
                scalers[response] = StandardScaler()
                train_y[response] = scalers[response].fit_transform(
                    train_y[response].values.reshape(-1, 1)
                )
                test_y[response] = scalers[response].transform(
                    test_y[response].values.reshape(-1, 1)
                )
        else:
            scalers = None

        print "Dataset size is %s" % len(dataset)
        print "Training dataset size is %s" % len(train_x)
        print "Validation dataset size is %s" % len(validate_xy)

        return train_x, test_x, train_y, test_y, validate_xy, scalers

    def yy_plots(self, y_data, yhat, model_name):
        """
        Plot the yy-plots

        :param y_data:
        :param yhat:
        :param model_name:
        :return:
        """
        # This need to be updated with the creating a figure with a size
        sns.set(color_codes=True)

        # find the items that are zero / zero across y and yhat and remove to look at
        # plots and other statistics
        clean_data = zip(y_data, yhat)
        clean_data = [x for x in clean_data if x != (0, 0)]
        y_data = np.asarray([y[0] for y in clean_data])
        yhat = np.asarray([y[1] for y in clean_data])

        # convert data to dataframe
        data = pd.DataFrame.from_dict({'Y': y_data, 'Yhat': yhat})

        with plt.rc_context(dict(sns.axes_style("whitegrid"))):
            fig = plt.figure(figsize=(6, 6), dpi=100)
            sns.regplot(
                x='Y',
                y='Yhat',
                data=data,
                ci=None,
                scatter_kws={"s": 50, "alpha": 1}
            )
            # plt.title("Training Set: Y-Y Plot for %s" % model_name)
            plt.tight_layout()
            plt.savefig('%s/fig_yy_%s.png' % (self.images_dir, model_name))
            fig.clf()
            plt.clf()

        # Hex plots for YY data
        sns.set(style="ticks")
        newplt = sns.jointplot(
            data['Y'], data['Yhat'], kind="hex"
        )
        # plt.subplots_adjust(top=0.9)
        # newplt.fig.suptitle("Training Set: Y-Y Plot for %s" % model_name)
        # plt.title("Training Set: Y-Y Plot for %s" % model_name)
        newplt.savefig('%s/fig_yy_hexplot_%s.png' % (self.images_dir, model_name))
        plt.clf()

    def anova_plots(self, y_data, yhat, model_name):
        residuals = y_data - yhat
        # figsize = width, height
        fig = plt.figure(figsize=(8, 4), dpi=100)

        ax1 = fig.add_subplot(1, 2, 1)
        ax1.plot(yhat, residuals, 'o')
        plt.axhline(y=0, color='grey', linestyle='dashed')
        ax1.set_xlabel('Fitted values')
        ax1.set_ylabel('Residuals')
        ax1.set_title('Residuals vs Fitted')

        ax2 = fig.add_subplot(1, 2, 2)
        sm.qqplot(residuals, line='s', ax=ax2)
        ax2.set_title('Normal Q-Q')

        plt.tight_layout()
        fig.savefig('%s/fig_anova_%s.png' % (self.images_dir, model_name))
        fig.clf()
        plt.clf()
