# connect to R from python

# pyenv virtualenv 2.7.14 modelica-2.7.14
# In R run: install.packages('randomForest')
# pip install rpy2==2.8.6

import rpy2.robjects as robjects
from rpy2.robjects.packages import importr


def is_int(value):
    try:
        int(value)
    except ValueError:
        return False
    return True


class ETSModel:
    def __init__(self, model, season):
        """
        Load the model from the R dataframe

        :param model: String or Int, Name of the resulting ensemble model to return
        :param season: String or Int, Season to analyze

        """
        # Import Libraries in R
        importr('randomForest')

        # check if the model is an int, if so, then look up the model name from predefined list
        if is_int(model) and is_int(season):
            model_name = self._model_int_to_str(int(model), int(season))
        else:
            model_name = self._lookup_model_name(model, season)

        robjects.r('load("%s")' % model_name)
        self.rf = robjects.r('rf')
        self.predict = robjects.r.predict

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
            "heating_system": "rf_HeatingElectricity_model.RData",
            "cooling_system": "rf_CoolingElectricity_model.RData",
            "heating_ambient": "rf_District.Heating.Hot.Water.Energy_model.RData",
            "cooling_ambient": "rf_District.Cooling.Chilled.Water.Energy_model.RData",
            "heating_outlet": "rf_ETS.Heating.Outlet.Temperature_model.RData",
            "cooling_outlet": "rf_ETS.Cooling.Outlet.Temperature_model.RData",
        }

        return lookup["%s_%s" % (season, model)]

    def yhat(self, month, hour, dayofweek, t_outdoor, rh, inlet_temp):
        data = {
            "Day.of.Week": dayofweek,
            "Month": month,
            "Hour": hour,
            "Site.Outdoor.Air.Drybulb.Temperature": t_outdoor,
            "Site.Outdoor.Air.Relative.Humidity": rh,
            "ETS.Heating.Inlet.Temperature": inlet_temp,
            "ETS.Cooling.Inlet.Temperature": inlet_temp,
        }
        dataf = robjects.DataFrame(data)

        return self.predict(self.rf, newdata=dataf)[0]
