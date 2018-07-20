this_week <- function (df) {
    get_active_cards(df, Sys.Date())
}

last_week <- function (df) {
    # Same as this week, just last week
    get_active_cards(df, Sys.Date() - 7L)
}

#' @importFrom pivotaltrackR getStories
get_active_cards <- function (df, date) {
    # For the week of `date`
    # This currently only checks for tickets completed. But it should also look for
    # comments and checklist items checked
    df <- filter_lists(df, c(building, "Done"))
    # Map trello cards to epics
    epics <- get_epics_from_desc(df$desc)
    stories <- getStories(
        label=epics[nchar(epics) > 0],
        accepted=paste(strftime(get_week_range(date), "%Y/%m/%d"), collapse="..")
    )
    # Join on counts of tickets
    if (length(stories)) {
        ticket_counts <- table(unlist(strsplit(as.data.frame(stories)$label, ", ")))
        df$tickets <- ticket_counts[epics]
        df$tickets[is.na(df$tickets)] <- 0
    } else {
        df$tickets <- 0L
    }
    return(df[df$tickets > 0,])
}

up_next <- function (df) {
    # This currently is scheduled cards that aren't yet "building"
    # It should be any upcoming milestones, not just due dates
    today <- Sys.Date()
    df <- filter_lists(df, c(specing, "Ready to build"))
    df[year(df$due) >= year(today) & isoweek(df$due) > isoweek(today) & !is.na(df$due), ]
}
