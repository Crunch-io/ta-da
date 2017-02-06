#' Query the users
#'
#' @param query Optional search string. The superadmin GUI advises: 'Search
#' names and emails, and/or make specific queries of Mongo, like
#' "preferences.labs:true"'
#' @return A data.frame with 4 columns: name, email, account_id, and id.
#' @importFrom httr GET content
#' @export
getUsers <- function (query=NULL) {
    if (is.null(query)) {
        out <- superGET(superadminURL("/users"))
    } else {
        out <- superGET(superadminURL("/users"), query=list(query=query))
    }
    out <- content(out)$users
    if (length(out)) {
        return(as.data.frame(do.call(rbind, out), stringsAsFactors=FALSE))
    } else {
        return(data.frame(name=character(0), email=character(0),
            account_id=character(0), id=character(0), stringsAsFactors=FALSE))
    }
}
