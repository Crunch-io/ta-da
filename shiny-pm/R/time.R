#' @importFrom lubridate ymd
parse_date <- function (x) {
    # We don't care about any timestamp, just keep the date
    ymd(substr(x, 1, 10))
}

#' @importFrom lubridate wday wday<- year isoweek
get_week_range <- function (date) {
    if (wday(date) < 2) {
        # Sunday is wday 1, but we want that to be a part of _last_ week
        date <- date - 7
    }
    # Set wday to Monday
    wday(date) <- 2
    return(c(date, date + 6))
}

same_week <- function (x, date) {
    # x can be vector but date is scalar
    year(x) %in% year(date) & isoweek(x) %in% isoweek(date)
}

format_date <- function (x, now=Sys.Date()) {
    if (x == now) return("Today!")
    if (year(x) == year(now)) {
        if (isoweek(x) == isoweek(now)) {
            fmt <- "%A"
        } else {
            fmt <- "%B %d"
        }
    } else {
        fmt <- "%d %b %Y"
    }

    strftime(x, fmt)
}
