#' Grab log entries that identifie 504 Gateway Timeouts
#'
#' @param ... arguments passed to [mapELB()]
#' @return A data.frame (tibble), via 'read_elb'
#' @export
find504s <- function (...) {
    analyzeELB(function (x) x[x$elb_status_code == 504,], ..., select_vars=FALSE)
}

findLogFiles <- function (start_date, end_date=start_date, base.dir=getOption("elbr.dir")) {
    dates <- seq(as.Date(start_date), as.Date(end_date), 1)
    dirs <- file.path(base.dir, strftime(dates, "%Y/%m/%d"))
    return(unlist(lapply(dirs, dir, pattern="\\.log$", full.names=TRUE)))
}
