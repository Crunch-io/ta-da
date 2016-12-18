library(elbr)

setwd("/var/www/logs/AWSLogs/910774676937/by_dataset/")

ids <- c("13858f67028b43c4be047ef0ddf73e4a",
    "321dd1047c454013b9243c962fe61594",
    "44a3c95cc63646fe9be124ad4129d2e8",
    "fdbb8a292b7a494a9b59705fe3b81c5a")

dfs <- lapply(ids, function (id) cleanLog(read.elb(paste0(id, ".log"))))

pct <- function (expr) {
    tbl <- table(expr)
    if ("TRUE" %in% names(tbl)) {
        return(round(100*as.numeric(tbl["TRUE"])/sum(tbl), 3))
    } else {
        return(0)
    }
}

reqsum <- function (df) {
    c(
        N=nrow(df),
        success=pct(df$status_code < 500),
        timeouts=sum(df$status_code == 504),
        median_time=median(df$response_time),
        time=quantile(df$response_time, c(.95, .99)) ## quantile appends 95% to the name
    )
}

reqSummary <- function (df) {
    ## Fill request time with 999 for timeouts
    df$response_time[is.na(df$response_time)] <- 999
    p1 <- reqsum(df)
    p2 <- reqsum(df[grep("cube", df$request_url),])
    names(p2) <- paste0("cube_", names(p2))
    p3 <- reqsum(df[df$user_agent == "web",])
    names(p3) <- paste0("web_", names(p3))
    c(p1, p2, p3)
}

out <- do.call(rbind, lapply(dfs, reqSummary))
out

lapply(dfs, function (df) {
    with(df[df$status_code == 504,],
        table(standardizeURLs(request_url), request_verb))
})
