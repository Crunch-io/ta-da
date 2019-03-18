#' Query the users
#'
#' @param query Optional search string. The superadmin GUI advises: 'Search
#' names and emails, and/or make specific queries of Mongo, like
#' "preferences.labs:true"'
#' @return A data.frame with 4 columns: name, email, account_id, and id.
#' @export
getUsers <- function (query=NULL) {
    if (is.null(query)) {
        out <- superGET(superadminURL("users"))
    } else {
        out <- superGET(superadminURL("users"), query=list(query=query))
    }
    out <- content(out)$users
    if (length(out)) {
        return(as.data.frame(do.call(rbind, out), stringsAsFactors=FALSE))
    } else {
        return(data.frame(name=character(0), email=character(0),
            account_id=character(0), id=character(0), stringsAsFactors=FALSE))
    }
}

#' Get a user record
#'
#' @param id ID of the user to fetch
#' @param query Optional search string. The superadmin GUI advises: 'Search
#' names and emails, and/or make specific queries of Mongo, like
#' "preferences.labs:true"'. If \code{id} is omitted and a query is provided,
#' will call \code{getUsers} to search, and will proceed to GET the user record
#' if the query returns only a single match.
#' @return A list.
#' @export
getUser <- function (id, query) {
    if (missing(id)) {
        users <- getUsers(query=query)
        if (nrow(users) == 1) {
            id <- users$id
        } else {
            stop("Query matched more than one user: ", paste(users$email, sep=", "))
        }
    }
    out <- superGET(superadminURL("users", id))
    return(content(out))
}

#' View and set feature flags for users
#'
#' @param x a user record (list)
#' @param value a list of new attributes to update with. Magically works with
#' \code{$$}. See examples.
#' @return Getter returns the flag elements from the user preferences. Setter
#' returns the user record.
#' @examples
#' \dontrun{
#' featureFlags(u)$notebooks <- TRUE
#' }
#' @export
featureFlags <- function (x) {
    Filter(is.logical, x$user$preferences)
}

#' @importFrom utils modifyList
#' @rdname featureFlags
#' @export
`featureFlags<-` <- function (x, value) {
    x$user$preferences <- modifyList(x$user$preferences, value)
    superPOST(superadminURL("users", x$user$id, "edit"),
        query=list(preferences_json=toJSON(x$user$preferences)))
    return(x)
}

#' @importFrom jsonlite toJSON
toJSON <- function (x, ...) {
    if (is.null(x)) return(structure('{}', class="json"))
    return(jsonlite::toJSON(x, auto_unbox=TRUE, null="null", na="null", force=TRUE, ...))
}
