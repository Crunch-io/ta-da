#' Grab log entries that match a pattern
#'
#' 'filterLogs' can take any pattern you give it. 'find504s' calls 'filterLogs'
#' with the pattern that identifies 504 Gateway Timeout responses.
#'
#' @param pattern character regular expression pattern to pass to 'egrep'
#' @param date character date string of the format YYYY/MM/DD, or any segment of
#' that (e.g. YYYY/MM).
#' @param base.dir character directory in which the ELB logs are located
#' @return A data.frame, via 'read.elb'
#' @export
filterLogs <- function (pattern="", date="", base.dir=getOption("elbr.dir")) {
    ## Date is YYYY/MM/DD, or any segment of that (e.g. YYYY/MM)
    in.dir <- file.path(base.dir, date)
    logs <- system(paste0('cd ', in.dir, ' && find . -name "*.log" | xargs -n 1 egrep "',
        pattern, '"'), intern=TRUE)
    return(read.elb(textConnection(logs)))
}

#' @rdname filterLogs
#' @export
find504s <- function (date="", base.dir=getOption("elbr.dir")) {
    filterLogs(" -1 -1 504 ", date, base.dir)
}

findLogFiles <- function (start_date, end_date=start_date, base.dir=getOption("elbr.dir")) {
    dates <- seq(as.Date(start_date), as.Date(end_date), 1)
    dirs <- file.path(base.dir, strftime(dates, "%Y/%m/%d"))
    return(unlist(lapply(dirs, dir, pattern="\\.log$", full.names=TRUE)))
}
