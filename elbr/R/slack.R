reportToSlack <- function (obj, send=TRUE) {
    if (send) {
        slack(channel="systems", username="jenkins", icon_emoji=":timer_clock:",
            text=md(obj))
    } else {
        print(obj)
    }
}

slack_url <- "https://hooks.slack.com/services/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"

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

    kwargs <- list(...)
    if (!(substr(kwargs$channel, 1, 1) %in% c("#", "@"))) {
        kwargs$channel <- paste0("#", kwargs$channel)
    }
    kwargs$parse <- "full"
    POST(slack_url, body=toJSON(kwargs, auto_unbox=TRUE),
        config=add_headers(`Content-Type`="application/json"))
}

#' Context to capture errors and report them in slack
#'
#' @param expr Code to evaluate in the context
#' @return The output of expr. If any error is hit, the error message will go to
#' Slack.
#' @export
with_slack_errors <- function (expr) {
    tryCatch(expr, error=function (e) {
        code <- deparse(tail(sys.calls(), 5)[[1]][[2]])
        msg <- paste0("Error in `", code, "`: ", e$message)
        slack(channel="systems", username="jenkins", icon_emoji=":interrobang:",
            text=msg)
    })
}

#' @importFrom utils capture.output
md <- function (df) {
    paste0("```\n", paste(capture.output(print(df)), collapse="\n"), "\n```")
}
