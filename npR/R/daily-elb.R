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
    body$title <- paste("ELB summary for", date_range_label(start, end))
    icon <- elb_icon_emoji(body[[1]]$color, perfect = results$n_5xx == 0)
    if (send) {
        slack(
            channel="systems",
            username="jenkins",
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
                    n_web=sum(segment == "Web app")
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
            max_time=max(max_time),
            pct_5xx=100*n_5xx/n_requests,
            pct_under200ms=100*sum(n_under200ms)/n_requests,
            mean_time=sum(total_time)/n_requests
        )
}

slackELBBody <- function (results) {
    pct_reqs <- function (num, denom=results$n_requests, ...) {
        pct <- format(100*num/denom, ...)
        paste(
            format(num, big.mark=","),
            paste0("(", pct, "%)")
        )
    }
    fields <- list(
        short_field("Total request count", format(results$n_requests, big.mark=",")),
        short_field("Number of 5XXs", pct_reqs(results$n_5xx, nsmall=4)),
        short_field("Number of 504s", format(results$n_504, big.mark=",")),
        short_field("Profiles request count", pct_reqs(results$n_profiles, nsmall=1)),
        short_field("Other Web app requests", pct_reqs(results$n_web, nsmall=1)),
        short_field("Stream request count", pct_reqs(results$n_stream, nsmall=1)),
        short_field("Requests under 200ms (%)", format(results$pct_under200ms, nsmall=1)),
        short_field("Mean request time", format(results$mean_time, nsmall=3)),
        short_field("Max request time", format(results$max_time, nsmall=3))
    )
    color <- nines_to_color(results$pct_5xx)
    return(list(list(
        fallback=paste("ELB summary:", color),
        fields=fields,
        color=color
    )))
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
