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

            print metamodel.algorithm_options

            # model = klass(metamodel.analysis_name, 79, downsample=None)
            # model.build(
            #     '../results/%s/simulation_results.csv' % metamodel.results_directory,
            #     metamodel.validation_id,
            #     metamodel.covariate_names,
            #     metamodel.covariate_types,
            #     metamodel.available_response_names,
            #     algorithm_options=metamodel.algorithm_options.get(model_name, {}),
            #     skip_cv=True
            # )

            for downsample in metamodel.downsamples:
                klass = globals()[model_name]
                # Set the random seed so that the test libraries are the same across the models
                model = klass(metamodel.analysis_name, 79, downsample=downsample)
                model.build(
                    '../results/%s/simulation_results.csv' % metamodel.results_directory,
                    metamodel.validation_id,
                    metamodel.covariate_names,
                    metamodel.covariate_types,
                    metamodel.available_response_names,
                    algorithm_options=metamodel.algorithm_options.get(model_name, {}),
                    skip_cv=False
                )
