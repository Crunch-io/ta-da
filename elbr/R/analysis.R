#' Basic summary statistics from a log
#'
#' @param logdf data.frame as returned by \code{\link{cleanLog}}.
#' @return A data.frame with one row.
#' @export
#' @importFrom stats median quantile
summarizeLog <- function (logdf) {
    data.frame(
        requests=nrow(logdf),
        server_errors=sum(logdf$status_code >= 500),
        response_time_mean=mean(logdf$response_time, na.rm=TRUE),
        response_time_median=median(logdf$response_time, na.rm=TRUE),
        response_time_95pctile=quantile(logdf$response_time, .95, na.rm=TRUE)
    )
}
