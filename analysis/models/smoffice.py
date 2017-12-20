# connect to R from python

# pyenv virtualenv 3.6.3 modelica-3.6.3
# install.packages('randomForest')
# pip install rpy2

import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
importr('randomForest')

def yhat(model_name, month, day, dayofweek):
	data = { 
		"Day": 1, 
		"Day.of.Week": 1, 
		"Month": 1,
		"Hour": 9,
		"Site.Outdoor.Air.Drybulb.Temperature": -0.6,
		"Site.Outdoor.Air.Relative.Humidity": 89,
		"ETS.Heating.Inlet.Temperature": 23.0854,
		"ETS.Cooling.Inlet.Temperature": 18.9123,
	}
	dataf = robjects.DataFrame(data)

	robjects.r('load("rf_%s_model.RData")' % model_name)
	
	rf = robjects.r('rf')
	predict = robjects.r.predict
	return predict(rf, newdata=dataf)[0]

print(yhat('HeatingElectricity', 1, 1, 1))