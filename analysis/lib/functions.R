
# Print the equation of a linear model to a format that is presentable in a table
print_eq = function(model){
  eq = ""
  for(i in 1:length(model$coefficients)){
    cf = round(model$coefficients[i], 4)
    if(i == 1){
      eq = paste("y =", cf)
    }else{
      eq = paste(eq, ifelse(sign(cf)==1, "+", "-"), abs(cf), "*", names(model$coefficients[i]))
    }
  }
  print_eq = eq
}

r_sq = function(y, yhat){
  #1 - (sum((actual-predict )^2)/sum((actual-mean(actual))^2))
  r_sq = 1 - (sum((y - yhat)^2)/sum((y - mean(y))^2))
}
subset_test_data_df = function(df, percent){
  # df is a dataframe
  drop = sample(c(1:nrow(df)), percent*nrow(df))
  keep = setdiff(c(1:nrow(df)), drop)
  
  test = df[drop,]
  model = df[keep,]
  
  subset_test_data_df = list("test"=test, "model"=model)
}

subset_test_data = function(x, y, percent){
  # X is is a dataframe
  # Y is a list
  drop = sample(c(1:length(y)), percent*length(y))
  keep = setdiff(c(1:length(y)), drop)
  
  xtest = x[drop,]
  ytest = y[drop]
  xmodel = x[keep,]
  ymodel = y[keep]    
  
  subset_test_data = list("xtest"=xtest, "ytest"=ytest, "xmodel"=xmodel, "ymodel"=ymodel)
}

# fit linear model with cross validation results
fit_model_and_cv = function(name, xdata, ydata, nsim){
  
  test_data = subset_test_data(xdata, ydata, 0.20)
  
  model = glm(test_data$ymodel ~ .,data=test_data$xmodel)
  final_model = stepAIC(model, direction="both")
  
  png(filename=paste(output_dir, 'lm_', name, '_summary.png', sep=''), height = 640, width = 640)
  par(mfrow=c(2,2))
  plot(final_model)
  dev.off()
  
  # cross validate - just once
  yhat = predict(model, newdata=test_data$xtest)
  png(filename=paste(output_dir, 'lm_', name, '_xy.png', sep=''), height = 640, width = 640)
  plot(test_data$ytest, yhat, uniform=TRUE, main=paste("XY - ", name, sep=''))
  abline(a=0, b=1, col="blue")
  dev.off()
  
  rmse = 1:nsim
  rsq = 1:nsim
  for (i in 1:nsim) {
    test_data = subset_test_data(xdata, ydata, 0.20)
    
    zz = glm(model$formula, data=test_data$xmodel)
    
    yhat = predict(zz, newdata=test_data$xtest, type="response")
    resid = test_data$ytest - yhat
    rmse[i] = sqrt(mean((test_data$ytest - yhat)^2)) 
    SST = sum((test_data$ytest - mean(test_data$ytest))^2) 
    SSR = sum((test_data$ytest - yhat)^2)
    rsq[i] = 1 - (SSR/SST)
  }
  
  png(filename=paste(output_dir, 'lm_', name, '_rmse_bloxplots.png', sep=''), height = 640, width = 640)
  par(mfrow = c(1, 2))
  # boxplot rmse
  zz = myboxplot(rmse, xlab = "", ylab = "Rmse", plot = F) 
  z1 = bxp(zz, xlab = "", ylab = "Median", cex = 1.25) 
  points(z1, mean(rmse), col = "red", cex = 1.25, pch = 16) 
  title(main = "RMSE: predicted\nvalues of the dropped")
  # boxplot rsq
  zz = myboxplot(rsq, xlab = "", ylab = "R-Squared", plot = F) 
  z1 = bxp(zz, xlab = "", ylab = "Median", cex = 1.25) 
  points(z1, mean(rsq), col = "red", cex = 1.25, pch = 16) 
  title(main = "R-Squared: predicted\nvalues of the dropped")
  dev.off()
  
  # return the models for storing and later analysis
  fit_model_and_cv = list(model=final_model, equation=print_eq(final_model))
}


