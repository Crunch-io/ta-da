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
    url <- gsub("/[0-9A-Z]{4,}/|/[0-9a-f]{32}/", "/ID/", url)
    # But batch ids are integers
    url <- sub("(.*/batches/)[0-9]+(.*)", "\\1ID\\2", url)
    # Remove progress hash
    url <- sub("(.*/progress/.*?)%3.*", "\\1/", url)
    # Remove whaam state hash
    url <- sub("(.*/)[0-9a-zA-Z]+==$", "\\1WHAAM", url)
    url <- sub("(.*\\?variableId=)[0-9a-zA-Z]+(.*)", "\\1ID\\2", url)
    # Prune long segments (which are probably bad requests)
    # (have to track the trailing slash because of how strsplit works)
    trailing_slash <- substr(url, nchar(url), nchar(url)) == "/"
    url <- paste0(vapply(strsplit(url, "/"), function (s) {
        s[nchar(s) > 39] <- "TOOLONG"
        paste(s, collapse="/")
    }, character(1)), ifelse(trailing_slash, "/", ""))
    # In case someone constructs a URL and gives a URL instead of id
    url <- sub("(.*)/https:.*", "\\1/PEBCAK", url)
    return(url)
}

ellipsize_middle <- function (str, n=40) {
    # Note: starting with scalar case, TODO generalize
    # TODO: handle edge cases
    size <- nchar(str)
    if (size > n) {
        allowed <- n - 3
        pre <- ceiling(allowed / 2)
        post <- floor(allowed / 2)
        str <- paste0(substr(str, 1, pre), "...", substr(str, size - post + 1, size))
    }
    return(str)
}
