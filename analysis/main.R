library(MASS)
library(relaimpo)
library(bootstrap)
library(rpart)
library(randomForest)
library(ggplot2)
library(doMC)

options(warn=-1)
registerDoMC()

source('./lib/functions.R')
source('./lib/boxplots.R')

output_dir = './output/'; dir.create(file.path(output_dir), showWarnings = FALSE)
models_dir = './models/'; dir.create(file.path(models_dir), showWarnings = FALSE)


# make sure to run the ruby post_process.rb script to stitch together the results.csv file
results = read.csv('../results.csv')

# massage some of the data
#   - convert energy results to power (over the hour)
#   - Building inlet is district cooling output, and vice versa
results$District.Heating.Hot.Water.Energy = results$District.Heating.Hot.Water.Energy / 3600 
results$District.Cooling.Chilled.Water.Energy = results$District.Cooling.Chilled.Water.Energy / 3600 
results$HeatingElectricity = results$HeatingElectricity / 3600
results$CoolingElectricity = results$CoolingElectricity / 3600
results$Total.Cooling = results$District.Cooling.Chilled.Water.Energy + results$CoolingElectricity
results$Total.Heating = results$District.Heating.Hot.Water.Energy + results$HeatingElectricity
colnames(results)[which(names(results) == "District.Heating.Outlet.Temperature")] = "ETS.Heating.Inlet.Temperature"
colnames(results)[which(names(results) == "District.Heating.Inlet.Temperature")] = "ETS.Heating.Outlet.Temperature"
colnames(results)[which(names(results) == "District.Cooling.Outlet.Temperature")] = "ETS.Cooling.Inlet.Temperature"
colnames(results)[which(names(results) == "District.Cooling.Inlet.Temperature")] = "ETS.Cooling.Outlet.Temperature"

# only deal with results that have flow rates for heating and cooling

heating_data = results[ results$District.Cooling.Mass.Flow.Rate == 0 & results$District.Heating.Mass.Flow.Rate > 0, ]
cooling_data = results[ results$District.Heating.Mass.Flow.Rate == 0 & results$District.Cooling.Mass.Flow.Rate > 0, ]
# remove some of this data for an overall heating / cooling test data set
heating_data_test = subset_test_data_df(heating_data, 0.10)
heating_data = heating_data_test$model
cooling_data_test = subset_test_data_df(cooling_data, 0.10)
cooling_data = cooling_data_test$model


png(filename=paste(output_dir, 'summary_out_vs_in.png', sep=''), height = 640, width = 640)
plot(heating_data$ETS.Heating.Inlet.Temperature + cooling_data$ETS.Cooling.Inlet.Temperature, 
     heating_data$ETS.Heating.Outlet.Temperature + cooling_data$ETS.Heating.Outlet.Temperature,
     main="Outlet Temperature vs Inlet Temperature", xlab="Inlet Temperature (°C)", ylab="Outlet Temperature (°C)")
dev.off()
png(filename=paste(output_dir, 'summary_total_power_vs_outdoor.png', sep=''), height = 640, width = 640)
par(mfrow=c(1,2))
plot(heating_data$Site.Outdoor.Air.Drybulb.Temperature, heating_data$Total.Heating,
     main="Total Heating Power", xlab="Outdoor Temperature (°C)", ylab="Heating Power (W)")
plot(cooling_data$Site.Outdoor.Air.Drybulb.Temperature, cooling_data$Total.Cooling,
     main="Total Cooling Power", xlab="Outdoor Temperature (°C)", ylab="Cooling Power (W)")
dev.off()

png(filename=paste(output_dir, 'summary_heating_power_vs_outdoor.png', sep=''), height = 640, width = 640)
par(mfrow=c(1,2))
plot(heating_data$Site.Outdoor.Air.Drybulb.Temperature, heating_data$District.Heating.Hot.Water.Energy,
     main="District Heating Power", xlab="Outdoor Temperature (°C)", ylab="District Heating Power (W)")
plot(heating_data$Site.Outdoor.Air.Drybulb.Temperature, heating_data$HeatingElectricity,
     main="Electric Heating Power", xlab="Outdoor Temperature (°C)", ylab="Electric Heating Power (W)")
