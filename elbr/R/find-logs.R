find_log_files <- function (start_date=NULL, end_date=start_date, base.dir=getOption("elbr.dir", ".")) {
    if (is.null(start_date)) {
        ## TODO: implement open ranges, not just all or within range
        return(dir(base.dir, pattern="\\.log$", full.names=TRUE, recursive=TRUE))
    }
    dates <- seq(as.Date(start_date), as.Date(end_date), 1)
    dirs <- file.path(base.dir, strftime(dates, "%Y/%m/%d"))
    return(unlist(lapply(dirs, dir, pattern="\\.log$", full.names=TRUE)))
}
