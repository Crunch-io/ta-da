#' Get the dataset ID from a URL
#'
#' @param url character vector of request URLs
#' @return A character vector of equal length containing the dataset IDs, or
#' \code{NA} if the url contains no dataset ID.
#' @export
#' @examples
#' extractDatasetID("http://crunch.io/datasets/8159d0c4e26fef8ea371a2d9338ceb91/")
#' is.na(extractDatasetID("http://crunch.io/users/"))
extractDatasetID <- function (url) {
    # Look for "/datasets/" (API) or "/dataset/" (whaam browser URLs)
    dsid <- sub("^.*/datasets?/([0-9a-f]{32})/.*$", "\\1", url)
    # If there is no dataset ID, return NA
    is.na(dsid) <- dsid == url
    return(dsid)
}

#' Categorize URLs by removing specifics
#'
#' Abstract away from entity ids and query specifics to see if certain endpoints
#' generally behave a certain way.
#'
#' @param url character vector of request URLs
#' @return A character vector of equal length containing URLs with the entity
#' IDs and query strings removed.
#' @export
#' @examples
#' standardizeURLs("https://crunch.io/api/datasets/000001/") == standardizeURLs("https://crunch.io/api/datasets/999999/")
standardizeURLs <- function (url) {
    # Remove hostname
    url <- sub("^https?://.*?/", "/", url)
    # Remove leading "api/", if exists
    url <- sub("^/api", "", url)
    # Substitute queryparam
    url <- sub("(.*/)(\\?.*)$", "\\1?QUERY", url)
    # Substitute ids
    url <- gsub("/[0-9X]+/|/[0-9a-f]{32}/", "/ID/", url)
    # Remove progress hash
    url <- sub("(.*/progress/.*?)%3.*", "\\1/", url)
    # Remove whaam state hash
    url <- sub("(.*/)[0-9a-zA-Z]+==$", "\\1WHAAM", url)
    # Prune long segments (which are probably bad requests)
    # (have to track the trailing slash because of how strsplit works)
    trailing_slash <- substr(url, nchar(url), nchar(url)) == "/"
    url <- paste0(vapply(strsplit(url, "/"), function (s) {
        s[nchar(s) > 39] <- "TOOLONG"
        paste(s, collapse="/")
    }, character(1)), ifelse(trailing_slash, "/", ""))
    return(url)
}
