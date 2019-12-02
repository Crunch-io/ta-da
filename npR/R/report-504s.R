#' Make a summary of Gateway Timeouts
#'
#' @param days Integer number of days to aggregate
#' @param before.date days before this day. Default is today (i.e. with days=1,
#' give the report for yesterday)
#' @param send Logical: send messages to Slack?
#' @export
#' @importFrom elbr ELBLog line_filter parse_request
#' @importFrom dplyr collect filter select %>%
summarize504s <- function (days, before.date=Sys.Date(), send=TRUE) {
    before.date <- as.Date(before.date)
    df <- ELBLog(before.date - days, before.date - 1) %>%
        line_filter(" -1 -1 504 ") %>%
        select(request, elb_status_code) %>%
        collect()
    if (nrow(df)) {
        require(superadmin)
        reqs <- parse_request(df$request)
        t1 <- tabulatedRequests(reqs)
        t2 <- tablulateDatasetsByName(reqs$request_url)

        reportToSlack <- function (obj, send=TRUE) {
            if (send) {
                slack(channel="app-status", username="jenkins", icon_emoji=":timer_clock:",
                    text=md(obj))
            } else {
                print(obj)
            }
        }
        reportToSlack(t1, send)
        reportToSlack(t2, send)
    }
}

tablulateDatasetsByName <- function (urls, rows=20) {
    tab <- sort(table(superadmin::extractDatasetID(urls)), decreasing=TRUE)
    out <- as.data.frame(tab, stringsAsFactors=FALSE, row.names="Var1")
    names(out) <- "N"
    out$name <- sapply(rownames(out), function (x) {
        # Look up the dataset name, and ellipsize it if it's long
        ellipsize_middle(superadmin::getDatasets(dsid=x)$name, 36)
    })
    if (nrow(out) > rows) {
        # Truncate the list
        out$N[rows] <- sum(out$N[rows:nrow(out)])
        out$name[rows] <- paste0("[", nrow(out) - rows + 1, " others]")
        rownames(out)[rows] <- "and"
        out <- out[seq_len(rows),]
    }
    return(out)
}

tabulatedRequests <- function (reqs) {
    req_urls <- paste(reqs$request_verb, standardizeURLs(reqs$request_url))
    tab <- sort(table(req_urls), decreasing=TRUE)
    return(data.frame(N=as.numeric(tab), row.names=names(tab)))
}
