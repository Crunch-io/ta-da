niter <- 1  ## We can do multiple at a time
for (i in seq_len(niter)) {
    ## Grab 2 vars at a time and xtab them
    xtabvars <- sample(names(ds), 2, replace=FALSE)
    fmla <- as.formula(paste0("~ `", xtabvars[1], "` + `", xtabvars[2], "`"))
    print(crtabs(fmla, data=ds))
}