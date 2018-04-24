# connect to R from python

import argparse
# pyenv virtualenv 2.7.14 modelica-2.7.14
# In R run: install.packages('randomForest')
# pip install rpy2==2.8.6
from datetime import datetime

from lib.ets_model import ETSModel

# parse the anlaysis.json and determine the model

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--analysis_id", default="3ff422c2-ca11-44db-b955-b39a47b011e7",
                    help="ID of the Analysis Models")
parser.add_argument("--model", default='system', help="Model Name: system, ambient, or outlet")
parser.add_argument("--season", default='heating', help="Season: heating or cooling")
parser.add_argument("-d", "--day_of_week", type=int, default=0, help="Day of Week: 0-Sun to 6-Sat")
parser.add_argument("-m", "--month", type=int, default=1, help="Month: 1-Jan to 12-Dec")
parser.add_argument("-H", "--hour", type=int, default=9, help="Hour of Day: 0 to 23")
parser.add_argument("-T", "--outdoor_drybulb", type=float, default=29.5,
                    help="Outdoor Drybulb Temperature")
parser.add_argument("-RH", "--outdoor_rh", type=float, default=50,
                    help="Percent Outdoor Relative Humidity")
parser.add_argument("-i", "--inlet_temp", type=float, default=20, help="Inlet Temperature")
parser.add_argument("--mass-flow-heating", type=float, default=0.05,
                    help="Heating Mass Flow Rate (kg/s)")
parser.add_argument("--mass-flow-cooling", type=float, default=0.05,
                    help="Cooling Mass Flow Rate (kg/s)")

args = parser.parse_args()

print "Loading model"

# Check which model is being loaded to determine the arguments (this is manual right now)

print datetime.now().strftime("%H:%M:%S.%f")
model = ETSModel("output/%s/models" % args.analysis_id, 0, 0)
print datetime.now().strftime("%H:%M:%S.%f")

# model = ETSModel(args.model, args.season)
print "Predicting..."
if args.analysis_id == '3ff422c2-ca11-44db-b955-b39a47b011e7':
    yhat = model.yhat(args.month, args.hour, args.day_of_week, args.outdoor_drybulb,
                      args.outdoor_rh, args.inlet_temp)
elif args.analysis_id == '66fb9766-26e7-4bed-bdf9-0fbfbc8d6c7e':
    yhat = model.yhat(args.month, args.hour, args.day_of_week, args.outdoor_drybulb,
                      args.outdoor_rh, args.inlet_temp, args.mass_flow_heating,
                      args.mass_flow_cooling)

print "Result is %s" % yhat
