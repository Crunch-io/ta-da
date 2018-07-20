format_cards <- function (df) {
    # This takes a board_cards data frame and returns name (href to trello), plus due date
    # Suitable for turning into a bunch of <li>
    df$dueDate <- strftime(df$due, "%d %b %Y")
    df$dueDate[is.na(df$dueDate)] <- ""
    lapply(seq_len(nrow(df)), function (i) {
        div(
            tags$a(href=df$url[i], df$name[i]),
            df$dueDate[i]
        )
    })
}
