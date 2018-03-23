# pyenv virtualenv 2.7.14 modelica-2.7.14
from lib.shared import unpickle_file
import gc

def is_int(value):
    try:
        int(value)
    except ValueError:
        return False
    return True


class ETSModel:
    def __init__(self, path_to_models, model, season):
        """
        Load the model from a pandas pickled dataframe

        :param path_to_models: String, String path to where the pickled models exist
        :param model: String or Int, Name of the resulting ensemble model to return
        :param season: String or Int, Season to analyze

        """
        # check if the model is an int, if so, then look up the model name from predefined list
        if is_int(model) and is_int(season):
            model_name = self._model_int_to_str(int(model), int(season))
        else:
            model_name = self._lookup_model_name(model, season)

        gc.disable()
        self.model = unpickle_file('%s/%s' % (path_to_models, model_name))
        gc.enable()

    def _model_int_to_str(self, model_int, season_int):
        """
        Look up the file based on some integers.

        Model Lookups
            0: hvac system
            1: ambient loop
            2: outlet temperature

        Season Lookups
            0: heating
            1: cooling

        :return: String, name of file to load
        """
        model_lookup = {
            0: "system",
            1: "ambient",
            2: "outlet",
        }
        season_lookup = {
            0: "heating",
            1: "cooling",
        }

        return self._lookup_model_name(model_lookup[model_int], season_lookup[season_int])

    def _lookup_model_name(self, model, season):
        """
        Look up the file that contains the RF model based on the model and the season.

        :param model: String, Name of the resulting ensemble model to return
        :param season: String, Season to analyze
        :return: String
        """
        lookup = {
            "heating_system": "HeatingElectricity.pkl",
            "cooling_system": "CoolingElectricity.pkl",
            "heating_ambient": "DistrictHeatingHotWaterEnergy.pkl",
            "cooling_ambient": "DistrictCoolingChilledWaterEnergy.pkl",
            "heating_outlet": "ETSHeatingOutletTemperature.pkl",
            "cooling_outlet": "ETSCoolingOutletTemperature.pkl",
        }

        return lookup["%s_%s" % (season, model)]

    def yhat_array(self, data):
        # Pass in the data as an array for quicker processing. The format is
        # [month, hour, dayofweek, t_outdoor, rh, inlet_temp]
        predictions = self.model.predict(data)
        return predictions


    def yhat(self, month, hour, dayofweek, t_outdoor, rh, inlet_temp):
        # The covariates need to be in the same order
        # covariates = [
        #     'Month',
        #     'Hour',
        #     'DayofWeek',
        #     'SiteOutdoorAirDrybulbTemperature',
        #     'SiteOutdoorAirRelativeHumidity',
        #     'ETSInletTemperature',
        # ]

        data = [[month, hour, dayofweek, t_outdoor, rh, inlet_temp]]
        predictions = self.model.predict(data)
        return predictions[0]
