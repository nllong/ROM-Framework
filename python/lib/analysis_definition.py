import json
import os

import numpy as np
import pandas as pd
from epw.epw_file import EpwFile


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
#     },
#     {
#       "name": "SomeOtherField",
#       "data_source": "values",
#       "values": [0.5, 0.75, 1.0]
#     },
#   ]
# }

class AnalysisDefinition:
    """
    Pass in a definition file and a weather file to generate distributions of models
    """
    def __init__(self, definition_file, weather_file):
        self.filename = None
        self.weather_file = None
        self.file = None
        self.analyses = []
        self.set_i = None
        self.lookup_prepend = None

        self.load_files(definition_file, weather_file)

    def load_files(self, definition_file, weather_file):
        if not os.path.exists(definition_file):
            raise Exception("File does not exist: %s" % definition_file)

        self.filename = definition_file
        self.weather_file = EpwFile(weather_file)
        self.file = json.load(open(self.filename))
        self.lookup_prepend = self.file['lookup_prepend']

        # print json.dumps(self.file, indent=2)

    def load_weather_file(self):
        """
        Load in the weather file and convert the field names to what is expected in the
        JSON file
        :return:
        """
        data = self.weather_file.as_dataframe()
        for variable in self.file['variables']:
            if variable['data_source'] == 'epw':
                data = data.rename(columns={ variable['data_source_field']: variable['name'] })

        return data

    def as_dataframe(self):
        """
        Return the dataframe with all the data needed to run the analysis defined in the
        json file

        :return: pandas dataframe
        """
        seed_df = self.load_weather_file()

        # Add in the static variables
        for variable in self.file['variables']:
            if variable['data_source'] == 'value':
                seed_df[variable['name']] = variable['value']

        # Now add in the combinitorials
        for variable in self.file['variables']:
            if variable['data_source'] == 'distribution':
                df_to_append = seed_df.copy(deep=True)
                values = np.linspace(
                    variable['distribution']['minimum'],
                    variable['distribution']['maximum'],
                    variable['distribution']['number_of_samples']
                ).tolist()

                for index, value in enumerate(values):
                    if index == 0:
                        # first time through add the variable to seed_df, no need to append
                        seed_df[variable['name']] = value
                    else:
                        df_to_append[variable['name']] = value
                        seed_df = pd.concat([seed_df, df_to_append])

            if variable['data_source'] == 'values':
                df_to_append = seed_df.copy(deep=True)

                for index, value in enumerate(variable['values']):
                    if index == 0:
                        # first time through add the variable to seed_df, no need to append
                        seed_df[variable['name']] = value
                    else:
                        df_to_append[variable['name']] = value
                        seed_df = pd.concat([seed_df, df_to_append])

        return seed_df

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
