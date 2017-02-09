reportToSlack <- function (obj, send=TRUE) {
    if (send) {
        slack(channel="systems", username="jenkins", icon_emoji=":timer_clock:",
            text=md(obj))
    } else {
        print(obj)
    }
}

#' @importFrom httr POST add_headers
#' @importFrom jsonlite toJSON
slack <- function (...) {
    # ''' Send a message to our Slack team
    #
    #     kwargs:
    #     * `text` message
    #     * `channel` to post in
    #     * `username` to post as
    #     * `icon_emoji` to use for username
    # '''
    u = "https://hooks.slack.com/services/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"
    kwargs <- list(...)
    if (!(substr(kwargs$channel, 1, 1) %in% c("#", "@"))) {
        kwargs$channel <- paste0("#", kwargs$channel)
    }
    kwargs$parse <- "full"
    POST(u, body=toJSON(kwargs, auto_unbox=TRUE),
        config=add_headers(`Content-Type`="application/json"))
}

#' @importFrom utils capture.output
md <- function (df) {
    paste0("```\n", paste(capture.output(print(df)), collapse="\n"), "\n```")
}
