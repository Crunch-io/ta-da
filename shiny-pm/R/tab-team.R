this_week <- function (df) {
    get_team_activity(df, Sys.Date())
}

last_week <- function (df) {
    # Same as this week, just last week
    get_team_activity(df, Sys.Date() - 7L)
}

#' @importFrom pivotaltrackR getStories
#' @importFrom lubridate ymd
get_team_activity <- function (df, date) {
    # For the week of `date`
    thisweek <- get_week_range(date)
    # This currently only checks for tickets completed. But it should also look for
    # comments and checklist items checked
    df <- filter(df, listName %in% c(building, "Done"))

    # Map trello cards to epics
    epics <- get_epics_from_desc(df$desc)
    stories <- getStories(
        label=epics[nchar(epics) > 0],
        accepted=paste(strftime(thisweek, "%Y/%m/%d"), collapse="..")
    )
    # Join on counts of tickets
    if (length(stories)) {
        ticket_counts <- table(unlist(strsplit(as.data.frame(stories)$label, ", ")))
        df$tickets <- ticket_counts[epics]
        df$tickets[is.na(df$tickets)] <- 0
    } else {
        df$tickets <- rep(0L, min(1L, nrow(df)))
    }

    # Look at milestones
    df$milestones <- lapply(df$milestones, function (x) {
        # Keep only those that are this week
        x[x$date >= thisweek[1] & x$date <= thisweek[2],]
    })
    # and comments
    df$comments <- lapply(df$comments, function (x) {
        # Keep only those that are this week
        x[x$date >= thisweek[1] & x$date <= thisweek[2],]
    })
    return(df[df$tickets > 0 | has_entries(df$milestones) | has_entries(df$comments),])
}

has_entries <- function (col) {
    # For a list column of data.frames, return logical where there are any rows
    vapply(col, NROW, integer(1)) > 0
}

up_next <- function (df) {
    # This currently is scheduled cards that aren't yet "building"
    # It should be any upcoming milestones, not just due dates
    thisweek <- get_week_range(Sys.Date())
    df$milestones <- lapply(df$milestones, function (x) {
        # Keep only those that are after this week
        x[x$date > thisweek[2],]
    })
    today <- Sys.Date()
    df <- filter(df, listName %in% c(specing, "Ready to build", building))

    ## Take that, get name, url, milestone name (or due), and date. Sort by date. Print the top 10?
    miles <- lapply(which(has_entries(df$milestones)), function (i) {
        x <- df$milestones[[i]]
        x$cardName <- df$name[i]
        x$cardUrl <- df$url[i]
        x
    })
    miles <- bind_rows(miles)
    return(bind_rows(miles))
}
