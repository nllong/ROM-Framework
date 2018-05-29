# !/usr/bin/env python
#
# Author: Nicholas Long (nicholas.l.long@colorado.edu)

import argparse

from lib.generators.linear_model import LinearModel
from lib.generators.random_forest import RandomForest
from lib.metamodels import Metamodels

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
parser.add_argument("-a", "--analysis_moniker", help="Name of the Analysis Model")
args = parser.parse_args()

if not args.analysis_moniker:
    print "Must pass in an Analysis ID or an Analysis name"
    exit(1)

print("Passed build_models.py args: %s" % args)

print("Loading metamodels.json")
metamodel = Metamodels('./metamodels.json')

if metamodel.set_analysis(args.analysis_moniker):
    # Set the random seed so that the ls
    # test libraries are the same across the models

    model = RandomForest(metamodel.analysis_name, 79)
    model.build(
        '../results/%s/simulation_results.csv' % metamodel.results_directory,
        metamodel.covariate_names,
        metamodel.covariate_types,
        metamodel.available_response_names
    )

    # load the model into the Metamodel class. Seems like we can simplify this to have the two
    # classes rely on each other.
    metamodel.load_models('RandomForest')
    single_df = model.read_dataframe("%s/%s" % (model.validation_dir, 'rf_validation.pkl'))
    metamodel.validate_dataframe(single_df, model.images_dir)


    ### Linear Models
    model = LinearModel(metamodel.analysis_name, 79)
    model.build(
        '../results/%s/simulation_results.csv' % metamodel.results_directory,
        metamodel.covariate_names,
        metamodel.covariate_types,
        metamodel.available_response_names
    )

    metamodel.load_models('LinearModel')
    single_df = model.read_dataframe("%s/%s" % (model.validation_dir, 'lm_validation.pkl'))
    metamodel.validate_dataframe(single_df, model.images_dir)

