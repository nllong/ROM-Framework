# Make sure that the python path is set, such as by running
# export PYTHONPATH=`pwd`

from python.lib.ets_model import ETSModel
import os

# def run_model(model, season, month, hour, day_of_week, t_outdoor, rh, inlet_temp):


def run_model(values):
    model = int(values[0])
    season = int(values[1])
    month = int(values[2])
    hour = int(values[3])
    day_of_week = int(values[4])
    t_outdoor = float(values[5])
    rh = float(values[6])
    inlet_temp = float(values[7])

    dirname = os.path.dirname(os.path.abspath(__file__))
    model = ETSModel(dirname + '/output/3ff422c2-ca11-44db-b955-b39a47b011e7/RandomForest/models', model, season)
    return model.yhat(month, hour, day_of_week, t_outdoor, rh, inlet_temp)
