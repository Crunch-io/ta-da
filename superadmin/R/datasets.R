#' Query the datasets
#'
#' @param ... Optional query parameters. Valid fields include "name", "dsid"
#' (the ID of a dataset), "email" of the owner.
#' @return A data.frame with 4 columns: name, email, account_id, and id.
#' @importFrom httr GET content
#' @export
getDatasets <- function (...) {
    query <- list(...)
    if (length(query)) {
        out <- superGET(superadminURL("/datasets"), query=query)
    } else {
        out <- superGET(superadminURL("/datasets"))
    }
    out <- content(out)$datasets
    col.names <- c("id", "name", "description", "archived", "pinned",
        "owner_name", "owner_type", "owner_id")
    if (length(out)) {
        return(as.data.frame(do.call(rbind, lapply(out,
            function (x) {
                x$owner_name <- x$owner$name
                return(x)
            })), stringsAsFactors=FALSE)[col.names])
    } else {
        return(as.data.frame(sapply(col.names,
            function (x) character(0), simplify=FALSE), stringsAsFactors=FALSE))
    }
}