dev.off()

png(filename=paste(output_dir, 'summary_cooling_power_vs_outdoor.png', sep=''), height = 640, width = 640)
par(mfrow=c(1,2))
plot(cooling_data$Site.Outdoor.Air.Drybulb.Temperature, cooling_data$District.Cooling.Chilled.Water.Energy,
     main="District Cooling Power", xlab="Outdoor Temperature (°C)", ylab="District Cooling Power (W)")
plot(cooling_data$Site.Outdoor.Air.Drybulb.Temperature, cooling_data$CoolingElectricity,
     main="Electric Cooling Power", xlab="Outdoor Temperature (°C)", ylab="Electric Cooling Power (W)")
dev.off()

png(filename=paste(output_dir, 'summary_mass_flowrate.png', sep=''), height = 640, width = 640)
par(mfrow=c(1,2))
hist(heating_data$District.Heating.Mass.Flow.Rate, prob=T, xlab='Heating Mass Flow Rate', main='Histogram Heating Mass Flow Rate')
ec = ecdf(heating_data$District.Heating.Mass.Flow.Rate)
lines(ec)
hist(cooling_data$District.Cooling.Mass.Flow.Rate, prob=T, xlab='Cooling Mass Flow Rate', main='Histogram Cooling Mass Flow Rate')
ec = ecdf(cooling_data$District.Cooling.Mass.Flow.Rate)
lines(ec)
dev.off()

png(filename=paste(output_dir, 'summary_district_energy.png', sep=''), height = 640, width = 640)
par(mfrow=c(1,2))
hist(heating_data$District.Heating.Hot.Water.Energy, breaks=50, prob=T, xlab='District Heating Power', main='Histogram District Heating Power')
ec = ecdf(heating_data$District.Heating.Hot.Water.Energy)
lines(ec)

# look at other pairwise data
png(filename=paste(output_dir, 'heating_pairwise.png', sep=''), height = 640, width = 640)
plot(heating_data[,c("Month", "Day.of.Week", "Hour", "ETS.Heating.Outlet.Temperature", "HeatingElectricity", "District.Heating.Hot.Water.Energy")])
dev.off()
png(filename=paste(output_dir, 'cooling_pairwise.png', sep=''), height = 640, width = 640)
plot(heating_data[,c("Month", "Day.of.Week", "Hour", "ETS.Cooling.Outlet.Temperature", "CoolingElectricity", "District.Cooling.Chilled.Water.Energy")])
dev.off()

hist(cooling_data$District.Cooling.Chilled.Water.Energy, prob=T, xlab='District Heating Power', main='Histogram Distrcit Cooling Power')
ec = ecdf(cooling_data$District.Cooling.Chilled.Water.Energy)
lines(ec)
dev.off()

##################################
#### Generalized Linear Model ####
##################################
heating_models_lm = list()
cooling_models_lm = list()
model_results = data.frame(y=character(), equation=character(), stringsAsFactors = FALSE)
yvars = c('ETS.Heating.Outlet.Temperature', 'District.Heating.Hot.Water.Energy', 'HeatingElectricity')
for(yvar in yvars){
  y = heating_data[,yvar]
  # remove mass flow rate 'District.Heating.Mass.Flow.Rate'
  x = heating_data[,c('Day.of.Week', 'Hour', 'Month', 'ETS.Heating.Inlet.Temperature', 'Site.Outdoor.Air.Relative.Humidity', 'Site.Outdoor.Air.Drybulb.Temperature')]
  lm_results = fit_model_and_cv(yvar, x, y, 100)
  heating_models_lm[[yvar]] = lm_results$model
  model_results[nrow(model_results)+1,] = c(yvar, lm_results$equation)
}
yvars = c('ETS.Cooling.Outlet.Temperature', 'District.Cooling.Chilled.Water.Energy', 'CoolingElectricity')
for(yvar in yvars){
  y = cooling_data[,yvar]
  # remove mass flow rate 'District.Cooling.Mass.Flow.Rate'
  x = cooling_data[,c('Day.of.Week', 'Hour', 'Month',  'ETS.Cooling.Inlet.Temperature', 'Site.Outdoor.Air.Relative.Humidity', 'Site.Outdoor.Air.Drybulb.Temperature')]
  lm_results = fit_model_and_cv(yvar, x, y, 100)
  cooling_models_lm[[yvar]] = lm_results$model
  model_results[nrow(model_results)+1,] = c(yvar, lm_results$equation)
}
# save the data to CSV for easy export
write.csv(model_results, paste(output_dir, 'linear_models.csv'))

