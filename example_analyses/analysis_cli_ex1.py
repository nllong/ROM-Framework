import argparse

from ..rom.metamodels import Metamodels

# parse the anlaysis.json and determine the model

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', help='Description file to use', default='metamodels.json')
parser.add_argument("-a", "--analysis_id", default="smoff_parametric_sweep",
                    help="ID of the Analysis Models")
downsample = parser.add_argument(
    '-d', '--downsample', default=None, type=float, help='Selected down sample value')
parser.add_argument("--model", default='LinearModel', choices=['LinearModel', 'RandomForest', 'SVR'])
parser.add_argument("--response", default='ETSOutletTemperature', help="Response name")
parser.add_argument("-d", "--day_of_week", type=int, default=0, help="Day of Week: 0-Sun to 6-Sat")
parser.add_argument("-m", "--month", type=int, default=1, help="Month: 1-Jan to 12-Dec")
parser.add_argument("-H", "--hour", type=int, default=9, help="Hour of Day: 0 to 23")
parser.add_argument("-T", "--outdoor_drybulb", type=float, default=29.5,
                    help="Outdoor Drybulb Temperature")
parser.add_argument("-RH", "--outdoor_rh", type=float, default=50,
                    help="Percent Outdoor Relative Humidity")
parser.add_argument("-i", "--inlet_temp", type=float, default=20, help="Inlet Temperature")

args = parser.parse_args()

print "Loading model"
metamodel = Metamodels(args.file)
metamodel.load_models(args.model, models_to_load=[args.response], downsample=args.downsample)

print "Predicting..."
yhat = metamodel.yhat(args.response, [args.month, args.hour, args.day_of_week, args.outdoor_drybulb,
                      args.outdoor_rh, args.inlet_temp])
print yhat


