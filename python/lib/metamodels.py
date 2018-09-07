import gc
import json
import os
import re
import time
import multiprocessing  # noqa
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from shared import unpickle_file, apply_cyclic_transform


class ETSModel:
    def __init__(self, response_name, model_file, scaler_file=None):
        """
        Load the model from a pandas pickled dataframe

        :param path_to_models: String, String path to where the pickled models exist
        :param model: String or Int, Name of the resulting ensemble model to return
        :param season: String or Int, Season to analyze

        """
        self.response_name = response_name
        self.model_file = model_file
        self.scaler_file = scaler_file
        if os.path.exists(model_file) and os.path.isfile(model_file):
            gc.disable()
            self.model = unpickle_file(model_file)
            gc.enable()
        else:
            raise Exception("File not found, unable to load: %s" % model_file)

        if os.path.exists(scaler_file) and os.path.isfile(scaler_file):
            gc.disable()
            self.scalers = unpickle_file(scaler_file)
            gc.enable()
        else:
            self.scalers = None

    def yhat(self, data):
        """
        Pass in the data as an array of array. The format is dependent on the model, but it must be an
        array of values to predict.

        e.g. [[month, hour, dayofweek, t_outdoor, rh, inlet_temp]]

        :param data: array of data to estimate
        :return:
        """
        # Transform the feature data
        if self.scalers:
            data[data.columns] = self.scalers['features'].transform(data[data.columns])

        predictions = self.model.predict(data)

        # Inverse transform out the response data
        if self.scalers:
            predictions = self.scalers[self.response_name].inverse_transform(predictions)

        return predictions

    def __str__(self):
        return self.model_file


