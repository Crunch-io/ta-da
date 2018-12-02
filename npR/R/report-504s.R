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

#' Categorize URLs by removing specifics
#'
#' Abstract away from entity ids and query specifics to see if certain endpoints
#' generally behave a certain way.
#'
#' @param url character vector of request URLs
#' @return A character vector of equal length containing URLs with the entity
#' IDs and query strings removed.
#' @export
#' @examples
#' standardizeURLs("https://crunch.io/api/datasets/000001/") == standardizeURLs("https://crunch.io/api/datasets/999999/")
standardizeURLs <- function (url) {
    # Remove hostname
    url <- sub("^https?://.*?/", "/", url)
    # Remove leading "api/", if exists
    url <- sub("^/api", "", url)
    # Substitute queryparam
    url <- sub("(.*/)(\\?.*)$", "\\1?QUERY", url)
    # Substitute ids
    url <- gsub("/[0-9A-Z]{4,}/|/[0-9a-f]{32}/", "/ID/", url)
    # But batch ids are integers
    url <- sub("(.*/batches/)[0-9]+(.*)", "\\1ID\\2", url)
    # Remove progress hash
    url <- sub("(.*/progress/.*?)%3.*", "\\1/", url)
    # Remove whaam state hash
    url <- sub("(.*/)[0-9a-zA-Z]+==$", "\\1WHAAM", url)
    url <- sub("(.*\\?variableId=)[0-9a-zA-Z]+(.*)", "\\1ID\\2", url)
    # Prune long segments (which are probably bad requests)
    # (have to track the trailing slash because of how strsplit works)
    trailing_slash <- substr(url, nchar(url), nchar(url)) == "/"
    url <- paste0(vapply(strsplit(url, "/"), function (s) {
        s[nchar(s) > 39] <- "TOOLONG"
        paste(s, collapse="/")
    }, character(1)), ifelse(trailing_slash, "/", ""))
    # In case someone constructs a URL and gives a URL instead of id
    url <- sub("(.*)/https:.*", "\\1/PEBCAK", url)
    return(url)
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
