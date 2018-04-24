# pyenv virtualenv 2.7.14 modelica-2.7.14
from shared import unpickle_file
import gc
import os

def is_int(value):
    try:
        int(value)
    except ValueError:
        return False
    return True


class ETSModel:
    def __init__(self, model_file):
        """
        Load the model from a pandas pickled dataframe

        :param path_to_models: String, String path to where the pickled models exist
        :param model: String or Int, Name of the resulting ensemble model to return
        :param season: String or Int, Season to analyze

        """
        # TODO: Check if the file exists
        self.model_file = model_file
        if os.path.isfile(model_file):
            gc.disable()
            self.model = unpickle_file(model_file)
            gc.enable()
        else:
            raise Exception("File not found, unable to load: %s" % model_file)

    def yhat(self, data):
        """
        Pass in the data as an array of array. The format is dependent on the model, but it must be an
        array of values to predict.

        e.g. [[month, hour, dayofweek, t_outdoor, rh, inlet_temp]]

        :param data: array of data to estimate
        :return:
        """
        predictions = self.model.predict(data)
        return predictions

    def __str__(self):
        return self.model_file