# R2 <- 1 - (sum((y-predict(heating_models_lm$District.Heating.Hot.Water.Energy))^2)/sum((y-mean(y))^2))

##################################
####  Classification Trees    ####
##################################

# clean up workspace before running CART
rm(list=setdiff(ls(), c("results", "output_dir", "models_dir", "cooling_data", "heating_data", "heating_data_test", "cooling_data_test", "cooling_models_lm", "heating_models_lm")))
source('./lib/functions.R')
source('./lib/boxplots.R')

# heating and cooling models
heating_models_cart = list()
cooling_models_cart = list()
yvars = c('ETS.Heating.Outlet.Temperature', 'District.Heating.Hot.Water.Energy', 'HeatingElectricity')
for(yvar in yvars){
  y = heating_data[,yvar]
  x = heating_data[,c('Day.of.Week', 'Hour', 'Month', 'ETS.Heating.Inlet.Temperature', 'Site.Outdoor.Air.Relative.Humidity', 'Site.Outdoor.Air.Drybulb.Temperature')]
  
  cart_results = fit_cart_and_cv(yvar, x, y, 50)
  heating_models_cart[[yvar]] = cart_results$model
  heating_models_cart[[paste(yvar,'_pruned',sep='')]] = cart_results$pruned_model
}
yvars = c('ETS.Cooling.Outlet.Temperature', 'District.Cooling.Chilled.Water.Energy', 'CoolingElectricity')
for(yvar in yvars){
  y = cooling_data[,yvar]
  x = cooling_data[,c('Day.of.Week', 'Hour', 'Month',  'ETS.Cooling.Inlet.Temperature', 'Site.Outdoor.Air.Relative.Humidity', 'Site.Outdoor.Air.Drybulb.Temperature')]
  
  cart_results = fit_cart_and_cv(yvar, x, y, 50)
  cooling_models_cart[[yvar]] = cart_results$model
  cooling_models_cart[[paste(yvar,'_pruned',sep='')]] = cart_results$pruned_model
}


##################################
####     Random Forests       ####
##################################
rm(list=setdiff(ls(), c("results", "output_dir", "models_dir", "cooling_data", "heating_data", "heating_data_test", "cooling_data_test", "cooling_models_lm", "heating_models_lm", "heating_models_cart", "cooling_models_cart")))
source('./lib/functions.R')
source('./lib/boxplots.R')

heating_models_rf = list()
cooling_models_rf = list()
yvars = c('ETS.Heating.Outlet.Temperature', 'District.Heating.Hot.Water.Energy', 'HeatingElectricity')
for(yvar in yvars){
  y = heating_data[,yvar]
  x = heating_data[,c('Day.of.Week', 'Hour', 'Month', 'ETS.Heating.Inlet.Temperature', 'Site.Outdoor.Air.Relative.Humidity', 'Site.Outdoor.Air.Drybulb.Temperature')]
  
  
  rf = fit_rf_and_cv(yvar, x, y)
  
  heating_models_rf[[yvar]] = rf$model
  heating_models_rf[[paste(yvar,'_rmse',sep='')]] = rf$rmse
  heating_models_rf[[paste(yvar,'_rsq',sep='')]] = rf$rsq
}

yvars = c('ETS.Cooling.Outlet.Temperature', 'District.Cooling.Chilled.Water.Energy', 'CoolingElectricity')
for(yvar in yvars){
  y = cooling_data[,yvar]
  x = cooling_data[,c('Day.of.Week', 'Hour', 'Month',  'ETS.Cooling.Inlet.Temperature', 'Site.Outdoor.Air.Relative.Humidity', 'Site.Outdoor.Air.Drybulb.Temperature')]
  
  rf = fit_rf_and_cv(yvar, x, y)
  
  cooling_models_rf[[yvar]] = rf$model
  cooling_models_rf[[paste(yvar,'_rmse',sep='')]] = rf$rmse
  cooling_models_rf[[paste(yvar,'_rsq',sep='')]] = rf$rsq
}



