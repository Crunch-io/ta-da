library(elbr)

filterLogs <- function (pattern="", date="", base.dir="/var/www/logs/AWSLogs/910774676937/elasticloadbalancing/eu-west-1/") {
    ## Date is YYYY/MM/DD, or any segment of that (e.g. YYYY/MM)
    in.dir <- file.path(base.dir, date)
    logs <- system(paste0('cd ', in.dir, ' && find . | xargs -n 1 egrep "',
        pattern, '"'), intern=TRUE)
    return(read.elb(textConnection(logs)))
}

loadDate <- function (date="", base.dir="/var/www/logs/AWSLogs/910774676937/elasticloadbalancing/eu-west-1/") {
    in.dir <- file.path(base.dir, date)
    files <- dir(in.dir, pattern="log$", full.names=TRUE, recursive=TRUE)
    return(do.call("rbind", lapply(files, function (x) cleanLog(read.elb(x)))))
}

# logs <- system('cd /var/www/logs/AWSLogs/910774676937/elasticloadbalancing/eu-west-1/2016/05/05 && find . | xargs -n 1 egrep " 500 500 "', intern=TRUE)
logs <- system('cd /var/www/logs/AWSLogs/910774676937/elasticloadbalancing/eu-west-1/2016/07/23 && find . | xargs -n 1 egrep " -1 -1 "', intern=TRUE)
df <- cleanLog(read.elb(textConnection(logs)))

table(standardizeURLs(df$request_url), df$request_verb)
