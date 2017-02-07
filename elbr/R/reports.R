summarize504s <- function (days, before.date=Sys.Date()) {
    dates <- strftime(rev(before.date - seq_len(days)), "%Y/%m/%d")
    df <- do.call(rbind, lapply(dates, find504s))
    if (nrow(df)) {
        df <- cleanLog(df)
        t1 <- table(standardizeURLs(df$request_url), df$request_verb)
        t2 <- as.data.frame(sort(table(extractDatasetID(df$request_url)),
            decreasing=TRUE))
        names(t2) <- "timeouts"
        reportToSlack(t1)
        reportToSlack(t2)
    }
}