##########################
### Compare the models ###
##########################

# run the predicts on all the models

heating_data_test$test$lm_tout = predict(heating_models_lm$ETS.Heating.Outlet.Temperature, newdata=heating_data_test$test)
heating_data_test$test$cart_tout = predict(heating_models_cart$ETS.Heating.Outlet.Temperature, newdata=heating_data_test$test)
heating_data_test$test$cartpruned_tout = predict(heating_models_cart$ETS.Heating.Outlet.Temperature_pruned, newdata=heating_data_test$test)
heating_data_test$test$rf_tout = predict(heating_models_rf$ETS.Heating.Outlet.Temperature, newdata=heating_data_test$test)
heating_data_test$test$lm_heatingelectricity = predict(heating_models_lm$HeatingElectricity, newdata=heating_data_test$test)
heating_data_test$test$cart_heatingelectricity = predict(heating_models_cart$HeatingElectricity, newdata=heating_data_test$test)
heating_data_test$test$cartpruned_heatingelectricity = predict(heating_models_cart$HeatingElectricity_pruned, newdata=heating_data_test$test)
heating_data_test$test$rf_heatingelectricity = predict(heating_models_rf$HeatingElectricity, newdata=heating_data_test$test)
heating_data_test$test$lm_districtheat = predict(heating_models_lm$District.Heating.Hot.Water.Energy, newdata=heating_data_test$test)
heating_data_test$test$cart_districtheat = predict(heating_models_cart$District.Heating.Hot.Water.Energy, newdata=heating_data_test$test)
heating_data_test$test$cartpruned_districtheat = predict(heating_models_cart$District.Heating.Hot.Water.Energy, newdata=heating_data_test$test)
heating_data_test$test$rf_districtheat = predict(heating_models_rf$District.Heating.Hot.Water.Energy, newdata=heating_data_test$test)
heating_data_test$test$lm_total_heating = heating_data_test$test$lm_heatingelectricity + heating_data_test$test$lm_districtheat
heating_data_test$test$cart_total_heating = heating_data_test$test$cart_heatingelectricity + heating_data_test$test$cart_districtheat
heating_data_test$test$cartpruned_total_heating = heating_data_test$test$cartpurned_heatingelectricity + heating_data_test$test$cartpruned_districtheat
heating_data_test$test$rf_total_heating = heating_data_test$test$rf_heatingelectricity + heating_data_test$test$rf_districtheat


png(filename=paste(output_dir, 'compare_heating_temperature.png', sep=''), height = 800, width = 800)
par(mfrow=c(2,2), oma=c(0,0,3,0))
plot(heating_data_test$test$ETS.Heating.Outlet.Temperature, heating_data_test$test$lm_tout, xlab = 'ETS Outlet Temp (°C)', ylab = 'LM Outlet Temp (°C)')
plot(heating_data_test$test$ETS.Heating.Outlet.Temperature, heating_data_test$test$cart_tout, xlab = 'ETS Outlet Temp (°C)', ylab = 'Cart Outlet Temp (°C)')
plot(heating_data_test$test$ETS.Heating.Outlet.Temperature, heating_data_test$test$cartpruned_tout, xlab = 'ETS Outlet Temp (°C)', ylab = 'Cart (Pruned) Outlet Temp (°C)')
plot(heating_data_test$test$ETS.Heating.Outlet.Temperature, heating_data_test$test$rf_tout, xlab = 'ETS Outlet Temp (°C)', ylab = 'RF Outlet Temp (°C)')
title("Heating Outlet Temperature", outer=TRUE)
dev.off()

