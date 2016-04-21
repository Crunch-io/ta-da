#' Aggregate over a log data.frame by a unit of time
#'
#' @param logdf data.frame as returned by \code{\link{cleanLog}}. Or rather,
#' a data.frame with a "timestamp" variable that is a datetime class.
#' @param unit character unit of time, passed to
#' \code{\link[lubridate]{floor_date}}.
#' @param FUN function to apply to each chunk of \code{logdf}. Default is
#' \code{\link{summarizeLog}}.
#' @return A data.frame with the time values as the rownames.
#' @export
#' @importFrom lubridate floor_date
byRollup <- function (logdf, unit=c("second", "minute", "hour", "day", "week",
                      "month", "year", "quarter"), FUN=elbr:::summarizeLog) {

    dfs <- split(logdf, lubridate::floor_date(logdf$timestamp, match.arg(unit)))
    do.call(rbind, lapply(dfs, FUN))
}
