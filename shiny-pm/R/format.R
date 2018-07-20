format_team_cards <- function (df) {
    # This takes a board_cards data frame and returns name (href to trello), plus due date
    # Suitable for turning into a bunch of <li>
    has_milestones <- vapply(df$milestones, NROW, integer(1)) > 0
    out <- tags$ul()
    out$children <- lapply(which(has_milestones),
        function (i) format_card(df[i,]))
    ongoing <- df[!has_milestones,]
    out$children <- c(out$children, list(tags$li("Ongoing", tags$ul(lapply(seq_len(nrow(ongoing)), function (i) format_card_short(ongoing[i,]))))))
    out
}

format_team_coming_cards <- function (df) {
    df <- df[order(df$date), ]
    tags$ul(lapply(seq_len(min(nrow(df), 10)), function (i) {
        tags$li(
            df$name[i],
            tags$a(href=df$cardUrl[i], df$cardName[i]),
            format_date(df$date[i])
        )
    }))
}

format_card <- function (df) {
    # df is one-row tibble here
    out <- format_card_short(df)
    details <- tags$ul()
    # if (!is.na(df$due)) {
    #     details$children <- c(details$children, list(tags$li(paste("Due", format_date(df$due)))))
    # }
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

format_card_short <- function (df) {
    out <- div(tags$a(href=df$url, df$name))
    if (!is.null(df$tickets) && df$tickets > 0) {
        out$children <- c(out$children, paste0("(", df$tickets, " tickets)"))
    }
    tags$li(out)
}

format_milestone <- function (name, date, state) {
    date <- format_date(date)
    if (state == "complete") {
        return(paste(name, date))
    } else {
        return(paste(name, "expected", date))
    }
}
