slack_url <- "https://hooks.slack.com/services/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"

#' @importFrom httr POST add_headers
#' @importFrom jsonlite toJSON
slack <- function (..., parsing="full") {
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
    kwargs$parse <- parsing
    POST(slack_url, body=toJSON(kwargs, auto_unbox=TRUE),
        config=add_headers(`Content-Type`="application/json"))
}

#' Context to capture errors and report them in slack
#'
#' @param expr Code to evaluate in the context
#' @return The output of expr. If any error is hit, the error message will go to
#' Slack.
#' @export
#' @importFrom utils tail
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

slack_linkify <- function (href, text) {
    # Make links that the Slack webhook will render correctly
    if (length(href) && length(text)) {
        return(paste0("<", href, "|", text, ">"))
    } else {
        return(character(0))
    }
}
