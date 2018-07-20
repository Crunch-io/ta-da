trello_cards <- function (board_url, token) {
    # comms=get_board_comments(board_url, token)
    miles <-
        get_board_checklists(board_url, token) %>%
        filter(name == "Milestones")
    lists <- get_board_lists(board_url, token)

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
        left_join(data_frame(idList=lists$id, listName=lists$name))

    return(cards)
}

parse_milestones <- function (miles) {
    # For each milestones checklist, parse dates
    miles$date <- suppressWarnings(
        ymd(sub(".*([0-9]{4}-[0-9]{2}-[0-9]{2})$", "\\1", miles$name))
    )
    # Remove date from milestone name
    miles$name <- sub(":? [0-9]{4}-[0-9]{2}-[0-9]{2}$", "", miles$name)
    return(miles[, c("name", "date", "state")])
}
