import gc
import json
import os
from collections import OrderedDict
from math import sqrt

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from lib.shared import save_dict_to_csv
from pandas.plotting import lag_plot
from sklearn.metrics import mean_squared_error

from shared import unpickle_file


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

        raise Exception("Could not load the model: %s" % id)

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

    def load_models(self, model_type, models_to_load=[]):
        """
        Load in the metamodels/generators
        """
        if not models_to_load:
            models_to_load = self.available_response_names

        self.rom_type = model_type
        print "Loading models %s" % models_to_load

        for response in models_to_load:
            print "Loading model for response: %s" % response

            self.models[response] = ETSModel(
                "output/%s/%s/models/%s.pkl" % (self.analysis_name, self.rom_type, response)
            )

        print "Finished loading models"
        print "The responses are:"
        for index, rs in enumerate(self.available_response_names):
            print "  %s: %s" % (index, rs)

        print "The covariates are:"
        for index, cv in enumerate(self.covariate_names):
            print "  %s: %s" % (index, cv)

    def yhat(self, response_name, data):
        """
        Return the estimate from the response_name

        :param response_name: Name of the model to evaluate
        :param data: pandas DataFrame
        :return:
        """
        if response_name not in self.available_response_names:
            raise Exception("Model does not have the response '%s'" % response_name)

        # verify that the covariates are defined in the dataframe, if not, then remove them before
        # calling the yhat method

        extra_columns_in_df = list(set(data.columns.values) - set(self.covariate_names))
        missing_data_in_df = list(set(self.covariate_names) - set(data.columns.values))

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
        data[self.covariate_types['float']] = data[self.covariate_types['float']].astype(float)
        data[self.covariate_types['int']] = data[self.covariate_types['int']].astype(int)

        # Order the data columns correctly -- this is a magic function.
        data = data[self.covariate_names]

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

            # Create heat maps
            # if save_figure:
            #     figure_filename = 'output/%s/%s/images/%s_%s.png' % (
            #         self.analysis_name,
            #         self.rom_type,
            #         file_prepend,
            #         response,
            #     )
            #
            #     # this is a bit cheezy right now, load in the file and process again
            #     df_heatmap = pd.read_csv(file_name, header=0)
            #
            #     # Remove the datetime column before converting the column headers to rounded floats
            #     df_heatmap = df_heatmap.drop(columns=['datetime'])
            #     df_heatmap.rename(columns=lambda x: round(float(x), 1), inplace=True)
            #
            #     plt.figure()
            #     f, ax = plt.subplots(figsize=(5, 12))
            #     sns.heatmap(df_heatmap)
            #     ax.set_title('%s - Mass Flow %s kg/s' % (response, unique_value))
            #     ax.set_xlabel('ETS Inlet Temperature')
            #     ax.set_ylabel('Hour of Year')
            #     plt.savefig(figure_filename)
            #     plt.close('all')

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
        if response_name not in self.available_response_names:
            raise Exception("Model does not have the response '%s'" % response_name)

        return self.models[response_name].model

    def validate_dataframe(self, df, image_save_dir):
        """
        Take the dataframe and perform various validations and create plots

        :param df:
        :return:
        """
        sns.set(color_codes=True)
        plt.rcParams['figure.figsize'] = [15, 10]
        sns.set(style="darkgrid")

        def date_formatter(x, pos):
            return pd.to_datetime(x)

        # Run the ROM for each of the response variables
        for response in self.available_response_names:
            df["Modeled %s" % response] = self.yhat(response, df)

        # create some plots, save them off
        for response in self.available_response_names:
            lmplot = sns.lmplot(
                x=response,
                y="Modeled %s" % response,
                data=df,
                ci=None,
                palette="muted",
                size=8,
                scatter_kws={"s": 50, "alpha": 1}
            )
            fig = lmplot.fig
            plt.title("Y-Y Plot for %s" % response)
            fig.savefig('%s/validation_%s.png' % (image_save_dir, response))
            fig.tight_layout()
            fig.clf()
            plt.clf()

        # create a subselection of the data, and run some other plots
        sub_data = {
            'Swing': df[df["DateTime"].between("2009-03-01 01:00", "2009-03-10 00:00")],
            'Summer': df[df["DateTime"].between("2009-07-01 01:00", "2009-07-10 00:00")],
            'Winter': df[df["DateTime"].between("2009-01-15 01:00", "2009-01-25 00:00")],
        }

        for season, season_df in sub_data.items():
            for response in self.available_response_names:
                selected_columns = ['DateTime', response, "Modeled %s" % response]
                melted_df = pd.melt(season_df[selected_columns],
                                    id_vars='DateTime',
                                    var_name='Variable',
                                    value_name='Value')
                melted_df['Dummy'] = 0

                fig, ax = plt.subplots()

                newplt = sns.tsplot(melted_df,
                                    time='DateTime',
                                    unit='Dummy',
                                    condition='Variable',
                                    value='Value',
                                    ax=ax)
                newplt.set_title("%s: RF vs EnergyPlus %s" % (season, response))
                ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(date_formatter))

                # put the labels at 45deg since they tend to be too long
                fig.autofmt_xdate()
                fig.savefig(
                    '%s/validation_timeseries_%s_%s.png' % (image_save_dir, season, response)
                )
                fig.clf()

        for response in self.available_response_names:
            plt.figure()
            lag_plot(df[response])
            plt.savefig('%s/%s_lag.png' % (image_save_dir, response))
            plt.title("Lag Plot for %s" % response)
            plt.clf()

        # calculate the RMSE and CVRSME
        errors = []
        for response in self.available_response_names:
            sum_of_error = (df[response] - df["Modeled %s" % response]).sum()
            sum_square_error = (
                    (df[response] - df["Modeled %s" % response]) ** 2
            ).sum()
            nmbe = 100 * (sum_of_error / ((len(df) - 1) * df[response].mean()))
            cvrmse = 100 * (sqrt(sum_square_error) / (
                    sqrt(len(df) - 1) * df[response].mean())
                            )
            rmse = sqrt(mean_squared_error(df[response], df["Modeled %s" % response]))

            errors.append(
                OrderedDict(
                    [
                        ('response', response),
                        ('rmse', rmse),
                        ('nmbe', nmbe),
                        ('cvrmse', cvrmse),
                    ]
                )
            )

        # save data to image dir, because that is the only directory that I know of right now
        save_dict_to_csv(errors, "%s/statistics.csv" % image_save_dir)

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

    @property
    def covariate_types(self):
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
        for cv in self.file[self.set_i]['covariates']:
            data_types[cv['type']].append(cv['name'])

        return data_types

    @property
    def covariate_names(self):
        """
        Returns a list of covariates. The order in the JSON file must be the order that is
        passed into the metamodel, otherwise the data will not make sense.

        :return: list
        """

        if self.set_i is None:
            raise Exception(
                "Attempting to access analysis without setting. Run analysis.set_analysis(<id>)"
            )

        return [cv['name'] for cv in self.file[self.set_i]['covariates']]

    @property
    def available_response_names(self):
        if self.set_i is None:
            raise Exception(
                "Attempting to access analysis without setting. Run analysis.set_analysis(<id>)"
            )

        return [cv['name'] for cv in self.file[self.set_i]['responses']]


if __name__ == "__main__":
    # test loading the analyses JSON
    a_file = Metamodels('../metamodels.json')

    if not a_file.set_analysis('dne'):
        print "Analysis not found"

    if a_file.set_analysis('3ff422c2-ca11-44db-b955-b39a47b011e7'):
        print "Found Analysis"
        print a_file.analysis['covariates']
        print a_file.covariate_names
        print a_file.available_response_names
