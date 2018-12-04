#' Generate a daily, weekly, whatever summary of web traffic
#' @inheritParams summarize504s
#' @export
#' @importFrom dplyr mutate summarize case_when if_else
elbSummary <- function (days, before.date=Sys.Date(), send=TRUE, ...) {
    before.date <- as.Date(before.date)
    start <- before.date - days
    end <- before.date - 1

    results <- computeELBSummary(start, end)
    body <- slackELBBody(results)
    body[[1]]$title <- paste("ELB summary for", date_range_label(start, end))
    icon <- elb_icon_emoji(body[[1]]$color, perfect = results$n_5xx == 0)
    if (send) {
        slack(
            channel="systems",
            username="crunchbot",
            icon_emoji=icon,
            attachments=body,
            ...
        )
    } else {
        print(body)
    }
}

computeELBSummary <- function (start, end) {
    # Map over the log files and get the data
    ELBLog(start, end) %>%
        select(
            request,
            elb_status_code,
            request_processing_time,
            backend_processing_time,
            response_processing_time,
            user_agent
        ) %>%
        collect(function (x) {
            # Per ELB file, do this
            x %>%
                mutate(
                    time=request_processing_time + backend_processing_time + response_processing_time,
                    time=if_else(is.na(time), 120, time),
                    segment=case_when(
                        grepl("POST.*/stream/", request) ~ "Stream",
                        grepl("profiles.*\\.crunch\\.io", request) ~ "Profiles",
                        grepl("WebKit|Firefox|Trident", user_agent) ~ "Web app",
                        grepl("scrunch", user_agent) ~ "Scrunch",
                        grepl("pycrunch", user_agent) ~ "Other pycrunch",
                        grepl("rcrunch", user_agent) ~ "R",
                        TRUE ~ "Other"
                    )
                ) %>%
                summarize(
                    # Only return a single row of partial aggregates
                    n_requests=n(),
                    n_5xx=sum(elb_status_code > 499),
                    n_504=sum(elb_status_code == 504),
                    total_time=sum(time),
                    max_time=max(time[elb_status_code != 504]),
                    n_under200ms=sum(time < .2),
                    n_stream=sum(segment == "Stream"),
                    n_profiles=sum(segment == "Profiles"),
                    n_web=sum(segment == "Web app"),
                    n_state=sum(grepl("GET.*/state/", request))
                )
            }
        ) %>%
        summarize(
            # Then reduce over the per-file quantities
            n_requests=sum(n_requests),
            n_5xx=sum(n_5xx),
            n_504=sum(n_504),
            n_stream=sum(n_stream),
            n_profiles=sum(n_profiles),
            n_web=sum(n_web),
            n_state=sum(n_state),
            max_time=max(max_time),
            pct_5xx=100*n_5xx/n_requests,
            pct_under200ms=100*sum(n_under200ms)/n_requests,
            mean_time=sum(total_time)/n_requests
        )
}

slackELBBody <- function (results) {
    pct_reqs <- function (num, digits=0, denom=results$n_requests, ...) {
        pct <- pretty(100*num/denom, digits, ...)
        paste(
            pretty(num),
            paste0("(", pct, "%)")
        )
    }
    fields <- list(
        short_field("Total request count", pretty(results$n_requests)),
        short_field("5XX errors", pct_reqs(results$n_5xx, 4)),
        short_field("504 errors", pretty(results$n_504)),
        short_field("Requests under 200ms (%)", pretty(results$pct_under200ms, 1)),
        short_field("Profiles requests", pct_reqs(results$n_profiles, 1)),
        short_field("Other web app requests", pct_reqs(results$n_web, 1)),
        short_field("Stream requests", pct_reqs(results$n_stream, 1)),
        short_field("State polling requests", pct_reqs(results$n_state, 1)),
        short_field("Mean request time", pretty(results$mean_time, 3)),
        short_field("Max request time", pretty(results$max_time, 3))
    )
    color <- nines_to_color(results$pct_5xx)
    return(list(list(
        fallback=paste("ELB summary:", color),
        fields=fields,
        color=color
    )))
}

pretty <- function (num, digits=0, ...) {
    format(round(num, digits), big.mark=",", nsmall=digits)
}

nines_to_color <- function (error_pct) {
    if (error_pct < 0.01) {
        return("good")
    } else if (error_pct < 0.1) {
        return("warning")
    } else {
        return("danger")
    }
}

elb_icon_emoji <- function (color, perfect=FALSE) {
    if (perfect) {
        base <- "parrot"
    } else {
        base <- list(
            good="simple_smile",
            warning="worried",
            danger="scream_cat"
        )[[color]]
    }
    return(paste0(":", base, ":"))
}

date_range_label <- function (start, end) {
    # ''' Pretty format a label for the range of dates'''
    daterange <- strftime(start, "%B %d")
    if (start != end) {
        daterange <- paste(daterange, "to", strftime(end, "%B %d"))
    }
    return(daterange)
}
