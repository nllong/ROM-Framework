from collections import OrderedDict
from math import sqrt

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from pandas.plotting import lag_plot
from sklearn.metrics import mean_squared_error

from shared import save_dict_to_csv


def validation_plot_energy_temp(melted_df, filename):
    with plt.rc_context(dict(sns.axes_style("whitegrid"))):
        f, ax = plt.subplots(figsize=(8, 5))
        newplt = sns.scatterplot(
            x="SiteOutdoorAirDrybulbTemperature",
            y="Energy",
            style="Model",
            data=melted_df,
            ax=ax).get_figure()
        ax.set_xlabel('Site Outdoor Air Drybulb Temperature (deg C)')
        ax.set_ylabel('Total HVAC Energy (GJ)')
        newplt.savefig(filename)
        plt.clf()


def validation_plot_timeseries(melted_df, filename):
    def date_formatter(x, pos):
        return pd.to_datetime(x)

    sns.set(color_codes=True)
    plt.rcParams['figure.figsize'] = [15, 10]

    with plt.rc_context(dict(sns.axes_style("whitegrid"))):
        fig, ax = plt.subplots()
        sns.tsplot(melted_df, time='DateTime', unit='Dummy', condition='Variable', value='Value',
                   ax=ax)
        # newplt.set_title("%s: %s vs EnergyPlus %s" % (season, model_data['moniker'], response))
        ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(date_formatter))

        # put the labels at 45deg since they tend to be too long
        fig.autofmt_xdate()
        fig.savefig(filename)
        fig.clf()
        plt.clf()


def validation_save_metrics(df, output_dir):
    # save the model performance data
    df.to_csv('%s/metrics.csv' % output_dir, index=False)
    df['disk_size'] = df['disk_size'].astype(float)
    df['ind'] = df.index
    df['Disk Size (Log)'] = np.log(df.disk_size)
    df['Response'] = df.response
    df['Type'] = df.model_type

    # plot the disk size
    with plt.rc_context(dict(sns.axes_style("whitegrid"))):
        f, ax = plt.subplots(figsize=(6.5, 6.5))
        newplt = sns.scatterplot(x="ind", y="Disk Size (Log)",
                                 style="Type", hue="Response",
                                 sizes=(10, 200), data=df, ax=ax).get_figure()
        ax.set_xlabel('Index')
        ax.set_ylabel('Log Disk Size (log(MB))')
        newplt.savefig('%s/fig_performance_disk_size.png' % (output_dir))
        plt.clf()

    # plot the load and run times
    table = pd.DataFrame.pivot_table(df,
                                     index=['Type'],
                                     values=['load_time', 'run_time_8760', 'run_time_single'],
                                     aggfunc=np.average)
    # covert back to a dataframe
    table = pd.DataFrame(table.to_records())
    table['Load Time (Log)'] = np.log(table.load_time)
    with plt.rc_context(dict(sns.axes_style('whitegrid'))):
        fig = plt.figure(figsize=(6.5, 6.5))
        # defaults to the ax in the figure.
        ax = sns.barplot(x='Type', y='Load Time (Log)', data=table)
        ax.set_xlabel('Model Type')
        ax.set_ylabel('Log Average Time (log(seconds))')
        plt.tight_layout()
        fig.savefig('%s/fig_performance_load_time.png' % output_dir)
        fig.clf()
        plt.clf()

    table.rename(columns={'run_time_single': 'Run Time - Single',
                          'run_time_8760': 'Run Time - 8760'}, inplace=True)
    table.to_csv('%s/load_time_metrics.csv' % output_dir, index=False)

    melted_df = pd.melt(table[['Type', 'Run Time - Single', 'Run Time - 8760']], id_vars='Type')
    with plt.rc_context(dict(sns.axes_style('whitegrid'))):
        fig = plt.figure(figsize=(6.5, 6.5))
        # defaults to the ax in the figure.
        ax = sns.barplot(x="Type", y="value", hue="variable", data=melted_df)
        ax.set_xlabel('Model Type')
        ax.set_ylabel('Log Average Time (log(seconds))')
        plt.tight_layout()
        fig.savefig('%s/fig_performance_run_time.png' % output_dir)
        fig.clf()
        plt.clf()