png(filename=paste(output_dir, 'compare_heating_electricy.png', sep=''), height = 800, width = 800)
par(mfrow=c(2,2), oma=c(0,0,3,0))
plot(heating_data_test$test$HeatingElectricity, heating_data_test$test$lm_heatingelectricity, xlab = 'Actual Heating Electricity (W)', ylab = 'LM Heating Electricity (W)')
plot(heating_data_test$test$HeatingElectricity, heating_data_test$test$cart_heatingelectricity, xlab = 'Actual Heating Electricity (W)', ylab = 'Cart Heating Electricity (W)')
plot(heating_data_test$test$HeatingElectricity, heating_data_test$test$cartpruned_heatingelectricity, xlab = 'Actual Heating Electricity (W)', ylab = 'Cart (Pruned) Heating Electricity (W)')
plot(heating_data_test$test$HeatingElectricity, heating_data_test$test$rf_heatingelectricity, xlab = 'Actual Heating Electricity (W)', ylab = 'RF Heating Electricity (W)')
title("Heating Power", outer=TRUE)
dev.off()

png(filename=paste(output_dir, 'compare_district_heating.png', sep=''), height = 800, width = 800)
par(mfrow=c(2,2), oma=c(0,0,3,0))
plot(heating_data_test$test$District.Heating.Hot.Water.Energy, heating_data_test$test$lm_districtheat, xlab = 'Actual District Heating Power (W)', ylab = 'LM District Heating Power (W)')
plot(heating_data_test$test$District.Heating.Hot.Water.Energy, heating_data_test$test$cart_districtheat, xlab = 'Actual District Heating Power (W)', ylab = 'Cart District Heating Power (W)')
plot(heating_data_test$test$District.Heating.Hot.Water.Energy, heating_data_test$test$cartpruned_districtheat, xlab = 'Actual District Heating Power (W)', ylab = 'Cart (Pruned) District Heating Power (W)')
plot(heating_data_test$test$District.Heating.Hot.Water.Energy, heating_data_test$test$rf_districtheat, xlab = 'Actual District Heating Power (W)', ylab = 'RF District Heating Power (W)')
title("District Heating Power", outer=TRUE)
dev.off()

png(filename=paste(output_dir, 'compare_total_heating.png', sep=''), height = 800, width = 800)
par(mfrow=c(2,2), oma=c(0,0,3,0))
plot(heating_data_test$test$Total.Heating, heating_data_test$test$lm_total_heating, xlab = 'Actual Total Heating Power (W)', ylab = 'LM Total Heating Power (W)')
plot(heating_data_test$test$Total.Heating, heating_data_test$test$cart_total_heating, xlab = 'Actual Total Heating Power (W)', ylab = 'Cart Total Heating Power (W)')
plot(heating_data_test$test$Total.Heating, heating_data_test$test$cartpruned_total_heating, xlab = 'Actual Total Heating Power (W)', ylab = 'Cart (Pruned) Total Heating Power (W)')
plot(heating_data_test$test$Total.Heating, heating_data_test$test$rf_total_heating, xlab = 'Actual Total Heating Power (W)', ylab = 'RF Total Heating Power (W)')
title("Total Heating Power", outer=TRUE)
dev.off()

# plot on the tout chart
png(filename=paste(output_dir, 'total_heating_outdoor.png', sep=''), height = 800, width = 800)
plot(heating_data_test$test$Site.Outdoor.Air.Drybulb.Temperature, heating_data_test$test$Total.Heating, xlab = 'Outdoor Temperature (°C)', ylab = 'Total Heating Power (W)')
points(heating_data_test$test$Site.Outdoor.Air.Drybulb.Temperature, heating_data_test$test$lm_total_heating, pch='+', col='red' )
points(heating_data_test$test$Site.Outdoor.Air.Drybulb.Temperature, heating_data_test$test$cart_total_heating, pch='x', col='green' )
points(heating_data_test$test$Site.Outdoor.Air.Drybulb.Temperature, heating_data_test$test$rf_total_heating, pch='-', col='blue' )
legend('topright', legend=c("Actual","LM","Cart","RF"), col=c("black","red","green","blue"), pch=c("o","+","x","-"))
dev.off()

