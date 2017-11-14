#' Query the slow requests catalog
#'
#' @param method HTTP verb, or "ANY" for any
#' @param path URL segment string to filter the results on, e.g. "stream" or "13deb231a"
#' @param threshold numeric cutoff value for the timing to include. Only requests taking longer than `threshold` will be included
#' @param limit integer number of requests to return
#' @return A list of `SlowRequest` data.frame objects.
#' @export
getSlowRequests <- function (method="ANY", path=NULL, threshold=NULL, limit=10) {
    query <- Filter(Negate(is.null), list(
        method=method,
        path=path,
        threshold=threshold,
        limit=limit
    ))
    out <- superGET(superadminURL("/tagging"), query=query)
    out <- content(out)$logs
    if (length(out)) {
        # Parse the results into "SlowRequest" data.frames with metadata
        out <- lapply(out, SlowRequest)
    }
    return(out)
}

#' Construct a SlowRequest data.frame
#' @param x a log entry as returned by `getSlowRequests()`
#' @return A `SlowRequest` object
#' @keywords internal
#' @export
SlowRequest <- function (x) {
    # Turn "timings_values" (sic) into a data.frame
    times <- x$timings_values
    tag <- vapply(times, function (a) a[[1]], character(1))
    df <- cbind(tag, as.data.frame(do.call(rbind,
        lapply(times, function (a) unlist(a[[2]][c("count", "min", "max", "total")])))))

    # Sort and arrange it
    df$pct <- 100 * df$total / df$total[df$tag == ""]
    df <- df[order(df$pct, decreasing=TRUE), c("pct", "total", "count", "max", "tag")]
    rownames(df) <- df$tag
    df$tag <- NULL

    # Include the other request metadata and set an attribute
    attr(df, "meta") <- x[setdiff(names(x), "timings_values")]
    class(df) <- c("SlowRequest", "data.frame")
    return(df)
}

#' @export
print.SlowRequest <- function (x, ..., threshold=10) {
    meta <- attr(x, "meta")
    headline <- paste(round(meta$total_time, 3), "seconds @", meta$utc)
    url <- paste(meta$request_method, meta$request_path)
    if (!is.null(meta$query_string) && nchar(meta$query_string)) {
        url <- paste(url, meta$query_string, sep="?")
    }
    user <- try(getUser(id=meta$user_id))
    user <- paste("User:",
        ifelse(inherits(user, "try-error"), meta$user_id, user$user$email))
    dsid <- datasetURLToId(meta$request_path)
    if (!identical(dsid, meta$request_path)) {
        ds <- try(getDatasets(dsid=dsid))
        if (!inherits(ds, "try-error")) {
            ds <- paste("Dataset:", ds$name)
            user <- paste(user, ds, sep="\n")
        }
    }
    cat(headline, url, user, "", sep="\n")

    class(x) <- "data.frame"
    keep <- x$pct > threshold
    x <- x[keep,]
    x$pct <- round(x$pct, 0)
    x$total <- round(x$total, 3)
    x$max <- round(x$total, 3)
    print(x)
    if (!all(keep)) {
        cat("...\n")
    }
}
