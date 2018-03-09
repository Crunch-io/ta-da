#' Load an ELB log file
#'
#' @param file A file name or connection. See [readr::read_delim()]
#' @param col_names Optional character vector to specify a subset of columns to
#' import. If you know you only want to work with a few columns, it is faster
#' to specify it at read time rather than filtering after. Default is everything.
#' @param ... Additional arguments passed to [readr::read_delim()]
#' @return A tibble.
#' @export
#' @importFrom readr read_delim
read_elb <- function (file,
                    col_names=c("timestamp", "elb", "client_port", "backend_port",
                            "request_processing_time", "backend_processing_time",
                            "response_processing_time", "elb_status_code",
                            "backend_status_code", "received_bytes", "sent_bytes",
                            "request", "user_agent", "ssl_cipher", "ssl_protocol"),
                    ...) {

    ## Allow specifying only a selection of columns. Fill in "col_types" with "-"
    all_cols <- eval(formals(sys.function())[["col_names"]])
    col_types <- unlist(strsplit("Tcccdddiiiicccc", ""))

    keepcols <- all_cols %in% match.arg(col_names, several.ok=TRUE)
    col_types[!keepcols] <- "-"

    readr::read_delim(
        file,
        col_names=all_cols[keepcols],
        col_types=paste(col_types, collapse=""),
        delim=" ",
        escape_backslash=TRUE,
        escape_double=FALSE,
        na=c("", "-1"),
        ...
    )
}

#' Do some general cleaning
#'
#' Delete some columns we don't care about ever, parse the timestamp,
#' add up response times, separate request verb from URL, etc. This was used
#' with the old `read.elb` function, which no longer exists. Timestamp parsing
#' and missingness are already handled by `read_elb`, and columns can be selected
#' in that function, too.
#' @param logdf a `data.frame` as returned from [read_elb()]
#' @return A `data.frame` cleaned up a bit.
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
