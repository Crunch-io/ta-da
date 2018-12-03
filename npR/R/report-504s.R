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
        t1 <- table(standardizeURLs(reqs$request_url), reqs$request_verb)
        t2 <- tablulateDatasetsByName(reqs$request_url)

        reportToSlack <- function (obj, send=TRUE) {
            if (send) {
                slack(channel="systems", username="jenkins", icon_emoji=":timer_clock:",
                    text=md(obj))
            } else {
                print(obj)
            }
        }
        reportToSlack(t1, send)
        reportToSlack(t2, send)
    }
}

tablulateDatasetsByName <- function (urls) {
    out <- as.data.frame(sort(table(superadmin::extractDatasetID(urls)), decreasing=TRUE),
        stringsAsFactors=FALSE, row.names="Var1")
    names(out) <- "timeouts"
    out$name <- sapply(rownames(out), function (x) {
        superadmin::getDatasets(dsid=x)$name
    })
    return(out)
}