class Metamodels(object):
    """
    Parse the file that defines the ROMs that have been created.
    """

    def __init__(self, filename):
        self.filename = None
        self.file = None
        self.set_i = None
        self.load_file(filename)
        self.models = {}
        self.rom_type = None

    def load_file(self, filename):
        if not os.path.exists(filename):
            raise Exception("File does not exist: %s" % filename)

        self.filename = filename
        self.file = json.load(open(self.filename))

    def set_analysis(self, moniker):
        """
        Set the index of the analysis based on the ID or the name of the analysis.

        :param moniker: str, Analysis ID or Name
        :return: boolean
        """
        for idx, analysis in enumerate(self.file):
            if analysis['name'] == moniker:
                self.set_i = idx

                return True

        raise Exception("Could not load the model: %s" % moniker)

    @property
    def results_directory(self):
        """
        Return the analysis ID from the metamodels.json file that was passed in. This should only
        be used to get the data out of the downloaded results from OpenStudio Server.

        :return: str, ID
        """
        return self.file[self.set_i]['results_directory']

    @property
    def analysis_name(self):
        """
        Return the analysis name from the metamodels.json file that was passed in

        :return: str, name
        """
        return self.file[self.set_i]['name']

    @property
    def downsamples(self):
        """
        Return the downsamples list

        :return: list, downsamples
        """
        return self.file[self.set_i].get('downsamples', None)

    @property
    def algorithm_options(self):
        """
        Return the algorithm options from the JSON data

        :return: dict, algorithm options
        """

        def _remove_comments(data):
            """
            This method recursively goes through a dict and removes any '_comments' keys
            :param data:
            :return:
            """
            for k, v in data.items():
                if isinstance(v, dict):
                    data[k] = _remove_comments(v)

            if '_comments' in data.keys():
                del data['_comments']

            return data

        options = self.file[self.set_i].get('algorithm_options', None)
        # Remove all the _comments strings from the algorithm_options string
        return _remove_comments(options)

    @property
    def validation_id(self):
        """
        Return the validation id

        :return: str, name
        """
        return self.file[self.set_i]['validation_datapoint_id']

    def load_models(self, model_type, models_to_load=[], downsample=None):
        """
        Load in the metamodels/generators

        :param model_type: str, type of model (e.g. RandomForest, LinearModel, etc)
        :param models_to_load: list, name of responses to load
        :param downsample: float, percent of downsample for loading the correct model
        :return: dict, { model, response, load time, disk size]

        """
        self.rom_type = model_type

        if not models_to_load:
            models_to_load = self.available_response_names(self.rom_type)

        print "Loading models %s" % models_to_load

        metrics = {'response': [], 'model_type': [], 'downsample': [],
                   'load_time': [], 'disk_size': []}
        for response in models_to_load:
            print "Loading model for response: %s" % response

            start = time.time()
            if downsample:
                path = "output/%s_%s/%s/models/%s.pkl" % (
                    self.analysis_name, downsample, self.rom_type, response)
                scaler_path = "output/%s_%s/%s/models/scalers.pkl" % (
                    self.analysis_name, downsample, self.rom_type)
            else:
                path = "output/%s/%s/models/%s.pkl" % (self.analysis_name, self.rom_type, response)
                scaler_path = "output/%s/%s/models/scalers.pkl" % (
                    self.analysis_name, self.rom_type)

            self.models[response] = ETSModel(response, path, scaler_path)
            metrics['response'].append(response)
            metrics['model_type'].append(model_type)
            metrics['downsample'].append(downsample)
            metrics['load_time'].append(time.time() - start)
            metrics['disk_size'].append(os.path.getsize(path))

        print "Finished loading models"
        print "The responses are:"
        for index, rs in enumerate(self.available_response_names(self.rom_type)):
            print "  %s: %s" % (index, rs)

        print "The covariates are:"
        for index, cv in enumerate(self.covariate_names(self.rom_type)):
            print "  %s: %s" % (index, cv)

        return metrics

    def yhat(self, response_name, data):
        """
        Return the estimate from the response_name

        :param response_name: Name of the model to evaluate
        :param data: pandas DataFrame
        :return:
        """
        if response_name not in self.available_response_names(self.rom_type):
            raise Exception("Model does not have the response '%s'" % response_name)

        # verify that the covariates are defined in the dataframe, if not, then remove them before
        # calling the yhat method

        extra_columns_in_df = list(
            set(data.columns.values) - set(self.covariate_names(self.rom_type)))
        missing_data_in_df = list(
            set(self.covariate_names(self.rom_type)) - set(data.columns.values))

        if len(extra_columns_in_df) > 0:
            # print "The following columns are not needed in DataFrame"
            print extra_columns_in_df
            print "Removing unneeded column before evaluation"
            data = data.drop(columns=extra_columns_in_df)

        if len(missing_data_in_df) > 0:
            print "Error: The following columns are missing in the DataFrame"
            print missing_data_in_df
            raise Exception("Need to define %s in DataFrame for model" % missing_data_in_df)

        # typecast the columns before running the analysis
        data[self.covariate_types(self.rom_type)['float']] = data[
            self.covariate_types(self.rom_type)['float']
        ].astype(float)
        data[self.covariate_types(self.rom_type)['int']] = data[
            self.covariate_types(self.rom_type)['int']
        ].astype(int)

        # Order the data columns correctly -- this is a magic function.
        data = data[self.covariate_names(self.rom_type)]

        # transform cyclical columns
        for cv in self.covariates(self.rom_type):
            if cv.get('algorithm_options', None):
                if cv['algorithm_options'].get(self.rom_type, None):
                    if cv['algorithm_options'][self.rom_type].get('variable_type', None):
                        if cv['algorithm_options'][self.rom_type]['variable_type'] == 'cyclical':
                            print("Transforming covariate to be cyclical %s" % cv['name'])
                            data[cv['name']] = data.apply(
                                apply_cyclic_transform,
                                column_name=cv['name'],
                                category_count=cv['algorithm_options'][self.rom_type][
                                    'category_count'],
                                axis=1
                            )

        return self.models[response_name].yhat(data)

    def save_csv(self, data, csv_name):
        lookup_table_dir = 'output/%s/%s/lookup_tables/' % (
            self.analysis_name,
            self.rom_type
        )
        if not os.path.exists(lookup_table_dir):
            os.makedirs(lookup_table_dir)

        file_name = '%s/%s.csv' % (
            lookup_table_dir,
            csv_name)

        data.to_csv(file_name, index=False)

    def save_2d_csvs(self, data, first_dimension, file_prepend, save_figure=False):
        """
        Generate 2D (time, first) CSVs based on the model loaded and the two dimensions.

        The rows are the datetimes as defined in the data (dataframe)

        :param data: pandas dataframe
        :param first_dimension: str, the column heading variable
        :param prepend_file_id: str, special variable to prepend to the file name
        :return: None
        """

        # create the lookup table directory - probably want to make this a base class for all
        # python scripts that use the filestructure to store the data
        lookup_table_dir = 'output/%s/%s/lookup_tables/' % (
            self.analysis_name,
            self.rom_type
        )
        if not os.path.exists(lookup_table_dir):
            os.makedirs(lookup_table_dir)

        for response in self.loaded_models:
            print "Creating CSV for %s" % response

            # TODO: look into using DataFrame.pivot() to transform data
            file_name = '%s/%s_%s.csv' % (
                lookup_table_dir,
                file_prepend,
                response
            )

            # Save the data times in a new dataframe (will be in order)
            save_df = pd.DataFrame.from_dict({'datetime': data['datetime'].unique()})
            for unique_value in data[first_dimension].unique():
                new_df = data[data[first_dimension] == unique_value]
                save_df[unique_value] = new_df[response].values

            save_df.to_csv(file_name, index=False)

    def save_3d_csvs(self, data, first_dimension, second_dimension, second_dimension_short_name,
                     file_prepend, save_figure=False):
        """
        Generate 3D (time, first, second) CSVs based on the model loaded and the two dimensions.
        The second dimension becomes individual files.

        The rows are the datetimes as defined in the data (dataframe)

        :param data: pandas dataframe
        :param first_dimension: str, the column heading variable
        :param second_dimension: str, the values that will be reported in the table
        :param second_dimension_short_name: str, short display name for second variable (for filename)
        :param file_prepend: str, special variable to prepend to the file name
        :return: None
        """

        # create the lookup table directory - probably want to make this a base class for all
        # python scripts that use the filestructure to store the data
        lookup_table_dir = 'output/%s/%s/lookup_tables/' % (
            self.analysis_name,
            self.rom_type
        )
        if not os.path.exists(lookup_table_dir):
            os.makedirs(lookup_table_dir)

        for response in self.loaded_models:
            print "Creating CSV for %s" % response

            # TODO: look into using DataFrame.pivot() to transform data
            for unique_value in data[second_dimension].unique():
                file_name = '%s/%s_%s_%s_%.2f.csv' % (
                    lookup_table_dir,
                    file_prepend,
                    response,
                    second_dimension_short_name,
                    unique_value)
                lookup_df = data[data[second_dimension] == unique_value]

                # Save the data times in a new dataframe (will be in order)
                save_df = pd.DataFrame.from_dict({'datetime': lookup_df['datetime'].unique()})
                for unique_value_2 in data[first_dimension].unique():
                    new_df = lookup_df[lookup_df[first_dimension] == unique_value_2]
                    save_df[unique_value_2] = new_df[response].values

                save_df.to_csv(file_name, index=False)

                # Create heat maps
                if save_figure:
                    figure_filename = 'output/%s/%s/images/%s_%s_%s_%.2f.png' % (
                        self.analysis_name,
                        self.rom_type,
                        file_prepend,
                        response,
                        second_dimension_short_name,
                        unique_value)

                    # this is a bit cheezy right now, load in the file and process again
                    df_heatmap = pd.read_csv(file_name, header=0)

                    # Remove the datetime column before converting the column headers to rounded floats
                    df_heatmap = df_heatmap.drop(columns=['datetime'])
                    df_heatmap.rename(columns=lambda x: round(float(x), 1), inplace=True)

                    plt.figure()
                    f, ax = plt.subplots(figsize=(5, 12))
                    sns.heatmap(df_heatmap)
                    ax.set_title('%s - Mass Flow %s kg/s' % (response, unique_value))
                    ax.set_xlabel('ETS Inlet Temperature')
                    ax.set_ylabel('Hour of Year')
                    plt.savefig(figure_filename)
                    plt.close('all')

    def model(self, response_name):
        if response_name not in self.available_response_names(self.rom_type):
            raise Exception("Model does not have the response '%s'" % response_name)

        return self.models[response_name].model

    @property
    def loaded_models(self):
        return self.models.keys()

    @property
    def analysis(self):
        if self.set_i is None:
            raise Exception(
                "Attempting to access analysis without setting. Run analysis.set_analysis(<id>)"
            )

        return self.file[self.set_i]

    def covariates(self, model_type):
        if self.set_i is None:
            raise Exception(
                "Attempting to access analysis without setting. Run analysis.set_analysis(<id>)"
            )

        # only return the covariates that don't have ignore true for the type of model
        results = []
        for cv in self.file[self.set_i]['covariates']:
            if not cv.get('algorithm_options', {}).get(model_type, {}).get('ignore', False):
                results.append(cv)

        return results

    def covariate_types(self, model_type):
        if self.set_i is None:
            raise Exception(
                "Attempting to access analysis without setting. Run analysis.set_analysis(<id>)"
            )

        # group the datetypes by column
        data_types = {
            'float': [],
            'str': [],
            'int': []
        }
        for cv in self.covariates(model_type):
            data_types[cv['type']].append(cv['name'])

        return data_types

    def covariate_names(self, model_type):
        """
        Returns a list of covariates. The order in the JSON file must be the order that is
        passed into the metamodel, otherwise the data will not make sense.

        :return: list
        """

        if self.set_i is None:
            raise Exception(
                "Attempting to access analysis without setting. Run analysis.set_analysis(<id>)"
            )

        return [cv['name'] for cv in self.covariates(model_type)]

    def available_response_names(self, _model_type):
        if self.set_i is None:
            raise Exception(
                "Attempting to access analysis without setting. Run analysis.set_analysis(<id>)"
            )

        return [cv['name'] for cv in self.file[self.set_i]['responses']]

    @classmethod
    def resolve_algorithm_options(cls, algorithm_options):

        for k, v in algorithm_options.items():
            if isinstance(v, dict):
                algorithm_options[k] = Metamodels.resolve_algorithm_options(v)
            elif isinstance(v, basestring) and 'eval(' in v:
                # remove eval() from string in file and then call it
                string_value = re.search('eval\((.*)\)', v).groups()[0]
                algorithm_options[k] = eval(string_value)

        return algorithm_options
