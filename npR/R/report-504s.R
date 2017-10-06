#' Make a summary of Gateway Timeouts
#'
#' @param days Integer number of days to aggregate
#' @param before.date days before this day. Default is today (i.e. with days=1,
#' give the report for yesterday)
#' @param send Logical: send messages to Slack?
#' @export
#' @importFrom elbr cleanLog standardizeURLs extractDatasetID
summarize504s <- function (days, before.date=Sys.Date(), send=TRUE) {
    dates <- strftime(rev(before.date - seq_len(days)), "%Y/%m/%d")
    df <- do.call(rbind, lapply(dates, find504s))
    if (nrow(df)) {
        require(superadmin)
        df <- cleanLog(df)
        t1 <- table(standardizeURLs(df$request_url), df$request_verb)
        t2 <- tablulateDatasetsByName(df$request_url)

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
    out <- as.data.frame(sort(table(extractDatasetID(urls)), decreasing=TRUE),
        stringsAsFactors=FALSE, row.names="Var1")
    names(out) <- "timeouts"
    out$name <- sapply(rownames(out), function (x) {
        superadmin::getDatasets(dsid=x)$name
    })
    return(out)
}
