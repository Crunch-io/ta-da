#' Pin or unpin a dataset
#'
#' @param dataset_id URL or id of a dataset
#' @return invisibly, the id of the dataset pinned or unpinned
#' @importFrom httr POST
#' @export
pin <- function (dataset_id) {
    superPOST(superadminURL("/datasets/pin"),
        query=list(dsid=datasetURLToId(dataset_id)))
    invisible(dataset_id)
}

#' @rdname pin
#' @export
unpin <- function (dataset_id) {
    superPOST(superadminURL("/datasets/unpin"),
        query=list(dsid=datasetURLToId(dataset_id)))
    invisible(dataset_id)
}

#' @importFrom httr parse_url build_url
superadminURL <- function (path, host=getOption("superadmin.api")) {
    u <- parse_url(host)
    u$path <- path
    return(build_url(u))
}

datasetURLToId <- function (url) {
    ## Parses ID from URL, if a URL. Otherwise just returns url
    sub("^.*?datasets/([0-9a-f]+)/.*$", "\\1", url)
}
