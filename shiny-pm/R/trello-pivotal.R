get_epics_from_desc <- function (desc) {
    # Parse trello card description and look for reference to a pivotal epic
    vapply(strsplit(desc, "\n"), function (x) {
        piv <- grep("^Pivotal epic", x, value=TRUE)
        if (length(piv)) {
            # TODO: allow more than one epic per card
            return(sub("^Pivotal epic: ?", "", piv[1]))
        } else {
            return("")
        }
    }, character(1))
}

#' @importFrom pivotaltrackR getStories
safely_get_stories <- function (...) {
    # Treat error as length-0 query result, so that if Pivotal is down or if
    # we're offline, it doesn't error
    tryCatch(getStories(...), error=function (e) list())
}
