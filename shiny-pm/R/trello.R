trello_cards <- function (board_url, token) {
    # comms=get_board_comments(board_url, token)
    miles <-
        get_board_checklists(board_url, token) %>%
        filter(name == "Milestones")
    lists <- get_board_lists(board_url, token)
    comms <- get_board_comments(board_url, token)

    cards <- get_board_cards(board_url, token) %>%
        mutate(
            dateLastActivity=parse_date(dateLastActivity),
            due=parse_date(due)
        ) %>%
        left_join(
            data_frame(
                id=miles$idCard,
                milestones=lapply(miles$checkItems, parse_milestones)
            )
        ) %>%
        left_join(
            data_frame(
                idList=lists$id,
                listName=lists$name,
                listPos=lists$pos
            )
        ) %>%
        left_join(parse_comments(comms))
    # Sort the cards so that the lists are right to left, and then within each,
    # top to bottom
    cards <- cards[order(-cards$listPos, cards$pos),]
    # Add a row to milestones for the due dates
    cards$milestones <- lapply(seq_len(nrow(cards)), function (i) {
        out <- cards$milestones[[i]]
        if (!is.na(cards$due[i])) {
            due <- data_frame(name="Done", date=cards$due[i], done=cards$dueComplete[i])
            if (NROW(out)) {
                out <- bind_rows(out, due)
            } else {
                out <- due
            }
        }
        return(out)
    })
    return(cards)
}

parse_milestones <- function (miles) {
    # For each milestones checklist, parse dates
    miles$date <- suppressWarnings(
        ymd(sub(".*([0-9]{4}-[0-9]{2}-[0-9]{2})$", "\\1", miles$name))
    )
    # Keep only those with dates set?
    miles <- miles[!is.na(miles$date),]
    # Remove date from milestone name
    miles$name <- sub(":? [0-9]{4}-[0-9]{2}-[0-9]{2}$", "", miles$name)
    # Turn state into a logical
    miles$done <- miles$state == "complete"
    return(miles[, c("name", "date", "done")])
}

parse_comments <- function (comms) {
    # Look for date in data.text, overwrite date
    date_in_text <- grepl("^[0-9]{4}-[0-9]{2}-[0-9]{2}", comms$data.text)
    comms$date[date_in_text] <- sub(
        "^([0-9]{4}-[0-9]{2}-[0-9]{2}).*",
        "\\1",
        comms$data.text[date_in_text]
    )
    comms$data.text[date_in_text] <- sub(
        "^[0-9]{4}-[0-9]{2}-[0-9]{2}:? ",
        "",
        comms$data.text[date_in_text]
    )
    # parse date
    df <- data_frame(
        id=comms$data.card.id,
        comment=comms$data.text,
        date=parse_date(comms$date),
        member=comms$memberCreator.fullName
    )
    out <- split(df, df$id)
    return(data_frame(
        id=names(out),
        comments=out
    ))
}
