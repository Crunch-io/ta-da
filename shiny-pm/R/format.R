format_cards <- function (df) {
    # This takes a board_cards data frame and returns name (href to trello), plus due date
    # Suitable for turning into a bunch of <li>
    out <- tags$ul()
    out$children <- lapply(seq_len(nrow(df)),
        function (i) format_card(df[i,]))
    out
}

format_card <- function (df) {
    # df is one-row tibble here
    out <- tags$li(tags$a(href=df$url, df$name))
    details <- tags$ul()
    # if (!is.na(df$due)) {
    #     details$children <- c(details$children, list(tags$li(paste("Due", format_date(df$due)))))
    # }
    if (!is.null(df$tickets) && df$tickets > 0) {
        details$children <- c(details$children, list(tags$li(paste(df$tickets, "tickets completed"))))
    }
    if (!is.null(df$milestones)) {
        miles <- df$milestones[[1]]
        if (NROW(miles)) {
            for (i in seq_len(nrow(miles))) {
                details$children <- c(details$children,
                    list(tags$li(format_milestone(miles[i, "name"], miles[i, "date"], miles[i, "state"]))))
            }
        }
    }
    if (length(details$children)) {
        out$children <- c(out$children, list(details))
    }
    return(out)
}

format_milestone <- function (name, date, state) {
    date <- format_date(date)
    if (state == "complete") {
        return(paste(name, date))
    } else {
        return(paste(name, "expected", date))
    }
}