# fit cart model and cross validate
fit_cart_and_cv = function(name, xdata, ydata, nsim){
  test_data = subset_test_data(xdata, ydata, 0.20)
  
  # Fit an initial model -- not really needed for cart
  fit = rpart(test_data$ymodel ~ ., method="anova", data=test_data$xmodel)
  png(filename=paste(output_dir, 'cart_', name, '.png', sep=''), height = 640, width = 640)
  plot(fit, uniform=TRUE, main=paste(name, sep=''))
  text(fit, use.n=TRUE, all=TRUE, cex=.75)
  dev.off()
  # plot the relative cross-validation error for each sub-tree 
  png(filename=paste(output_dir, 'cart_', name, 'cp-cv.png', sep=''), height = 640, width = 640)
  plotcp(fit)
  dev.off()
  
  # cross validate - just once 
  yhat = predict(fit, newdata=test_data$xtest)
  # plot xy
  png(filename=paste(output_dir, 'cart_', name, '_xy_single.png', sep=''), height = 640, width = 640)
  plot(test_data$ytest, yhat, uniform=TRUE, main=paste("XY - ", name, sep=''))
  dev.off()
  
  rmse = 1:nsim
  rsq = 1:nsim
  for (i in 1:nsim) {
    test_data = subset_test_data(xdata, ydata, 0.20)
    
    zz = rpart(test_data$ymodel ~ ., method="anova", data=test_data$xmodel)
    
    yhat = predict(zz, newdata=test_data$xtest)
    resid = test_data$ytest - yhat
    rmse[i] = sqrt(mean((test_data$ytest - yhat)^2)) 
    SST = sum((test_data$ytest - mean(test_data$ytest))^2) 
    SSR = sum((test_data$ytest - yhat)^2)
    rsq[i] = 1 - (SSR/SST)
  }
  
  png(filename=paste(output_dir, 'cart_', name, '_rmse_bloxplots.png', sep=''), height = 640, width = 640)
  par(mfrow = c(1, 2))
  # boxplot rmse
  zz = myboxplot(rmse, xlab = "", ylab = "Rmse", plot = F) 
  z1 = bxp(zz, xlab = "", ylab = "Median", cex = 1.25) 
  points(z1, mean(rmse), col = "red", cex = 1.25, pch = 16) 
  title(main = "RMSE: predicted\nvalues of the dropped")
  # boxplot rsq
  zz = myboxplot(rsq, xlab = "", ylab = "R-Squared", plot = F) 
  z1 = bxp(zz, xlab = "", ylab = "Median", cex = 1.25) 
  points(z1, mean(rsq), col = "red", cex = 1.25, pch = 16) 
  title(main = "R-Squared: predicted\nvalues of the dropped")
  dev.off()
  
  ###### prune the model
  fit_pruned = prune(fit, cp=0.05)
  png(filename=paste(output_dir, 'cart_', name, '_pruned.png', sep=''), height = 640, width = 640)
  plot(fit_pruned, uniform=TRUE, main=paste("XY - ", name, sep=''))
  text(fit_pruned, use.n=TRUE, all=TRUE, cex=.75)
  dev.off()

  # cross validate - just once for now
  yhat = predict(fit_pruned, newdata=test_data$xtest)
  png(filename=paste(output_dir, 'cart_', name, '_pruned_xy.png', sep=''), height = 640, width = 640)
  plot(test_data$ytest, yhat, uniform=TRUE, main=paste("XY - Pruned ", name, sep=''))
  dev.off()

  
  rmse = 1:nsim
  rsq = 1:nsim
  for (i in 1:nsim) {
    test_data = subset_test_data(xdata, ydata, 0.20)
    
    zz = rpart(test_data$ymodel ~ ., method="anova", data=test_data$xmodel)
    zz_pruned = prune(zz, cp=0.05)
    
    yhat = predict(zz, newdata=test_data$xtest)
    resid = test_data$ytest - yhat
    rmse[i] = sqrt(mean((test_data$ytest - yhat)^2)) 
    SST = sum((test_data$ytest - mean(test_data$ytest))^2) 
    SSR = sum((test_data$ytest - yhat)^2)
    rsq[i] = 1 - (SSR/SST)
  }
  
  png(filename=paste(output_dir, 'cart_', name, '_rmse_bloxplots_pruned.png', sep=''), height = 640, width = 640)
  par(mfrow = c(1, 2))
  # boxplot rmse
  zz = myboxplot(rmse, xlab = "", ylab = "Rmse", plot = F) 
  z1 = bxp(zz, xlab = "", ylab = "Median", cex = 1.25) 
  points(z1, mean(rmse), col = "red", cex = 1.25, pch = 16) 
  title(main = "RMSE: predicted\nvalues of the dropped")
  # boxplot rsq
  zz = myboxplot(rsq, xlab = "", ylab = "R-Squared", plot = F) 
  z1 = bxp(zz, xlab = "", ylab = "Median", cex = 1.25) 
  points(z1, mean(rsq), col = "red", cex = 1.25, pch = 16) 
  title(main = "R-Squared: predicted\nvalues of the dropped")
  dev.off()

  fit_cart_and_cv = list(model=fit, pruned_model=fit_pruned)
}


# fit cart model and cross validate
fit_rf_and_cv = function(name, xdata, ydata){
  test_data = subset_test_data(xdata, ydata, 0.20)
  
  rf = foreach(ntree=rep(25, 4), .combine=combine, .multicombine=TRUE, .packages='randomForest') %dopar% {
    randomForest(test_data$ymodel ~ ., data=test_data$xmodel, importance=TRUE, ntree=ntree)
  }      
  
  yhat = predict(rf, newdata=test_data$xtest)
  
  png(filename=paste(output_dir, 'rf_', name, '_cv.png', sep=''), height = 640, width = 640)
  plot(test_data$ytest, yhat, uniform=TRUE, main=paste("RF - ", name, sep=''))
  abline(a=0, b=1, col="blue")
  dev.off()
  
  png(filename=paste(output_dir, 'rf_', name, '_importance.png', sep=''), height = 1024, width = 1024)
  varImpPlot(rf, sort=T)
  dev.off()
  
  resid = test_data$ytest - yhat
  rmse = sqrt(mean((test_data$ytest - yhat)^2)) 
  SST = sum((test_data$ytest - mean(test_data$ytest))^2) 
  SSR = sum((test_data$ytest - yhat)^2)
  rsq = 1 - (SSR/SST)
  
  # save the model object
  save(rf, file = paste(models_dir, 'rf_', name, '_model.RData', sep=''))
  
  fit_rf_and_cv = list(model=rf, rmse=rmse, rsq=rsq)
}
  
  

