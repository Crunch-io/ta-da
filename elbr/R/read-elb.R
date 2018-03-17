#' Load an ELB log file
#'
#' @param file A file name or connection. See [readr::read_delim()]
#' @param columns Optional character vector to specify a subset of columns to
#' import. If you know you only want to work with a few columns, it is faster
#' to specify it at read time rather than filtering after. Unlike the behavior
#' of `read_delim()`'s `col_names`, these may be specified out of order, and the
#' `data.frame` you get back will be in the order you specify.
#'
#' Default is to return everything.
#' @param ... Additional arguments passed to [readr::read_delim()]
#' @return A tibble.
#' @export
#' @importFrom readr read_delim
read_elb <- function (file,
                    columns=c("timestamp", "elb", "client_port", "backend_port",
                            "request_processing_time", "backend_processing_time",
                            "response_processing_time", "elb_status_code",
                            "backend_status_code", "received_bytes", "sent_bytes",
                            "request", "user_agent", "ssl_cipher", "ssl_protocol"),
                    ...) {

    ## Allow specifying only a selection of columns. Fill in "col_types" with "-"
    all_cols <- eval(formals(sys.function())[["columns"]])
    col_types <- unlist(strsplit("Tcccdddiiiicccc", ""))

    columns <- match.arg(columns, several.ok=TRUE)
    keepcols <- all_cols %in% columns
    col_types[!keepcols] <- "-"

    out <- read_delim(
        file,
        col_names=all_cols[keepcols],
        col_types=paste(col_types, collapse=""),
        delim=" ",
        escape_backslash=TRUE,
        escape_double=FALSE,
        na=c("", "-1"),
        ...
    )
    if (!identical(names(out), columns)) {
        ## Reorder
        out <- out[, columns]
    }
    return(out)
}

#' Split the 'request' into verb, url, protocol
#'
#' @param x Character vector, the "request" column from an ELB data.frame
#' @return A `data.frame` with three columns: "request_verb", "request_url",
#' and "request_protocol".
#' @export
parse_request <- function (x) {
    ## Split the 'request' into verb, url, protocol
    reqs <- as.data.frame(matrix(unlist(strsplit(x, " ")), ncol=3, byrow=TRUE),
        stringsAsFactors=FALSE)
    names(reqs) <- c("request_verb", "request_url", "request_protocol")
    return(reqs)
}
