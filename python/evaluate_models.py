# !/usr/bin/env python
#
# Author: Nicholas Long (nicholas.l.long@colorado.edu)

import argparse

from lib.generators.linear_model import LinearModel
from lib.generators.random_forest import RandomForest
from lib.metamodels import Metamodels
import pandas as pd
from lib.validation import validate_dataframe
import os
import seaborn as sns; sns.set(style="ticks", color_codes=True)

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--analysis_moniker", help="Name of the Analysis Model")
available_models = parser.add_argument("-m", "--model_type", choices=['LinearModel', 'RandomForest'], default='RandomForest', help="Type of model to build")
del available_models.choices[0]
args = parser.parse_args()

if not args.analysis_moniker:
    print "Must pass in an Analysis ID or an Analysis name"
    exit(1)

print("Passed build_models.py args: %s" % args)

print("Loading metamodels.json")
metamodel = Metamodels('./metamodels.json')

if metamodel.set_analysis(args.analysis_moniker):
    for downsample in metamodel.downsamples:
        # go through the cv_results and create some plots
        for model_name in available_models.choices:
            if args.model_type == 'All' or args.model_type == model_name:
                base_dir = "output/%s_%s/%s" % (args.analysis_moniker, downsample, model_name)
                output_dir = "%s/images/cv_results" % base_dir

                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                for response in metamodel.available_response_names:
                    # load the cv results
                    df = pd.read_csv('%s/cv_results_%s.csv' % (base_dir, response))
                    df = df.drop('response', 1)
                    # Fill in the max_depth that has NA when it was set to auto
                    df = df.fillna(0)
                    df = df.drop('downsample', 1)
                    df = df.drop('mean_score_time', 1)
                    df = df.drop('rank_test_score', 1)
                    df = df.drop('mean_train_score', 1)
                    # df = df.drop('max_depth', 1)
                    df = df.drop(df.columns[[0]], axis=1)
                    plt = sns.pairplot(df)
                    plt.savefig('%s/fig_cv_%s_pairplot.png' % (output_dir, response))





