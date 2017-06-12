# s <- getStories(search="(created:-7days..today OR accepted:-7days..today) label:user-reported")
#
# table(s$current_state)
#
# get reported (yesterday, last week)
# get accepted (time)
#
# count accepted, count reported (by state?), net (excluding icebox?)
#
# of those accepted, difftime between created and accepted
#
# of new ones, search for [...], which means it hasn't been processed from usersnap (do this for daily only), and print their URLs in slack
#
# also note triage (unstarted vs. unscheduled)

#' Support Reports
#' @param date string Pivotal date query
#' @param subtitle string to use as "pretext" in Slack attachment
#' @param ... additional arguments passed to `slack`
#' @return A `httr` response from the slack POST.
#' @importFrom pivotaltrackR getStories
#' @export
supportReport <- function (date="yesterday", subtitle=paste("Date range:", date), ...) {
    search <- paste(date, "label:user-reported")
    accepted <- as.data.frame(getStories(accepted=search))
    created <- as.data.frame(getStories(created=search))

    ## Assess net support stack (created and not iceboxed - accepted)
    new <- sum(created$current_state != "unscheduled")
    done <- nrow(accepted)
    net <- new - done

    ## For new stories, print how many,
    ## For new tickets, check for ones that have the raw usersnap title
    needs_triage <- grepl("[...]", created$name, fixed=TRUE)
    needs_triage <- slack_linkify(created$url[needs_triage],
        created$name[needs_triage])

    color <- ifelse(net > 0, "warning", "good")
    fields <- list()
    fields <- c(fields, list(
        list(
            title="New active tickets",
            value=new,
            short=TRUE
        ),
        list(
            title="Net tickets",
            value=net,
            short=TRUE
        )))
    if (done) {
        ## For accepted stories, print how many, plus names and age of tickets
        a <- data.frame(name=slack_linkify(accepted$url, accepted$name),
            age=difftime(accepted$accepted_at, accepted$created_at, units="days"))
        fields <- c(fields, list(list(
            title=paste(done, "accepted tickets"),
            value=paste("* ", a$name, " (", round(a$age, 1), " days old)", sep="", collapse="\n"),
            short=FALSE
        )))
    }
    if (length(needs_triage)) {
        fields <- c(fields, list(list(
            title=paste(length(needs_triage), "tickets needing triage:"),
            value=paste("* ", needs_triage, sep="", collapse="\n"),
            short=FALSE
        )))
    }
    body <- list(list(
        pretext=subtitle,
        fallback=paste("Support Report:", color),
        fields=fields,
        color=color
    ))
    slack(attachments=body, ..., channel="@npr", icon_emoji=":ambulance:", username="Support Report", parsing=NULL)
}


slack_linkify <- function (href, text) {
    if (length(href) && length(text)) {
        return(paste0("<", href, "|", text, ">"))
    } else {
        return(character(0))
    }
}
