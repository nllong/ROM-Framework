# adapted from http://civil.colorado.edu/~balajir/CVEN5454/R-sessions/sess1/myboxplot.r

myboxplot=function (x, ..., range = 1.5, width = NULL, varwidth = FALSE, 
                    notch = FALSE, outline = TRUE, names, boxwex = 0.8, plot = TRUE, 
                    border = par("fg"), col = NULL, log = "", pars = NULL, horizontal = FALSE, 
                    add = FALSE, at = NULL) 
{
  args = list(x, ...)
  namedargs = if (!is.null(attributes(args)$names)) 
    attributes(args)$names != ""
  else 
    rep(FALSE, length.out = length(args))
  pars = c(args[namedargs], pars)
  groups = if (is.list(x))
    x
  else 
    args[!namedargs]
  if (0 == (n <- length(groups))) 
    stop("invalid first argument")
  if (length(class(groups))) 
    groups <- unclass(groups)
  if (!missing(names)) 
    attr(groups, "names") <- names
  else {
    if (is.null(attr(groups, "names"))) 
      attr(groups, "names") <- 1:n
    names = attr(groups, "names")
  }
  for (i in 1:n) groups[i] <- list(myboxplot.stats(groups[[i]], 
                                                   range))
  stats = matrix(0, nr = 5, nc = n)
  conf = matrix(0, nr = 2, nc = n)
  ng = out = group = numeric(0)
  ct = 1
  for (i in groups) {
    stats[, ct] = i$stats
    conf[, ct] = i$conf
    ng <- c(ng, i$n)
    if ((lo = length(i$out))) {
      out = c(out, i$out)
      group = c(group, rep.int(ct, lo))
    }
    ct = ct + 1
  }
  z = list(stats = stats, n = ng, conf = conf, out = out, 
            group = group, names = names)
  if (plot) {
    bxp(z, width, varwidth = varwidth, notch = notch, boxwex = boxwex, 
        border = border, col = col, log = log, pars = pars, 
        outline = outline, horizontal = horizontal, add = add, 
        at = at)
    invisible(z)
  }
  else z
}

# adapted from http://civil.colorado.edu/~balajir/CVEN5454/R-sessions/sess1/myboxplot-stats.r

#This function replaces boxplot.stats --- it uses the middle 50% and
#middle 90% instead of middle 50%(IQR) and 1.5*IQR.
myboxplot.stats <- function (x, coef = NULL, do.conf = TRUE, do.out =
                               TRUE)
{
  nna = !is.na(x)
  n = sum(nna)
  stats = quantile(x, c(.05,.25,.5,.75,.95), na.rm = TRUE)
  iqr = diff(stats[c(2, 4)])
  out = x < stats[1] | x > stats[5]
  conf = if (do.conf)
    stats[3] + c(-1.58, 1.58) * diff(stats[c(2, 4)])/sqrt(n)
  list(stats = stats, n = n, conf = conf, out = x[out & nna])
} 
