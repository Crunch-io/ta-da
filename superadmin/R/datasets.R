#' Query the datasets
#'
#' @param ... Optional query parameters. Valid fields include "name", "dsid"
#' (the ID of a dataset), "email" of the owner.
#' @return A data.frame with 4 columns: name, email, account_id, and id.
#' @importFrom httr content
#' @export
getDatasets <- function (...) {
    query <- list(...)
    if (length(query)) {
        out <- superGET(superadminURL("datasets"), query=query)
    } else {
        out <- superGET(superadminURL("datasets"))
    }
    out <- content(out)$datasets
    col.names <- c("id", "name", "description", "archived",
        "project_name", "project_id")
    if (length(out)) {
        df <- as.data.frame(do.call(rbind, lapply(out,
            function (x) {
                x$project_name <- x$project$name
                x$project_id <- x$project$id
                return(x)
            })), stringsAsFactors=FALSE)
        ## Return the ones we care about. Intersect in order to future proof
        return(df[intersect(col.names, names(df))])
    } else {
        return(as.data.frame(sapply(col.names,
            function (x) character(0), simplify=FALSE), stringsAsFactors=FALSE))
    }
}

#' Get the dataset ID from a URL
#'
#' @param url character vector of request URLs or URL segments
#' @return A character vector of equal length containing the dataset IDs, or
#' \code{NA} if the url contains no dataset ID.
#' @export
#' @examples
#' extractDatasetID("http://crunch.io/datasets/8159d0c4e26fef8ea371a2d9338ceb91/")
#' is.na(extractDatasetID("http://crunch.io/users/"))
extractDatasetID <- function (url) {
    # Look for "/datasets/" (API) or "/dataset/" (whaam browser URLs)
    dsid <- sub("^.*?datasets?/([0-9a-f]{32})/.*$", "\\1", url)
    # If there is no dataset ID, return NA
    is.na(dsid) <- dsid == url
    return(dsid)
}
