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
        # Collapse to a sequence (remove gaps)
        gantt$track <- match(gantt$track, sort(unique(gantt$track)))
        # Create different bar labels and suppress them for short bars
        gantt$bar_label <- gantt$name
        gantt$bar_label[(gantt$end - gantt$start) < 28] <- NA
    }
    return(gantt)
}

TRELLO_COLORS <- c(
    green="#61bd4f",
    yellow="#f2d600",
    orange="#ff9f1a",
    red="#eb5a46",
    purple="#c377e0",
    blue="#055a8c",
    sky="#00c2e0",
    lime="#51e898"
)

ggantt <- function (df) {
    label_to_color <- structure(TRELLO_COLORS[df$label_color],
        .Names=df$label)[!duplicated(df$label)]
    midpoints <- df$start + round(.5*(df$end - df$start))
    p <- ggplot(
        df,
        aes(
            colour=label,
            text=paste(
                paste0("___", name),
                paste("Start:", format(start, "%d %b %Y")), 
                paste("Expected:", format(end, "%d %b %Y")),
                sep="<br />"
            )
        )
    )
    if (nrow(df)) {
        p <- p +
            # Bars
            geom_segment(aes(x=start, xend=end, y=track, yend=track), size=6) +
            # Labels
            geom_text(
                aes(x=midpoints, y=track, label=bar_label),
                colour=ifelse(df$label_color %in% c("blue"), "#F0F0F0", "#0F0F0F"),
                size=3
            ) +
            # Map labels to Trello colors
            scale_color_manual(values=label_to_color) +
            # TODO: pass in a time window?
            coord_cartesian(
                xlim=c(min(df$start), max(df$end)),
                ylim=c(min(df$track), max(c(df$track, 10)))
            ) +
            scale_x_date(
                date_breaks="1 months",
                labels=function (x) format(x, "%b ‘%y", tz="UTC")
            ) +
            # Line for today
            # TODO: this "alpha" doesn't seem to be working
            geom_segment(aes(x=Sys.Date(), xend=Sys.Date(), y=0, yend=max(c(track, 10)) + 1), size=.25, colour="black", alpha=0.1) +
            # TODO: this should work instead, but plotly isn't showing it while ggplot
            # geom_vline(xintercept=Sys.Date(), size=.25, colour="black") +
            theme_gantt()
    }
    p
}

# Hack the plotly S3 object to fix the tooltips
hack_plotly <- function (p) {
    p$x$data <- lapply(p$x$data, function (z) {
        z$text <- sub("^start:.*<br />___(.*)$", "\\1", z$text)
        if (!isTRUE(z$showlegend)) {
            z$hoverinfo <- "none"
        }
        z
    })
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
