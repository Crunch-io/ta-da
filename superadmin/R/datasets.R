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
    col.names <- c("id", "name", "description", "archived",
        "owner_name", "owner_type", "owner_id")
    if (length(out)) {
        df <- as.data.frame(do.call(rbind, lapply(out,
            function (x) {
                x$owner_name <- x$owner$name
                return(x)
            })), stringsAsFactors=FALSE)
        ## Return the ones we care about. Intersect in order to future proof
        return(df[intersect(col.names, names(df))])
    } else {
        return(as.data.frame(sapply(col.names,
            function (x) character(0), simplify=FALSE), stringsAsFactors=FALSE))
    }
}

datasetURLToId <- function (url) {
    ## Parses ID from URL, if a URL. Otherwise just returns url
    sub("^.*?datasets/([0-9a-f]+)/.*$", "\\1", url)
}
