#' Perform some analysis across a bunch of ELB log files
#'
#' @param FUN A function to map over each log data frame
#' @param start_date `Date` or date string specifying a starting point for
#' finding log files. Use `NULL`, the default, to get all log files.
#' @param end_date `Date` or date string to close the range. Default is
#' `start_date`, i.e. it takes all log files for a single day, if one is given.
#' @param files Vector of file names to read in; an alternative to specifying
#' date ranges.
#' @param select_vars logical: should we only read in the variables named in
#' `FUN`? Default is `TRUE`, which provides a speed boost by not loading data
#' we don't need for the current analysis, but in cases where `FUN` doesn't
#' name every variable we want to keep, set this to `FALSE`.
#' @param results For `reduceELB`, the results of `mapELB`
#' @param ... Arguments passed to `mapELB`
#' @return A list of query results.
#' @export
analyzeELB <- function (...) reduceELB(mapELB(...))

#' @export
#' @rdname analyzeELB
#' @importFrom parallel mclapply
mapELB <- function (FUN, start_date=NULL, end_date=start_date, files=find_log_files(start_date, end_date), select_vars=TRUE) {
    ## Only keep the columns we need
    ## Note that if FUN just wants to return a data.frame with all cols, this would fail unless it referenced the cols by name
    if (select_vars) {
        cnames <- all.vars(body(FUN))
    } else {
        cnames <- eval(formals(read_elb)[["columns"]])
    }
    parallel::mclapply(files, function (f) FUN(read_elb(f, columns=cnames)))
}

#' @export
#' @rdname analyzeELB
#' @importFrom dplyr bind_rows
reduceELB <- function (results) {
    # n, .count, .mean, .table
    if (is.data.frame(results[[1]])) {
        return(bind_rows(results))
    }
    measures <- names(results[[1]])
    out <- lapply(measures, function (m) {
        if (m == "n" || endsWith(m, "_count")) {
            sum(vapply(results, function (x) x[[m]], integer(1)))
        } else if (endsWith(m, "_max")) {
            max(vapply(results, function (x) x[[m]], numeric(1)))
        } else if (endsWith(m, "_mean")) {
            ## Weight by n, then we'll divide by that sum
            sum(vapply(results, function (x) x[[m]] * x[["n"]], numeric(1)))
        } else if (endsWith(m, "_table")) {
            sumTables(lapply(results, function (x) x[[m]]))
        } else {
            ## Concatenate
            unlist(lapply(results, function (x) x[[m]]))
        }
    })
    names(out) <- measures

    ## divide means by n
    means <- endsWith(names(out), "_mean")
    out[means] <- lapply(out[means], function (x) x / out[["n"]])
    out
}

sumTables <- function (list_of_tables) {
    ## Assuming 1d table for now
    allnames <- sort(unique(unlist(lapply(list_of_tables, names))))
    tbl <- array(
        rep(0L, length(allnames)),
        dim=length(allnames),
        dimnames=list(allnames)
    )
    out <- Reduce(function (x, y) {
        x[names(y)] <- x[names(y)] + y
        x
    }, list_of_tables, init=tbl)

    structure(
        array(
            out,
            dim=length(out),
            dimnames=structure(list(names(out)), .Names="")
        ),
        class="table"
    )
}
