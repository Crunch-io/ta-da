summarize504s <- function (days, before.date=Sys.Date(), send=TRUE) {
    dates <- strftime(rev(before.date - seq_len(days)), "%Y/%m/%d")
    df <- do.call(rbind, lapply(dates, find504s))
    if (nrow(df)) {
        require(superadmin)
        df <- cleanLog(df)
        t1 <- table(standardizeURLs(df$request_url), df$request_verb)
        t2 <- as.data.frame(sort(table(extractDatasetID(df$request_url)),
            decreasing=TRUE))
        names(t2) <- "timeouts"
        t2$name <- sapply(rownames(t2), function (x) {
            getDatasets(dsid=x)$name
        })
        reportToSlack(t1, send)
        reportToSlack(t2, send)
        superDisconnect()
    }
}
