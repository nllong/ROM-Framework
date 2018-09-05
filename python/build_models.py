# !/usr/bin/env python
#
# Author: Nicholas Long (nicholas.l.long@colorado.edu)

import argparse

from lib.generators.linear_model import LinearModel
from lib.generators.random_forest import RandomForest
from lib.generators.svr import SVR
from lib.metamodels import Metamodels
import pandas as pd
from lib.validation import validate_dataframe


parser = argparse.ArgumentParser()
parser.add_argument("-a", "--analysis_moniker", help="Name of the Analysis Model")
available_models = parser.add_argument(
    "-m", "--model_type", choices=['All', 'LinearModel', 'RandomForest', 'SVR'],
    default='All', help="Type of model to build")
downsample = parser.add_argument(
    "-d", "--downsample", default=None, type=float, help="Build only specific downsample value")
del available_models.choices[0]
args = parser.parse_args()

if not args.analysis_moniker:
    print "Must pass in an Analysis ID or an Analysis name"
    exit(1)

print("Passed build_models.py args: %s" % args)

print("Loading metamodels.json")
metamodel = Metamodels('./metamodels.json')

if metamodel.set_analysis(args.analysis_moniker):
    for model_name in available_models.choices:
        if args.model_type == 'All' or args.model_type == model_name:
            # Full sample but no cross validation
            klass = globals()[model_name]
            # Set the random seed so that the test libraries are the same across the models

            if args.downsample and args.downsample not in metamodel.downsamples:
                print("Downsample argument must exist in the downsample list in the JSON")
                exit(1)

            # check if the model name has any downsampling override values
            algo_options = metamodel.algorithm_options.get(model_name, {})
            algo_options = Metamodels.resolve_algorithm_options(algo_options)
            downsamples = metamodel.downsamples
            if algo_options.get('downsamples', None):
                downsamples = algo_options.get('downsamples')

            print("Running model '%s' with downsamples '%s'" % (model_name, downsamples))
            for downsample in downsamples:
                if args.downsample and args.downsample != downsample:
                    continue

                klass = globals()[model_name]
                # Set the random seed so that the test libraries are the same across the models
                model = klass(metamodel.analysis_name, 79, downsample=downsample)
                model.build(
                    '../results/%s/simulation_results.csv' % metamodel.results_directory,
                    metamodel,
                    algorithm_options=algo_options,
                    skip_cv=downsample > 0.5
                )