# Cooling
cooling_data_test$test$lm_tout = predict(cooling_models_lm$ETS.Cooling.Outlet.Temperature, newdata=cooling_data_test$test)
cooling_data_test$test$cart_tout = predict(cooling_models_cart$ETS.Cooling.Outlet.Temperature, newdata=cooling_data_test$test)
cooling_data_test$test$cartpruned_tout = predict(cooling_models_cart$ETS.Cooling.Outlet.Temperature_pruned, newdata=cooling_data_test$test)
cooling_data_test$test$rf_tout = predict(cooling_models_rf$ETS.Cooling.Outlet.Temperature, newdata=cooling_data_test$test)
cooling_data_test$test$lm_coolingelectricity = predict(cooling_models_lm$CoolingElectricity, newdata=cooling_data_test$test)
cooling_data_test$test$cart_coolingelectricity = predict(cooling_models_cart$CoolingElectricity, newdata=cooling_data_test$test)
cooling_data_test$test$cartpurned_coolingelectricity = predict(cooling_models_cart$CoolingElectricity_pruned, newdata=cooling_data_test$test)
cooling_data_test$test$rf_coolingelectricity = predict(cooling_models_rf$CoolingElectricity, newdata=cooling_data_test$test)
cooling_data_test$test$lm_districtcooling = predict(cooling_models_lm$District.Cooling.Chilled.Water.Energy, newdata=cooling_data_test$test)
cooling_data_test$test$cart_districtcooling = predict(cooling_models_cart$District.Cooling.Chilled.Water.Energy, newdata=cooling_data_test$test)
cooling_data_test$test$cartpruned_districtcooling = predict(cooling_models_cart$District.Cooling.Chilled.Water.Energy, newdata=cooling_data_test$test)
cooling_data_test$test$rf_districtcooling = predict(cooling_models_rf$District.Cooling.Chilled.Water.Energy, newdata=cooling_data_test$test)
cooling_data_test$test$lm_total_cooling = cooling_data_test$test$lm_coolingelectricity + cooling_data_test$test$lm_districtcooling
cooling_data_test$test$cart_total_cooling = cooling_data_test$test$cart_coolingelectricity + cooling_data_test$test$cart_districtcooling
cooling_data_test$test$cartpruned_total_cooling = cooling_data_test$test$cartpurned_coolingelectricity + cooling_data_test$test$cartpruned_districtcooling
cooling_data_test$test$rf_total_cooling = cooling_data_test$test$rf_coolingelectricity + cooling_data_test$test$rf_districtcooling

png(filename=paste(output_dir, 'compare_cooling_temperature.png', sep=''), height = 800, width = 800)
par(mfrow=c(2,2), oma=c(0,0,3,0))
plot(cooling_data_test$test$ETS.Cooling.Outlet.Temperature, cooling_data_test$test$lm_tout, xlab = 'ETS Outlet Temp (°C)', ylab = 'LM Outlet Temp (°C)')
plot(cooling_data_test$test$ETS.Cooling.Outlet.Temperature, cooling_data_test$test$cart_tout, xlab = 'ETS Outlet Temp (°C)', ylab = 'Cart Outlet Temp (°C)')
plot(cooling_data_test$test$ETS.Cooling.Outlet.Temperature, cooling_data_test$test$cartpruned_tout, xlab = 'ETS Outlet Temp (°C)', ylab = 'Cart (Pruned) Outlet Temp (°C)')
plot(cooling_data_test$test$ETS.Cooling.Outlet.Temperature, cooling_data_test$test$rf_tout, xlab = 'ETS Outlet Temp (°C)', ylab = 'RF Outlet Temp (°C)')
title("Cooling Outlet Temperature", outer=TRUE)
dev.off()

png(filename=paste(output_dir, 'compare_cooling_electricy.png', sep=''), height = 800, width = 800)
par(mfrow=c(2,2), oma=c(0,0,3,0))
plot(cooling_data_test$test$CoolingElectricity, cooling_data_test$test$lm_coolingelectricity, xlab = 'Actual Cooling Electricity (W)', ylab = 'LM Cooling Electricity (W)')
plot(cooling_data_test$test$CoolingElectricity, cooling_data_test$test$cart_coolingelectricity, xlab = 'Actual Cooling Electricity (W)', ylab = 'Cart Cooling Electricity (W)')
plot(cooling_data_test$test$CoolingElectricity, cooling_data_test$test$cartpurned_coolingelectricity, xlab = 'Actual Cooling Electricity (W)', ylab = 'Cart (Pruned) Cooling Electricity (W)')
plot(cooling_data_test$test$CoolingElectricity, cooling_data_test$test$rf_coolingelectricity, xlab = 'Actual Cooling Electricity (W)', ylab = 'RF Cooling Electricity (W)')
title("Cooling Power", outer=TRUE)
dev.off()

