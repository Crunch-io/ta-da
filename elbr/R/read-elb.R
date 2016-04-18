#' Load an ELB log file
#'
#' @param file A file name or connection. See \code{\link[utils]{read.table}}
#' @param stringsAsFactors The standard \code{data.frame} argument, but
#' defaulted to \code{TRUE}.
#' @param ... Additional arguments passed to \code{read.delim}
#' @return A \code{data.frame}.
#' @export
#' @importFrom utils read.delim
read.elb <- function (file, stringsAsFactors=FALSE, ...) {
    read.delim(file,
        sep=" ",
        header=FALSE,
        stringsAsFactors=stringsAsFactors,
        col.names=c("timestamp", "elb", "client_port", "backend_port",
                    "request_processing_time", "backend_processing_time",
                    "response_processing_time", "elb_status_code",
                    "backend_status_code", "received_bytes", "sent_bytes",
                    "request", "user_agent", "ssl_cipher", "ssl_protocol"),
        ...)
}

#' Do some general cleaning
#'
#' Delete some columns we don't care about ever, parse the timestamp,
#' add up response times, separate request verb from URL, etc.
#' @param logdf a \code{data.frame} as returned from \code{\link{read.elb}}
#' @return A \code{data.frame} cleaned up a bit.
#' @export
#' @importFrom lubridate ymd_hms
cleanLog <- function (logdf) {
    ## ELB log timestamps are in microseconds
    op <- options(digits.secs=6)
    on.exit(options(op))

    ## Simplify the user-agent string to either web, R, or python
    ua <- ifelse(grepl("rcrunch", logdf$user_agent), "R", "web")
    ua[logdf$user_agent == "-" | grepl("pycrunch", logdf$user_agent)] <- "python"

    ## Split the 'request' into verb, url, protocol, and keep the first two
    reqs <- as.data.frame(do.call(rbind, strsplit(logdf$request, " ")),
        stringsAsFactors=FALSE)[,1:2]
    names(reqs) <- c("request_verb", "request_url")

    ## Collect the things we want to keep
    out <- cbind(
        timestamp=ymd_hms(logdf$timestamp),
        reqs,
        status_code=logdf$elb_status_code,
        logdf[c("received_bytes", "sent_bytes")],
        response_time=with(logdf, request_processing_time +
            backend_processing_time + response_processing_time),
        user_agent=ua)

    ## -1 response time means the request didn't respond
    out$response_time[out$response_time < 0] <- NA
    return(out)
}
