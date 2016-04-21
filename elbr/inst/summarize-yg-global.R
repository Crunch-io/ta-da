library(crunch)
library(elbr)
library(lubridate)

setwd("/var/www/logs/AWSLogs/910774676937/by_dataset/")

login("neal+yougov@crunch.io")

yg <- getTeams()[["YouGov Global"]]
u <- urls(datasets(yg))
length(u) ## 415
ids <- vapply(u,
    function (x) tail(unlist(strsplit(x, "/")), 1),
    character(1),
    USE.NAMES=FALSE)
logs <- paste0(ids, ".log")

since_october <- intersect(logs, dir())
length(since_october) ## 410, so 5 haven't been touched since

summarize.elb <- function (filename) {
    df <- read.elb(filename)
    return(data.frame(
        started=min(df$timestamp),
        last=max(df$timestamp),
        cubes=length(grep("/cube/", df$request))
    ))
}

sums <- do.call(rbind, lapply(since_october, summarize.elb))
summary(sumdf)
head(sumdf)
quantile(sumdf$cubes, seq(0, 1, .05))
table(sumdf$cubes==0)
table(sumdf$cubes==0)/410
table(sumdf$cubes==0)/415
table(sumdf$cubes==20)/415
table(sumdf$cubes>20)/415
quantile(sumdf$cubes, seq(.90, 1, .01))

last <- ymd_hms(sumdf$last)
summary(last)
summary(last[sumdf$cubes>0])
summary(last[sumdf$cubes>20])
sort(last[sumdf$cubes>100])
