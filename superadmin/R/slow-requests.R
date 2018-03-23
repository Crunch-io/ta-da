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
    out <- superGET(superadminURL("/tracing"), query=query)
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
    # "total_time" is a lie because it is when the client gave up, but zz9 etc.
    # may still update timings.
    x$actual_total_time <- head(df$total, 1)
    attr(df, "meta") <- x[setdiff(names(x), "timings_values")]
    class(df) <- c("SlowRequest", "data.frame")
    return(df)
}

#' @export
print.SlowRequest <- function (x, ..., threshold=10, header=TRUE) {
    if (header) {
        headdata <- formatSRmeta(x)
        h <- c(headdata$headline, headdata$url, paste("User:", headdata$user))
        if (!is.null(headdata$dataset)) {
            h <- c(h, paste("Dataset:", headdata$dataset))
        }
        h <- paste(c(h, "\n"), collapse="\n")
        cat(h)
    }

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

#' @export
formatSRmeta <- function (req, threshold=119) {
    meta <- attr(req, "meta")
    # Keep max actual total time in case there are multiple via groupSRs
    headline <- paste(round(max(meta$actual_total_time), 3), "seconds @", meta$utc)
    url <- paste(meta$request_method, meta$request_path)
    qs <- meta$query_string
    if (!is.null(qs) && nchar(qs)) {
        qs <- ifelse(nchar(qs) > 20, paste0(substr(qs, 1, 17), "..."), qs)
        url <- paste(url, qs, sep="?")
    }
    user <- vapply(unique(meta$user_id), function (i) {
        u <- try(getUser(id=i))
        return(ifelse(inherits(u, "try-error"), i, u$user$email))
    }, character(1))
    base <- superadminURL("/tagging")

    out <- list(
        times=length(meta$actual_total_time),
        headline=headline,
        url=url,
        seealso_url=paste(base, httr:::compose_query(list(
            method=meta$request_method,
            path=meta$request_path,
            threshold=threshold
        )), sep="?"),
        user=user
    )
    dsid <- extractDatasetID(meta$request_path)
    if (!is.na(dsid)) {
        out$dataset <- dsid
        out$seealso_dataset <- paste(base, httr:::compose_query(list(
            method="ANY",
            path=dsid,
            threshold=threshold
        )), sep="?")
        ds <- try(getDatasets(dsid=dsid))
        if (!inherits(ds, "try-error")) {
            out$dataset <- ds$name
        }
    }
    return(out)
}

#' @export
keepRecentSRs <- function (reqs, minutes=60) {
    timestamps <- vapply(reqs, function (x) attr(x, "meta")$utc, character(1))
    dt <- difftime(Sys.time(), from8601(timestamps), units="mins")
    return(reqs[dt < minutes])
}

from8601 <- function (x) {
    ## Crunch timestamps look like "2015-02-12T10:28:05.632000+00:00"

    if (all(grepl("^[0-9]{4}-[0-9]{2}-[0-9]{2}$", na.omit(x)))) {
        ## return Date if resolution == D
        return(as.Date(x))
    }

    ## Check for timezone
    if (any(grepl("+", x, fixed=TRUE))) {
        ## First, strip out the : in the time zone
        x <- sub("^(.*[+-][0-9]{2}):([0-9]{2})$", "\\1\\2", x)
        pattern <- "%Y-%m-%dT%H:%M:%OS%z"
    } else {
        pattern <- "%Y-%m-%dT%H:%M:%OS"
    }
    ## Then parse
    return(strptime(x, pattern, tz="UTC"))
}

#' @export
groupSRs <- function (reqs) {
    ## TODO: this needs testing
    ## Collapse by request_method + request_path; collect times and emails from
    meta <- lapply(reqs, attr, "meta")
    ids <- vapply(meta,
        function (x) paste(x$request_method, x$request_path),
        character(1))
    tab <- sort(table(ids), decreasing=TRUE)
    if (any(tab) > 1) {
        reqs <- lapply(names(tab), function (u) {
            these <- reqs[ids == u]
            ## Get total time from each, keep biggest one
            times <- vapply(meta[ids == u], function (x) x$actual_total_time,
                numeric(1))
            this <- these[[which.max(times)]]
            ## Then collect total times, user_id
            m <- attr(this, "meta")
            m$actual_total_time <- times
            m$user_id <- vapply(meta[ids == u], function (x) x$user_id,
                character(1))
            attr(this, "meta") <- m
            return(this)
        })
    }
    return(reqs)
}
