library(crunch)
library(elbr)
library(lubridate)

setwd("/var/www/logs/AWSLogs/910774676937/by_dataset/")

login("neal+yougov@crunch.io")

yg <- getTeams()[["YouGov Global"]]
globalDatasets <- datasets(yg)
u <- urls(globalDatasets)
length(u) ## 506 ## 585
ids <- vapply(u,
    function (x) tail(unlist(strsplit(x, "/")), 1),
    character(1),
    USE.NAMES=FALSE)
logs <- paste0(ids, ".log")

since_october <- intersect(logs, dir())
length(since_october) ## 500, so 6 haven't been touched since
## Now 585

summarize.elb <- function (filename) {
    df <- read.elb(filename)
    return(data.frame(
        started=min(df$timestamp),
        last=max(df$timestamp),
        cubes=length(grep("/cube/", df$request))
    ))
}

sumdf <- do.call(rbind, lapply(since_october, summarize.elb))
summary(sumdf)
head(sumdf)
quantile(sumdf$cubes, seq(0, 1, .05))
table(sumdf$cubes==0)
table(sumdf$cubes==0)/nrow(sumdf)
table(sumdf$cubes<20)/nrow(sumdf)
quantile(sumdf$cubes, seq(.90, 1, .01))

last <- ymd_hms(sumdf$last)
summary(last)
summary(last[sumdf$cubes>0])
summary(last[sumdf$cubes>20])
sort(last[sumdf$cubes>100])

table(last > ymd("2016-07-12")) ## Two weeks ago
#
# FALSE  TRUE
#   446    54

archive.these <- c(setdiff(logs, dir()), ## Those from before october
    since_october[last <= ymd("2016-05-20")])
these.urls <- paste0("https://beta.crunch.io/api/datasets/", substr(archive.these, 1, 32), "/")
to.archive <- datasets(yg)[these.urls]
myself <- self(me())

for (u in urls(to.archive)) crPATCH(u, body=toJSON(list(current_editor=myself)))

is.archived(to.archive) <- TRUE
