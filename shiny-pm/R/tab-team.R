get_team_activity <- function (df, date=Sys.Date()) {
    # For the week of `date`
    thisweek <- get_week_range(date)
    # This currently only checks for tickets completed. But it should also look for
    # comments and checklist items checked
    df <- filter(df, listName %in% c(building, "Done"))

    # Map trello cards to epics
    epics <- get_epics_from_desc(df$desc)
    stories <- safely_get_stories(
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

    # Look at milestones and comments
    df$milestones <- filter_this_week(df$milestones)
    df$comments <- filter_this_week(df$comments)
    # Subset on what we care about
    df <- df[df$tickets > 0 | has_entries(df$milestones) | has_entries(df$comments),]
    # Return a list of tbls to format
    m <- has_entries(df$milestones)
    return(list(
        milestones=df[m,],
        ongoing=df[!m,]
    ))
}

has_entries <- function (col) {
    # For a list column of data.frames, return logical where there are any rows
    vapply(col, NROW, integer(1)) > 0
}

filter_this_week <- function (col, date=Sys.Date()) {
    # Given a list column of data.frames with a $date column, keep only those
    # rows from the requested week.
    if (length(date) != 2) {
        date <- get_week_range(date)
    }
    return(lapply(col, function (x) {
        # Keep only those that are this week
        x[x$date >= date[1] & x$date <= date[2],]
    }))
}

up_next <- function (df) {
    # Return a df of any upcoming milestones for expected features
    df <- filter(df, listName %in% c(specing, "Ready to build", building))
    thisweek <- get_week_range(Sys.Date())
    df$milestones <- lapply(df$milestones, function (x) {
        # Keep only those that are after this week
        x[x$date > thisweek[2],]
    })

    # Take that, get name, url, milestone name, and date.
    # We will sort by date and print the top 10
    miles <- lapply(which(has_entries(df$milestones)), function (i) {
        x <- df$milestones[[i]]
        x$cardName <- df$name[i]
        x$cardUrl <- df$url[i]
        x
    })
    return(bind_rows(miles))
}
