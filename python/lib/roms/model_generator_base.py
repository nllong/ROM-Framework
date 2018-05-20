import os
import time

import numpy as np


class ModelGeneratorBase(object):
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
