# !/usr/bin/env python
#
# Author: Nicholas Long (nicholas.l.long@colorado.edu)

import argparse
import os
import shutil

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from lib.metamodels import Metamodels

sns.set(style="ticks", color_codes=True)

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--analysis_moniker", help="Name of the Analysis Model")
available_models = parser.add_argument(
    "-m", "--model_type", choices=['All', 'LinearModel', 'RandomForest', 'SVR'],
    default='All', help="Type of model to build")
downsample = parser.add_argument(
    "-d", "--downsample", default=None, type=float, help="Evaluate only specific downsample value")
del available_models.choices[0]
args = parser.parse_args()

if not args.analysis_moniker:
    print "Must pass in an Analysis ID or an Analysis name"
    exit(1)

print("Passed build_models.py args: %s" % args)

print("Loading metamodels.json")
metamodel = Metamodels('./metamodels.json')


def process_cv_results(cv_result_file, response, output_dir):
    if os.path.exists(cv_result_file):
        # load the cv results
        print("Reading CV results file: %s" % cv_result_file)
        df = pd.read_csv(cv_result_file)
        df = df.drop('response', 1)
        # Fill in the max_depth that has NA when it was set to auto
        df = df.fillna(0)
        df = df.drop('downsample', 1)
        df = df.drop('mean_score_time', 1)
        df = df.drop('rank_test_score', 1)
        df = df.drop('mean_train_score', 1)
        # df = df.drop('max_depth', 1)
        df = df.drop(df.columns[[0]], axis=1)
        newplt = sns.pairplot(df)
        newplt.savefig('%s/fig_cv_%s_pairplot.png' % (output_dir, response))
        plt.clf()

        # plot specific xy plots
        f, ax = plt.subplots(figsize=(6.5, 6.5))
        sns.despine(f, left=True, bottom=True)
        newplt = sns.jointplot(
            df['mean_fit_time'], df['mean_test_score'], kind="hex"
        ).set_axis_labels('Mean Fit Time (seconds)', 'Mean Test Score (fraction)')
        newplt.savefig('%s/fig_cv_%s_time_v_score_hex.png' % (output_dir, response))
        plt.clf()

        # plot specific xy plots -- darkgrid background
        with plt.rc_context(dict(sns.axes_style("whitegrid"))):
            f, ax = plt.subplots(figsize=(6.5, 6.5))
            newplt = sns.scatterplot(x=df['mean_fit_time'], y=df['mean_test_score'],
                                     ax=ax).get_figure()
            ax.set_xlabel('Mean Fit Time (seconds)')
            ax.set_ylabel('Mean Test Score (fraction)')
            newplt.savefig('%s/fig_cv_%s_time_v_score.png' % (output_dir, response))
            plt.clf()


def process_model_results(model_results_file, output_dir):
    if os.path.exists(model_results_file):
        # Process the model results
        df = pd.read_csv(model_results_file)
        df['index_1'] = df.index

        melted_df = pd.melt(
            df[['name', 'time_to_build', 'time_to_cv']],
            id_vars='name',
            var_name='model',
            value_name='time'
        )

        fig = plt.figure(figsize=(8, 3), dpi=100)
        # defaults to the ax in the figure.
        ax = sns.barplot(x='time', y='name', hue='model', data=melted_df, ci=None)
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('')
        plt.tight_layout()
        fig.savefig('%s/fig_time_to_build.png' % output_dir)
        fig.clf()
        plt.clf()


if metamodel.set_analysis(args.analysis_moniker):
    # go through the cv_results and create some plots
    for model_name in available_models.choices:
        if args.model_type == 'All' or args.model_type == model_name:
            last_dir = None
            all_model_results = None

            if args.downsample and args.downsample not in metamodel.downsamples:
                print("Downsample argument must exist in the downsample list in the JSON")
                exit(1)

            # check if the model name has any downsampling override values
            algo_options = metamodel.algorithm_options.get(model_name, {})
            algo_options = Metamodels.resolve_algorithm_options(algo_options)
            downsamples = metamodel.downsamples
            if algo_options.get('downsamples', None):
                downsamples = algo_options.get('downsamples')

            for index, downsample in enumerate(downsamples):
                if args.downsample and args.downsample != downsample:
                    continue

                base_dir_ds = "output/%s_%s/%s" % (args.analysis_moniker, downsample, model_name)
                last_dir = base_dir_ds
                output_dir = "%s/images/cv_results" % base_dir_ds

                if os.path.exists(output_dir):
                    shutil.rmtree(output_dir)
                os.makedirs(output_dir)

                # Process the model results
                model_results_file = '%s/model_results.csv' % base_dir_ds
                process_model_results(model_results_file, output_dir)

                # if this is the first file, then read it into the all_model_results to
                # create a dataframe to add all the model results together
                if index == 0:
                    if os.path.exists(model_results_file):
                        all_model_results = pd.read_csv(model_results_file)
                else:
                    if os.path.exists(model_results_file):
                        all_model_results = pd.concat(
                            [all_model_results, pd.read_csv(model_results_file)]
                        )

                for response in metamodel.available_response_names(model_name):
                    # Process the CV results
                    cv_result_file = '%s/cv_results_%s.csv' % (base_dir_ds, response)
                    process_cv_results(cv_result_file, response, output_dir)

            # save any combined datasets
            all_model_results.to_csv('%s/all_model_results.csv' % last_dir, index=False)
