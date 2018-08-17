import os
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import pearsonr
from sklearn.model_selection import train_test_split


class ModelGeneratorBase(object):
    """
    Base class for generating ROMs
    """

    def __init__(self, analysis_id, random_seed=None):
        self.analysis_id = analysis_id
        self.random_seed = random_seed if random_seed else np.random.seed(time.time())
        self.model_results = []
        self.model_type = self.__class__.__name__

        # Initiliaze responses and covariates
        self.responses = []
        self.covariates = []

        print "initializing %s" % self.model_type

        # Initialize the directories where results are to be stored.
        self.base_dir = 'output/%s/%s' % (self.analysis_id, self.model_type)
        self.images_dir = '%s/images' % self.base_dir
        self.models_dir = '%s/models' % self.base_dir
        self.validation_dir = 'output/%s/ValidationData' % self.analysis_id

        # create directory if not exist for each of the above
        for dir in ['base_dir', 'images_dir', 'models_dir', 'validation_dir']:
            if not os.path.exists(getattr(self, dir)):
                os.makedirs(getattr(self, dir))

    def save_dataframe(self, dataframe, path):
        dataframe.to_pickle(path)

    def read_dataframe(self, path):
        return pd.read_pickle(path)

    def train_test_validate_split(self, dataset, covariates, responses, id_and_value, **kwargs):
        """
        Use the built in method to generate the train and test data. This adds an additional
        set of data for validation. This vaildation dataset is a unique ID that is pulled out
        of the dataset before the test_train method is called.
        """
        print "Initial dataset size is %s" % len(dataset)
        validate_xy = pd.DataFrame()
        if id_and_value:
            validate_xy = dataset[dataset['_id'] == id_and_value]
            # Covert the validation dataset datetime to actual datetime objects
            validate_xy['DateTime'] = pd.to_datetime(dataset['DateTime'])

            dataset = dataset[dataset['_id'] != id_and_value]

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
        plt.title("Training Set: Y-Y Plot for %s" % model_name)
        fig.tight_layout()
        fig.savefig('%s/test_%s.png' % (self.images_dir, model_name))
        fig.clf()
        plt.clf()
