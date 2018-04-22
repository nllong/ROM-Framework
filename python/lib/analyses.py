import json
import os

from ets_model import ETSModel


class Analyses:
    """
    Parse the file that defines the ROMs that have been created.

    TODO: Rename this to ROMs or metamodels or something else
    """

    def __init__(self, filename):
        self.filename = None
        self.file = None
        self.set_i = None
        self.load_file(filename)
        self.models = {}

    def load_file(self, filename):
        if not os.path.exists(filename):
            raise Exception("File does not exist: %s" % filename)

        self.filename = filename
        self.file = json.load(open(self.filename))

    def set_analysis(self, id):
        """
        # TODO: need to pass in which models should be loaded, if any. Perhaps, make an explicit
        # call to load the models

        :param id: str, Analysis ID
        :return: boolean
        """
        for idx, analysis in enumerate(self.file):
            if analysis['id'] == id:
                self.set_i = idx
                self.load_models()

                print "The responses are:"
                for index, rs in enumerate(self.response_names):
                    print "  %s: %s" % (index, rs)

                print "The covariates are:"
                for index, cv in enumerate(self.covariate_names):
                    print "  %s: %s" % (index, cv)

                return True

        raise Exception("Could not load the model: %s" % id)

    def load_models(self):
        """
        Load in the metamodels/roms
        """
        print self.file[self.set_i]
        print "Starting to load models, there are a total of %s models" % len(
            self.file[self.set_i]['responses'])

        for response in self.file[self.set_i]['responses']:
            print "Loading model for response: %s" % response['name']

            self.models[response['name']] = ETSModel(
                "output/%s/models/%s.pkl" % (self.file[self.set_i]['id'], response['name']))

        print "Finished loading models"

    def yhat(self, response_name, data):
        """
        Return the estimate from the response_name

        :param response_name: Name of the model to evaluate
        :param data: pandas DataFrame
        :return:
        """
        if response_name not in self.response_names:
            raise Exception("Model does not have the response '%s'" % response_name)

        # verify that the covariates are defined in the dataframe, if not, then remove them before
        # calling the yhat method

        extra_columns_in_df = list(set(data.columns.values) - set(self.covariate_names))
        missing_data_in_df = list(set(self.covariate_names) - set(data.columns.values))

        if len(extra_columns_in_df) > 0:
            print "The following columns are not needed in DataFrame"
            print extra_columns_in_df
            print "Removing unneeded column before evaluation"
            data = data.drop(columns=extra_columns_in_df)

        if len(missing_data_in_df) > 0:
            print "Error: The following columns are missing in the DataFrame"
            print missing_data_in_df
            raise Exception("Need to define %s in DataFrame for model" % missing_data_in_df)

        return self.models[response_name].yhat(data)

    def model(self, response_name):
        if response_name not in self.response_names:
            raise Exception("Model does not have the response '%s'" % response_name)

        return self.models[response_name].model

    @property
    def analysis(self):
        if self.set_i is None:
            raise Exception(
                "Attempting to access analysis without setting. Run analysis.set_analysis(<id>)"
            )

        return self.file[self.set_i]

    @property
    def covariate_names(self):
        if self.set_i is None:
            raise Exception(
                "Attempting to access analysis without setting. Run analysis.set_analysis(<id>)"
            )

        return [cv['name'] for cv in self.file[self.set_i]['covariates']]

    @property
    def response_names(self):
        if self.set_i is None:
            raise Exception(
                "Attempting to access analysis without setting. Run analysis.set_analysis(<id>)"
            )

        return [cv['name'] for cv in self.file[self.set_i]['responses']]


if __name__ == "__main__":
    # test loading the analyses JSON
    a_file = Analyses('../analyses.json')

    if not a_file.set_analysis('dne'):
        print "Analysis not found"

    if a_file.set_analysis('3ff422c2-ca11-44db-b955-b39a47b011e7'):
        print "Found Analysis"
        print a_file.analysis['covariates']
        print a_file.covariate_names
        print a_file.response_names