png(filename=paste(output_dir, 'compare_district_cooling.png', sep=''), height = 800, width = 800)
par(mfrow=c(2,2), oma=c(0,0,3,0))
plot(cooling_data_test$test$District.Cooling.Chilled.Water.Energy, cooling_data_test$test$lm_districtcooling, xlab = 'Actual District Cooling Power (W)', ylab = 'LM District Cooling Power (W)')
plot(cooling_data_test$test$District.Cooling.Chilled.Water.Energy, cooling_data_test$test$cart_districtcooling, xlab = 'Actual District Cooling Power (W)', ylab = 'Cart District Cooling Power (W)')
plot(cooling_data_test$test$District.Cooling.Chilled.Water.Energy, cooling_data_test$test$cartpruned_districtcooling, xlab = 'Actual District Cooling Power (W)', ylab = 'Cart (Pruned) District Cooling Power (W)')
plot(cooling_data_test$test$District.Cooling.Chilled.Water.Energy, cooling_data_test$test$rf_districtcooling, xlab = 'Actual District Cooling Power (W)', ylab = 'RF District Cooling Power (W)')
title("District Cooling Power", outer=TRUE)
dev.off()

png(filename=paste(output_dir, 'compare_total_cooling.png', sep=''), height = 800, width = 800)
par(mfrow=c(2,2), oma=c(0,0,3,0))
plot(cooling_data_test$test$Total.Cooling, cooling_data_test$test$lm_total_cooling, xlab = 'Actual Total Cooling Power (W)', ylab = 'LM Total Cooling Power (W)')
plot(cooling_data_test$test$Total.Cooling, cooling_data_test$test$cart_total_cooling, xlab = 'Actual Total Cooling Power (W)', ylab = 'Cart Total Cooling Power (W)')
plot(cooling_data_test$test$Total.Cooling, cooling_data_test$test$cartpruned_total_cooling, xlab = 'Actual Total Cooling Power (W)', ylab = 'Cart (Pruned) Total Cooling Power (W)')
plot(cooling_data_test$test$Total.Cooling, cooling_data_test$test$rf_total_cooling, xlab = 'Actual Total Cooling Power (W)', ylab = 'RF Total Cooling Power (W)')
title("Total Cooling Power", outer=TRUE)
dev.off()

# plot on the outdoor temperature chart
png(filename=paste(output_dir, 'total_cooling_outdoor.png', sep=''), height = 800, width = 800)
plot(cooling_data_test$test$Site.Outdoor.Air.Drybulb.Temperature, cooling_data_test$test$Total.Cooling, xlab = 'Outdoor Temperature (°C)', ylab = 'Total Cooling Power (W)')
points(cooling_data_test$test$Site.Outdoor.Air.Drybulb.Temperature, cooling_data_test$test$lm_total_cooling, pch='+', col='red' )
points(cooling_data_test$test$Site.Outdoor.Air.Drybulb.Temperature, cooling_data_test$test$cart_total_cooling, pch='x', col='green' )
points(cooling_data_test$test$Site.Outdoor.Air.Drybulb.Temperature, cooling_data_test$test$rf_total_cooling, pch='-', col='blue' )
legend('topleft', legend=c("Actual","LM","Cart","RF"), col=c("black","red","green","blue"), pch=c("o","+","x","-"))
dev.off()

