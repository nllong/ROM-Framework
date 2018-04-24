import cPickle
import csv
import gzip
import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def save_2d_csvs(data, rom, analysis_id, first_dimension, second_dimension, prepend_file_id,
                 save_figure=False):
    """
    The rows are the datetimes as defined in the data (dataframe)

    :param data: pandas dataframe
    :param rom: Metamodel Object, the ROM that was run to create the dataframe
    :param analysis_id: str, the analysis_id, will be used to save the file in the correct location
    :param first_dimension: str, the column heading variable
    :param second_dimension: str, the values that will be reported in the table
    :param prepend_file_id: str, special variable to prepend to the file name
    :return: None
    """
    for rs in rom.loaded_models:
        print "Creating CSV for %s" % rs

        # TODO: look into using DataFrame.pivot() to transform data
        for unique_value in data[second_dimension].unique():
            file_name = 'output/%s/lookup_tables/%s_%s_mass_flow_%.2f.csv' % (
            analysis_id, prepend_file_id, rs, unique_value)
            lookup_df = data[data[second_dimension] == unique_value]

            # Save the data times in a new dataframe (will be in order)
            save_df = pd.DataFrame.from_dict({'datetime': lookup_df['datetime'].unique()})
            for unique_value_2 in data[first_dimension].unique():
                new_df = lookup_df[lookup_df[first_dimension] == unique_value_2]
                save_df[unique_value_2] = new_df[rs].values

            save_df.to_csv(file_name, index=False)

            # Create heat maps
            if save_figure:
                figure_filename = 'output/%s/images/heatmap_%s_%s_mass_flow_%.2f.png' % (
                    analysis_id, prepend_file_id, rs, unique_value)

                # this is a bit cheezy right now, load in the file and process again
                df_heatmap = pd.read_csv(file_name, header=0)
                # Remove the datetime column before converting the column headers to rounded floats
                df_heatmap = df_heatmap.drop(columns=['datetime'])
                df_heatmap.rename(columns=lambda x: round(float(x), 1), inplace=True)

                plt.figure()
                f, ax = plt.subplots(figsize=(5, 12))
                sns.heatmap(df_heatmap)
                ax.set_title('%s - Mass Flow %s kg/s' % (rs, unique_value))
                ax.set_xlabel('ETS Inlet Temperature')
                ax.set_ylabel('Hour of Year')
                plt.savefig(figure_filename)
                plt.close('all')


def pickle_file(obj, filename, gzipfile=False):
    """

    :param obj:
    :param filename: Filename, without the extension
    :param gzipfile:
    :return:
    """
    if gzipfile:
        gfile = gzip.open('%s.pklzip' % filename, 'wb')
    else:
        gfile = open('%s.pkl' % filename, 'wb')
    cPickle.dump(obj, gfile)
    gfile.close()


def unpickle_file(filename):
    extension = os.path.splitext(filename)[1]
    if extension == '.pklzip':
        gfile = gzip.open(filename, 'rb')
    else:
        gfile = open(filename, 'rb')
    return cPickle.load(gfile)


def save_dict_to_csv(data, filename):
    with open(filename, 'wb') as cfile:
        writer = csv.DictWriter(cfile, data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def zipdir(path, ziph, extension=None):
    """
    Flattened zip directory
    :param path:
    :param ziph:
    :param extension:
    :return:
    """
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for a_file in files:
            filename = os.path.join(root, a_file)
            if extension:
                if a_file.endswith(extension):
                    ziph.write(filename, os.path.basename(filename))
            else:
                ziph.write(filename, os.path.basename(filename))
