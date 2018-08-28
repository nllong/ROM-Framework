import fnmatch
import os
import shutil
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.model_selection import train_test_split


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

        # Initiliaze responses and covariates
        self.responses = []
        self.covariates = []

        print("initializing %s" % self.model_type)

        # Initialize the directories where results are to be stored.
        if self.downsample:
            self.base_dir = 'output/%s_%s/%s' % (self.analysis_id, self.downsample, self.model_type)
        else:
            self.base_dir = 'output/%s/%s' % (self.analysis_id, self.model_type)
        self.images_dir = '%s/images' % self.base_dir
        self.models_dir = '%s/models' % self.base_dir
        if self.downsample:
            self.validation_dir = 'output/%s_%s/ValidationData' % (self.analysis_id, self.downsample)
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

    def build(self, data_file, validation_id, covariates, data_types, responses, **kwargs):
        self.responses = responses
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
        self.dataset[data_types['float']] = self.dataset[data_types['float']].astype(float)
        self.dataset[data_types['int']] = self.dataset[data_types['int']].astype(int)

    def train_test_validate_split(self, dataset, covariates, responses, id_and_value,
                                  downsample=None):
        """
        Use the built in method to generate the train and test data. This adds an additional
        set of data for validation. This vaildation dataset is a unique ID that is pulled out
        of the dataset before the test_train method is called.

        :param dataset: dataframe, data to process
        :param covariates: list, of covariates to keep in the dataset
        :param responses: list, of responses to keep in the dataset
        :param id_and_value: str, unique ID of model to extract
        :param kwargs: downsample - fraction of dataframe to keep (after validation data extraction)
        :return: dataframes, dataframe: 1) dataset with removed validation data, 2) validation data
        """
        print "Initial dataset size is %s" % len(dataset)
        if id_and_value and id_and_value in dataset['_id'].unique():
            print('Extracting validation dataset and converting to date time')
            validate_xy = dataset[dataset['_id'] == id_and_value]

            # Covert the validation dataset datetime to actual datetime objects
            # validate_xy['DateTime'] = pd.to_datetime(dataset['DateTime'])
            #
            # Constrain to minute precision to make this method much faster
            validate_xy['DateTime'] = validate_xy['DateTime'].astype('datetime64[m]')

            dataset = dataset[dataset['_id'] != id_and_value]
        else:
            raise Exception("Validation id does not exist in dataframe. ID was %s" % id_and_value)

        if downsample:
            num_rows = int(len(dataset.index.values) * downsample)
            print("Downsampling dataframe by %s to %s rows" % (downsample, num_rows))
            dataset = dataset.sample(n=num_rows)

        train_x, test_x, train_y, test_y = train_test_split(
            dataset[covariates],
            dataset[responses],
            train_size=0.7,
            test_size=0.3,
            random_state=self.random_seed
        )

        print "Dataset size is %s" % len(dataset)
        print "Training dataset size is %s" % len(train_x)
        print "Validation dataset size is %s" % len(validate_xy)

        return train_x, test_x, train_y, test_y, validate_xy

    def yy_plots(self, y_data, yhat, model_name):
        """
        Plot the yy-plots

        :param y_data:
        :param yhat:
        :param model_name:
        :return:
        """
        sns.set(color_codes=True)
        plt.rcParams['figure.figsize'] = [15, 10]
        sns.set(style="darkgrid")

        # find the items that are zero / zero across y and yhat and remove to look at
        # plots and other statistics
        clean_data = zip(y_data, yhat)
        clean_data = [x for x in clean_data if x != (0, 0)]
        y_data = np.asarray([y[0] for y in clean_data])
        yhat = np.asarray([y[1] for y in clean_data])

        # convert data to dataframe
        data = pd.DataFrame.from_dict({'Y': y_data, 'Yhat': yhat})
        lmplot = sns.lmplot(
            x='Y',
            y='Yhat',
            data=data,
            ci=None,
            palette="muted",
            height=8,
            scatter_kws={"s": 50, "alpha": 1}
        )
        fig = lmplot.fig
        plt.title("Training Set: Y-Y Plot for %s" % (model_name))
        fig.tight_layout()
        fig.savefig('%s/test_%s.png' % (self.images_dir, model_name))
        fig.clf()
        plt.clf()
