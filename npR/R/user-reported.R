#' Support Reports
#'
#' @param date string a Pivotal date query. See
#' \url{https://www.pivotaltracker.com/help/articles/advanced_search/#search_keywords}.
#' The search query will take that string and search for "accepted:that" and
#' "created:that", plus "label:user-reported".
#' @param subtitle string to use as "pretext" in Slack attachment
#' @param ... additional arguments passed to `slack`
#' @return A `httr` response from the slack POST. Called for side effect of
#' posting in Slack.
#' @examples
#' \dontrun{
#' supportReport("2017/08/14..2017/09/13", channel="#support")
#' supportReport("yesterday", channel="@npr")
#' }
#' @export
supportReport <- function (date="yesterday", subtitle=paste("Date range:", date), ...) {
    search <- paste(date, "label:user-reported")
    accepted <- as.data.frame(pivotaltrackR::getStories(accepted=search))
    created <- as.data.frame(pivotaltrackR::getStories(created=search))

    ## Assess net support stack (created and not iceboxed - accepted)
    new <- sum(created$current_state != "unscheduled")
    done <- nrow(accepted)
    net <- new - done

    ## For new stories, print how many, and which are open
    new_tickets <- !(created$current_state %in% c("accepted", "unscheduled"))

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
    if (sum(new_tickets)) {
        new_tickets <- slack_linkify(created$url[new_tickets],
            created$name[new_tickets])
        fields <- c(fields, list(list(
            title=paste(length(new_tickets), "new open tickets"),
            value=paste("* ", new_tickets, sep="", collapse="\n"),
            short=FALSE
        )))
    }
    body <- list(list(
        pretext=subtitle,
        fallback=paste("Pivotal Tracker Support Report:", color),
        fields=fields,
        color=color
    ))
    slack(attachments=body, ..., channel="@npr", icon_emoji=":ambulance:", username="Pivotal Tracker Support Report", parsing=NULL)
}