def validate_dataframe(df, metadata, image_save_dir):
    """
    Take the dataframe and perform various validations and create plots

    :param df: Contains the actual and modeled data for various ROMs
    :return:
    """
    # create some new columns for total energy
    df['Total Heating Energy'] = df['HeatingElectricity'] + df['DistrictHeatingHotWaterEnergy']
    df['Total Cooling Energy'] = df['CoolingElectricity'] + df['DistrictCoolingChilledWaterEnergy']
    df['Total HVAC Energy'] = df['Total Heating Energy'] + df['Total Cooling Energy']

    # aggregate the data and break out the cooling and heating totals.
    for model_type, model_data in metadata.items():
        for response in model_data['responses']:
            modeled_name = "Modeled %s %s" % (model_data['moniker'], response)
            heating_col_name = 'Total Heating Energy %s' % model_data['moniker']
            cooling_col_name = 'Total Cooling Energy %s' % model_data['moniker']
            total_col_name = 'Total HVAC Energy %s' % model_data['moniker']

            # calculate the total hvac energy for each model type
            if 'Heating' in modeled_name:
                if heating_col_name not in df.columns.values:
                    # initialize the columns
                    df[heating_col_name] = 0
                df[heating_col_name] += df[modeled_name]

            if 'Cooling' in modeled_name:
                if cooling_col_name not in df.columns.values:
                    # initialize the columns
                    df[cooling_col_name] = 0
                df[cooling_col_name] += df[modeled_name]

            # if 'Cooling' in modeled_name:
            #     df['Total Cooling Energy %s' % model_data['moniker']] += df[modeled_name]

        # sum up the heating and cooling columns for the total energy for each model_type
        heating_col_name = 'Total Heating Energy %s' % model_data['moniker']
        cooling_col_name = 'Total Cooling Energy %s' % model_data['moniker']
        total_col_name = 'Total HVAC Energy %s' % model_data['moniker']

        if total_col_name not in df.columns.values:
            df[total_col_name] = 0

        if heating_col_name in df.columns.values:
            df[total_col_name] += df[heating_col_name]

        if cooling_col_name in df.columns.values:
            df[total_col_name] += df[cooling_col_name]

    # Run the ROM for each of the response variables
    errors = []
    for model_type, model_data in metadata.items():
        for response in model_data['responses']:
            modeled_name = "Modeled %s %s" % (model_data['moniker'], response)

            lmplot = sns.lmplot(
                x=response,
                y=modeled_name,
                data=df,
                ci=None,
                palette="muted",
                height=8,
                scatter_kws={"s": 50, "alpha": 1}
            )
            fig = lmplot.fig
            fig.savefig(
                '%s/fig_validation_%s_%s.png' % (image_save_dir, response, model_data['moniker']))
            fig.tight_layout()
            fig.clf()
            plt.clf()

            # Lag plot for each response variable
            plt.figure()
            lag_plot(df[response])
            plt.savefig('%s/fig_lag_%s_%s.png' % (image_save_dir, model_data['moniker'], response))
            plt.clf()

            sum_of_error = (df[response] - df[modeled_name]).sum()
            sum_square_error = ((df[response] - df[modeled_name]) ** 2).sum()
            nmbe = 100 * (sum_of_error / ((len(df) - 1) * df[response].mean()))
            cvrmse = (100 / df[response].mean()) * (sqrt(sum_square_error / (len(df) - 1)))
            rmse = sqrt(mean_squared_error(df[response], df[modeled_name]))

            errors.append(
                OrderedDict(
                    [
                        ('response', response),
                        ('model_type', model_type),
                        ('rmse', rmse),
                        ('nmbe', nmbe),
                        ('cvrmse', cvrmse),
                    ]
                )
            )

            # save data to image dir, because that is the only directory that I know of right now
        save_dict_to_csv(errors, "%s/statistics.csv" % image_save_dir)

    # one off plots
    lmplot = sns.lmplot(
        x='SiteOutdoorAirDrybulbTemperature',
        y='Total HVAC Energy',
        data=df,
        ci=None,
        palette="muted",
        height=8,
        scatter_kws={"s": 50, "alpha": 1},
        fit_reg=False,
    )
    fig = lmplot.fig
    plt.title("Total Energy vs Temperature (Actual)")
    fig.savefig('%s/fig_validation_energy_actual.png' % image_save_dir)
    fig.tight_layout()
    fig.clf()
    plt.clf()

    all_columns = ['SiteOutdoorAirDrybulbTemperature', 'Total HVAC Energy']
    for model_type, model_data in metadata.items():
        all_columns.append('Total HVAC Energy %s' % model_data['moniker'])
        melted_df = pd.melt(
            df[['SiteOutdoorAirDrybulbTemperature', 'Total HVAC Energy',
                'Total HVAC Energy %s' % model_data['moniker']]],
            id_vars='SiteOutdoorAirDrybulbTemperature',
            var_name='Model',
            value_name='Energy'
        )
        melted_df['Dummy'] = 0
        filename = '%s/fig_validation_energy_combined_%s.png' % (
            image_save_dir, model_data['moniker'])
        validation_plot_energy_temp(melted_df, filename)

    # plot energy vs outdoor temperature for all of the responses
    melted_df = pd.melt(
        df[all_columns],
        id_vars='SiteOutdoorAirDrybulbTemperature',
        var_name='Model',
        value_name='Energy'
    )
    melted_df['Dummy'] = 0
    filename = '%s/fig_validation_energy_combined_all.png' % image_save_dir
    validation_plot_energy_temp(melted_df, filename)

    # create a subselection of the data, and run some other plots
    sub_data = {
        'Swing': df[df["DateTime"].between("2009-03-01 01:00", "2009-03-10 00:00")],
        'Summer': df[df["DateTime"].between("2009-07-01 01:00", "2009-07-10 00:00")],
        'Winter': df[df["DateTime"].between("2009-01-15 01:00", "2009-01-25 00:00")],
    }

    for season, season_df in sub_data.items():
        # gather a list of all the responses and the modeled column names
        all_responses = {}
        for model_type, model_data in metadata.items():
            for response in model_data['responses']:
                modeled_name = "Modeled %s %s" % (model_data['moniker'], response)
                if response in all_responses.keys():
                    all_responses[response].append(modeled_name)
                else:
                    all_responses[response] = [modeled_name]

        # plot each modeled response invividually
        for model_type, model_data in metadata.items():
            for response in model_data['responses']:
                modeled_name = "Modeled %s %s" % (model_data['moniker'], response)

                selected_columns = ['DateTime', response, modeled_name]
                melted_df = pd.melt(season_df[selected_columns],
                                    id_vars='DateTime',
                                    var_name='Variable',
                                    value_name='Value')
                melted_df['Dummy'] = 0
                filename = '%s/fig_validation_ts_%s_%s_%s.png' % (
                    image_save_dir, season, response, model_data['moniker'])
                validation_plot_timeseries(melted_df, filename)

        # now plot all the modeled responses together
        for response, models in all_responses.items():
            selected_columns = ['DateTime', response] + models
            print selected_columns

            melted_df = pd.melt(season_df[selected_columns],
                                id_vars='DateTime',
                                var_name='Variable',
                                value_name='Value')
            melted_df['Dummy'] = 0
            filename = '%s/fig_validation_ts_%s_%s_combined.png' % (
                image_save_dir, season, response)
            validation_plot_timeseries(melted_df, filename)

        print all_responses

        # plot all the modeled timeseries resutls on a single plot
