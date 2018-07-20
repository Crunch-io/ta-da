specing <- c("1. Define the problem", "2. Brainstorm solutions", "3. Product spec",
                         "4. Technical spec")
building <- c("5. Build minimum testable version", "6. Building and finishing",
                            "7. Announcing")

filter_lists <- function (.data, list_names) {
    # Trello board_cards have lists by id; map list names to ids and filter
    .data[list_filter(.data, list_names),]
}

list_filter <- function (.data, list_names) {
    # This just constructs the filter but returns a logical vector, not the filtered data
    # c("Inbox", "Revisit later", "Backlog", "1. Define the problem",
    #     "2. Brainstorm solutions", "3. Product spec", "4. Technical spec",
    #     "Ready to build", "5. Build minimum testable version", "6. Building and finishing",
    #     "7. Announcing", "Done")
    list_map <- get_lists()
    .data$idList %in% list_map$id[list_map$name %in% list_names]
}

get_lists <- function () {
    # Hack.
    getOption("shinypm.lists")
}
