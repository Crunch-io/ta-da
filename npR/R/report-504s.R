#' Make a summary of Gateway Timeouts
#'
#' @param days Integer number of days to aggregate
#' @param before.date days before this day. Default is today (i.e. with days=1,
#' give the report for yesterday)
#' @param send Logical: send messages to Slack?
#' @export
#' @importFrom elbr cleanLog standardizeURLs extractDatasetID find504s
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

slowRequestReport <- function (minutes=60, max.reports=5, send=FALSE,
                               channel="#systems", ...) {
    ## Query slow requests, check timestamps, go `minutes` back
    require(superadmin)
    ## Assume no more than 100
    reports <- getSlowRequests(threshold=119, limit=100)
    reports <- keepRecentSRs(reports, minutes)
    if (length(reports) == 0) {
        return()
    }

    reports <- groupSRs(reports)
    ## TODO: sort by max time, truncate max.reports if necessary (but report how many)

    ## Prepare reports
    out <- lapply(reports, md, header=FALSE)
    heads <- lapply(reports, formatSRmeta)
    heads <- lapply(heads, slackifySRhead)
    obj <- paste(heads, out, sep="\n", collapse="\n\n")
    if (send) {
        slack(channel=channel, username="crunchbot", icon_emoji=":thinking_face:",
            text=obj, parsing=NULL, ...)
    } else {
        cat(obj)
    }
}

slackifySRhead <- function (headdata) {
    h <- b(headdata$headline)
    if (headdata$times > 1) {
        h <- paste(h, paste0("(", headdata$times, " times)"))
    }
    h <- c(
        h,
        paste(headdata$url, slack_linkify(headdata$seealso_url, "More of this endpoint")),
        paste(b("User:"), paste(headdata$user, collapse=", "))
    )
    if (!is.null(headdata$dataset)) {
        h <- c(h, paste(b("Dataset:"), headdata$dataset,
            slack_linkify(headdata$seealso_dataset, "More of this dataset")))
    }
    return(paste(c(h, "\n"), collapse="\n"))
}

# h <- c(headdata$headline, headdata$url, paste("User:", headdata$user))
# if (!is.null(headdata$dataset)) {
#     h <- c(h, paste("Dataset:", headdata$dataset))
# }
# h <- paste(c(h, "\n"), collapse="\n")
