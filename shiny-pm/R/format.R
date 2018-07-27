format_team_cards <- function (dfs) {
    out <- as.ul(dfs$milestones, format_card, class="ul-top")
    if (NROW(dfs$ongoing)) {
        # We have some cards we're working that don't have milestones this week
        # so include them but with less detail
        out <- tag.append(out,
            li("Ongoing", as.ul(dfs$ongoing, format_card))
        )
    }
    out
}

format_team_coming_cards <- function (df) {
    # This df is a bespoke shape, see up_next()
    formatter <- function (data) {
        li(
            tags$a(href=data$cardUrl, data$cardName),
            data$name,
            format_date(data$date)
        )
    }

    df[order(df$date), ] %>%
        head(10) %>%
        as.ul(formatter, class="ul-top")
}

format_card <- function (df) {
    # df is one-row tibble here
    out <- format_card_short(df)
    details <- ul()
    if (!is.null(df$milestones)) {
        miles <- df$milestones[[1]]
        if (NROW(miles)) {

            for (i in seq_len(nrow(miles))) {
                details <- tag.append(details,
                    li(
                        bold(format_milestone(miles$name[i], miles$date[i], miles$done[i])))
                    )
            }
        }
    }
    if (!is.null(df$comments)) {
        comms <- df$comments[[1]]
        if (NROW(comms)) {
            for (i in seq_len(nrow(comms))) {
                details <- tag.append(details,
                    li(format_comment(comms$comment[i], comms$date[i], comms$member[i])))
            }
        }
    }
    if (length(details$children)) {
        out <- tag.append(out, details)
    }
    return(out)
}

format_card_short <- function (df) {
    out <- div(tags$a(href=df$url, df$name))
    if (!is.null(df$tickets) && df$tickets > 0) {
        out$children <- c(out$children, paste0("(", df$tickets, " tickets)"))
    }
    li(out)
}

format_milestone <- function (name, date, done) {
    if (done) {
        return(paste(name, format_date(date)))
    } else {
        out <- paste(name, "expected", format_date(date))
        if (date <= Sys.Date()) {
            out <- tags$span(out, style="color:#722580")
        }
        return(out)
    }
}

format_comment <- function (comment, date, member) {
    italics(paste(paste0('"', comment, '"'), member, sep=" -- "))
}
