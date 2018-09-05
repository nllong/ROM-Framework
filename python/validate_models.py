# !/usr/bin/env python
#
# Author: Nicholas Long (nicholas.l.long@colorado.edu)

import argparse
import os

import pandas as pd

from lib.metamodels import Metamodels
from lib.validation import validate_dataframe

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--analysis_moniker", help="Name of the Analysis Model")
available_models = parser.add_argument("-m", "--model_type",
                                       choices=['All', 'LinearModel', 'RandomForest'],
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

if metamodel.set_analysis(args.analysis_moniker):
    if args.downsample and args.downsample not in metamodel.downsamples:
        print("Downsample argument must exist in the downsample list in the JSON")
        exit(1)

    for downsample in metamodel.downsamples:
        if args.downsample and args.downsample != downsample:
            continue

        validation_dir = "output/%s_%s/ValidationData" % (args.analysis_moniker, downsample)
        output_dir = "%s/images" % validation_dir

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # VALIDATE MODELS - load the model into the Metamodel class. Seems like we can simplify
        # this to have the two classes rely on each other.
        metadata = {}

        # loading the rf or lm data results in the same results since the data are from the same model
        single_df = pd.read_pickle("%s/%s" % (validation_dir, 'rf_validation.pkl'))

        for model_type in [('RandomForest', 'RF'), ('LinearModel', 'LM'), ('SVR', 'SVR')]:
            metadata[model_type[0]] = {'responses': [], 'moniker': model_type[1]}
            metamodel.load_models(model_type[0], downsample=downsample)

            # Run the ROM for each of the response variables
            for response in metamodel.available_response_names:
                metadata[model_type[0]]['responses'].append(response)
                single_df["Modeled %s %s" % (model_type[1], response)] = metamodel.yhat(response,
                                                                                        single_df)

        validate_dataframe(single_df, metadata, validation_dir)
