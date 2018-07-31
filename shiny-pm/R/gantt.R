prep_gantt_data <- function (df) {
    # Take trello cards df and prepare data for ggplotting
    gantt <- df %>%
        filter(!is.na(due)) %>%
        filter(listName %in% c(building, specing, "Done", "Ready to build")) %>%
        mutate(
            start=sapply(milestones, function (x) {
                if ("Kickoff" %in% x$name) {
                    x$date[x$name == "Kickoff"]
                } else {
                    min(x$date)
                }
            }),
            end=due,
            label=vapply(labels, function (x) head(x, 1)$name, character(1)),
            label_color=vapply(labels, function (x) head(x, 1)$color, character(1))
        ) %>%
        select(name, start, end, label, label_color)
    if (nrow(gantt)) {
        # bc sapply drops the class
        gantt$start <- as.Date(gantt$start, origin="1970-01-01")
        # If only one date (due date), back-date it two months (TODO: flag these)
        gantt$start[gantt$start == gantt$end] <- gantt$end[gantt$start == gantt$end] - 60
        # Group tracks
        gantt <- gantt[order(gantt$end),]
        gantt$track <- seq_len(nrow(gantt))
        for (i in gantt$track[-1]) {
            cands <- gantt$end[1:i] < gantt$start[i] & !duplicated(gantt$track[1:i], fromLast=TRUE)
            if (any(cands)) {
                gantt$track[i] <- gantt$track[which(cands)[1]]
            }
        }
        print(gantt$track)
        # Collapse to a sequence (remove gaps)
        gantt$track <- match(gantt$track, sort(unique(gantt$track)))
    }

    return(gantt)
}

ggantt <- function (df) {
    p <- ggplot(df, aes(colour=label, text=name))
    if (nrow(df)) {
        p <- p +
            # Line for today
            geom_segment(aes(x=Sys.Date(), xend=Sys.Date(), y=min(track), yend=max(track)), size=.25, colour="black") +
            # Bars
            geom_segment(aes(x=start, xend=end, y=track, yend=track), size=6) +
            # Labels
            geom_text(aes(x=start + round(.5*(end - start)), y=track, label=name), colour="black", size=3) +
            theme_gantt()
    }
    p
}

# Modified from https://stats.andrewheiss.com/misc/gantt.html
theme_gantt <- function (base_size=11) {
    theme_bw(base_size) %+replace%
        theme(
            panel.background = element_rect(fill="#ffffff", colour=NA),
            axis.title.x=element_blank(),
            axis.title.y=element_blank(),
            title=element_text(vjust=1.2),
            panel.border = element_blank(),
            axis.line=element_blank(),
            panel.grid.minor=element_blank(),
            panel.grid.major.y = element_blank(),
            panel.grid.major.x = element_line(size=0.5, colour="grey80"),
            axis.ticks=element_blank(),
            axis.text.y=element_blank(),
            legend.position="bottom",
            axis.title=element_text(size=rel(0.8)),
            strip.text=element_text(size=rel(1)),
            strip.background=element_rect(fill="#ffffff", colour=NA),
            panel.spacing.y=unit(1.5, "lines"),
            legend.key = element_blank()
        )
}
