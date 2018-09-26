#' Confirm the user's authentication status
#' 
#' Given the request, determine whether the user is authenticated with
#' Crunch. Set the token if so.  
#' @param cookie Character cookie from the request object
#' @return Logical: `TRUE`/`FALSE` whether authed.
#' @export
#' @importFrom crunch tokenAuth
setToken <- function (cookie) {
    authed <- FALSE
    if (!is.null(cookie)) {
        token <- sub(".*token=([0-9a-f]+).*", "\\1", cookie)
        if (!identical(token, cookie)) {
            # The regex worked, so we have a token
            tokenAuth(token, "hack.crunch.io")
            authed <- TRUE
        }
    }
    return(authed)
}
