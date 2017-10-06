#' @export
userSnapChat <- function (start=end - 1, end=Sys.Date(),
                          subtitle=paste("Usersnaps from", start, "to", end),
                          ...) {
    require(useRsnap)
    end <- as.Date(end)
    start <- as.Date(start)

    offset <- 0
    limit <- 20
    reps <- list()
    last_fetched <- Sys.Date() + 10000
    while (last_fetched > start) {
        reps <- c(reps, getReports(limit=limit, offset=offset))
        created <- as.Date(vapply(reps,
            function (x) substr(x$creation, 1, 10), character(1)))
        last_fetched <- tail(created, 1)
        offset <- offset + limit
    }
    reps <- reps[created >= start & created <= end]

    ## total open, active/untouched (separate sent to pivotal by get on entity)
    closed <- vapply(reps, function (x) x$closed, logical(1))
    untouched <- vapply(reps,
        function (x) !x$closed && length(x$comments) == 0 && is.null(x$assignee),
        logical(1))
    needs_triage <- vapply(reps[untouched], slackURLForUsersnap, character(1))
    active <- vapply(reps[!untouched & !closed], slackURLForUsersnap, character(1))

    color <- ifelse(TRUE, "warning", "good") ## TODO: compare something?
    fields <- list(
        list(
            title="New open reports",
            value=sum(!closed),
            short=TRUE
        ),
        list(
            title="New reports already closed",
            value=sum(closed),
            short=TRUE
        )
    )
    if (length(active)) {
        fields <- c(fields, list(list(
            title=paste(length(active), "reports being handled:"),
            value=paste("* ", active, sep="", collapse="\n"),
            short=FALSE
        )))
    }
    if (length(needs_triage)) {
        fields <- c(fields, list(list(
            title=paste(length(needs_triage), "reports needing triage:"),
            value=paste("* ", needs_triage, sep="", collapse="\n"),
            short=FALSE
        )))
    }
    body <- list(list(
        pretext=subtitle,
        fallback=paste("UserSnapchat", color),
        fields=fields,
        color=color
    ))
    slack(attachments=body, ..., channel="@npr", icon_emoji=":ambulance:", username="UserSnapchat", parsing=NULL)
}

slackURLForUsersnap <- function (x) {
    web_url_root <- "https://usersnap.com/a/#/crunch-io/p"# + project + ticketnr
    u <- file.path(web_url_root, getOption("usersnap.project"), x$ticketnr)
    return(slack_linkify(u, x$subject))
}

# $closed
# active:

#subject
