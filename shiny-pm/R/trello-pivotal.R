get_epics_from_desc <- function (desc) {
    # Parse trello card description and look for reference to a pivotal epic
    lapply(strsplit(desc, "\n"), function (x) {
        piv <- grep("^Pivotal epic", x, value=TRUE)
        if (length(piv)) {
            # This allows that there may be more than one epic per card
            epics <- sub("^Pivotal epic: ?", "", piv)
            return(unlist(strsplit(epics, ", ?")))
        } else {
            return(character(0))
        }
    })
}

#' @importFrom pivotaltrackR getStories
safely_get_stories <- function (...) {
    # Treat error as length-0 query result, so that if Pivotal is down or if
    # we're offline, it doesn't error
    tryCatch(getStories(...), error=function (e) list())
}
