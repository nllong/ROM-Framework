# !/usr/bin/env python
#
# Author: Nicholas Long (nicholas.l.long@colorado.edu)

import argparse
import os

from lib.metamodels import Metamodels

from lib.generators.linear_model import LinearModel
from lib.generators.random_forest import RandomForest

# path = os.path.realpath(__file__)
# isn't the current path this anyway?
# os.chdir(path)

# Name: Small Office Building
# Covariates: Inlet Temperature
# Analysis ID: 3ff422c2-ca11-44db-b955-b39a47b011e7
# Number of Samples: 100

# Name: Small Office Building
# Covariates: Inlet Temperature, Delta T
# Analysis ID: 5564b7d5-4def-498b-ad5b-d4f12a46327
# Number of Samples: 10

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--analysis_id", default="3ff422c2-ca11-44db-b955-b39a47b011e7",
                    help="ID of the Analysis Models")
args = parser.parse_args()
print("Passed build_models.py args: %s" % args)

print("Loading metamodels.json")
analysis_file = Metamodels('./metamodels.json')
if analysis_file.set_analysis(args.analysis_id):
    # Set the random seed so that the test libraries are the same across the models

    model = RandomForest(args.analysis_id, 79)
    model.build(
        'output/%s/simulation_results.csv' % args.analysis_id,
        analysis_file.covariate_names,
        analysis_file.covariate_types,
        analysis_file.available_response_names
    )

    model = LinearModel(args.analysis_id, 79)
    model.build(
        'output/%s/simulation_results.csv' % args.analysis_id,
        analysis_file.covariate_names,
        analysis_file.covariate_types,
        analysis_file.available_response_names
    )

    # build_lm(
    #     'output/%s/simulation_results.csv' % args.analysis_id,
    #     analysis_file.covariate_names,
    #     analysis_file.covariate_types,
    #     analysis_file.available_response_names
    # )
