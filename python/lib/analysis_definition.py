import json
import os

import numpy


# {
#   "variables": [
#     {
#       "name": "Month",
#       "data_source": "weather_file"
#     },
#     {
#       "name": "ETSInletTemperature",
#       "data_source": "distribution",
#       "distribution": {
#         "minimum": 15,
#         "maximum": 25,
#         "number_of_samples": 10
#       }
#     },
#     {
#       "name": "DistrictHeatingMassFlowRate",
#       "data_source": "value",
#       "value": 0.5
#     },
#     {
#       "name": "DistrictCoolingMassFlowRate",
#       "data_source": "distribution",
#       "distribution": {
#         "minimum": 0.02,
#         "maximum": 4,
#         "number_of_samples": 10
#       }
#     }
#   ]
# }

class AnalysisDefinition:
    def __init__(self, filename):
        self.filename = None
        self.file = None
        self.analyses = []
        self.set_i = None

        self.load_file(filename)

    def load_file(self, filename):
        if not os.path.exists(filename):
            raise Exception("File does not exist: %s" % filename)

        self.filename = filename
        self.file = json.load(open(self.filename))
        self.process_file()

    def process_file(self):
        """
        Process the file. Convert any distributions into selected values and save
        back into the dict
        """
        for variable in self.file['variables']:
            if variable['data_source'] == 'distribution':
                # assuming that the minimum, maximum, and number_of_samples are defined
                variable['values'] = numpy.linspace(
                    variable['distribution']['minimum'],
                    variable['distribution']['maximum'],
                    variable['distribution']['number_of_samples']
                ).tolist()

        print self.file

        # read in the static values and the generated values to generate the input for
        # the metamodels

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
