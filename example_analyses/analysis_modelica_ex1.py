# Make sure that the python path is set, such as by running
# export PYTHONPATH=`pwd`

from ..rom.metamodels import Metamodels


def load_models(metamodel_filename, model_type, models_to_load, downsample):
    metamodels = Metamodels(metamodel_filename)
    metamodels.load_models(model_type, models_to_load=models_to_load, downsample=downsample)

    return metamodels


def run_model(values):
    model = int(values[0])
    response = int(values[1])
    downsample = float(values[2])
    month = int(values[3])
    hour = int(values[4])
    day_of_week = int(values[5])
    t_outdoor = float(values[6])
    rh = float(values[7])
    inlet_temp = float(values[8])

    if model == 1:
        model = 'LinearModel'
    elif model == 2:
        model = 'RandomForest'
    elif model == 3:
        model = 'SVR'

    if response == 1:
        response = 'CoolingElectricity'
    elif response == 2:
        response = 'HeatingElectricity'
    elif response == 3:
        response = 'DistrictCoolingChilledWaterEnergy'
    elif response == 4:
        response = 'DistrictHeatingHotWaterEnergy'
    elif response == 5:
        response = 'ETSOutletTemperature'

    print('Loading model')
    metamodel = Metamodels('metamodels.json')
    metamodel.load_models(model, models_to_load=[response], downsample=downsample)

    print('Predicting...')
    return metamodel.yhat(response, [month, hour, day_of_week, t_outdoor, rh, inlet_temp])
