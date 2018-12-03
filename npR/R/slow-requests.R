#' Send a useful summary of slow request timings from superadmin to slack
#'
#' @param minutes How big of a window into the past do we care?
#' @param threshold How many seconds is "too slow"? Passed to superadmin query
#' @param max.reports How many reports should we include in the Slack message?
#' @param send Should we send to Slack at all? If not, just prints to screen
#' @param channel Which Slack channel should the report be sent to?
#' @param ... Additional arguments passed to `slack()`
#' @return If `send`, the Slack API response object. If not, then whatever `print`' returns.
#' @export
slowRequestReport <- function (minutes=60, threshold=119, max.reports=5, send=TRUE,
                               channel="#systems", ...) {
    ## Query slow requests, check timestamps, go `minutes` back
    require(superadmin)
    ## Assume no more than 100
    reports <- getSlowRequests(threshold=threshold, limit=100)
    reports <- keepRecentSRs(reports, minutes)
    if (length(reports) == 0) {
        return()
    }
    title <- paste(
        length(reports), "requests >",
        threshold, "s during the last",
        minutes, "m:"
    )

    ## TODO: this function may not be working
    reports <- groupSRs(reports)
    ## TODO: sort by max time, truncate max.reports if necessary
    reports <- head(reports, min(length(reports), max.reports))

    ## Make attachments
    body <- lapply(reports, slackifySRReport)
    if (send) {
        slack(channel=channel, username=title, icon_emoji=":thinking_face:",
            attachments=body, parsing=NULL, ...)
    } else {
        print(body)
    }
}

slackifySRReport <- function (r) {
    ## Take a SlowRequest object and format it as a Slack attachment
    txt <- md(r, header=FALSE)
    h <- formatSRmeta(r)
    url <- paste(h$url, slack_linkify(h$seealso_url, "More of this endpoint"))
    txt <- paste(url, txt, sep="\n")
    headline <- h$headline
    if (h$times > 1) {
        headline <- paste(headline, paste0("(", h$times, " times)"))
    }
    if (is.null(h$dataset)) {
        dataset <- "None"
    } else {
        dataset <- paste(h$dataset,
            slack_linkify(h$seealso_dataset, "More of this dataset"),
            sep="\n")
    }
    return(list(
        pretext=b(headline),
        fields=list(
            list(title="Dataset", value=dataset, short=TRUE),
            list(title="User", value=h$user, short=TRUE)
        ),
        text=txt,
        color="warning",
        mrkdwn_in=c("text", "pretext")
    ))
}
