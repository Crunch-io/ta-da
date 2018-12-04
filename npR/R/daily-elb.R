#' Generate a daily, weekly, whatever summary of web traffic
#' @inheritParams summarize504s
#' @export
#' @importFrom dplyr mutate summarize case_when if_else
elbSummary <- function (days, before.date=Sys.Date(), send=TRUE) {
    before.date <- as.Date(before.date)
    start <- before.date - days
    end <- before.date - 1
    # Map over the log files and get the data
    df <- ELBLog(start, end) %>%
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
                    max_time=max(time),
                    n_under200ms=sum(time < .2),
                    n_stream=sum(segment == "Stream")
                )
            }
        ) %>%
        summarize(
            # Then reduce over the per-file quantities
            n_requests=sum(n_requests),
            n_5xx=sum(n_5xx),
            n_504=sum(n_504),
            n_stream=sum(n_stream),
            max_time=max(max_time),
            pct_5xx=100*n_5xx/n_requests,
            pct_under200ms=100*sum(n_under200ms)/n_requests,
            mean_time=sum(total_time)/n_requests
        )

    report <- slackELBReport(results)
    body <- report$body
    body$title <- paste("ELB summary for", date_range_label(start, end))
    if (send) {
        slack(channel="systems", username="jenkins",
            icon_emoji=report$icon_emoji, attachments=body, ...)
    } else {
        print(body)
    }
}

slackELBReport <- function (results) {
    if (results$pct_5xx < 0.001) {
        ## Five nines!
        color <- "good"
        icon_emoji <- ifelse(summary['sum_500s'] == 0, ":parrot:", ":sunglasses:")
    } else if (results$pct_5xx < 0.01) {
        color <- "good"
        icon_emoji <- ":simple_smile:"
    } else if (results$pct_5xx < 0.1) {
        ## Three nines
        color <- "warning"
        icon_emoji <- ":worried:"
    } else {
        color <- "danger"
        icon_emoji <- ":scream_cat:"
    }

    with(results,
        fields <- list(
            short_field("Total request count", n_requests),
            short_field("Number of 5XXs", n_5xx),
            short_field("Number of 504s", n_504),
            short_field("5XX error rate (%)", round(pct_5xx, 4)),
            short_field("Stream request count", n_stream),
            short_field("Requests under 200ms (%)", round(pct_under200ms, 1)),
            short_field("Mean request time", round(mean_time, 3)),
            short_field("Max request time", round(max_time, 3)),
        )
    )
    body <- list(list(
        fallback=paste("ELB summary:", color),
        fields=fields,
        color=color
    ))
    return(list(body=body, icon_emoji=icon_emoji))
}

date_range_label <- function (start, end) {
    # ''' Pretty format a label for the range of dates'''
    daterange <- strftime(start, "%B %d")
    if (start != end) {
        daterange <- paste(daterange, "to", strftime(end, "%B %d"))
    }
    return(daterange)
}
