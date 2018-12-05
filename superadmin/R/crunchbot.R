#' Run code and cat the result as JSON
#' @param expr Code to run
#' @param ... Additional arguments passed to [jsonlite::toJSON()]
#' @return Invisibly, the return of `expr`
#' @export
crunchbot <- function (expr, ...) {
    out <- force(expr)
    cat(toJSON(out, unbox=TRUE, ...))
    invisible(out)
}
