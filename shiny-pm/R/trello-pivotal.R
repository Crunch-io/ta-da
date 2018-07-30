TRELLO_TO_PIVOTAL_USER <- list(
    `58caca25c9a9df1a5e01bbbb`=2194681, # '@xistence'
    `555a0698e4278d8e17f8ba65`=1417930, # '@percious'
    `5556bbc0b1c778789479e952`=1322978  # '@enrique'
)

PIVOTAL_TEAM <- list(
    # '@enrique': self, '@jj', '@cferejohn', '@msteitle', '@jose', '@diana', '@natalia'
    `1322978`=c(1322978, 1143396, 1144452, 1773660, 2225701, 2997296, 3001046),
    # '@percious': self, '@malecki', '@karol', '@slobodan', '@sebastian', '@scanny'
    `1417930`=c(1417930, 1144426, 2256901, 2978511, 3020826, 3069926),
    # '@xistence': self, '@fumanchu', '@jtate', '@amol', '@arivera', '@j1m', '@david'
    `2194681`=c(2194681, 1143654, 1144430, 1940137, 2932377, 2971357, 2978510)
)

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