rsquares = data.frame(lm=rep(NA,6), cart=rep(NA,6), cart_pruned=rep(NA,6), rf=rep(NA,6))
rownames(rsquares) = c("Heating Outlet Temperature", "Heating Electricity", "District Heating Power", "Cooling Outlet Temperature", "Cooling Electricity", "District Cooling Power")
rsquares["Heating Outlet Temperature","lm"] = r_sq(heating_data_test$test$ETS.Heating.Outlet.Temperature, heating_data_test$test$lm_tout)
rsquares["Heating Outlet Temperature","cart"] = r_sq(heating_data_test$test$ETS.Heating.Outlet.Temperature, heating_data_test$test$cart_tout)
rsquares["Heating Outlet Temperature","cart_pruned"] = r_sq(heating_data_test$test$ETS.Heating.Outlet.Temperature, heating_data_test$test$cartpruned_tout)
rsquares["Heating Outlet Temperature","rf"] = r_sq(heating_data_test$test$ETS.Heating.Outlet.Temperature, heating_data_test$test$rf_tout)
rsquares["Heating Electricity","lm"] = r_sq(heating_data_test$test$HeatingElectricity, heating_data_test$test$lm_heatingelectricity)
rsquares["Heating Electricity","cart"] = r_sq(heating_data_test$test$HeatingElectricity, heating_data_test$test$cart_heatingelectricity)
rsquares["Heating Electricity","cart_pruned"] = r_sq(heating_data_test$test$HeatingElectricity, heating_data_test$test$cartpruned_heatingelectricity)
rsquares["Heating Electricity","rf"] = r_sq(heating_data_test$test$HeatingElectricity, heating_data_test$test$rf_heatingelectricity)
rsquares["District Heating Power","lm"] = r_sq(heating_data_test$test$District.Heating.Hot.Water.Energy, heating_data_test$test$lm_districtheat)
rsquares["District Heating Power","cart"] = r_sq(heating_data_test$test$District.Heating.Hot.Water.Energy, heating_data_test$test$cart_districtheat)
rsquares["District Heating Power","cart_pruned"] = r_sq(heating_data_test$test$District.Heating.Hot.Water.Energy, heating_data_test$test$cartpruned_districtheat)
rsquares["District Heating Power","rf"] = r_sq(heating_data_test$test$District.Heating.Hot.Water.Energy, heating_data_test$test$rf_districtheat)
rsquares["Cooling Outlet Temperature","lm"] = r_sq(cooling_data_test$test$ETS.Cooling.Outlet.Temperature, cooling_data_test$test$lm_tout)
rsquares["Cooling Outlet Temperature","cart"] = r_sq(cooling_data_test$test$ETS.Cooling.Outlet.Temperature, cooling_data_test$test$cart_tout)
rsquares["Cooling Outlet Temperature","cart_pruned"] = r_sq(cooling_data_test$test$ETS.Cooling.Outlet.Temperature, cooling_data_test$test$cartpruned_tout)
rsquares["Cooling Outlet Temperature","rf"] = r_sq(cooling_data_test$test$ETS.Cooling.Outlet.Temperature, cooling_data_test$test$rf_tout)
rsquares["Cooling Electricity","lm"] = r_sq(cooling_data_test$test$CoolingElectricity, cooling_data_test$test$lm_coolingelectricity)
rsquares["Cooling Electricity","cart"] = r_sq(cooling_data_test$test$CoolingElectricity, cooling_data_test$test$cart_coolingelectricity)
rsquares["Cooling Electricity","cart_pruned"] = r_sq(cooling_data_test$test$CoolingElectricity, cooling_data_test$test$cartpurned_coolingelectricity)
rsquares["Cooling Electricity","rf"] = r_sq(cooling_data_test$test$CoolingElectricity, cooling_data_test$test$rf_coolingelectricity)
rsquares["District Cooling Power","lm"] = r_sq(cooling_data_test$test$District.Cooling.Chilled.Water.Energy, cooling_data_test$test$lm_districtcooling)
rsquares["District Cooling Power","cart"] = r_sq(cooling_data_test$test$District.Cooling.Chilled.Water.Energy, cooling_data_test$test$cart_districtcooling)
rsquares["District Cooling Power","cart_pruned"] = r_sq(cooling_data_test$test$District.Cooling.Chilled.Water.Energy, cooling_data_test$test$cartpruned_districtcooling)
rsquares["District Cooling Power","rf"] = r_sq(cooling_data_test$test$District.Cooling.Chilled.Water.Energy, cooling_data_test$test$rf_districtcooling)
write.csv(rsquares, paste(output_dir, 'rsquares.csv', sep=''))
