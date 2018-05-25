import os
import time

import numpy as np
import seaborn as sns
from scipy.stats import spearmanr, pearsonr
import matplotlib.pyplot as plt
import numpy as np


class ModelGeneratorBase(object):
    """
    Base class for generating ROMs
    """
    def __init__(self, analysis_id, random_seed=None):
        self.analysis_id = analysis_id
        self.random_seed = random_seed if random_seed else np.random.seed(time.time())
        self.model_results = []
        self.model_type = self.__class__.__name__

        print "initializing %s" % self.model_type

        # Initialize the directories where results are to be stored.
        self.base_dir = 'output/%s/%s' % (self.analysis_id, self.model_type)
        self.images_dir = '%s/images' % self.base_dir
        self.models_dir = '%s/models' % self.base_dir

        # create directory if not exist for each of the above
        for dir in ['base_dir', 'images_dir', 'models_dir']:
            if not os.path.exists(getattr(self, dir)):
                os.makedirs(getattr(self, dir))

    def yy_plots(self, y_data, yhat, model_name):
        """
        Plot the yy-plots

        :param y_data:
        :param yhat:
        :param model_name:
        :return:
        """
        # find the items that are zero / zero across y and yhat and remove to look at
        # plots and other statistics
        clean_data = zip(y_data, yhat)
        clean_data = [x for x in clean_data if x != (0, 0)]
        y_data = np.asarray([y[0] for y in clean_data])
        yhat = np.asarray([y[1] for y in clean_data])

        plt.scatter(y_data, yhat)
        plt.subplots_adjust(left=0.125)
        plt.xlabel('y')
        plt.ylabel('yhat')
        plt.savefig('%s/%s.png' % (self.images_dir, model_name))
        plt.clf()

        sns.jointplot(y_data, yhat, kind='hex', stat_func=pearsonr)
        plt.xlabel('y')
        plt.ylabel('yhat')
        plt.savefig('%s/%s_hex.png' % (self.images_dir, model_name))
        plt.clf()
